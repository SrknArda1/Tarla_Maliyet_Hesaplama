# ============================================================
#  app.py  -  FLASK WEB UYGULAMASI (ANA DOSYA)
# ------------------------------------------------------------
#  Bu dosya web sunucusudur. Tarayicidan gelen istekleri
#  karsilar, analiz.py'ye hesap yaptirir, sonucu HTML
#  sablonuyla birlestirip kullaniciya gosterir.
#
#  LARAVEL <-> FLASK karsiligi (sana tanidik gelsin diye):
#    Route::get('/yol', ...)   ->  @app.route("/yol")
#    Controller fonksiyonu     ->  route altindaki def
#    Blade view (.blade.php)   ->  Jinja2 sablon (.html)
#    return view('ad', $veri)  ->  return render_template("ad.html", veri=...)
#    $request->input('alan')   ->  request.form.get("alan")
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, send_file
import io                      # bellekte dosya olusturmak icin (Excel/CSV indirme)
import analiz                  # kendi analiz modulumuz (analiz.py)
import gorseller               # kendi grafik modulumuz (gorseller.py)

# Flask uygulamasini baslat. __name__ Flask'a dosya konumunu bildirir.
app = Flask(__name__)


# OZEL JINJA FILTRESI: sablonda {{ deger|tl }} yazinca sayiyi
# "12.500 TL" gibi okunakli bicime cevirir. (Laravel'deki @ benzeri
# bir yardimci; binlik ayraci nokta, ondalik atilir.)
@app.template_filter("tl")
def tl_bicimle(deger):
    try:
        return f"{float(deger):,.0f}".replace(",", ".") + " TL"
    except (ValueError, TypeError):
        return str(deger)


# ------------------------------------------------------------
#  ANA SAYFA  ->  http://127.0.0.1:5000/
#  Tum kayitlari tablo halinde + ozet kutularini gosterir.
# ------------------------------------------------------------
@app.route("/")
def anasayfa():
    df = analiz.verileri_oku()                  # CSV'yi oku + hesaplari yap
    istatistik = analiz.genel_istatistik(df)    # numpy ile genel ozet

    # DataFrame'i sablonda dongu ile basabilmek icin sozluk listesine cevir.
    # to_dict("records") -> [{sutun: deger, ...}, {...}] formati verir.
    kayitlar = df.to_dict("records")

    return render_template(
        "anasayfa.html",
        kayitlar=kayitlar,
        istatistik=istatistik,
    )


# ------------------------------------------------------------
#  VERI EKLEME  ->  http://127.0.0.1:5000/ekle
#  GET  : bos formu gosterir
#  POST : formu kaydeder ve ana sayfaya yonlendirir
# ------------------------------------------------------------
@app.route("/ekle", methods=["GET", "POST"])
def ekle():
    if request.method == "POST":
        # Form gonderildi -> veriyi CSV'ye yaz
        analiz.yeni_kayit_ekle(request.form)
        # Kayittan sonra ana sayfaya don (PRG: Post-Redirect-Get deseni)
        return redirect(url_for("anasayfa"))

    # GET istegi -> bos formu goster
    return render_template("ekle.html")


# ------------------------------------------------------------
#  KAYIT SILME  ->  /sil/3  gibi
#  <int:kayit_id> = URL'deki sayiyi parametre olarak alir.
# ------------------------------------------------------------
@app.route("/sil/<int:kayit_id>")
def sil(kayit_id):
    analiz.kayit_sil(kayit_id)
    return redirect(url_for("anasayfa"))


# ------------------------------------------------------------
#  ANALIZ SAYFASI  ->  /analiz
#  Grafikleri uretir, tarla/urun ozet tablolarini ve sezon
#  karsilastirmasini gosterir. Sezon/tarla/urun ile filtrelenir.
# ------------------------------------------------------------
@app.route("/analiz")
def analiz_sayfasi():
    df_tum = analiz.verileri_oku()

    # URL'den filtre parametrelerini al: /analiz?sezon=2024&urun=Bugday
    # request.args -> URL'deki ? sonrasi degerler (Laravel: $request->query()).
    sezon = request.args.get("sezon", "Hepsi")
    tarla = request.args.get("tarla", "Hepsi")
    urun = request.args.get("urun", "Hepsi")

    # Secilen filtreye gore veriyi daralt
    df = analiz.filtrele(df_tum, sezon, tarla, urun)

    # Filtre sonucu bos olabilir; o zaman grafik uretme (hata vermesin)
    grafikler = {}
    if not df.empty:
        grafikler = gorseller.tum_grafikleri_uret(df, analiz)

    # Pivot tabloyu sablona uygun hale getir
    pivot = analiz.pivot_tablo(df) if not df.empty else None

    # Sezon karsilastirma (merge ornegi)
    _, sezon_karsilastirma = analiz.sezonlari_birlestir(df_tum)

    return render_template(
        "analiz.html",
        grafikler=grafikler,
        istatistik=analiz.genel_istatistik(df) if not df.empty else None,
        tarla_ozeti=analiz.tarlaya_gore_ozet(df).to_dict("records") if not df.empty else [],
        urun_ozeti=analiz.urune_gore_ozet(df).to_dict("records") if not df.empty else [],
        sezon_ozeti=analiz.sezon_karsilastirma(df).to_dict("records") if not df.empty else [],
        # filtre menulerini doldurmak icin tum benzersiz degerler
        sezon_listesi=sorted(df_tum["sezon"].astype(str).unique()),
        tarla_listesi=sorted(df_tum["tarla_adi"].unique()),
        urun_listesi=sorted(df_tum["urun_adi"].unique()),
        secili={"sezon": sezon, "tarla": tarla, "urun": urun},
        # pivot tablo: sutun adlari + satirlar
        pivot_sutunlar=list(pivot.columns) if pivot is not None else [],
        pivot_satirlar=pivot.reset_index().to_dict("records") if pivot is not None else [],
        karsilastirma=sezon_karsilastirma.to_dict("records") if sezon_karsilastirma is not None else [],
    )


# ------------------------------------------------------------
#  CSV RAPORU INDIRME  ->  /rapor/csv?sezon=2024 ...
#  Filtrelenmis veriyi CSV dosyasi olarak indirir.
# ------------------------------------------------------------
@app.route("/rapor/csv")
def rapor_csv():
    df = analiz.verileri_oku()
    df = analiz.filtrele(
        df,
        request.args.get("sezon", "Hepsi"),
        request.args.get("tarla", "Hepsi"),
        request.args.get("urun", "Hepsi"),
    )

    # DataFrame'i bellekte CSV metnine cevir (diske yazmadan).
    cikti = io.BytesIO()
    cikti.write(df.to_csv(index=False).encode("utf-8-sig"))  # utf-8-sig: Turkce karakter
    cikti.seek(0)

    return send_file(
        cikti,
        mimetype="text/csv",
        as_attachment=True,                 # tarayicida acma, indir
        download_name="maliyet_raporu.csv",
    )


# ------------------------------------------------------------
#  EXCEL RAPORU INDIRME  ->  /rapor/excel?sezon=2024 ...
#  Filtrelenmis veriyi .xlsx Excel dosyasi olarak indirir.
# ------------------------------------------------------------
@app.route("/rapor/excel")
def rapor_excel():
    df = analiz.verileri_oku()
    df = analiz.filtrele(
        df,
        request.args.get("sezon", "Hepsi"),
        request.args.get("tarla", "Hepsi"),
        request.args.get("urun", "Hepsi"),
    )

    # DataFrame'i bellekte Excel dosyasina yaz (openpyxl motoru ile).
    cikti = io.BytesIO()
    with pd_excel_writer(cikti) as writer:
        df.to_excel(writer, index=False, sheet_name="Maliyet Raporu")
    cikti.seek(0)

    return send_file(
        cikti,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="maliyet_raporu.xlsx",
    )


def pd_excel_writer(buffer):
    """Excel yazici nesnesi olusturur (openpyxl motorunu kullanir)."""
    import pandas as pd
    return pd.ExcelWriter(buffer, engine="openpyxl")


# ------------------------------------------------------------
#  UYGULAMAYI BASLAT
#  Bu blok sadece dosya DOGRUDAN calistirilinca devreye girer
#  (python app.py). debug=True -> kod degisince otomatik yenile.
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

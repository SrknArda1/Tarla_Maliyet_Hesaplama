# ============================================================
#  analiz.py  -  VERI ISLEME VE ANALIZ KATMANI
# ------------------------------------------------------------
#  Bu dosya projenin "beyni"dir. Flask (app.py) sadece web
#  isini yapar; tum hesap, gruplama ve analiz BURADA olur.
#  Laravel'deki "Model" katmanina benzer dusunebilirsin.
#
#  Kullanilan kutuphaneler:
#    - pandas : tablolu veri (CSV) okuma, gruplama, pivot
#    - numpy  : sayisal hesaplar (ortalama, std, min, max)
# ============================================================

import os
import pandas as pd      # pandas'i kisaca "pd" diye cagiririz (gelenek)
import numpy as np       # numpy'i kisaca "np" diye cagiririz (gelenek)

# CSV dosyamizin yolu. __file__ = bu dosyanin konumu.
# Boylece proje hangi klasorden calistirilirsa calistirilsin yol dogru olur.
DOSYA_YOLU = os.path.join(os.path.dirname(__file__), "veri", "kayitlar.csv")

# Maliyet kalemlerimizin sutun adlari. Tek yerde tanimlayip her yerde
# kullanmak, ileride yeni kalem eklemeyi kolaylastirir.
MALIYET_SUTUNLARI = [
    "maliyet_tohum",
    "maliyet_gubre",
    "maliyet_ilac",
    "maliyet_sulama",
    "maliyet_iscilik",
    "maliyet_makine",
]


def verileri_oku():
    """
    CSV dosyasini okur ve uzerine HESAPLANMIS sutunlar ekler.
    Geriye bir pandas DataFrame dondurur (DataFrame = Excel tablosu gibi).

    Eklenen sutunlar:
      - toplam_maliyet  : 6 maliyet kaleminin toplami
      - toplam_gelir    : hasat miktari * satis fiyati
      - kar_zarar       : gelir - maliyet
      - durum           : "Kar" / "Zarar" metni
      - maliyet_kategori: "Dusuk" / "Orta" / "Yuksek"  (pd.cut ile)
    """
    # 1) CSV'yi oku. read_csv satir satir okuyup tabloya cevirir.
    df = pd.read_csv(DOSYA_YOLU)

    # 2) VERI TEMIZLEME: bos (NaN) maliyet hucrelerini 0 yap.
    #    Kullanici formda bir kalemi bos birakirsa program patlamaz.
    for sutun in MALIYET_SUTUNLARI:
        df[sutun] = df[sutun].fillna(0)

    # 3) TOPLAM MALIYET: 6 maliyet sutununu yatayda topla.
    #    axis=1 -> "satir boyunca topla" demektir (her tarla icin ayri).
    df["toplam_maliyet"] = df[MALIYET_SUTUNLARI].sum(axis=1)

    # 4) TOPLAM GELIR: hasat miktari (kg) * kg basina satis fiyati.
    #    Iki sutunu carpinca pandas otomatik satir satir carpar.
    df["toplam_gelir"] = df["hasat_miktari_kg"] * df["satis_fiyati_kg"]

    # 5) KAR / ZARAR: gelir - maliyet. Pozitifse kar, negatifse zarar.
    df["kar_zarar"] = df["toplam_gelir"] - df["toplam_maliyet"]

    # 6) DURUM metni: numpy.where -> "kosul dogruysa A, degilse B".
    #    SQL'deki CASE WHEN ... THEN ... ELSE ... mantiginin aynisi.
    df["durum"] = np.where(df["kar_zarar"] >= 0, "Kar", "Zarar")

    # 7) MALIYET KATEGORISI: pd.cut bir sayi sutununu "araliklara" boler.
    #    Burada toplam maliyeti 3 dilime ayirip etiket veriyoruz.
    #    Sunumdaki "Dusuk / Orta / Yuksek" maddesi tam olarak budur.
    df["maliyet_kategori"] = pd.cut(
        df["toplam_maliyet"],
        bins=[0, 40000, 80000, float("inf")],   # araliklar: 0-40bin, 40-80bin, 80bin+
        labels=["Dusuk", "Orta", "Yuksek"],
    )

    return df


def tarlaya_gore_ozet(df):
    """
    TARLAYA GORE TOPLAM MALIYET TABLOSU (sunumdaki 1. cikti).
    groupby = SQL'deki GROUP BY. Ayni tarla adina sahip satirlari
    tek grupta toplar.
    """
    ozet = df.groupby("tarla_adi").agg(
        kayit_sayisi=("id", "count"),
        toplam_maliyet=("toplam_maliyet", "sum"),
        toplam_gelir=("toplam_gelir", "sum"),
        kar_zarar=("kar_zarar", "sum"),
    ).reset_index()   # reset_index: grup adini tekrar normal sutun yapar

    # En cok kar edenden en aza dogru sirala
    ozet = ozet.sort_values("kar_zarar", ascending=False)
    return ozet


def urune_gore_ozet(df):
    """
    URUNE GORE KAR/ZARAR OZETI (sunumdaki 2. cikti).
    Ayni mantik, bu sefer urun adina gore grupluyoruz.
    """
    ozet = df.groupby("urun_adi").agg(
        kayit_sayisi=("id", "count"),
        toplam_maliyet=("toplam_maliyet", "sum"),
        toplam_gelir=("toplam_gelir", "sum"),
        kar_zarar=("kar_zarar", "sum"),
    ).reset_index()
    ozet = ozet.sort_values("kar_zarar", ascending=False)
    return ozet


def maliyet_kalemleri_toplami(df):
    """
    6 maliyet kaleminin GENEL toplamini hesaplar.
    Pasta grafigi (maliyet dagilimi) bu veriyi kullanir.
    Geriye {kalem_adi: toplam} seklinde bir sozluk doner.
    """
    sonuc = {}
    for sutun in MALIYET_SUTUNLARI:
        # "maliyet_tohum" -> "Tohum"  (okunakli etiket)
        etiket = sutun.replace("maliyet_", "").capitalize()
        sonuc[etiket] = float(df[sutun].sum())
    return sonuc


def sezon_karsilastirma(df):
    """
    SEZON BAZLI KARSILASTIRMA (sunumdaki 3. cikti).
    Her sezon icin toplam maliyet, gelir ve kari hesaplar.
    """
    ozet = df.groupby("sezon").agg(
        toplam_maliyet=("toplam_maliyet", "sum"),
        toplam_gelir=("toplam_gelir", "sum"),
        kar_zarar=("kar_zarar", "sum"),
    ).reset_index()
    return ozet


def pivot_tablo(df):
    """
    PIVOT TABLO: satirlar = tarla, sutunlar = urun, hucreler = kar/zarar.
    Hangi tarlada hangi urunun ne kadar kar ettigini tek bakista gosterir.
    Excel'deki "Ozet Tablo" ozelliginin Python karsiligidir.
    """
    pv = pd.pivot_table(
        df,
        index="tarla_adi",       # satirlar
        columns="urun_adi",      # sutunlar
        values="kar_zarar",      # hucre degeri
        aggfunc="sum",           # ayni hucreye birden cok kayit duserse topla
        fill_value=0,            # bos hucreleri 0 yap
    )
    return pv


def sezonlari_birlestir(df):
    """
    SEZONLAR ARASI VERI BIRLESTIRME - merge ve concat ornegi
    (sunumdaki "merge ve concat" maddesi).

    1) Veriyi sezona gore iki ayri tabloya boluyoruz.
    2) concat ile alt alta tekrar birlestiriyoruz (dikey birlestirme).
    3) merge ile iki sezonun ozetini YAN YANA getiriyoruz (yatay birlestirme),
       boylece "2024 kari vs 2025 kari" karsilastirmasi cikar.
    """
    sezonlar = sorted(df["sezon"].unique())   # ornek: [2024, 2025]

    # --- concat ornegi: parcalari alt alta birlestir ---
    parcalar = [df[df["sezon"] == s] for s in sezonlar]
    birlesik = pd.concat(parcalar, ignore_index=True)

    # --- merge ornegi: ilk iki sezonun urun bazli karini yan yana koy ---
    karsilastirma = None
    if len(sezonlar) >= 2:
        s1, s2 = sezonlar[0], sezonlar[1]

        sol = df[df["sezon"] == s1].groupby("urun_adi")["kar_zarar"].sum().reset_index()
        sol = sol.rename(columns={"kar_zarar": f"kar_{s1}"})

        sag = df[df["sezon"] == s2].groupby("urun_adi")["kar_zarar"].sum().reset_index()
        sag = sag.rename(columns={"kar_zarar": f"kar_{s2}"})

        # merge: iki tabloyu "urun_adi" sutunundan eslestir (SQL JOIN gibi)
        karsilastirma = pd.merge(sol, sag, on="urun_adi", how="outer").fillna(0)
        karsilastirma["fark"] = karsilastirma[f"kar_{s2}"] - karsilastirma[f"kar_{s1}"]

    return birlesik, karsilastirma


def genel_istatistik(df):
    """
    NUMPY ILE GENEL ISTATISTIK.
    Sunumda "NumPy ile maliyet hesaplamalari" yaziyor; iste o kisim.
    Kar/zarar sutununu numpy dizisine cevirip istatistik cikariyoruz.
    """
    kar = df["kar_zarar"].to_numpy()              # pandas sutunu -> numpy dizisi
    maliyet = df["toplam_maliyet"].to_numpy()

    return {
        "kayit_sayisi": int(len(df)),
        "toplam_maliyet": float(np.sum(maliyet)),
        "toplam_kar": float(np.sum(kar)),
        "ortalama_kar": float(np.mean(kar)),       # numpy: ortalama
        "std_kar": float(np.std(kar)),             # numpy: standart sapma
        "en_yuksek_kar": float(np.max(kar)),       # numpy: en buyuk
        "en_dusuk_kar": float(np.min(kar)),        # numpy: en kucuk
        "karli_kayit": int(np.sum(kar >= 0)),      # kar >= 0 olanlarin sayisi
        "zararli_kayit": int(np.sum(kar < 0)),
    }


def filtrele(df, sezon=None, tarla=None, urun=None):
    """
    Veriyi sezon / tarla / urun'e gore filtreler.
    Parametre None ise o filtre uygulanmaz. CSV-Excel raporu ve
    analiz sayfasindaki filtreleme bu fonksiyonu kullanir.
    """
    sonuc = df
    if sezon and sezon != "Hepsi":
        # CSV'den okununca sezon sayi olabilir; metne cevirip karsilastir
        sonuc = sonuc[sonuc["sezon"].astype(str) == str(sezon)]
    if tarla and tarla != "Hepsi":
        sonuc = sonuc[sonuc["tarla_adi"] == tarla]
    if urun and urun != "Hepsi":
        sonuc = sonuc[sonuc["urun_adi"] == urun]
    return sonuc


def yeni_kayit_ekle(form):
    """
    Web formundan gelen veriyi CSV'ye YENI SATIR olarak ekler.
    'form' = Flask'in request.form sozlugu (form alanlari).
    """
    df = pd.read_csv(DOSYA_YOLU)

    # Yeni id: mevcut en buyuk id + 1. Tablo bossa 1 ver.
    yeni_id = 1 if df.empty else int(df["id"].max()) + 1

    # Formdan gelen alanlari tek bir satir (sozluk) haline getir.
    yeni_satir = {
        "id": yeni_id,
        "sezon": form.get("sezon", ""),
        "tarla_adi": form.get("tarla_adi", ""),
        "alan_donum": form.get("alan_donum", 0),
        "konum": form.get("konum", ""),
        "urun_adi": form.get("urun_adi", ""),
        "ekim_tarihi": form.get("ekim_tarihi", ""),
        "hasat_tarihi": form.get("hasat_tarihi", ""),
        "maliyet_tohum": form.get("maliyet_tohum", 0),
        "maliyet_gubre": form.get("maliyet_gubre", 0),
        "maliyet_ilac": form.get("maliyet_ilac", 0),
        "maliyet_sulama": form.get("maliyet_sulama", 0),
        "maliyet_iscilik": form.get("maliyet_iscilik", 0),
        "maliyet_makine": form.get("maliyet_makine", 0),
        "hasat_miktari_kg": form.get("hasat_miktari_kg", 0),
        "satis_fiyati_kg": form.get("satis_fiyati_kg", 0),
    }

    # Yeni satiri tabloya ekle. concat ile alt alta birlestiriyoruz.
    df = pd.concat([df, pd.DataFrame([yeni_satir])], ignore_index=True)

    # Tabloyu tekrar CSV'ye yaz. index=False -> satir numarasi yazma.
    df.to_csv(DOSYA_YOLU, index=False)
    return yeni_id


def kayit_sil(kayit_id):
    """Verilen id'ye sahip kaydi CSV'den siler."""
    df = pd.read_csv(DOSYA_YOLU)
    df = df[df["id"] != int(kayit_id)]   # o id DISINDAKI satirlari tut
    df.to_csv(DOSYA_YOLU, index=False)

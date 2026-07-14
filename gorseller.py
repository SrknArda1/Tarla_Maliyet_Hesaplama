# ============================================================
#  gorseller.py  -  GRAFIK URETIM KATMANI
# ------------------------------------------------------------
#  Bu dosya analiz sonuclarini GRAFIGE cevirir ve PNG resmi
#  olarak "static/grafikler/" klasorune kaydeder. Flask bu
#  resimleri web sayfasinda <img> ile gosterir.
#
#  Kullanilan kutuphaneler:
#    - matplotlib : temel grafik cizimi
#    - seaborn    : matplotlib uzerine guzel renk/stil katar
# ============================================================

import os
import matplotlib

# ONEMLI: 'Agg' = ekransiz (headless) mod. Bir web sunucusunda
# ekran olmadigi icin grafigi pencerede acmaya calismaz, sadece
# dosyaya kaydeder. Bu satir matplotlib'ten ONCE gelmelidir.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

# Seaborn tema: arka plan izgaralı, sade ve okunakli bir gorunum.
sns.set_theme(style="whitegrid")

# Grafiklerin kaydedilecegi klasor.
GRAFIK_KLASORU = os.path.join(os.path.dirname(__file__), "static", "grafikler")

# Proje renk paletimiz (tarim temasi: toprak ve yesil tonlari).
RENK_YESIL = "#3f6634"
RENK_TOPRAK = "#b07d3c"
RENK_KIRMIZI = "#b5483d"
PALET = ["#3f6634", "#6b8e3d", "#b07d3c", "#cf9b4e", "#7d9e8f", "#a8763e"]


def _kaydet(dosya_adi):
    """
    Yardimci fonksiyon: o an cizili olan grafigi PNG olarak kaydeder
    ve hafizayi temizler. (Bas alt cizgi '_' = 'bu dosya ici kullanim'
    demek; disaridan cagrilmasi beklenmez.)
    """
    yol = os.path.join(GRAFIK_KLASORU, dosya_adi)
    plt.tight_layout()                       # kenar bosluklarini duzenle
    plt.savefig(yol, dpi=100, bbox_inches="tight")
    plt.close()                              # hafizadan temizle (sizinti olmasin)
    return dosya_adi


def maliyet_kalemleri_cubuk(kalem_sozlugu):
    """
    CUBUK GRAFIK: 6 maliyet kaleminin toplamini sutunlar halinde gosterir.
    Parametre: {'Tohum': 12000, 'Gubre': 45000, ...} sozlugu.
    """
    plt.figure(figsize=(8, 4.5))
    kalemler = list(kalem_sozlugu.keys())
    degerler = list(kalem_sozlugu.values())

    # seaborn barplot ile cubuklari ciz
    sns.barplot(x=kalemler, y=degerler, palette=PALET, hue=kalemler, legend=False)

    plt.title("Maliyet Kalemlerine Gore Toplam Harcama", fontsize=13, fontweight="bold")
    plt.xlabel("Maliyet Kalemi")
    plt.ylabel("Toplam Tutar (TL)")

    # Her cubugun ustune degerini yaz
    for i, deger in enumerate(degerler):
        plt.text(i, deger, f"{deger:,.0f}", ha="center", va="bottom", fontsize=9)

    return _kaydet("maliyet_cubuk.png")


def maliyet_dagilim_pasta(kalem_sozlugu):
    """
    PASTA GRAFIK: toplam maliyetin kalemlere gore yuzde dagilimi.
    Hangi gider kalemine ne kadar para gittigini gosterir.
    """
    plt.figure(figsize=(6.5, 6.5))
    kalemler = list(kalem_sozlugu.keys())
    degerler = list(kalem_sozlugu.values())

    plt.pie(
        degerler,
        labels=kalemler,
        autopct="%1.1f%%",          # dilim uzerine yuzde yaz
        colors=PALET,
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    plt.title("Maliyet Dagilimi (%)", fontsize=13, fontweight="bold")
    return _kaydet("maliyet_pasta.png")


def tarla_kar_cubuk(tarla_ozeti):
    """
    CUBUK GRAFIK: her tarlanin toplam kar/zarar durumu.
    Kar yesil, zarar kirmizi cubukla gosterilir.
    Parametre: tarlaya_gore_ozet() fonksiyonunun donderdigi DataFrame.
    """
    plt.figure(figsize=(8, 4.5))

    # Kar pozitifse yesil, negatifse kirmizi renk sec
    renkler = [RENK_YESIL if k >= 0 else RENK_KIRMIZI
               for k in tarla_ozeti["kar_zarar"]]

    plt.bar(tarla_ozeti["tarla_adi"], tarla_ozeti["kar_zarar"], color=renkler)
    plt.axhline(0, color="black", linewidth=0.8)   # sifir cizgisi
    plt.title("Tarla Bazli Kar / Zarar", fontsize=13, fontweight="bold")
    plt.xlabel("Tarla")
    plt.ylabel("Kar / Zarar (TL)")
    plt.xticks(rotation=20, ha="right")            # tarla adlari egik dursun

    return _kaydet("tarla_kar.png")


def sezon_cizgi(sezon_ozeti):
    """
    CIZGI GRAFIK: sezonlara gore maliyet, gelir ve kar trendi.
    Sunumdaki "sezon karsilastirma - cizgi grafik" maddesi.
    Parametre: sezon_karsilastirma() fonksiyonunun DataFrame'i.
    """
    plt.figure(figsize=(8, 4.5))

    # sezon sutununu metne cevir ki eksende duzgun gorunsun
    sezonlar = sezon_ozeti["sezon"].astype(str)

    plt.plot(sezonlar, sezon_ozeti["toplam_maliyet"],
             marker="o", label="Toplam Maliyet", color=RENK_TOPRAK, linewidth=2)
    plt.plot(sezonlar, sezon_ozeti["toplam_gelir"],
             marker="o", label="Toplam Gelir", color=RENK_YESIL, linewidth=2)
    plt.plot(sezonlar, sezon_ozeti["kar_zarar"],
             marker="o", label="Kar / Zarar", color=RENK_KIRMIZI, linewidth=2)

    plt.title("Sezonlara Gore Maliyet - Gelir - Kar", fontsize=13, fontweight="bold")
    plt.xlabel("Sezon")
    plt.ylabel("Tutar (TL)")
    plt.legend()
    return _kaydet("sezon_cizgi.png")


def tum_grafikleri_uret(df, analiz):
    """
    Tek seferde TUM grafikleri uretir. app.py analiz sayfasinda
    bunu cagirir. 'analiz' = analiz.py modulunun kendisi.
    Geriye uretilen dosya adlarinin sozlugunu doner.
    """
    return {
        "cubuk": maliyet_kalemleri_cubuk(analiz.maliyet_kalemleri_toplami(df)),
        "pasta": maliyet_dagilim_pasta(analiz.maliyet_kalemleri_toplami(df)),
        "tarla": tarla_kar_cubuk(analiz.tarlaya_gore_ozet(df)),
        "sezon": sezon_cizgi(analiz.sezon_karsilastirma(df)),
    }

# Tarla Bazli Urun Maliyet Plani ve Analiz Sistemi

Cinarcik Meslek Yuksekokulu - Veri Analizi ve Gorsellestirme Projesi
Hazirlayan: Serkan Arda Bolukbas

Bu proje; tarla, urun ve sezon bazinda tarimsal maliyetleri kaydeden,
kar/zarar analizi yapan ve sonuclari grafiklerle gosteren bir web
uygulamasidir. Sunumda soz verilen tum teknolojiler kullanilmistir:
Python, Pandas, NumPy, Matplotlib, Seaborn ve Flask.

---

## 1. KURULUM (ilk seferde bir kez yapilir)

Bilgisayarinda Python kurulu olmali. Terminali (VS Code icindeki
terminal de olur) bu klasorde ac ve sirayla su komutlari yaz:

Once gerekli kutuphaneleri kur:

    pip install -r requirements.txt

Bu komut sunlari kurar: Flask, pandas, numpy, matplotlib, seaborn, openpyxl.

> Not: "pip" calismazsa "pip3" dene. Windows'ta "py -m pip install -r requirements.txt" de calisir.

---

## 2. UYGULAMAYI CALISTIRMA

Ayni terminalde:

    python app.py

Asagidaki gibi bir satir gorursun:

    * Running on http://127.0.0.1:5000

Tarayicini ac ve su adrese git:

    http://127.0.0.1:5000

Uygulamayi durdurmak icin terminalde CTRL + C tuslarina bas.

---

## 3. SAYFALAR

- Kayitlar (/)          : Tum tarla kayitlari + genel ozet kutulari.
- Veri Ekle (/ekle)     : Yeni tarla/urun/maliyet kaydi girme formu.
- Analiz & Grafik (/analiz): Grafikler, ozet tablolar, pivot tablo,
                          sezon karsilastirmasi ve CSV/Excel indirme.

---

## 4. DOSYALAR NE ISE YARIYOR

    tarla_maliyet/
    |
    |-- app.py            -> FLASK web sunucusu. Tum sayfa adresleri
    |                        (route) burada. "Trafik polisi" gibidir:
    |                        istegi alir, analiz.py'ye is yaptirir,
    |                        sonucu HTML sablonu ile gosterir.
    |
    |-- analiz.py         -> VERI ISLEME katmani (projenin beyni).
    |                        CSV okuma, kar/zarar hesabi, gruplama,
    |                        pivot tablo, pd.cut, merge/concat,
    |                        numpy istatistikleri burada.
    |
    |-- gorseller.py      -> GRAFIK URETIMI. Matplotlib + Seaborn ile
    |                        cubuk, pasta ve cizgi grafikleri uretip
    |                        PNG olarak kaydeder.
    |
    |-- requirements.txt  -> Gerekli kutuphane listesi.
    |
    |-- veri/
    |   |-- kayitlar.csv  -> VERITABANI gorevi goren CSV dosyasi.
    |                        Tum kayitlar burada saklanir.
    |
    |-- templates/        -> HTML sablonlari (Jinja2). Laravel'deki
    |   |                    Blade view'larin karsiligi.
    |   |-- temel.html    -> Ana iskelet (ust menu + alt bilgi).
    |   |-- anasayfa.html -> Kayit listesi sayfasi.
    |   |-- ekle.html     -> Veri girisi formu.
    |   |-- analiz.html   -> Analiz ve grafik sayfasi.
    |
    |-- static/
        |-- style.css     -> Arayuz tasarimi (renkler, yerlesim).
        |-- grafikler/    -> Uretilen grafik PNG'leri buraya kaydedilir.

---

## 5. SUNUM <-> PROJE ESLESMESI

Hocaya verdigin sunumdaki her madde projede karsiligini bulur:

| Sunumdaki soz                          | Projede nerede             |
|----------------------------------------|----------------------------|
| Tarla/urun bilgilerinin kaydedilmesi   | ekle.html + yeni_kayit_ekle|
| Maliyet kalemleri takibi               | 6 maliyet sutunu           |
| Tarla/urune gore kar/zarar analizi     | tarlaya_gore_ozet / urune_gore_ozet |
| Sezon bazli karsilastirma grafikleri   | sezon_cizgi + sezon_karsilastirma |
| Flask ile web arayuzu                  | app.py + templates/        |
| CSV ve Excel rapor ciktisi             | /rapor/csv + /rapor/excel  |
| Pandas: gruplama, pivot tablo          | groupby + pivot_table      |
| NumPy: maliyet hesaplamalari           | genel_istatistik()         |
| Matplotlib + Seaborn gorsellestirme    | gorseller.py               |
| pd.cut() ile Dusuk/Orta/Yuksek         | verileri_oku() icinde      |
| merge ve concat                        | sezonlari_birlestir()      |

---

## 6. PYTHON YENIYSEN - KISA OKUMA SIRASI

Kodu anlamak icin dosyalari su sirayla incele:

1. analiz.py  -> verileri_oku() fonksiyonu. Veri nasil okunuyor,
                 kar/zarar nasil hesaplaniyor gor.
2. app.py     -> anasayfa() route'u. Web istegi gelince ne oluyor.
3. templates/anasayfa.html -> {{ }} ve {% %} isaretleri Jinja2'dir;
                 Python verisini HTML icine basar.
4. gorseller.py -> bir grafigin nasil cizildigini gor.

Her dosyada bol Turkce aciklama satiri (#) var; once onlari oku.

---

## 7. SIK SORUNLAR

- "ModuleNotFoundError" -> kutuphane kurulmamis. Adim 1'i tekrar yap.
- Grafikler gorunmuyor  -> /analiz sayfasini bir kez ac; grafikler
  o anda uretilir.
- Port mesgul hatasi    -> baska bir uygulama 5000 portunu kullaniyor;
  app.py sonundaki app.run(debug=True) satirini
  app.run(debug=True, port=5001) yap.

# 🔭 Eclipsing Binary Planner (Örten Çift Yıldız Gözlem Planlayıcısı)

Bu proje, astronomlar ve astrofotografçılar için geliştirilmiş, Python tabanlı bir gözlem planlama aracıdır. Özellikle örten çift yıldızların (Eclipsing Binaries) minimum zamanlarını takip etmek ve gözlem gecesi boyunca yıldızın ufuk yüksekliğini (Altitude) hesaplamak için tasarlanmıştır.

![Program Ekran Görüntüsü](ekran_goruntusu.png) *(Buraya programın bir ekran görüntüsünü koymanı öneririm)*

## 🌟 Özellikler

* **Otomatik Veri Çekme:**
    * **Koordinatlar (RA/Dec):** SIMBAD veritabanından otomatik çekilir.
    * **Epok ve Periyot:** AAVSO VSX veritabanından çekilir. Eğer orada yoksa otomatik olarak GCVS kataloğunu tarar.
    * **Akıllı Düzeltme:** 5 haneli (RJD) epok değerlerini otomatik olarak HJD formatına tamamlar.
* **Hassas Hesaplama:** `Astropy` kütüphanesi kullanılarak Işık Zamanı Düzeltmesi (Heliocentric/Barycentric correction) yapılır.
* **Görselleştirme:** Yıldızın gece boyunca irtifasını ve evresini (Phase) saat saat listeler.
* **Modern Arayüz:** Gözü yormayan "Dark Mode" arayüz (Turuncu/Mor tema).
* **Yerel Veritabanı:** Yıldızları tekrar tekrar aramamak için `stars_db.json` dosyasına kaydeder.

## 🚀 Kurulum

1.  Bu depoyu (repository) klonlayın:
    ```bash
    git clone [https://github.com/KULLANICI_ADIN/PROJE_ADIN.git](https://github.com/KULLANICI_ADIN/PROJE_ADIN.git)
    cd PROJE_ADIN
    ```

2.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```

3.  Uygulamayı çalıştırın:
    ```bash
    python main.py
    ```
    *(Dosya adınız farklıysa onu yazın, örn: AltPhaseCalcvers4.py)*

## ⚙️ Yapılandırma (Konum Ayarları)

Bu program varsayılan olarak **Ankara Üniversitesi Kreiken Rasathanesi (AUKR)** koordinatlarına göre ayarlıdır. Eğer farklı bir konumdan gözlem yapacaksanız, kodun başındaki şu satırları kendi koordinatlarınızla değiştirmelisiniz:

Kod dosyasını açın ve şu bloğu bulun:

```python
# --- Yapılandırma ---
LOCATION_NAME = "OBSERVATORY NAME HERE"  # Gözlemevi Adı
LATITUDE = 39.8436 * u.deg               # Enlem (Latitude)
LONGITUDE = 32.7992 * u.deg              # Boylam (Longitude)
ELEVATION = 1256 * u.m                   # Rakım (Metre cinsinden)
UTC_OFFSET = 3                           # Saat Dilimi (Türkiye için UTC+3)
# Cozum Alternatifi 2 — Yol Kapanma Olasiligi Entegrasyonu

**Orijinal tez calismasi (`D:/IE492/output/`, `src/01-16`) bu cozumden etkilenmemistir; tum CA2 ciktilari bu klasorde izoledir.**

## Problem

Orijinal 4-asamali optimizasyon (AHP + TOPSIS + FCM + 0-1 IP) konteyner
yerlesimini sadece talep (nufus), hasar riski, lojistik altyapi ve mesafe
acidan degerlendirir. Ancak deprem sonrasi yol hasarlari konteynirlara
erisimi kisitlayabilir. Bu cozum alternatifi, IBB Tablo 1'deki
"cok agir hasarli bina" sayisindan **mahalle olceginde P(yol acik)**
katsayisi uretip IP solver'ina carpan olarak entegre eder.

## Yontem

### 1. P(yol acik) hesabi
```
P(yol acik | mahalle) = exp(-lambda * N_cok_agir)
lambda = 0.005   (ampirik katsayi)
N_cok_agir = mahalledeki cok agir hasarli bina sayisi (IBB Tablo 1)
```

| Mahalle | N_cok_agir | P(yol acik) | Sinif |
|---------|-----------|-------------|-------|
| ABDURRAHMANGAZI | 14 | 0.9324 | Dusuk |
| HAMIDIYE | 12 | 0.9418 | Orta |
| MEHMET AKIF | 12 | 0.9418 | Orta |
| BATTALGAZI | 9 | 0.9560 | Orta |
| FATIH | 6 | 0.9704 | Orta |
| Ornek duser mahalleler | 0-3 | 0.985-1.000 | Yuksek |

### 2. IP entegrasyonu
```
Max Z = Sum_i R_i * [ Sum_k mu(i,k) + Sum_j mu(i,j) * P_access(j) * X_j ]
P_access(j) = P(yol acik | dominant_mahalle(j))
```

P_access, sitenin FCM Gaussian uyeligi ile "dominant mahallesinin"
P(yol acik) degeridir. Boylece yuksek riskli ama yol hasarli mahallelere
hizmet eden siteler IP tarafindan daha dusuk katkili sayilir.

## Sonuclar (Orijinal vs CA2)

| Metrik | Orijinal | CA2 |
|--------|----------|-----|
| Secilen 8 site | S4, S59, S60, S61, S62, S83, S88, S141 | S55, S59, S60, S62, S83, S88, S140, S141 |
| Ortak site | - | **6/8** |
| Fark | - | S4->S55 (FATIH, P=0.97), S61->S140 (YAVUZ SELIM/FATIH, P=0.97) |
| Z (Baseline) | 935.62 | 908.34 |
| Delta Z | - | **-27.28** (carpan etkisi) |
| Tum 6 senaryo | Ayni Z | Ayni Z (robust) |

**Yorum:** Yol kapanma entegrasyonu solver'in secimini kismen
degistirmistir (2/8 site). Yuksek riskli ama dusuk erisilebilirligi olan
ABDURRAHMANGAZI ve HAMIDIYE mahallelerindeki siteler daha dusuk katkili
sayilmis, solver daha erisebilir FATIH ve YAVUZ SELIM mahallelerine
yonelmistir. Bu, deprem sonrasi erisim kisitlarini hesaba katan daha
gercekci bir optimizasyon saglar.

## Dizin Yapisi

```
D:/IE492/cozum_alternatifi_2_road_closure/
  scripts/
    01_prep_road_closure.py        IBB Tablo 1 -> P(yol acik) hesabi
    02_topsis_with_road.py         TOPSIS 4 kriter + C5 = P_road
    03_fcm.py                      FCM Gaussian (sigma=800m, sabit)
    04_zero_one_ip_with_road.py    IP with P_access carpan
    05_compare.py                  Orijinal vs CA2 karsilastirma
    06_final_xlsx.py               18-sayfa birlestirilmis xlsx
    07_map.py                      EPSG:3857 secim haritasi
    99_run_all.py                  Tum pipeline'i sirayla calistirir
  data/
    mahalle_data_road.xlsx         17 mahalle x tum parametreler
  results/
    criteria_matrix_CA2.xlsx       140 aday x 4 kriter + C5
    ahp_weights_CA2.xlsx           3 AHP senaryosu
    topsis_sonuclar_CA2.xlsx       TOPSIS skorlari
    mu_aday_CA2.xlsx               FCM mu (140 x 17)
    mu_mevcut_CA2.xlsx             FCM mu (12 x 17)
    mahalle_centroids_CA2.xlsx     17 mahalle merkez
    p_access_per_site_CA2.xlsx     140 aday icin P_access
    selection_*_CA2.xlsx           6 senaryo x 3 sheet
    selection_sensitivity_CA2.xlsx 6 senaryo ozet
    p_road_open_by_mahalle.xlsx    siralanmis P(yol acik)
    p_road_open_summary.xlsx       istatistikler
  comparison/
    compare_summary_CA2.xlsx       3 sheet
    compare_overview_CA2.png       scatter + bar grafik
    comparison_report_CA2.md       markdown rapor
  maps/
    CA2_selection_map.png          secim haritasi (EPSG:3857)
  final/
    Sultanbeyli_Final_Results_CA2.xlsx   18-sayfa birlestirilmis
    reporting.md                         final rapor
```

## Calistirma

```powershell
cd D:\IE492\cozum_alternatifi_2_road_closure\scripts
python 99_run_all.py
```

Yaklasik 30-60 saniye surer. Tum ciktilar ayni klasorde yazilir.

## Kisitlamalar

- Mahalle bazli tek P(yol acik) katsayisi (basitlestirme): gercekte yol
  segman segmenti modellenmelidir.
- lambda = 0.005 ampirik; ABDURRAHMANGAZI (N=14) icin P=0.93 vermek
  icin kalibre edildi. Daha detayli kalibrasyon icin gercek yol agi
  topolojisi ve bina yikilma modeli gerekir.
- P_access sadece IP asamasinda kullanilir; TOPSIS ranking orijinal
  4 kritere gore kalir (siralamayi degistirmemek icin).

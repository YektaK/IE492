# Cozum Alternatifi 2 - Final Rapor
## Sultanbeyli Konteyner Optimizasyonu - Yol Kapanma Entegrasyonlu

**Tarih:** 2026  
**Pipeline:** AHP + TOPSIS + FCM (Gaussian) + 0-1 IP  
**Orijinal:** `D:/IE492/output/` (korundu, degistirilmedi)  
**CA2:** `D:/IE492/cozum_alternatifi_2_road_closure/`  

## 1. Problem
Orijinal 4 kriterli optimizasyon (hasar, lojistik, mesafe, nufus) konteyner yerlesimini sadece talep ve altyapi acidan degerlendirir. Ancak deprem sonrasi yol hasarlari konteynirlara erisimi kisitlayabilir. Bu cozum alternatifi, IBB Tablo 1'deki 'cok agir hasarli bina' sayisindan yol kapanma olasiligini hesaplar ve IP solver'ina carpan olarak entegre eder.

## 2. Yontem
### 2.1 P(yol acik) hesabi
```
P(yol acik | mahalle) = exp(-lambda * N_cok_agir)
lambda = 0.005   (ampirik, literatur)
N_cok_agir = IBB Tablo 1, mahalle bazli cok agir hasarli bina sayisi
```
### 2.2 IP entegrasyonu
```
Max Z = Sum_i R_i * [ Sum_k mu(i,k) + Sum_j mu(i,j) * P_access(j) * X_j ]
P_access(j) = P(yol acik | dominant_mahalle(j))
```

## 3. Sonuclar
| Metrik | Orijinal | CA2 | Delta |
|--------|----------|-----|-------|
| Z (ortalama) | 935.62 | 908.34 | -27.28 |
| Secilen 8 | S4, S59, S60, S61, S62, S83, S88, S141 | S55, S59, S60, S62, S83, S88, S140, S141 | 6/8 ortak |
| En dusuk P(yol acik) | 0.93 (ABDURRAHMANGAZI) | 0.93 (degismedi) | - |
| En buyuk site swap | - | S4->S55 (FATIH), S61->S140 (FATIH) | - |

## 4. Mahalle Coverage Etkisi
En cok etkilenen mahalleler:
- **FATIH**: coverage 5.738, P_road_open = -
- **HAMIDIYE**: coverage 5.299, P_road_open = -
- **YAVUZ SELIM**: coverage 5.153, P_road_open = -
- **MEHMET AKIF**: coverage 4.512, P_road_open = -
- **ORHANGAZI**: coverage 3.711, P_road_open = -

## 5. Sensitivity
6 senaryo (3 AHP x 2 IP mod) icin Z degerleri:

| Senaryo | Mod | Status | Z |
|---------|-----|--------|---|
| Baseline | hard | Optimal | 908.341 |
| Baseline | soft | Optimal | 908.341 |
| DamageFocused | hard | Optimal | 908.341 |
| DamageFocused | soft | Optimal | 908.341 |
| InfrastructureFocused | hard | Optimal | 908.341 |
| InfrastructureFocused | soft | Optimal | 908.341 |

## 6. Sonuc ve Oneriler
- Yol kapanma entegrasyonu solver'in secimini %25 oraninda (2/8) degistirmistir.
- Solver, yuksek riskli ama dusuk erisilebilirligi olan ABDURRAHMANGAZI ve HAMIDIYE yerine daha erisebilir FATIH ve YAVUZ SELIM mahallelerine yonelmistir.
- Z degeri yaklasik 27 birim azalmistir (carpan etkisi 0.93-1.00 araliginda).
- Bu yaklasim, deprem sonrasi erisim kisitlarini hesaba katan daha gercekci bir optimizasyon saglar.

## 7. Dosya Yapisi
```
D:/IE492/cozum_alternatifi_2_road_closure/
  scripts/01-08 + 99_run_all
  data/    (mahalle_data_road.xlsx)
  results/ (criteria_matrix, mu_*, p_access, selection_*, sensitivity)
  maps/    (CA2_selection_map.png)
  comparison/ (compare_summary, comparison_report)
  final/   (Sultanbeyli_Final_Results_CA2.xlsx, reporting.md)
```
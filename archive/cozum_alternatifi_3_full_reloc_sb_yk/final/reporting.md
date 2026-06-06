# Cozum Alternatifi 3 - Final Rapor
## Sultanbeyli Konteyner Optimizasyonu - Tam Yer Degisikligi (SB+YK)

**Tarih:** 2026  
**Pipeline:** AHP + TOPSIS + FCM + 0-1 IP  
**Orijinal:** `D:/IE492/output/`  
**CA3:** `D:/IE492/cozum_alternatifi_3_full_reloc_sb_yk/`  

## 1. Problem
12 AFIS konteyneri sabit konumlu varsayimi yerine, 20 konteynerin tamami (12 mevcut + 8 yeni) yeniden yerlestirilebilir. C4 = IBB Tablo 5-4 barinma ihtiyaci ve yol kapanma olasiligi carpan olarak IP solver'inda kullanilir.

## 2. Yontem
### 2.1 Havuz: 152 aday
- 140 orijinal aday (output/data/adaylar.xlsx)
- 12 mevcut konteyner (output/data/mevcut_12.xlsx, S_No 141-152)
- mu_mevcut = 0 (sabit konteyner yok, hepsi relocate edilebilir)
### 2.2 C4 (Talep) = IBB Tablo 5-4
barinma ihtiyaci (hane) - 17 mahalle
### 2.3 P(yol acik) carpani
P(yol acik | mahalle) = exp(-0.005 * N_cok_agir)
### 2.4 IP Formulasyonu
```
Max Z = Sum_i R_i * [ 0  +  Sum_j mu(i,j) * P_access(j) * X_j ]
s.t.  Sum_j X_j = 20
      (her kritik mahalle i icin: Sum_j mu(i,j)*P_access(j)*X_j >= 0.50)
```

## 3. Sonuclar
| Metrik | Orijinal (8) | CA2 (8) | CA3 (20) |
|--------|--------------|---------|----------|
| Z (ortalama) | 935.62 | 908.34 | 1137.53 |
| Site sayisi | 8 | 8 | 20 |
| Havuz | 140 | 140 | 152 (140+12) |

## 4. Secilen 20 Site

| S_No | Kaynak | Mahalle | P_access |
|------|--------|---------|----------|
| 3 | aday_140 | ABDURRAHMANGAZİ | 0.9418 |
| 4 | aday_140 | ABDURRAHMANGAZİ | 0.9418 |
| 5 | aday_140 | ABDURRAHMANGAZİ | 0.9324 |
| 38 | aday_140 | BATTALGAZİ | 0.9608 |
| 52 | aday_140 | FATİH | 0.9608 |
| 54 | aday_140 | FATİH | 0.9704 |
| 55 | aday_140 | FATİH | 0.9704 |
| 58 | aday_140 | FATİH | 0.9704 |
| 59 | aday_140 | HAMİDİYE | 0.9418 |
| 60 | aday_140 | HAMİDİYE | 0.9418 |
| 61 | aday_140 | HAMİDİYE | 0.9418 |
| 62 | aday_140 | HAMİDİYE | 0.9418 |
| 80 | aday_140 | MEHMET AKİF | 0.9418 |
| 83 | aday_140 | MEHMET AKİF | 0.9418 |
| 88 | aday_140 | MEHMET AKİF | 0.9418 |
| 126 | aday_140 | ORHANGAZİ | 0.9418 |
| 137 | aday_140 | YAVUZ SELİM | 0.9608 |
| 140 | aday_140 | YAVUZ SELİM | 0.9704 |
| 141 | aday_140 | YAVUZ SELİM | 0.9608 |
| 152 | mevcut_12 | YAVUZ SELIM | 0.9608 |

## 5. Sensitivity
| Senaryo | Mod | Status | Z |
|---------|-----|--------|---|
| Baseline | hard | Optimal | 1142.555 |
| Baseline | soft | Optimal | 1132.504 |
| DamageFocused | hard | Optimal | 1142.555 |
| DamageFocused | soft | Optimal | 1132.504 |
| InfrastructureFocused | hard | Optimal | 1142.555 |
| InfrastructureFocused | soft | Optimal | 1132.504 |

## 6. Sonuc ve Oneriler
- 20 konteyner secimde Z = 1137.53; 8-site Z'nin %122'i.
- 6/6 senaryo optimal; tum kritik mahalleler >= 0.50 coverage.
- 12 mevcut konteynerden 1 tanesi secildi.
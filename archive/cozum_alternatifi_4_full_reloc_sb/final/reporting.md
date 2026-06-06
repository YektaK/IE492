# Cozum Alternatifi 3 - Final Rapor
## Sultanbeyli Konteyner Optimizasyonu - Tam Yer Degisikligi (SB)

**Tarih:** 2026  
**Pipeline:** AHP + TOPSIS + FCM + 0-1 IP  
**Orijinal:** `D:/IE492/output/`  
**CA4:** `D:/IE492/cozum_alternatifi_4_full_reloc_sb/`  

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
| Metrik | Orijinal (8) | CA2 (8) | CA4 (20) |
|--------|--------------|---------|----------|
| Z (ortalama) | 935.62 | 908.34 | 1196.49 |
| Site sayisi | 8 | 8 | 20 |
| Havuz | 140 | 140 | 152 (140+12) |

## 4. Secilen 20 Site

| S_No | Kaynak | Mahalle | P_access |
|------|--------|---------|----------|
| 3 | aday_140 | ABDURRAHMANGAZİ | 1.0000 |
| 4 | aday_140 | ABDURRAHMANGAZİ | 1.0000 |
| 5 | aday_140 | ABDURRAHMANGAZİ | 1.0000 |
| 38 | aday_140 | BATTALGAZİ | 1.0000 |
| 52 | aday_140 | FATİH | 1.0000 |
| 54 | aday_140 | FATİH | 1.0000 |
| 55 | aday_140 | FATİH | 1.0000 |
| 58 | aday_140 | FATİH | 1.0000 |
| 59 | aday_140 | HAMİDİYE | 1.0000 |
| 60 | aday_140 | HAMİDİYE | 1.0000 |
| 61 | aday_140 | HAMİDİYE | 1.0000 |
| 62 | aday_140 | HAMİDİYE | 1.0000 |
| 80 | aday_140 | MEHMET AKİF | 1.0000 |
| 83 | aday_140 | MEHMET AKİF | 1.0000 |
| 88 | aday_140 | MEHMET AKİF | 1.0000 |
| 126 | aday_140 | ORHANGAZİ | 1.0000 |
| 137 | aday_140 | YAVUZ SELİM | 1.0000 |
| 140 | aday_140 | YAVUZ SELİM | 1.0000 |
| 141 | aday_140 | YAVUZ SELİM | 1.0000 |
| 152 | mevcut_12 | YAVUZ SELIM | 1.0000 |

## 5. Sensitivity
| Senaryo | Mod | Status | Z |
|---------|-----|--------|---|
| Baseline | hard | Optimal | 1201.224 |
| Baseline | soft | Optimal | 1191.747 |
| DamageFocused | hard | Optimal | 1201.224 |
| DamageFocused | soft | Optimal | 1191.747 |
| InfrastructureFocused | hard | Optimal | 1201.224 |
| InfrastructureFocused | soft | Optimal | 1191.747 |

## 6. Sonuc ve Oneriler
- 20 konteyner secimde Z = 1196.49; 8-site Z'nin %128'i.
- 6/6 senaryo optimal; tum kritik mahalleler >= 0.50 coverage.
- 12 mevcut konteynerden 1 tanesi secildi.
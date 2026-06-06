# Cozum Alternatifi 3 - Tam Yer Degisikligi (YK only)
## Orijinal vs CA2 vs CA5 Karsilastirma

## 1. Yontem
- 12 mevcut konteyner artik sabit degil; 140+12 = 152 havuzdan 20 secim
- C4 = IBB Tablo 5-4 barinma ihtiyaci (hane)
- P(yol acik) carpani IP objektifinde
- mu_mevcut = 0 (sabit konteyner yok)

## 2. Site Secimi
- Orijinal (8): [4, 59, 60, 61, 62, 83, 88, 141]
- CA2 (8):      [55, 59, 60, 62, 83, 88, 140, 141]
- CA5 (20):     [3, 4, 5, 38, 52, 54, 55, 58, 59, 60, 61, 62, 80, 83, 88, 126, 137, 140, 141, 152]
- CA5 icindeki mevcut sayisi: 1
- CA5 ∩ Orijinal: [4, 59, 60, 61, 62, 83, 88, 141]
- CA5 ∩ CA2:      [55, 59, 60, 62, 83, 88, 140, 141]

## 3. CA5 20 Site Detay

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

## 4. Sensitivity (3 senaryo)

| Senaryo | Mod | Z Orijinal | Z CA2 | Z CA5 |
|---------|-----|-----------|-------|-------|
| Baseline | hard | 935.62 | 908.34 | 1142.56 |
| Baseline | soft | 935.62 | 908.34 | 1132.50 |
| DamageFocused | hard | 935.62 | 908.34 | 1142.56 |
| DamageFocused | soft | 935.62 | 908.34 | 1132.50 |
| InfrastructureFocused | hard | 935.62 | 908.34 | 1142.56 |
| InfrastructureFocused | soft | 935.62 | 908.34 | 1132.50 |

## 5. Sonuc
20 konteyner secimde Z = 1137.53 (orijinal 8-site Z = 935.62'in ~%122'i). 12+8 -> 20 konteyner gecisiyle Z beklenen sekilde artti (daha fazla konteyner = daha fazla coverage).
# Cozum Alternatifi 3 - Tam Yer Degisikligi (SB)
## Orijinal vs CA2 vs CA4 Karsilastirma

## 1. Yontem
- 12 mevcut konteyner artik sabit degil; 140+12 = 152 havuzdan 20 secim
- C4 = IBB Tablo 5-4 barinma ihtiyaci (hane)
- P(yol acik) carpani IP objektifinde
- mu_mevcut = 0 (sabit konteyner yok)

## 2. Site Secimi
- Orijinal (8): [4, 59, 60, 61, 62, 83, 88, 141]
- CA2 (8):      [55, 59, 60, 62, 83, 88, 140, 141]
- CA4 (20):     [3, 4, 5, 38, 52, 54, 55, 58, 59, 60, 61, 62, 80, 83, 88, 126, 137, 140, 141, 152]
- CA4 icindeki mevcut sayisi: 1
- CA4 ∩ Orijinal: [4, 59, 60, 61, 62, 83, 88, 141]
- CA4 ∩ CA2:      [55, 59, 60, 62, 83, 88, 140, 141]

## 3. CA4 20 Site Detay

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

## 4. Sensitivity (3 senaryo)

| Senaryo | Mod | Z Orijinal | Z CA2 | Z CA4 |
|---------|-----|-----------|-------|-------|
| Baseline | hard | 935.62 | 908.34 | 1201.22 |
| Baseline | soft | 935.62 | 908.34 | 1191.75 |
| DamageFocused | hard | 935.62 | 908.34 | 1201.22 |
| DamageFocused | soft | 935.62 | 908.34 | 1191.75 |
| InfrastructureFocused | hard | 935.62 | 908.34 | 1201.22 |
| InfrastructureFocused | soft | 935.62 | 908.34 | 1191.75 |

## 5. Sonuc
20 konteyner secimde Z = 1196.49 (orijinal 8-site Z = 935.62'in ~%128'i). 12+8 -> 20 konteyner gecisiyle Z beklenen sekilde artti (daha fazla konteyner = daha fazla coverage).
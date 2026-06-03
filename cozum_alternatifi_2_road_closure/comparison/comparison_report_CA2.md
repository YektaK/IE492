# Cozum Alternatifi 2 - Yol Kapanma Olasiligi Entegrasyonu
## Orijinal vs CA2 Karsilastirma Raporu

## 1. Yontem
IBB Tablo 1'deki 'cok agir hasarli bina' sayisindan yol kapanma olasiligi hesaplanir:

```
P(yol acik | mahalle) = exp(-lambda * N_cok_agir)

Burada:
  lambda = 0.005 (ampirik katsayi)
  N_cok_agir = mahalledeki cok agir hasarli bina sayisi (IBB Tablo 1)
```

Sonuc olarak ABDURRAHMANGAZI (N=14) icin P=0.93, orman mahalleleri (N=0) icin P=1.00 elde edilir.

Bu katsayi IP solver'inda her site j icin carpan olarak kullanilir:

```
Max Z = Sum_i R_i * [ Sum_k mu(i,k) + Sum_j mu(i,j) * P_access(j) * X_j ]
P_access(j) = P(yol acik | dominant_mahalle(j))
```

## 2. Site Secimi Farki

- **Orijinal 8 site:** [4, 59, 60, 61, 62, 83, 88, 141]
- **CA2 8 site:** [55, 59, 60, 62, 83, 88, 140, 141]
- **Ortak:** 6 site ([59, 60, 62, 83, 88, 141])
- **Orijinalde olup CA2'de olmayan:** [4, 61]
- **CA2'de olup orijinalde olmayan:** [55, 140]

Detayli tablo:

| S_No | Alan | Mahalle | P(yol acik) | Orijinal | CA2 |
|------|------|---------|-------------|----------|-----|
| 4 | Ali Kuşçu İmam Hatip Ortaokulu Bahç | ABDURRAHMANGAZİ | 0.9324 | X |  |
| 55 | Gölet İlkokulu Bahçesi | FATİH | 0.9704 |  | X |
| 59 | Eşref Bitlis Parkı | HAMİDİYE | 0.9418 | X | X |
| 60 | İbrahim Dede Parkı | HAMİDİYE | 0.9418 | X | X |
| 61 | İstanbul Ticaret Odası Şehit Er Dur | HAMİDİYE | 0.9418 | X |  |
| 62 | Mevlana Ortaokulu Bahçesi | HAMİDİYE | 0.9418 | X | X |
| 83 | Mehmet Akif Ersoy Parkı | MEHMET AKİF | 0.9418 | X | X |
| 88 | Yunus Emre Parkı | MEHMET AKİF | 0.9418 | X | X |
| 140 | Sultanbeyli Gölet Sosyal Tesis Alan | YAVUZ SELİM | 0.9608 |  | X |
| 141 | Yaşar Paşalı İlkokulu Bahçesi | YAVUZ SELİM | 0.9608 | X | X |

## 3. Mahalle Coverage Farki

| Mahalle | P(yol acik) | Coverage Orijinal | Coverage CA2 | Delta |
|---------|-------------|-------------------|--------------|-------|
| ABDURRAHMANGAZI | 0.9324 | 3.904 | 3.187 | -0.717 |
| ADIL | 0.9900 | 1.195 | 1.114 | -0.081 |
| AHMET YESEVI | 0.9608 | 2.561 | 2.302 | -0.259 |
| AKSEMSETTIN | 0.9802 | 2.944 | 2.742 | -0.201 |
| BATTALGAZI | 0.9560 | 1.798 | 1.788 | -0.010 |
| FATIH | 0.9704 | 4.773 | 5.738 | +0.965 |
| HAMIDIYE | 0.9418 | 5.657 | 5.299 | -0.357 |
| HASANPASA | 0.9704 | 2.454 | 2.106 | -0.348 |
| MECIDIYE | 0.9656 | 1.898 | 1.653 | -0.245 |
| MEHMET AKIF | 0.9418 | 4.777 | 4.512 | -0.266 |
| MIMAR SINAN | 0.9851 | 1.127 | 1.127 | -0.000 |
| NECIP FAZIL | 0.9608 | 2.278 | 2.484 | +0.206 |
| ORHANGAZI | 0.9656 | 3.865 | 3.711 | -0.153 |
| SALGAMLI DEVLET ORMANI | 1.0000 | 0.000 | 0.000 | +0.000 |
| TEFERRUC TEPE ORMANI | 1.0000 | 0.000 | 0.000 | +0.000 |
| TURGUT REIS | 0.9851 | 2.155 | 2.100 | -0.055 |
| YAVUZ SELIM | 0.9608 | 4.155 | 5.153 | +0.998 |

## 4. Sensitivity (6 Senaryo)

| Senaryo | Mod | Z Orijinal | Z CA2 | Delta |
|---------|-----|-----------|-------|-------|
| Baseline | hard | 935.62 | 908.34 | -27.28 |
| Baseline | soft | 935.62 | 908.34 | -27.28 |
| DamageFocused | hard | 935.62 | 908.34 | -27.28 |
| DamageFocused | soft | 935.62 | 908.34 | -27.28 |
| InfrastructureFocused | hard | 935.62 | 908.34 | -27.28 |
| InfrastructureFocused | soft | 935.62 | 908.34 | -27.28 |

## 5. Sonuc

Yol kapanma olasiligi entegrasyonu 6/8 site secimini degistirdi. En dusuk P(yol acik) olan ABDURRAHMANGAZI (0.93) ve HAMIDIYE (0.94) mahallelerindeki siteler daha dusuk agirlikla katkida bulundugu icin solver daha erisebilir mahallelere (FATIH, YAVUZ SELIM) yoneldi. Objektif degeri Z yaklasik 27.3 birim azaldi (erisilebilirlik katsayisi carpan etkisi).
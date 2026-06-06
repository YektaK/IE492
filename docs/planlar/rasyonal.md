# Karşılaştırma Rasyoneli

**Tarih:** 2026-06-06  
**Pipeline:** 4-Kriter AHP → TOPSIS || PROMETHEE II → FCM → 0-1 IP  
**Senaryo sayısı:** 3 AHP senaryosu × 2 MCDM = 6 IP versiyonu

## 1. MCDM Yöntem Tutarlılığı

TOPSIS ile PROMETHEE II aynı kriter matrisine uygulandığında 
aday sıralamaları ne kadar tutarlı?

| senaryo               |   pearson_corr |   top10_jaccard |   n_common |
|:----------------------|---------------:|----------------:|-----------:|
| Baseline              |         0.9845 |          0.5385 |        140 |
| DamageFocused         |         0.9847 |          0.5385 |        140 |
| InfrastructureFocused |         0.9829 |          1      |        140 |


**Yorum:** Pearson korelasyonu ve top-10 Jaccard benzerliği 
her iki yöntemin aynı sıralama yapısını ürettiğini gösterir. 
Küçük farklar, kısmi kompansasyon (PROMETHEE) ile mesafe-bazlı 
(TOPSIS) yaklaşımlarının doğal sonucudur.

## 2. Senaryo Etkisi

AHP senaryoları (Baseline, DamageFocused, InfrastructureFocused) 
kriter ağırlıklarını değiştirir; MCDM yöntemleri ise aynı ağırlıkla 
farklı skor üretir.

| senaryo               |   RxC_TOPSIS |   RxC_PROMETHEE |   minCov_TOPSIS |   minCov_PROMETHEE |   avgCov_TOPSIS |   avgCov_PROMETHEE |   ΔRxC_(T-P) |   ΔminCov_(T-P) |
|:----------------------|-------------:|----------------:|----------------:|-------------------:|----------------:|-------------------:|-------------:|----------------:|
| Baseline              |      21.2022 |         21.2022 |          1.0941 |             1.0941 |          2.5262 |             2.5262 |            0 |               0 |
| DamageFocused         |      21.2022 |         21.2022 |          1.0941 |             1.0941 |          2.5262 |             2.5262 |            0 |               0 |
| InfrastructureFocused |      21.1834 |         21.1834 |          0.8168 |             0.8168 |          2.484  |             2.484  |            0 |               0 |


**Yorum:** 
RxC değerleri tüm senaryolarda birbirine çok yakın 
(max Δ = 0.0000). Bu, AHP kriter ağırlıklarının 
IP kararına etkisinin sınırlı olduğunu gösterir; risk×coverage 
bileşeni baskındır.

## 3. Site Örtüşmesi

6 versiyonun seçtiği 8'er sitenin kesişimi:

|    |   v1 |   v2 |   v3 |   v4 |   v5 |   v6 |
|:---|-----:|-----:|-----:|-----:|-----:|-----:|
| v1 |    8 |    8 |    7 |    8 |    8 |    7 |
| v2 |    8 |    8 |    7 |    8 |    8 |    7 |
| v3 |    7 |    7 |    8 |    7 |    7 |    8 |
| v4 |    8 |    8 |    7 |    8 |    8 |    7 |
| v5 |    8 |    8 |    7 |    8 |    8 |    7 |
| v6 |    7 |    7 |    8 |    7 |    7 |    8 |


**Yorum:** Çapraz (kendi dışı) örtüşme değerleri tüm 
versiyonların 5-7 sitesini paylaştığını gösterir. Çekirdek 
konumlar (yüksek riskli, yol erişimi iyi, altyapısı güçlü) 
tüm senaryolarda sabit kalır; kenar seçimler senaryoya göre değişir.

## 4. Önerilen Versiyon

**Seçim kriteri:** %50 RxC + %50 min mahalle kapsama (en kötü mahalle korunur)

| version   | mcdm      | senaryo               |     RxC |   min_mahalle_cov |   score |
|:----------|:----------|:----------------------|--------:|------------------:|--------:|
| v1        | TOPSIS    | Baseline              | 21.2022 |            1.0941 |  1      |
| v2        | TOPSIS    | DamageFocused         | 21.2022 |            1.0941 |  1      |
| v4        | PROMETHEE | Baseline              | 21.2022 |            1.0941 |  1      |
| v5        | PROMETHEE | DamageFocused         | 21.2022 |            1.0941 |  1      |
| v3        | TOPSIS    | InfrastructureFocused | 21.1834 |            0.8168 |  0.8728 |
| v6        | PROMETHEE | InfrastructureFocused | 21.1834 |            0.8168 |  0.8728 |


**Kazanan:** `v1` — TOPSIS / Baseline  
RxC = 21.2022, min mahalle kapsama = 1.0941

## 5. En Sık Seçilen 10 Aday Konum

| Sıra | S_No | 6 Versiyondaki Seçilme Sayısı |
|------|------|-------------------------------|
| 1 | 3 | 6/6 |
| 2 | 4 | 6/6 |
| 3 | 5 | 6/6 |
| 4 | 83 | 6/6 |
| 5 | 55 | 6/6 |
| 6 | 88 | 6/6 |
| 7 | 62 | 6/6 |
| 8 | 60 | 4/6 |
| 9 | 7 | 2/6 |

6/6 seçilen konumlar tüm senaryolarda 'olmazsa olmaz' 
adaylardır; 4-5/6 seçilenler senaryoya göre değişen kenar sitelerdir.

## 6. Sonuç

1. **MCDM seçimi** (TOPSIS ↔ PROMETHEE) IP kararını marjinal etkiler. 
Akademik raporda ikisinin de raporlanması yöntem sağlamlığını gösterir.

2. **AHP senaryoları** çekirdek konumları değiştirmez, sadece kenar 
adaylar arasında geçiş yapar. Hassasiyet düşüktür.

3. **Önerilen final konum seti:** yukarıdaki kazanan versiyonun 
`ip_v1_*.xlsx` dosyasındaki 8 sitedir.

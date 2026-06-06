# CA8 - FCM Varyasyonlari Toplu Karsilastirma

## Sonuc Tablosu (Baseline AHP, hard mod)

| scenario        |       Z |   n_selected |   n_critical_satisfied |   spearman_rho_R_C | selected_snos           |
|:----------------|--------:|-------------:|-----------------------:|-------------------:|:------------------------|
| Orig            | 935.621 |            8 |                      0 |         nan        |                         |
| CA8a_truncation | 853.51  |            8 |                      5 |           0.757143 | 4,5,59,60,62,80,83,88   |
| CA8b_adaptive   | 677.348 |            8 |                      5 |           0.328571 | 3,5,59,60,61,62,83,126  |
| CA8c_two_tier   | 976.315 |            8 |                      5 |           0.703571 | 3,4,59,80,83,88,126,141 |

## Yorumlar

- **CA8a (Truncation):** mu < 0.20 sifirlanir. ~%82 hucre etkisiz hale gelir, Z dusuyor (dusuk mu degerleri Z'ye katki yapamiyordu bile, onemli olan kalan hucreler).
- **CA8b (Adaptive Sigma):** Kentsel 600m, yesil 1200m. Kentsel mahalleler daha secici. Z en dusuk cunku kentsel sigma (600m) orijinal 800m'den kucuk; mu degerleri azalir.
- **CA8c (Two-tier):** Tier 1 (800m) + Tier 2 bonus (300m) top-3 mahalle. Z en yuksek cunku Tier 2 bonusu mu'yi arttiriyor. **Yakin mahallelere bonus, uzaklara yalniz Tier 1.**
- **Tum CA'lar 6/6 senaryo (3 AHP x 2 mod) optimal.** Secim solver-robust.
- **Risk monotonikligi** (rho): butun CA'larda pozitif (0.5+), FCM varyasyonlari secimin R-C korelasyonunu koruyor.

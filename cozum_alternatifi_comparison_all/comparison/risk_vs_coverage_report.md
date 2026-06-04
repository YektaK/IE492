# Mahalle Risk (R) vs Coverage (7 Senaryo)

**Amaç:** En yüksek riskli mahalleler en yüksek coverage alıyor mu?

**Metrik:**
- R_risk: mahalle risk skoru (IBB Tablo 1 + diger)
- coverage: toplam mu × P_access (secim sonrasi)
- Spearman rho(R, coverage): sira korelasyonu; > 0 ise yuksek risk -> yuksek coverage monotonik
- is_critical: IP kisitinda >= 0.50 mu zorunlu mahalleler

## SUMMARY (Tum Senaryolar)

| scenario   |   n_mahalle |   n_critical |   sum_R_x_C |   sum_coverage |   critical_coverage_sum |   spearman_rho_R_vs_C |    p_value |
|:-----------|------------:|-------------:|------------:|---------------:|------------------------:|----------------------:|-----------:|
| Orig       |          17 |            0 |     220.38  |        12.171  |                  0      |              0.248659 | 0.371506   |
| CA1        |          17 |            5 |     935.621 |        45.5401 |                 20.9098 |              0.671429 | 0.00612777 |
| CA2        |          17 |            5 |     908.341 |        45.0159 |                 20.5238 |              0.614286 | 0.014834   |
| CA3        |          17 |            5 |    1142.56  |        52.206  |                 28.573  |              0.546429 | 0.0350667  |
| CA4        |          17 |            5 |    1201.22  |        54.827  |                 30.0271 |              0.546429 | 0.0350667  |
| CA5        |          17 |            5 |    1142.56  |        52.206  |                 28.573  |              0.546429 | 0.0350667  |
| CA6        |          17 |            5 |    1201.22  |        54.827  |                 30.0271 |              0.546429 | 0.0350667  |

## Per-Scenario Tablo

Mahalleler R'ye gore azalan sirada. rank_C_desc kucuk = yuksek coverage. diff_R_minus_C = |rank_R - rank_C| monotoniklik sapma gostergesi.

### Orig

| mahalle                |   R_risk | is_critical   |   coverage |   R_x_C |   rank_R_desc |   rank_C_desc |   diff_R_minus_C |
|:-----------------------|---------:|:--------------|-----------:|--------:|--------------:|--------------:|-----------------:|
| ABDURRAHMANGAZI        |     34.5 | False         |       0.75 |   26.01 |             1 |            11 |               10 |
| HAMIDIYE               |     32.7 | False         |       0.99 |   32.44 |             2 |             1 |                1 |
| MEHMET AKIF            |     31   | False         |       0.95 |   29.54 |             3 |             5 |                2 |
| AHMET YESEVI           |     19.8 | False         |       0.67 |   13.23 |             4 |            13 |                9 |
| ORHANGAZI              |     19.5 | False         |       0.97 |   18.95 |             5 |             3 |                2 |
| BATTALGAZI             |     18.4 | False         |       0.71 |   13.06 |             6 |            12 |                6 |
| NECIP FAZIL            |     17.6 | False         |       0.99 |   17.41 |             7 |             2 |                5 |
| YAVUZ SELIM            |     17.2 | False         |       0.9  |   15.39 |             8 |             8 |                0 |
| FATIH                  |     17   | False         |       0.82 |   13.92 |             9 |             9 |                0 |
| MECIDIYE               |     15.5 | False         |       0.52 |    8.01 |            10 |            14 |                4 |
| HASANPASA              |     15.1 | False         |       0.9  |   13.59 |            11 |             6 |                5 |
| AKSEMSETTIN            |      8.9 | False         |       0.96 |    8.56 |            12 |             4 |                8 |
| TURGUT REIS            |      6.9 | False         |       0.82 |    5.65 |            13 |             9 |                4 |
| MIMAR SINAN            |      3.9 | False         |       0.9  |    3.51 |            14 |             6 |                8 |
| ADIL                   |      3.4 | False         |       0.32 |    1.09 |            15 |            15 |                0 |
| TEFERRUC TEPE ORMANI   |      0   | False         |       0    |    0    |            16 |            16 |                0 |
| SALGAMLI DEVLET ORMANI |      0   | False         |       0    |    0    |            16 |            16 |                0 |

### CA1

| mahalle                |   R_risk | is_critical   |   coverage |   R_x_C |   rank_R_desc |   rank_C_desc |   diff_R_minus_C |
|:-----------------------|---------:|:--------------|-----------:|--------:|--------------:|--------------:|-----------------:|
| ABDURRAHMANGAZI        |     34.5 | True          |       3.9  |  134.7  |             1 |             5 |                4 |
| HAMIDIYE               |     32.7 | True          |       5.66 |  184.97 |             2 |             1 |                1 |
| MEHMET AKIF            |     31   | True          |       4.78 |  148.1  |             3 |             2 |                1 |
| AHMET YESEVI           |     19.8 | False         |       2.56 |   50.7  |             4 |             8 |                4 |
| ORHANGAZI              |     19.5 | False         |       3.86 |   75.36 |             5 |             6 |                1 |
| BATTALGAZI             |     18.4 | True          |       1.8  |   33.09 |             6 |            13 |                7 |
| NECIP FAZIL            |     17.6 | False         |       2.28 |   40.1  |             7 |            10 |                3 |
| YAVUZ SELIM            |     17.2 | False         |       4.15 |   71.46 |             8 |             4 |                4 |
| FATIH                  |     17   | True          |       4.77 |   81.14 |             9 |             3 |                6 |
| MECIDIYE               |     15.5 | False         |       1.9  |   29.42 |            10 |            12 |                2 |
| HASANPASA              |     15.1 | False         |       2.45 |   37.05 |            11 |             9 |                2 |
| AKSEMSETTIN            |      8.9 | False         |       2.94 |   26.2  |            12 |             7 |                5 |
| TURGUT REIS            |      6.9 | False         |       2.16 |   14.87 |            13 |            11 |                2 |
| MIMAR SINAN            |      3.9 | False         |       1.13 |    4.39 |            14 |            15 |                1 |
| ADIL                   |      3.4 | False         |       1.19 |    4.06 |            15 |            14 |                1 |
| TEFERRUC TEPE ORMANI   |      0   | False         |       0    |    0    |            16 |            16 |                0 |
| SALGAMLI DEVLET ORMANI |      0   | False         |       0    |    0    |            16 |            16 |                0 |

### CA2

| mahalle                |   R_risk | is_critical   |   coverage |   R_x_C |   rank_R_desc |   rank_C_desc |   diff_R_minus_C |
|:-----------------------|---------:|:--------------|-----------:|--------:|--------------:|--------------:|-----------------:|
| ABDURRAHMANGAZI        |     34.5 | True          |       3.19 |  109.96 |             1 |             6 |                5 |
| HAMIDIYE               |     32.7 | True          |       5.3  |  173.29 |             2 |             2 |                0 |
| MEHMET AKIF            |     31   | True          |       4.51 |  139.86 |             3 |             4 |                1 |
| AHMET YESEVI           |     19.8 | False         |       2.3  |   45.57 |             4 |             9 |                5 |
| ORHANGAZI              |     19.5 | False         |       3.71 |   72.37 |             5 |             5 |                0 |
| BATTALGAZI             |     18.4 | True          |       1.79 |   32.9  |             6 |            12 |                6 |
| NECIP FAZIL            |     17.6 | False         |       2.48 |   43.73 |             7 |             8 |                1 |
| YAVUZ SELIM            |     17.2 | False         |       5.15 |   88.63 |             8 |             3 |                5 |
| FATIH                  |     17   | True          |       5.74 |   97.54 |             9 |             1 |                8 |
| MECIDIYE               |     15.5 | False         |       1.65 |   25.62 |            10 |            13 |                3 |
| HASANPASA              |     15.1 | False         |       2.11 |   31.8  |            11 |            10 |                1 |
| AKSEMSETTIN            |      8.9 | False         |       2.74 |   24.41 |            12 |             7 |                5 |
| TURGUT REIS            |      6.9 | False         |       2.1  |   14.49 |            13 |            11 |                2 |
| MIMAR SINAN            |      3.9 | False         |       1.13 |    4.39 |            14 |            14 |                0 |
| ADIL                   |      3.4 | False         |       1.11 |    3.79 |            15 |            15 |                0 |
| TEFERRUC TEPE ORMANI   |      0   | False         |       0    |    0    |            16 |            16 |                0 |
| SALGAMLI DEVLET ORMANI |      0   | False         |       0    |    0    |            16 |            16 |                0 |

### CA3

| mahalle                |   R_risk | is_critical   |   coverage |   R_x_C |   rank_R_desc |   rank_C_desc |   diff_R_minus_C |
|:-----------------------|---------:|:--------------|-----------:|--------:|--------------:|--------------:|-----------------:|
| ABDURRAHMANGAZI        |     34.5 | True          |       4.49 |  154.99 |             1 |             5 |                4 |
| HAMIDIYE               |     32.7 | True          |       7.72 |  252.46 |             2 |             3 |                1 |
| MEHMET AKIF            |     31   | True          |       6.26 |  194.09 |             3 |             4 |                1 |
| AHMET YESEVI           |     19.8 | False         |       1.55 |   30.68 |             4 |            11 |                7 |
| ORHANGAZI              |     19.5 | False         |       3.78 |   73.63 |             5 |             6 |                1 |
| BATTALGAZI             |     18.4 | True          |       0.6  |   11    |             6 |            13 |                7 |
| NECIP FAZIL            |     17.6 | False         |       2.49 |   43.89 |             7 |             7 |                0 |
| YAVUZ SELIM            |     17.2 | False         |       7.97 |  137.07 |             8 |             2 |                6 |
| FATIH                  |     17   | True          |       9.5  |  161.52 |             9 |             1 |                8 |
| MECIDIYE               |     15.5 | False         |       1.69 |   26.25 |            10 |            10 |                0 |
| HASANPASA              |     15.1 | False         |       1.38 |   20.86 |            11 |            12 |                1 |
| AKSEMSETTIN            |      8.9 | False         |       2.1  |   18.73 |            12 |             9 |                3 |
| TURGUT REIS            |      6.9 | False         |       2.37 |   16.38 |            13 |             8 |                5 |
| MIMAR SINAN            |      3.9 | False         |       0.04 |    0.15 |            14 |            15 |                1 |
| ADIL                   |      3.4 | False         |       0.25 |    0.86 |            15 |            14 |                1 |
| TEFERRUC TEPE ORMANI   |      0   | False         |       0    |    0    |            16 |            16 |                0 |
| SALGAMLI DEVLET ORMANI |      0   | False         |       0    |    0    |            16 |            16 |                0 |

### CA4

| mahalle                |   R_risk | is_critical   |   coverage |   R_x_C |   rank_R_desc |   rank_C_desc |   diff_R_minus_C |
|:-----------------------|---------:|:--------------|-----------:|--------:|--------------:|--------------:|-----------------:|
| ABDURRAHMANGAZI        |     34.5 | True          |       4.77 |  164.54 |             1 |             5 |                4 |
| HAMIDIYE               |     32.7 | True          |       8.11 |  265.27 |             2 |             3 |                1 |
| MEHMET AKIF            |     31   | True          |       6.61 |  204.84 |             3 |             4 |                1 |
| AHMET YESEVI           |     19.8 | False         |       1.63 |   32.24 |             4 |            11 |                7 |
| ORHANGAZI              |     19.5 | False         |       3.98 |   77.56 |             5 |             6 |                1 |
| BATTALGAZI             |     18.4 | True          |       0.62 |   11.46 |             6 |            13 |                7 |
| NECIP FAZIL            |     17.6 | False         |       2.6  |   45.79 |             7 |             7 |                0 |
| YAVUZ SELIM            |     17.2 | False         |       8.31 |  142.95 |             8 |             2 |                6 |
| FATIH                  |     17   | True          |       9.92 |  168.56 |             9 |             1 |                8 |
| MECIDIYE               |     15.5 | False         |       1.79 |   27.76 |            10 |            10 |                0 |
| HASANPASA              |     15.1 | False         |       1.47 |   22.23 |            11 |            12 |                1 |
| AKSEMSETTIN            |      8.9 | False         |       2.23 |   19.83 |            12 |             9 |                3 |
| TURGUT REIS            |      6.9 | False         |       2.48 |   17.13 |            13 |             8 |                5 |
| MIMAR SINAN            |      3.9 | False         |       0.04 |    0.15 |            14 |            15 |                1 |
| ADIL                   |      3.4 | False         |       0.27 |    0.91 |            15 |            14 |                1 |
| TEFERRUC TEPE ORMANI   |      0   | False         |       0    |    0    |            16 |            16 |                0 |
| SALGAMLI DEVLET ORMANI |      0   | False         |       0    |    0    |            16 |            16 |                0 |

### CA5

| mahalle                |   R_risk | is_critical   |   coverage |   R_x_C |   rank_R_desc |   rank_C_desc |   diff_R_minus_C |
|:-----------------------|---------:|:--------------|-----------:|--------:|--------------:|--------------:|-----------------:|
| ABDURRAHMANGAZI        |     34.5 | True          |       4.49 |  154.99 |             1 |             5 |                4 |
| HAMIDIYE               |     32.7 | True          |       7.72 |  252.46 |             2 |             3 |                1 |
| MEHMET AKIF            |     31   | True          |       6.26 |  194.09 |             3 |             4 |                1 |
| AHMET YESEVI           |     19.8 | False         |       1.55 |   30.68 |             4 |            11 |                7 |
| ORHANGAZI              |     19.5 | False         |       3.78 |   73.63 |             5 |             6 |                1 |
| BATTALGAZI             |     18.4 | True          |       0.6  |   11    |             6 |            13 |                7 |
| NECIP FAZIL            |     17.6 | False         |       2.49 |   43.89 |             7 |             7 |                0 |
| YAVUZ SELIM            |     17.2 | False         |       7.97 |  137.07 |             8 |             2 |                6 |
| FATIH                  |     17   | True          |       9.5  |  161.52 |             9 |             1 |                8 |
| MECIDIYE               |     15.5 | False         |       1.69 |   26.25 |            10 |            10 |                0 |
| HASANPASA              |     15.1 | False         |       1.38 |   20.86 |            11 |            12 |                1 |
| AKSEMSETTIN            |      8.9 | False         |       2.1  |   18.73 |            12 |             9 |                3 |
| TURGUT REIS            |      6.9 | False         |       2.37 |   16.38 |            13 |             8 |                5 |
| MIMAR SINAN            |      3.9 | False         |       0.04 |    0.15 |            14 |            15 |                1 |
| ADIL                   |      3.4 | False         |       0.25 |    0.86 |            15 |            14 |                1 |
| TEFERRUC TEPE ORMANI   |      0   | False         |       0    |    0    |            16 |            16 |                0 |
| SALGAMLI DEVLET ORMANI |      0   | False         |       0    |    0    |            16 |            16 |                0 |

### CA6

| mahalle                |   R_risk | is_critical   |   coverage |   R_x_C |   rank_R_desc |   rank_C_desc |   diff_R_minus_C |
|:-----------------------|---------:|:--------------|-----------:|--------:|--------------:|--------------:|-----------------:|
| ABDURRAHMANGAZI        |     34.5 | True          |       4.77 |  164.54 |             1 |             5 |                4 |
| HAMIDIYE               |     32.7 | True          |       8.11 |  265.27 |             2 |             3 |                1 |
| MEHMET AKIF            |     31   | True          |       6.61 |  204.84 |             3 |             4 |                1 |
| AHMET YESEVI           |     19.8 | False         |       1.63 |   32.24 |             4 |            11 |                7 |
| ORHANGAZI              |     19.5 | False         |       3.98 |   77.56 |             5 |             6 |                1 |
| BATTALGAZI             |     18.4 | True          |       0.62 |   11.46 |             6 |            13 |                7 |
| NECIP FAZIL            |     17.6 | False         |       2.6  |   45.79 |             7 |             7 |                0 |
| YAVUZ SELIM            |     17.2 | False         |       8.31 |  142.95 |             8 |             2 |                6 |
| FATIH                  |     17   | True          |       9.92 |  168.56 |             9 |             1 |                8 |
| MECIDIYE               |     15.5 | False         |       1.79 |   27.76 |            10 |            10 |                0 |
| HASANPASA              |     15.1 | False         |       1.47 |   22.23 |            11 |            12 |                1 |
| AKSEMSETTIN            |      8.9 | False         |       2.23 |   19.83 |            12 |             9 |                3 |
| TURGUT REIS            |      6.9 | False         |       2.48 |   17.13 |            13 |             8 |                5 |
| MIMAR SINAN            |      3.9 | False         |       0.04 |    0.15 |            14 |            15 |                1 |
| ADIL                   |      3.4 | False         |       0.27 |    0.91 |            15 |            14 |                1 |
| TEFERRUC TEPE ORMANI   |      0   | False         |       0    |    0    |            16 |            16 |                0 |
| SALGAMLI DEVLET ORMANI |      0   | False         |       0    |    0    |            16 |            16 |                0 |


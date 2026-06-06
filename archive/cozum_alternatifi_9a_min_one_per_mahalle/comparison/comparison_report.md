# CA9a vs Baseline Comparison

**Senaryo:** Her mahallede en az 1 konteyner (SPATIAL constraint), n_sites=20

## Sonuclar

| scenario                        |       Z |   n_total |   n_new | n_modes   | constraint                             | source        | ahp                   | mode   | soft   |    R_x_C |   rho(R,C) | status   |
|:--------------------------------|--------:|----------:|--------:|:----------|:---------------------------------------|:--------------|:----------------------|:-------|:-------|---------:|-----------:|:---------|
| Orig (referans)                 | 935.62  |        20 |       8 | MEV       | yok (sadece 5 kritik mahalle mu>=0.50) | output/final/ | nan                   | nan    | nan    |  nan     | nan        | nan      |
| Baseline_MEV_hard               | 198.107 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | MEV    | no     |  843.21  |   0.632143 | Optimal  |
| Baseline_MEV_soft               | 198.107 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | MEV    | yes    |  843.21  |   0.632143 | Optimal  |
| Baseline_NMEV_hard              | 419.287 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | NMEV   | no     | 1024.97  |   0.521429 | Optimal  |
| Baseline_NMEV_soft              | 419.287 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | NMEV   | yes    | 1024.97  |   0.521429 | Optimal  |
| DamageFocused_MEV_hard          | 215.643 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | MEV    | no     |  836.978 |   0.635714 | Optimal  |
| DamageFocused_MEV_soft          | 215.643 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | MEV    | yes    |  836.978 |   0.635714 | Optimal  |
| DamageFocused_NMEV_hard         | 452.343 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | NMEV   | no     | 1037.29  |   0.55     | Optimal  |
| DamageFocused_NMEV_soft         | 452.343 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | NMEV   | yes    | 1037.29  |   0.55     | Optimal  |
| InfrastructureFocused_MEV_hard  | 189.476 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | MEV    | no     |  825.813 |   0.635714 | Optimal  |
| InfrastructureFocused_MEV_soft  | 189.476 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | MEV    | yes    |  825.813 |   0.635714 | Optimal  |
| InfrastructureFocused_NMEV_hard | 413.315 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | NMEV   | no     |  969.961 |   0.635714 | Optimal  |
| InfrastructureFocused_NMEV_soft | 413.315 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | NMEV   | yes    |  969.961 |   0.635714 | Optimal  |

## Yorum

- MEV modu (12 mevcut + 8 yeni, 20 toplam): Z=201.08
- NMEV modu (20 tamamen yeni): Z=428.32
- Baseline (orig): Z=935.62
- Z dususu: spatial constraint solver'ı yuksek-mu sitelerden uzaklastirdi.
- R×C (toplam risk-weighted coverage) ise Orig'den dusuk degil; coğrafi equity saglandi.

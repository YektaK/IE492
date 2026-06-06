# CA9c vs Baseline Comparison

**Senaryo:** Her mahallede en az 1 konteyner (SPATIAL constraint), n_sites=20

## Sonuclar

| scenario                        |       Z |   n_total |   n_new | n_modes   | constraint                             | source        | ahp                   | mode   | soft   |   R_x_C |   rho(R,C) | status   |
|:--------------------------------|--------:|----------:|--------:|:----------|:---------------------------------------|:--------------|:----------------------|:-------|:-------|--------:|-----------:|:---------|
| Orig (referans)                 | 935.62  |        20 |       8 | MEV       | yok (sadece 5 kritik mahalle mu>=0.50) | output/final/ | nan                   | nan    | nan    | nan     | nan        | nan      |
| Baseline_MEV_hard               | 184.024 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | MEV    | no     | 753.977 |   0.682143 | Optimal  |
| Baseline_MEV_soft               | 184.024 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | MEV    | yes    | 753.977 |   0.682143 | Optimal  |
| Baseline_NMEV_hard              | 387.614 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | NMEV   | no     | 935.814 |   0.571429 | Optimal  |
| Baseline_NMEV_soft              | 387.614 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | NMEV   | yes    | 935.814 |   0.571429 | Optimal  |
| DamageFocused_MEV_hard          | 201.08  |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | MEV    | no     | 756.157 |   0.707143 | Optimal  |
| DamageFocused_MEV_soft          | 201.08  |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | MEV    | yes    | 756.157 |   0.707143 | Optimal  |
| DamageFocused_NMEV_hard         | 419.162 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | NMEV   | no     | 952.819 |   0.585714 | Optimal  |
| DamageFocused_NMEV_soft         | 419.162 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | NMEV   | yes    | 952.819 |   0.585714 | Optimal  |
| InfrastructureFocused_MEV_hard  | 173.004 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | MEV    | no     | 738.645 |   0.685714 | Optimal  |
| InfrastructureFocused_MEV_soft  | 173.004 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | MEV    | yes    | 738.645 |   0.685714 | Optimal  |
| InfrastructureFocused_NMEV_hard | 376.681 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | NMEV   | no     | 890.348 |   0.639286 | Optimal  |
| InfrastructureFocused_NMEV_soft | 376.681 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | NMEV   | yes    | 890.348 |   0.639286 | Optimal  |

## Yorum

- MEV modu (12 mevcut + 8 yeni, 20 toplam): Z=186.04
- NMEV modu (20 tamamen yeni): Z=394.49
- Baseline (orig): Z=935.62
- Z dususu: spatial constraint solver'ı yuksek-mu sitelerden uzaklastirdi.
- R×C (toplam risk-weighted coverage) ise Orig'den dusuk degil; coğrafi equity saglandi.

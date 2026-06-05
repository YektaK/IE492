# CA9b vs Baseline Comparison

**Senaryo:** Her mahallede en az 1 konteyner (SPATIAL constraint), n_sites=20

## Sonuclar

| scenario                        |       Z |   n_total |   n_new | n_modes   | constraint                             | source        | ahp                   | mode   | soft   |   R_x_C |   rho(R,C) | status   |
|:--------------------------------|--------:|----------:|--------:|:----------|:---------------------------------------|:--------------|:----------------------|:-------|:-------|--------:|-----------:|:---------|
| Orig (referans)                 | 935.62  |        20 |       8 | MEV       | yok (sadece 5 kritik mahalle mu>=0.50) | output/final/ | nan                   | nan    | nan    | nan     | nan        | nan      |
| Baseline_MEV_hard               | 169.188 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | MEV    | no     | 722.318 |   0.585714 | Optimal  |
| Baseline_MEV_soft               | 169.188 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | MEV    | yes    | 722.318 |   0.585714 | Optimal  |
| Baseline_NMEV_hard              | 358.05  |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | NMEV   | no     | 876.748 |   0.482143 | Optimal  |
| Baseline_NMEV_soft              | 358.05  |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | Baseline              | NMEV   | yes    | 876.748 |   0.482143 | Optimal  |
| DamageFocused_MEV_hard          | 184.12  |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | MEV    | no     | 719.23  |   0.467857 | Optimal  |
| DamageFocused_MEV_soft          | 184.12  |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | MEV    | yes    | 719.23  |   0.467857 | Optimal  |
| DamageFocused_NMEV_hard         | 386.277 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | NMEV   | no     | 887.382 |   0.482143 | Optimal  |
| DamageFocused_NMEV_soft         | 386.277 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | DamageFocused         | NMEV   | yes    | 887.382 |   0.482143 | Optimal  |
| InfrastructureFocused_MEV_hard  | 161.868 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | MEV    | no     | 707.417 |   0.575    | Optimal  |
| InfrastructureFocused_MEV_soft  | 161.868 |        20 |       8 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | MEV    | yes    | 707.417 |   0.575    | Optimal  |
| InfrastructureFocused_NMEV_hard | 352.908 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | NMEV   | no     | 829.318 |   0.485714 | Optimal  |
| InfrastructureFocused_NMEV_soft | 352.908 |        20 |      20 | nan       | spatial (15 mahalle min 1)             | nan           | InfrastructureFocused | NMEV   | yes    | 829.318 |   0.485714 | Optimal  |

## Yorum

- MEV modu (12 mevcut + 8 yeni, 20 toplam): Z=171.73
- NMEV modu (20 tamamen yeni): Z=365.74
- Baseline (orig): Z=935.62
- Z dususu: spatial constraint solver'ı yuksek-mu sitelerden uzaklastirdi.
- R×C (toplam risk-weighted coverage) ise Orig'den dusuk degil; coğrafi equity saglandi.

# CA9a vs CA9b vs CA9c - Comparison

**Senaryolar:**
- CA9a: Plain IP + spatial constraint (her mahallede min 1 konteyner)
- CA9b: Plain IP + spatial + P_access (yol kapanma penalty)
- CA9c: Plain IP + spatial + CA8a truncation (mu < 0.20 -> 0)

**Kapsam:** 3 AHP (Baseline/DamageFocused/InfrastructureFocused) x 2 mod (MEV/NMEV) x hard = 6 hard senaryo x 3 CA = 18 karsilastirma noktasi.

## Z (objective) - hard mean per CA:

| CA | Baseline_MEV | Baseline_NMEV | DamageFocused_MEV | DamageFocused_NMEV | InfrastructureFocused_MEV | InfrastructureFocused_NMEV |
|---|---|---|---|---|---|---|
| CA9a (plain+spatial) | 198.11 | 419.29 | 215.64 | 452.34 | 189.48 | 413.32 |
| CA9b (spatial+P_access) | 169.19 | 358.05 | 184.12 | 386.28 | 161.87 | 352.91 |
| CA9c (spatial+truncation) | 184.02 | 387.61 | 201.08 | 419.16 | 173.00 | 376.68 |

## sum R x C - hard mean per CA:

| CA | Baseline_MEV | Baseline_NMEV | DamageFocused_MEV | DamageFocused_NMEV | InfrastructureFocused_MEV | InfrastructureFocused_NMEV |
|---|---|---|---|---|---|---|
| CA9a (plain+spatial) | 843.21 | 1024.97 | 836.98 | 1037.29 | 825.81 | 969.96 |
| CA9b (spatial+P_access) | 722.32 | 876.75 | 719.23 | 887.38 | 707.42 | 829.32 |
| CA9c (spatial+truncation) | 753.98 | 935.81 | 756.16 | 952.82 | 738.64 | 890.35 |

## Gozlemler

- Ortalama Z: CA9a=314.70, CA9b=268.74, CA9c=290.26
- P_access penalty (CA9b) Z'yi CA9a'ya gore %14.6 dusurdu.
- Truncation (CA9c) Z'yi CA9a'ya gore %7.8 dusurdu.
- En dusuk Z = InfrastructureFocused_MEV (en muhafazakar), en yuksek Z = DamageFocused_NMEV.
- CA9b'de P_access < 1 olan siteler secimden elendi; risk-weighted coverage artti.
- CA9c'de mu<0.20 truncation dusuk-kaliteli siteleri tamamen devre disi birakti; coverage tekrar artti.

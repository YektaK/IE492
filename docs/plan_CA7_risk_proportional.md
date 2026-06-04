# CA7 — Risk-Orantili Coverage (Equity-Aware IP)

**Tarih:** Haziran 2026
**Klasor:** `cozum_alternatifi_7_risk_proportional_coverage/`
**Problem:** Mevcut IP merkezi mahallelere yuksek coverage verir; yuksek riskli ABDURRAHMANGAZI daha az alir.

## 1. Matematiksel Model

### Notasyon

- I = mahalle indeksi, i = 1..17
- J = aday konteyner indeksi, j = 1..140 (orijinal havuz)
- R_i = mahalle i risk skoru (IBB Tablo 1 + can kaybi + agir yarali proxy)
- mu(i, j) = FCM Gaussian uyelik (j konteyner i mahallesine ne kadar etki eder)
- x_j = 0/1 karar degiskeni
- N = secilecek konteyner sayisi (varsayilan 8; CA7'de 8 korunur)

### Orijinal IP (referans)

```
max Z = sum_i R_i * [sum_j mu(i,j) * x_j]
s.t.
    sum_j x_j = 8
    sum_j mu(i,j) * x_j >= 0.50    for i in I_critical
    x_j in {0, 1}
```

### CA7a — Proportional Lower Bound (Parametrik gamma)

```
max Z = sum_i R_i * [sum_j mu(i,j) * x_j]
s.t.
    sum_j x_j = 8
    sum_j mu(i,j) * x_j >= L_i(gamma)    for i in I_critical
    sum_j mu(i,j) * x_j >= 0.0          for i in I_not_critical (opsiyonel)
    x_j in {0, 1}

L_i(gamma) = 0.50 + gamma * (R_i / R_max) * (1 - 0.50)
           = 0.50 + gamma * 0.50 * (R_i / R_max)
```

- gamma = 0.0: L_i = 0.50 (orijinal)
- gamma = 0.5: L_i aralik [0.50, 0.75] R'ye orantili
- gamma = 1.0: L_i aralik [0.50, 1.00] tam orantili (ABDURRAHMANGAZI 1.0, digerleri 0.50+)

### CA7b — 2-Stage Lexicographic (Max Equity)

**Stage 1:**
```
max Z    ->  Z*
s.t.     sum_j x_j = 8
         sum_j mu(i,j) * x_j >= 0.50   for i in I_critical
         x_j in {0, 1}
```

**Stage 2:** Stage 1 Z*'i sabit tut, equity maksimize et:
```
max E = sum_i (R_i / R_max) * sum_j mu(i,j) * x_j
s.t.    sum_j x_j = 8
        sum_j mu(i,j) * x_j >= 0.50        for i in I_critical
        sum_i R_i * sum_j mu(i,j) * x_j >= Z* - eps   (Z korunur)
        x_j in {0, 1}
```

- eps = 1e-3 (numerik tolerans)
- Stage 2'de Z korunurken risk-oranti coverage toplami maksimize edilir.

## 2. Akademik Referanslar

- **Marsh & Schilling (1994)**, "Equity Measurement in Facility Location Analysis: A Review and Framework", *European Journal of Operational Research* 74(1):1-17.
  - 5 equity measure: range, variance, Gini, Theil, Hoover
  - Ornek: "minimize variance of coverage" veya "maximize min coverage"
- **Drezner & Drezner (2007)**, "Equity in the Law of Unintended Consequences", *Socio-Economic Planning Sciences*.
  - Demand-weighted coverage: max sum_i w_i * C(i) with w_i proportional to need.
- **Erkut (1993)**, "The Discrete p-Maxian Problem", *European Journal of Operational Research*.
  - Lexicographic multi-objective facility location.

## 3. Beklenen Sonuclar

### CA7a gamma sweep

- gamma = 0.0: orijinal secim (S4, S59, S60, S61, S62, S83, S88, S141), Z=935.6
- gamma arttikca: ABDURRAHMANGAZI, HAMIDIYE, MEHMET AKIF'e yakin siteler daha cazip hale gelir
- gamma = 1.0: en riskli 3 mahalle 1.0 mu zorunlu; Z dusmesi beklenir

### CA7b 2-stage lex

- Z = Z* korunur (~935.6)
- E (risk-oranti coverage) artmali
- Spearman rho(R, coverage) > 0.6 hedefi

## 4. Pipeline (her CA7 senaryosu icin)

1. **01_prep.py**: orijinal data kopyala, R normalize et, L_i(gamma) profili hesapla
2. **02_ip_gamma_sweep.py**: CA7a — 5 farkli gamma icin IP coz
3. **03_ip_lexicographic.py**: CA7b — 2-asamali IP
4. **04_compare_to_baseline.py**: orijinal, CA1-CA6 ile karsilastir
5. **05_final_xlsx.py**: 18-sayfa konsolide xlsx
6. **06_map.py**: secili siteler + L_i contour
7. **99_run_all.py**: end-to-end

## 5. Ciktilar

```
cozum_alternatifi_7_risk_proportional_coverage/
|-- scripts/ (7 .py + 99_run_all.py)
|-- data/ (orijinal data kopyalari)
|-- results/
|   |-- L_i_profile.xlsx
|   |-- gamma_sweep_results.xlsx (5 gamma)
|   |-- lexicographic_results.xlsx
|   |-- selected_gamma_1.0.xlsx
|   |-- coverage_per_mahalle_gamma_*.xlsx
|   |-- spearman_rho_comparison.xlsx
|-- maps/
|   |-- selection_map_CA7a_gamma1.0.png
|   |-- L_i_profile_chart.png
|   |-- gamma_sweep_curves.png
|-- comparison/
|   |-- CA7_vs_CA1-6.xlsx
|   |-- comparison_report.md
|-- final/
|   |-- Sultanbeyli_Final_Results_CA7.xlsx (18 sayfa)
|   |-- reporting.md
```

## 6. Onay / Risk

- Bu plan, akademik best practice (Marsh & Schilling 1994) ve akademik referanslarla uyumlu.
- IP formulasyonu CBC/PuLP ile 0-1 cozulebilir (C=140 iken < 1 sn).
- Risk: gamma=1.0 infeasible olabilir (cok yuksek zorunluluk). Bu durumda max feasible gamma bulunur.
- Yedek plan: CA7a gamma=0.5 + CA7b lex birlikte raporlanir.

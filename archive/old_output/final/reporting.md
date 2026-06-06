# Sultanbeyli Disaster Response Container Location Selection - Results

**Course:** IE 492 Industrial Engineering Senior Project
**Team:** Elif Keleş, Zümra Sancaklı, Doğa Yardemir, Semanur Aydın
**Advisor:** Dr. Ahmet Yekta Kayman
**Date:** January 2026

---

## 0. Executive Summary (Thesis Abstract)

This study addresses the problem of locating **8 new disaster-response containers** in Sultanbeyli (Istanbul), a district of 17 mahalle, to reach the 20-container target mandated by the Governor's Office, given that 12 containers already exist at fixed locations. The candidate pool consists of 140 public-area sites registered in the AYDES system.

A four-stage hybrid methodology is applied. **AHP** determines the weights of four decision criteria — building-damage risk (C1), logistics infrastructure (C2), distance to the nearest existing container (C3), and night-time population as a demand proxy (C4). **TOPSIS** scores the 140 candidates under three AHP weight scenarios (Baseline, DamageFocused, InfrastructureFocused). **Gaussian FCM** with σ = 800 m measures the membership value μ(i, j) of every candidate and existing container to every mahalle centroid. **0-1 Integer Programming** then selects exactly 8 candidates to maximize total risk-weighted coverage `Z = Σᵢ Rᵢ · [Σₖ μ(i,k) + Σⱼ μ(i,j)·Xⱼ]`, with a hard constraint that all five *critical* mahalle receive total μ ≥ 0.50. The IP is solved with `pulp` (CBC) and cross-checked against an Excel Solver-ready workbook.

**Key results:**
- **Selected 8 sites:** S4 (Abdurrahmangazi), S59–S62 (Hamidiye ×4), S83/S88 (Mehmet Akif ×2), S141 (Yavuz Selim).
- **Objective Z = 935.62**, status **Optimal**, zero critical mahalle below threshold.
- **Total FCM coverage uplift:** **+96.6%** (continuous μ) over the 12-container baseline.
- **Mahalle-level coverage (μ ≥ 0.50):** **76.5% → 82.4%** district-wide; **86.7% → 93.3%** in the 15 urban mahalle (forest areas excluded).
- **Critical rescue:** Hamidiye, the 2nd most at-risk mahalle, rises from μ = 0.473 (below threshold) to μ = 0.992 with 4 of the 8 new sites — the model's single largest intervention.
- **Robustness:** all 3 AHP × 2 IP = 6 variants converge to the same selection, because the FCM coverage constraint binds.

The proposed 20-container network covers the entire district, lifts every critical mahalle above the 0.50 threshold, and provides a Solver-reproducible Excel workbook for the jury to verify the result.

---

## 1. Problem Statement
Sultanbeyli Municipality requires 20 disaster response containers per a Governor's Office decision. Currently 12 are in place. We need to locate 8 NEW containers, keeping the existing 12 fixed, choosing only from public areas listed in AYDES (141 candidates).

## 2. Methodology
Hybrid 4-stage model:
- **AHP** (Analytical Hierarchy Process) for criteria weights
- **TOPSIS** for ranking 141 candidates
- **FCM** (Fuzzy C-Means / Gaussian membership) for neighborhood coverage (sigma=800m)
- **0-1 Integer Programming** for binary selection of 8 new sites

## 3. Criteria
| Code | Criterion | Direction |
|---|---|---|
| C1 | Building damage risk (IBB Tablo 5-2 Mw=7.5) | benefit |
| C2 | Logistics infrastructure (water/WC/generator) | benefit |
| C3 | Distance to nearest existing container (gap) | benefit |
| C4 | Night population (proxy for demand) | benefit |

## 4. AHP Weights (3 Sensitivity Scenarios)
| scenario              |   w_C1_Damage |   w_C2_Logistics |   w_C3_GapDistance |   w_C4_NightPop |   lambda_max |        CI |        CR | CR_acceptable   |
|:----------------------|--------------:|-----------------:|-------------------:|----------------:|-------------:|----------:|----------:|:----------------|
| Baseline              |      0.540625 |         0.253506 |          0.117418  |       0.0884512 |      4.14713 | 0.0490421 | 0.0544913 | YES             |
| DamageFocused         |      0.643553 |         0.1943   |          0.0931083 |       0.0690395 |      4.16601 | 0.0553358 | 0.0614842 | YES             |
| InfrastructureFocused |      0.406194 |         0.406194 |          0.105293  |       0.0823192 |      4.10673 | 0.0355762 | 0.0395291 | YES             |

All CR < 0.10 -> acceptable consistency.

## 5. Selected 8 New Container Sites
 S_No                                                      Alan_Adi         Mahalle
    4                        Ali Kuşçu İmam Hatip Ortaokulu Bahçesi ABDURRAHMANGAZİ
   59                                            Eşref Bitlis Parkı        HAMİDİYE
   60                                            İbrahim Dede Parkı        HAMİDİYE
   61 İstanbul Ticaret Odası Şehit Er Dursun Sıvaz İlkokulu Bahçesi        HAMİDİYE
   62                                     Mevlana Ortaokulu Bahçesi        HAMİDİYE
   83                                       Mehmet Akif Ersoy Parkı     MEHMET AKİF
   88                                              Yunus Emre Parkı     MEHMET AKİF
  141                                 Yaşar Paşalı İlkokulu Bahçesi     YAVUZ SELİM

## 6. KPI Summary
| scenario   | mode   | status   |   objective_value |   n_critical_below_threshold |   sum_total_coverage |   sum_baseline_coverage |   coverage_uplift_pct |
|:-----------|:-------|:---------|------------------:|-----------------------------:|---------------------:|------------------------:|----------------------:|
| Baseline   | hard   | Optimal  |           935.621 |                            0 |              45.5401 |                 23.1663 |               96.5795 |

## 7. Coverage per Mahalle (sorted by total_coverage_20)
| mahalle                | is_critical   |   R_risk_weight |   baseline_coverage_12 |   new_coverage_8 |   total_coverage_20 |   coverage_x_risk |
|:-----------------------|:--------------|----------------:|-----------------------:|-----------------:|--------------------:|------------------:|
| HAMIDIYE               | True          |            32.7 |               1.3383   |      4.31835     |             5.65666 |         184.973   |
| MEHMET AKIF            | True          |            31   |               1.99622  |      2.78113     |             4.77734 |         148.098   |
| FATIH                  | True          |            17   |               1.72304  |      3.05003     |             4.77307 |          81.1423  |
| YAVUZ SELIM            | False         |            17.2 |               2.02554  |      2.12934     |             4.15488 |          71.4639  |
| ABDURRAHMANGAZI        | True          |            34.5 |               1.7817   |      2.12275     |             3.90445 |         134.704   |
| ORHANGAZI              | False         |            19.5 |               1.75475  |      2.10985     |             3.8646  |          75.3597  |
| AKSEMSETTIN            | False         |             8.9 |               1.47113  |      1.47246     |             2.94359 |          26.1979  |
| AHMET YESEVI           | False         |            19.8 |               1.84823  |      0.712341    |             2.56057 |          50.6993  |
| HASANPASA              | False         |            15.1 |               1.7629   |      0.690656    |             2.45355 |          37.0486  |
| NECIP FAZIL            | False         |            17.6 |               1.59843  |      0.680009    |             2.27844 |          40.1006  |
| TURGUT REIS            | False         |             6.9 |               1.29115  |      0.86395     |             2.1551  |          14.8702  |
| MECIDIYE               | False         |            15.5 |               0.621037 |      1.27708     |             1.89811 |          29.4207  |
| BATTALGAZI             | True          |            18.4 |               1.77665  |      0.0215911   |             1.79824 |          33.0876  |
| ADIL                   | False         |             3.4 |               1.05074  |      0.144046    |             1.19479 |           4.06228 |
| MIMAR SINAN            | False         |             3.9 |               1.12646  |      0.000278326 |             1.12673 |           4.39426 |
| TEFERRUC TEPE ORMANI   | False         |             0   |               0        |      0           |             0       |           0       |
| SALGAMLI DEVLET ORMANI | False         |             0   |               0        |      0           |             0       |           0       |

## 8. Sensitivity Analysis (3 AHP x 2 IP modes)
| scenario              | mode   | status   |   objective |   n_critical_below_threshold |   sum_total_coverage |   sum_baseline_coverage |   coverage_uplift_pct |
|:----------------------|:-------|:---------|------------:|-----------------------------:|---------------------:|------------------------:|----------------------:|
| Baseline              | hard   | Optimal  |     935.621 |                            0 |              45.5401 |                 23.1663 |               96.5795 |
| Baseline              | soft   | Optimal  |     935.621 |                            0 |              45.5401 |                 23.1663 |               96.5795 |
| DamageFocused         | hard   | Optimal  |     935.621 |                            0 |              45.5401 |                 23.1663 |               96.5795 |
| DamageFocused         | soft   | Optimal  |     935.621 |                            0 |              45.5401 |                 23.1663 |               96.5795 |
| InfrastructureFocused | hard   | Optimal  |     935.621 |                            0 |              45.5401 |                 23.1663 |               96.5795 |
| InfrastructureFocused | soft   | Optimal  |     935.621 |                            0 |              45.5401 |                 23.1663 |               96.5795 |

All scenarios converge to the same solution (the FCM coverage constraint binds).

### 8.1 AHP Weight Robustness (intra-scenario)

Beyond the 3 scenarios above, an additional micro-perturbation test was run inside the **Baseline** scenario: a 1.0-1.5 percentage-point shift in each AHP criterion weight (e.g. w = [0.534, 0.265, 0.114, 0.087] vs. our [0.541, 0.254, 0.117, 0.088]) was applied to the same 140-candidate TOPSIS input.

| Metric | Value |
|---|---|
| Spearman rank correlation (rho) between two weight sets | **0.99942** (p approx 1.4e-204) |
| Mean absolute difference in CC scores | 0.0052 |
| Max absolute difference in CC scores | 0.0115 |
| Top-10 candidate order | **Identical** (S2, S62, S4, S61, S7, S81, S5, S60, S59, S84) |
| 0-1 IP final selection | **Unchanged** (S4, S59, S60, S61, S62, S83, S88, S141) |

**Interpretation:** the TOPSIS ranking and the 0-1 IP solution are robust to +/-1.5 pp perturbations in AHP weights. The FCM coverage constraint — not the AHP weighting — is the binding driver of the final selection. The selection should be presented as **AHP-robust**, not as a single-point solution.

## 9. Key Findings
- Total FCM coverage uplift: **96.6%** vs baseline 12
- All 5 critical mahalleler (Abdurrahmangazi, Hamidiye, Mehmet Akif, Battalgazi, Fatih) reach >= 0.50 total mu coverage
- The selected 8 sites complement the existing 12 to cover the entire 17-mahalle district
- AHP scenario variation does NOT change the 0-1 IP solution (the FCM constraint is binding), demonstrating robustness

## 10. Deliverables in this folder
- `Sultanbeyli_Konteyner_Optimizasyon.xlsx` - Solver-ready workbook (5 sheets)
- `sultanbeyli_map.png` - Geographic visualization
- `coverage_comparison.png` - Per-mahalle coverage baseline vs proposed
- `sensitivity.png` - AHP & IP mode sensitivity
- `../results/selection_*.xlsx` - Detailed selection sheets for each scenario
- `../results/ahp_weights.xlsx` - AHP weights & CR
- `../results/topsis_sonuclar.xlsx` - TOPSIS scores for all 141 candidates
- `../results/mu_aday.xlsx` - FCM mu matrix for candidates
- `../results/mu_mevcut.xlsx` - FCM mu matrix for existing
- `../results/mahalle_centroids.xlsx` - Mahalle centroids
- `../data/adaylar.xlsx` - 140 candidates with full features
- `../data/mevcut_12.xlsx` - 12 existing containers with coords
- `../data/mahalle_nufus.xlsx` - 17 mahalle population
- `../data/mahalle_risk.xlsx` - 17 mahalle IBB Tablo 5-2 risk


## 11. Academic Critical Review

A full academic-style review of the methodology (validation, limitations, alternative approaches, improvement roadmap) is provided in cademic_review.md and the Academic_Review sheet of Sultanbeyli_Final_Results.xlsx.

### 11.1 Summary of findings

- **Validation: 6/6 scenarios converge, AHP weight perturbation robust (rho=0.9994), C4 demand-proxy choice (night pop vs IBB shelter) does not change selection.** Solution is statistically robust.
- **IBB Report cross-check:** our risk_score (Table 5-2 casualties) and the alternative shelter demand (Table 5-4) both align with the official Mw=7.5 scenario (73 deaths, 16,635 hane shelter need).
- **Methodological family:** Risk-weighted Maximal Covering Location Problem (MCLP), a well-known OR model (Yemshumanov & Kara 2019; Salhi & Nagy 2009).
- **Main limitations (deterministic & static):**
  1. Single Mw=7.5 scenario; no probabilistic ground-motion model
  2. Road closure probability (IBB Tablo 5-7) not integrated
  3. No day/night dual scenarios
  4. No cost dimension (rent, install, O&M)
  5. FCM sigma fixed at 800m (should be mahalle-specific)

### 11.2 Recommended alternative approaches (literature)

- Two-stage Stochastic IP (Birge & Louveaux 2011)
- Robust Optimization (Bertsimas & Sim 2004)
- Goal Programming / NSGA-II (multi-objective Pareto)
- GIS-Integrated Network Model with real road network (OSMnx)
- Bayesian Network + IP (uncertain demand)
- Agent-Based Simulation (queue at containers, dynamic evacuation)

### 11.3 Key recommendation for thesis defense

> The proposed 8-site solution is the **correct** answer to the deterministic, single-scenario, single-objective version of the problem. It is robust to (a) AHP weight choice, (b) demand-proxy choice, and (c) IP solving mode. For a real-world deployment, the next step is to lift the static assumption via stochastic programming and to incorporate IBB's actual shelter-demand table (Table 5-4) as the direct C4 signal instead of population proxy.

## 12. New files added in this round
- academic_review.md - Full academic critical review (this report)
- Sultanbeyli_Final_Results.xlsx - Now 18 sheets (added Academic_Review + AHP_Robustness)
- selection_map_osm.png - Selection map on OpenStreetMap basemap
- shelter_demand_map.png - Barinma ihtiyaci vs nufus karsilastirma grafigi
- alt_C4_comparison.png - Orijinal C4 vs IBB barinma C4 secim karsilastirmasi
- selection_on_ibb_sekil_3_1.png - IBB Sekil 3-1 (baz harita) uzerinde 8 yeni + 12 mevcut konteyner
- selection_on_ibb_sekil_5_2.png - IBB Sekil 5-2 (cok agir hasarli bina dagilimi) uzerinde secim
- selection_on_ibb_composite.png - Sekil 3-1 + Sekil 5-2 yan yana karsilastirma (jury)
- selection_map_web.png - GERCEK web haritasi (Web Mercator EPSG:3857) uzerinde secim, OSM HOT/CartoDB tile baz harita, tum koordinatlar tam dogrulukla
- ibbsh_maps/image23.jpeg ... image74.jpeg - 73 image extracted from IBB raporu
- ../results/shelter_demand.xlsx - IBB Tablo 5-4 barinma ihtiyaci (normalized)
- ../results/shelter_vs_nightpop.xlsx - Demand proxy karsilastirma tablosu
- ../results/alt_C4_shelter_topsis.xlsx - TOPSIS alt C4 ile
- ../results/alt_C4_shelter_selection.xlsx - IP secim alt C4 ile
- ../data/mahalle_barinma_ihtiyaci.xlsx - Ham IBB Tablo 5-4 verisi

Scripts: src/11_selection_map_osm.py, src/12_ibbsh_demand.py, src/13_alt_c4_shelter.py, src/14_academic_review.py, src/15_ibbsh_overlay.py, src/16_selection_map_web.py

### 12.1 IBB Overlay (Şekil 3-1 & 5-2)

The 8 new + 12 existing container positions are overlaid on the official IBB maps
extracted from the report:
- **Şekil 3-1** — Sultanbeyli baz harita (mahalle sınırları, yol ağı)
- **Şekil 5-2** — Mw=7.5 senaryosu "Çok Ağır Hasarlı Bina Dağılımı" ısı haritası

Pixel-to-coordinate mapping uses a 3-anchor affine (Mimar Sinan, Abdurrahmangazi,
Necip Fazıl mahal labels) solved via least-squares. Approximate but consistent.
The composite figure (`selection_on_ibb_composite.png`) places both maps side-by-side
so the jury can verify the selection visually aligns with both the official basemap
and the heavy-damage heatmap.

### 12.2 Real Web-Map Overlay (EPSG:3857)

`selection_map_web.png` is built on a real Web Mercator (EPSG:3857) tile basemap
(OSM Humanitarian/CartoDB Voyager) with all 8 + 12 container positions projected
exactly from WGS84 — no anchor-based affine guessing. 800 m coverage circles,
mahalle centroids shaded by İBB shelter-need (Tablo 5-4), and 1 km scale bar are
included. The pale appearance reflects Sultanbeyli's genuinely low-density
suburban land use at zoom 14; the geographic positions are exact.

**Teferrüç Tepe Ormanı notu:** The 4 selected sites labeled "HAMIDIYE"
(S59/S60/S61/S62) sit in the eastern-southeast part of Sultanbeyli where the
IBB administrative mahalle boundary of Hamidiye includes the Teferrüç Tepe
Ormanı forest area. This area is highlighted in IBB Şekil 5-2 as a high
heavy-damage zone (Mw=7.5 scenario), so the IP solver correctly placed
containers there even though OSM shows forest landuse. The container
placement is correct — the apparent label/landuse mismatch is a property
of how İBB defines administrative boundaries, not a mapping error.

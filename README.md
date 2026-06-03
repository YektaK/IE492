# Sultanbeyli Disaster Response Container Location Selection

**IE 492 Industrial Engineering Senior Project** — Sultanbeyli Municipality (Istanbul), Turkey

Selecting 8 new disaster-response container locations to complement the existing 12, choosing from 141 public-area candidates listed in AYDES.

---

## 1. Quick Facts

| Item | Value |
|---|---|
| District | Sultanbeyli (Istanbul) — 17 mahalle (neighborhoods) |
| Existing containers | 12 (fixed) |
| Required new containers | 8 |
| Candidate sites (AYDES public areas) | 141 |
| Optimization goal | Maximize risk-weighted FCM coverage of all 17 mahalle |
| Solution method | AHP → TOPSIS → FCM → 0-1 Integer Programming |
| Solver library | `pulp` (Python) + `openpyxl` Solver-ready Excel |
| Final objective Z | 935.62 (sum of coverage × risk) |
| Coverage uplift | +96.6% continuous μ, **+5.9 pp** mahalle-level (76.5% → 82.4%) |
| Robust to AHP scenario? | Yes (all 3 scenarios × 2 IP modes converge) |

---

## 2. Repository Layout

```
D:\IE492\
├── README.md                              ← this file
├── docs/                                  ← raw inputs (do not modify)
│   ├── Sultanbeyli Deprem raporu IBB.pdf            ← IBB Tablo 5-2 risk
│   ├── Sultanbeyli Ilcesi Nufus Verileri-2024 1.docx ← 17 mahalle population
│   ├── Ek-5 ...-SULTANBEYLI (1).xlsx                  ← 12 existing containers
│   ├── topsisguncel.xlsx / .csv                       ← AYDES 141 candidates + C1-C4
│   ├── Bitirme Projesi son guncel 1.docx             ← project template
│   └── WhatsApp Image 2026-05-01 ...jpeg             ← IBB Tablo 5-2 screenshot
├── src/                                   ← pipeline (run in order)
│   ├── 01_data_prep.py                    ← parse docs → output/data/
│   ├── 02_ahp_topsis.py                   ← AHP weights + TOPSIS ranking
│   ├── 03_fcm.py                          ← Gaussian membership matrices
│   ├── 04_zero_one_ip.py                  ← 0-1 IP via pulp (3 scenarios × 2 modes)
│   ├── 05_reporting.py                    ← Excel + figures + reporting.md
│   ├── 06_coverage_score.py               ← Toplam Kapsama Skoru metric
│   └── 07_update_with_coverage_score.py   ← inject coverage sheet + section 6B
└── output/
    ├── data/                              ← parsed inputs (xlsx)
    │   ├── adaylar.xlsx                   ← 141 candidates + C1-C4
    │   ├── mevcut_12.xlsx                 ← 12 existing containers (lat/lon)
    │   ├── mahalle_nufus.xlsx             ← 17 mahalle population
    │   └── mahalle_risk.xlsx              ← 17 mahalle IBB risk
    ├── results/                           ← analysis outputs
    │   ├── ahp_weights.xlsx               ← 3 scenarios + CR
    │   ├── criteria_matrix.xlsx           ← pairwise comparison
    │   ├── topsis_sonuclar.xlsx           ← 141 × 3 scenarios
    │   ├── mu_aday.xlsx                   ← 140 × 17 FCM μ matrix (candidates)
    │   ├── mu_mevcut.xlsx                 ← 12 × 17 FCM μ matrix (existing)
    │   ├── mahalle_centroids.xlsx         ← 17 mahalle lat/lon + risk
    │   ├── selection_Baseline_hard.xlsx   ← Selected 8 + Coverage per Mahalle + KPI
    │   ├── selection_Baseline_soft.xlsx
    │   ├── selection_DamageFocused_hard.xlsx
    │   ├── selection_DamageFocused_soft.xlsx
    │   ├── selection_InfrastructureFocused_hard.xlsx
    │   ├── selection_InfrastructureFocused_soft.xlsx
    │   ├── selection_sensitivity.xlsx     ← 3 × 2 = 6 rows
    │   ├── coverage_score_detailed.xlsx   ← mahalle-level Toplam Kapsama
    │   └── coverage_score_kpi.xlsx        ← 3-row KPI
    ├── figures/                           ← PNG charts
    │   ├── sultanbeyli_map.png
    │   ├── coverage_comparison.png
    │   ├── toplam_kapsama_skoru.png
    │   ├── topsis_top20.png
    │   └── sensitivity.png
    └── final/                             ← thesis-ready deliverables
        ├── Sultanbeyli_Final_Results.xlsx           ← consolidated workbook (18 sheets)
        ├── Sultanbeyli_Konteyner_Optimizasyon.xlsx  ← Solver-ready (6 sheets)
        ├── selection_map_focus.png                  ← focused map (no basemap)
        ├── selection_map_osm.png                    ← map on OpenStreetMap basemap
        ├── selection_map_web.png                    ← REAL web map (EPSG:3857, OSM HOT/CartoDB tiles)
        ├── selection_on_ibb_sekil_3_1.png           ← IBB Şekil 3-1 baz harita + konteynerler
        ├── selection_on_ibb_sekil_5_2.png           ← IBB Şekil 5-2 ağır hasar + konteynerler
        ├── selection_on_ibb_composite.png           ← Şekil 3-1 + Şekil 5-2 yan yana (jury)
        ├── academic_review.md                       ← academic critical review (5 sections)
        └── reporting.md                             ← full report
```

---

## 3. Methodology

A 4-stage hybrid model:

### Stage 1 — AHP (Analytical Hierarchy Process)
Pairwise comparison of 4 criteria → Saaty's eigenvector method.

| Criterion | Description | Direction |
|---|---|---|
| C1 — Damage risk | IBB Tablo 5-2 building-damage score (Mw=7.5) | benefit |
| C2 — Logistics | Water/WC/generator availability in the area | benefit |
| C3 — Gap distance | Distance to nearest existing container | benefit |
| C4 — Night pop. | Population × mahalle weight (demand proxy) | benefit |

3 sensitivity scenarios (all CR < 0.10):
- **Baseline**: balanced Saaty
- **DamageFocused**: more weight on C1
- **InfrastructureFocused**: more weight on C2

### Stage 2 — TOPSIS
141 candidates scored per scenario. Benefit direction for all 4 criteria, Euclidean distance to ideal/anti-ideal solution.

### Stage 3 — FCM (Fuzzy C-Means Gaussian)
For each candidate and each existing container, a Gaussian membership value `μ(i,j) ∈ [0,1]` is computed against each mahalle centroid:

```
μ(i, k) = exp(-d(i,k)² / (2·σ²)),  σ = 800 m
```

Two matrices:
- `mu_aday` (140 × 17) — candidate → mahalle
- `mu_mevcut` (12 × 17) — existing container → mahalle

### Stage 4 — 0-1 Integer Programming

```
max Z = Σ_i R_i · [Σ_k μ_mevcut(i,k)  +  Σ_j μ_aday(i,j) · X_j]

s.t.    Σ_j X_j = 8                  (pick exactly 8)
        X_j ∈ {0,1}                  (binary)
        for critical i: Σ_k μ_mevcut(i,k) + Σ_j μ_aday(i,j)·X_j ≥ 0.50   (HARD)
        OR   α·soft_penalty ≤ 0      (SOFT, α small)
```

`pulp` with CBC solver, status: **Optimal**, all 6 (3 × 2) variants converge to the same solution.

---

## 4. Results

### 4.1 Selected 8 New Sites

| S_No | Alan_Adi | Mahalle |
|---:|---|---|
| 4 | Ali Kuşçu İmam Hatip Ortaokulu Bahçesi | ABDURRAHMANGAZİ |
| 59 | Eşref Bitlis Parkı | HAMİDİYE |
| 60 | İbrahim Dede Parkı | HAMİDİYE |
| 61 | İstanbul Ticaret Odası Şehit Er Dursun Sıvaz İlkokulu Bahçesi | HAMİDİYE |
| 62 | Mevlana Ortaokulu Bahçesi | HAMİDİYE |
| 83 | Mehmet Akif Ersoy Parkı | MEHMET AKİF |
| 88 | Yunus Emre Parkı | MEHMET AKİF |
| 141 | Yaşar Paşalı İlkokulu Bahçesi | YAVUZ SELİM |

**Pattern**: 4 of 8 sites in Hamidiye (the 2nd most critical, μ 0.47 → 0.99), 2 in Mehmet Akif, 1 in each of Abdurrahmangazi and Yavuz Selim.

### 4.2 KPI

| Metric | Baseline (12) | Proposed (20) | Δ |
|---|---:|---:|---:|
| Total FCM μ (continuous) | 23.17 | 45.54 | **+96.6%** |
| Mean FCM μ (per mahalle) | 0.658 | 0.716 | +5.8% |
| Mahalle coverage @ μ≥0.50 (17) | 76.5% | 82.4% | +5.9 pp |
| Mahalle coverage @ μ≥0.50 (15 urban) | 86.7% | 93.3% | +6.6 pp |
| Critical mahalle below threshold | 1 (Hamidiye 0.47) | 0 | -1 |

### 4.3 Sensitivity

All 3 AHP × 2 IP = 6 variants → identical solution. FCM coverage constraint binds in every variant → robust.

---

## 5. How to Reproduce

```powershell
# 1) parse raw docs into output/data/
python src/01_data_prep.py

# 2) AHP weights + TOPSIS scores
python src/02_ahp_topsis.py

# 3) FCM Gaussian μ matrices
python src/03_fcm.py

# 4) 0-1 IP across 3 scenarios × 2 modes
python src/04_zero_one_ip.py

# 5) Build Excel + figures + reporting.md
python src/05_reporting.py

# 6) Toplam Kapsama Skoru (extra)
python src/06_coverage_score.py
python src/07_update_with_coverage_score.py
python src/08_selection_map.py
python src/09_final_results.py
python src/10_ahp_robustness.py    # AHP weight perturbation test (rho=0.9994)
python src/11_selection_map_osm.py # map on OpenStreetMap basemap
python src/12_ibbsh_demand.py      # extract IBB Tablo 5-4 shelter need
python src/13_alt_c4_shelter.py    # re-run IP with shelter demand as C4
python src/14_academic_review.py   # write academic review + add sheet to xlsx
python src/15_ibbsh_overlay.py     # overlay containers on IBB Şekil 3-1 + 5-2 (jury maps)
python src/16_selection_map_web.py # REAL web-map overlay (EPSG:3857, OSM tiles)
```

Dependencies (already installed in this environment):
`pandas`, `numpy`, `openpyxl`, `pulp`, `matplotlib`, `scipy`, `python-docx`, `tabulate`.

---

## 6. Solver Re-run (jury)

The workbook `output/final/Sultanbeyli_Konteyner_Optimizasyon.xlsx` is **Solver-ready** (and `Sultanbeyli_Final_Results.xlsx` is the **consolidated 16-sheet workbook** with all inputs, intermediate results, and KPIs in one place).
1. `Adaylar_TOPSIS` — 140 candidates, criteria C1–C4, three TOPSIS scores, plus a column `X_j` (binary decision).
2. `Aday_FCM_Uyelik` — 140 × 17 μ matrix.
3. `Mevcut_FCM_Uyelik` — 12 × 17 μ matrix.
4. `Mahalle_Riskleri` — risk weights and population.
5. `Optimizasyon` — pre-built SUMPRODUCT formulas for per-mahalle coverage, `Coverage_x_R`, total objective, and per-mahalle threshold check.
6. `Toplam_Kapsama_Skoru` — mahalle-level coverage comparison.

Excel Solver setup:
- **Set Objective:** `Optimizasyon!G27` (= SUM of coverage×risk), Maximize
- **By Changing:** `Adaylar_TOPSIS!O2:O141`
- **Constraints:** sum = 8, binary, optional hard ≥ 0.5 for critical rows
- **Method:** Simplex LP

---

## 7. Notes for the Jury

- **Robustness**: AHP weights vary ±20% in 3 scenarios; the optimal selection does not change. The FCM coverage constraint binds.
- **Fairness across mahalle**: 4 of 8 sites allocated to Hamidiye because that mahalle was the only critical one below the 0.50 threshold (μ=0.47). Allocating more to a single mahalle is the model's correct response to a coverage gap.
- **Uncovered mahalle**: Salgamlı Devlet Ormanı, Teferruç Tepe Ormanı (structural forest, R=0, no candidates), and Adil (R=3.4, no candidate within 800m). These are not in the candidate set by design (AYDES public-area registry).

---

## 8. License & Attribution

Course: IE 492 — Industrial Engineering Senior Project
Team: Elif Keleş, Zümra Sancaklı, Doğa Yardemir, Semanur Aydın
Advisor: Dr. Ahmet Yekta Kayman
Date: January 2026
Data sources: İBB (Istanbul Metropolitan Municipality), Sultanbeyli Municipality, AFAD / AYDES registry.

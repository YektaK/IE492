# Sultanbeyli Disaster Response Container Location Selection

**IE 492 Industrial Engineering Senior Project** — Sultanbeyli Municipality (Istanbul), Turkey

Multi-criteria, multi-scenario, multi-method optimization for placing 8 new disaster-response containers alongside 12 existing ones, using 141 AYDES-registered public-area candidates.

---

## 1. Quick Facts

| Item | Value |
|---|---|
| District | Sultanbeyli (Istanbul) — 17 mahalle |
| Existing containers | 12 (fixed) |
| Required new containers | 8 (default; configurable via `--K`) |
| Candidate sites (AYDES public areas) | 141 |
| Solution methods | 6 MILP + LSCP + Lexicographic + Eps-Constraint + Single-Stage + Compromise + Gini + Sigma Grid |
| Scenarios | A (Referans), B (Yol Kapanmasi) |
| FCM sigma | 800 m (default); two-tier 800+300 m also available |
| Solver | `pulp` CBC, all < 100 ms |
| Default point solution | RxC = 21.20, min_cov = 1.09, Z = 22.33 |

---

## 2. Repository Layout

```
D:\IE492\
├── README.md
├── experiments_config.json          ← config-driven experiment definitions
├── data/
│   ├── scenarios/scenarios.xlsx     ← scenario definitions (A, B)
│   └── processed/                   ← 10 processed xlsx files
├── src/
│   ├── scenario_utils.py            ← shared Q_i loader, FCM path resolver
│   ├── 01_data_prep.py              ← parse raw data → processed xlsx
│   ├── 02_ahp_weights.py            ← AHP weights (3 scenarios)
│   ├── 03a_topsis.py                ← TOPSIS scores
│   ├── 03b_promethee.py             ← PROMETHEE II scores
│   ├── 04_fcm.py                    ← Gaussian membership (configurable sigma)
│   ├── 05_ip.py                     ← 0-1 MILP (6 versions), main IP
│   ├── 06_compare.py                ← comparison tables
│   ├── 07_reporting.py              ← final report + map
│   ├── 08_lscp.py                   ← Location Set Covering Problem
│   ├── 09_gini.py                   ← Gini inequality analysis
│   ├── 10_infra_score.py            ← infrastructure composite score
│   ├── 11_lexicographic.py          ← two-stage lexicographic (RxC → min_C)
│   ├── 12_sigma_grid.py             ← FCM sigma sensitivity grid
│   ├── 13_eps_constraint.py         ← epsilon-constraint Pareto front
│   ├── 14_single_stage.py           ← equity-integrated single-stage MILP
│   ├── 15_compromise.py             ← compromise programming (L1/L2/Linf)
│   └── run_all_scenarios.py         ← experiment runner (reads config)
├── docs/
│   ├── analiz_karnesi.md            ← method checklist
│   ├── sonuclar_ve_yorumlama.md     ← detailed results + interpretation
│   └── rapor/FINAL_RAPOR.md         ← final report (Turkish)
├── results/
│   ├── ahp/mcdm/fcm/models/         ← pipeline outputs
│   ├── lscp/lexicographic/          ← scenario-aware method outputs
│   ├── epsilon/single_stage/compromise/
│   └── gini/sigma_grid/comparison/
└── figures/
```

---

## 3. Pipeline (7 Stages)

```
01_data_prep → 02_ahp → 03a_topsis / 03b_promethee → 04_fcm → 05_ip → 06_compare → 07_reporting
```

### Stage 1 — Data Preparation (`01_data_prep.py`)
Parses raw municipal documents (IBB earthquake report, AYDES registry, population data) into 10 processed xlsx files + scenario definitions.

### Stage 2 — AHP Weights (`02_ahp_weights.py`)
Pairwise comparison of 4 criteria (C1 Population, C2 Earthquake, C3 Accessibility, C4 Transportation) across 3 scenarios:
- **Baseline**: balanced
- **DamageFocused**: higher C1 weight
- **InfrastructureFocused**: higher C2 weight

All CR < 0.10.

### Stage 3 — MCDM Scores
Parallel execution:
- `03a_topsis.py` → TOPSIS CC_j scores (3 scenarios × 141 candidates)
- `03b_promethee.py` → PROMETHEE phi_j scores (3 scenarios × 141 candidates)

Both with benefit direction for all 4 criteria.

### Stage 4 — Fuzzy Coverage (`04_fcm.py`)
Gaussian membership μ(i,j) = exp(-d²/2σ²) with configurable sigma (default 800 m).

Two matrices: candidate→mahalle (140×17) and existing→mahalle (12×17).

### Stage 5 — 0-1 Integer Programming (`05_ip.py`)
Main MILP solver across 6 versions (TOPSIS/PROMETHEE × 3 AHP scenarios):

```
max Z = Σ_i R_i · C_i  +  β · Σ_j q_j · X_j
C_i = Q_i · (μ_mev_i + Σ_j μ_ij · P_j · X_j)
s.t. Σ_j X_j = K,  X_j ∈ {0,1}
```

### Stage 6 — Comparison (`06_compare.py`)
Cross-tabulation of all 6 versions, MCDM agreement, scenario sensitivity.

### Stage 7 — Reporting (`07_reporting.py`)
Consolidated FINAL_REPORT.xlsx with 18 sheets + map.

---

## 4. All Solution Methods (11 total)

| # | Method | File | Description |
|---|--------|------|-------------|
| 1 | MILP (6 v.) | `05_ip.py` | Main IP — 6 versions (2 MCDM × 3 AHP) |
| 2 | LSCP | `08_lscp.py` | Location Set Covering — min K for μ ≥ 0.50 |
| 3 | Gini | `09_gini.py` | Coverage inequality across mahalle |
| 4 | Infra Score | `10_infra_score.py` | C2 composite replacement |
| 5 | Lexicographic | `11_lexicographic.py` | A1: max RxC → A2: max min_C |
| 6 | Sigma Grid | `12_sigma_grid.py` | σ ∈ [400,1200] sensitivity |
| 7 | Eps-Constraint | `13_eps_constraint.py` | Pareto front (RxC vs min_C) |
| 8 | Single-Stage | `14_single_stage.py` | Equity-integrated (Z + α·Equity) |
| 9 | Compromise | `15_compromise.py` | L1/L2/Linf compromise programming |
| — | **Scenarios** | `experiments_config.json` | 12 experiment configurations |

---

## 5. Configuration-Driven Experiments

All experiments are defined in `experiments_config.json`. Each config specifies scenario, sigma, beta, K, truncation, and which methods to run.

### Available Dimensions

| Parameter | CLI flag | Values | Default |
|-----------|----------|--------|---------|
| Scenario | `--scenario` | A (Referans), B (Yol Kapanmasi) | A |
| FCM sigma | `--sigma` | 800, 300, 800_300 (two-tier) | 800 |
| Quality weight | `--beta` | 0.0 – 1.0 | 0.30 |
| New containers | `--K` | integer | 8 |
| Truncation | `--truncate` | 0.0 – 0.50 (mu < threshold → 0) | 0 |
| No mevcut | `--no-mevcut` | flag | off |

### Quick Start

```powershell
# Full pipeline (default: Scenario A, sigma=800)
python src/01_data_prep.py
python src/02_ahp_weights.py
python src/03a_topsis.py
python src/03b_promethee.py
python src/04_fcm.py
python src/05_ip.py

# Run with road-closure scenario
python src/05_ip.py --scenario B

# Change sigma
python src/04_fcm.py --sigma 800_300
python src/05_ip.py --sigma 800_300

# All parameters
python src/05_ip.py --scenario B --K 20 --beta 0.5 --sigma 800_300 --truncate 0.2 --no-mevcut
```

### Experiment Runner

```powershell
# List all defined experiments
python src/run_all_scenarios.py --list

# Run all experiments
python src/run_all_scenarios.py

# Run specific experiment
python src/run_all_scenarios.py --name Baseline_SA
python src/run_all_scenarios.py --name RoadClosure

# Run individual methods with any CLI args
python src/11_lexicographic.py --scenario B
python src/13_eps_constraint.py --scenario B --beta 0.5
python src/14_single_stage.py --K 20 --no-mevcut
```

### Defined Experiments

| Experiment | Scenario | Sigma | Beta | K | Note |
|------------|----------|-------|------|---|------|
| Baseline_SA | A | 800 | 0.30 | 8 | Default reference |
| RoadClosure_SB | B | 800 | 0.30 | 8 | Road closure scenario |
| TwoTier_SA | A | 800_300 | 0.30 | 8 | Two-tier FCM |
| TwoTier_SB | B | 800_300 | 0.30 | 8 | Two-tier + road closure |
| BetaGrid_SA | A | 800 | 0–1.0 | 8 | 7 beta values |
| FullReloc_SA | A | 800 | 0.30 | 20 | No existing containers |
| FullReloc_SB | B | 800 | 0.30 | 20 | No existing + road closure |
| Truncation_SA | A | 800 | 0.30 | 8 | mu < 0.20 → 0 |

---

## 6. Methods Reference (CLI)

### `05_ip.py` — Main MILP
```
python src/05_ip.py [--scenario {A,B}] [--K K] [--beta B] [--sigma S] [--truncate T] [--no-mevcut]
```
Outputs: `results/models/{ip,coverage}_v{N}_{MCDM}_{AHP}_S{scenario}[_sg{sigma}][_b{beta}][_K{K}][_t{truncate}][_nomez].xlsx`

### `08_lscp.py` — Location Set Covering
```
python src/08_lscp.py [--scenario {A,B}] [--sigma S] [--K K] [--truncate T] [--no-mevcut]
```

### `11_lexicographic.py` — Two-stage Lexicographic
```
python src/11_lexicographic.py [--scenario {A,B}] [--sigma S] [--beta B]
                               [--K K] [--truncate T] [--no-mevcut]
```

### `13_eps_constraint.py` — Epsilon-Constraint
```
python src/13_eps_constraint.py [--scenario {A,B}] [--sigma S] [--beta B]
                                [--K K] [--truncate T] [--no-mevcut]
```

### `14_single_stage.py` — Single-Stage MILP
```
python src/14_single_stage.py [--scenario {A,B}] [--sigma S] [--beta B]
                              [--K K] [--truncate T] [--no-mevcut]
```

### `15_compromise.py` — Compromise Programming
```
python src/15_compromise.py [--scenario {A,B}]
```

---

## 7. Default Point Solution

### Selected 8 Sites (Scenario A, Baseline)

| S_No | Alan_Adi | Mahalle |
|------|----------|---------|
| 4 | Ali Kuscu Imam Hatip Ortaokulu Bahcesi | ABDURRAHMANGAZI |
| 59 | Esref Bitlis Parki | HAMIDIYE |
| 60 | Ibrahim Dede Parki | HAMIDIYE |
| 61 | Istanbul Ticaret Odasi Sehit Er Dursun Sivaz Ilkokulu Bahcesi | HAMIDIYE |
| 62 | Mevlana Ortaokulu Bahcesi | HAMIDIYE |
| 83 | Mehmet Akif Ersoy Parki | MEHMET AKIF |
| 88 | Yunus Emre Parki | MEHMET AKIF |
| 141 | Yasar Pasali Ilkokulu Bahcesi | YAVUZ SELIM |

### KPI (12 → 20 containers)

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total FCM μ | 23.17 | 45.54 | +96.6% |
| Mahalle min coverage | 0.47 | 1.09 | +132% |
| Mahalle below 0.50 | 1 | 0 | eliminated |

---

## 8. Dependencies

`pandas`, `numpy`, `openpyxl`, `pulp`, `matplotlib`, `scipy`, `python-docx`, `tabulate`

---

## 9. License & Attribution

Course: IE 492 — Industrial Engineering Senior Project
Team: Elif Keles, Zumra Sancakli, Doga Yardemir, Semanur Aydin
Advisor: Dr. Ahmet Yekta Kayman
Date: June 2026
Data: IBB (Istanbul Metropolitan Municipality), Sultanbeyli Municipality, AFAD / AYDES

# Sultanbeyli Disaster Response Container Location Selection

**IE 492 Industrial Engineering Senior Project** — Sultanbeyli Municipality (Istanbul), Turkey

Multi-criteria, multi-scenario, multi-method optimization for placing 8 new disaster-response containers alongside 12 existing ones, using 140 processed AYDES-registered public-area candidates.

---

## 1. Quick Facts

| Item                                 | Value                                                                                                                    |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| District                             | Sultanbeyli (Istanbul) — 17 source mahalle records; 15 active modeled mahalle after excluding forest/unpopulated records |
| Existing containers                  | 12 (fixed)                                                                                                               |
| Required new containers              | 8 (default; configurable via `--K`)                                                                                      |
| Candidate sites (AYDES public areas) | 140 processed candidate rows                                                                                             |
| Solution methods                     | up to 12 MILP variants + LSCP + MCLP + Lexicographic + Eps-Constraint + Single-Stage + Compromise + Gini + Sigma Grid    |
| Scenarios                            | A (Referans), B (Yol Kapanmasi)                                                                                          |
| Coverage sigma                       | 800 m fixed, `Adaptive`, `RoadNetwork`, and legacy composite `800_300`                                                   |
| Solver                               | `pulp` HiGHS (preferred) / CBC, all < 100 ms                                                                             |
| Academic documentation               | `docs/IE492_Academic_Documentation.md` — thesis-ready technical reference (985 lines)                                    |

---

## 2. Repository Layout

```
D:\IE492\
├── README.md
├── requirements.txt                 ← Python dependencies
├── experiments_config.json          ← config-driven experiment definitions
├── data/
│   ├── scenarios/scenarios.xlsx     ← scenario definitions (A, B)
│   └── processed/                   ← 10 processed xlsx files
├── src/
│   ├── config.py                    ← central constants (COVERAGE_THRESHOLD, TRUNCATION_THRESHOLD, etc.)
│   ├── solver_core.py               ← PuLP helpers (get_solver, build_base_variables_and_coverage)
│   ├── scenario_utils.py            ← shared Q_i loader, fuzzy coverage path resolver, haversine
│   ├── visualization.py             ← standardized Folium/Matplotlib visualization engine
│   ├── app_runner.py                ← shared Streamlit command/output resolver
│   ├── 01_data_prep.py              ← parse raw data → processed xlsx
│   ├── 02_ahp_weights.py            ← AHP weights (3 scenarios, eigenvalue method)
│   ├── 03a_topsis.py                ← TOPSIS scores (L2 + MinMax normalization)
│   ├── 03b_promethee.py             ← PROMETHEE II scores
│   ├── 03c_vikor.py                 ← VIKOR scores
│   ├── 03d_electre.py               ← ELECTRE net outranking flow scores
│   ├── 04_fuzzy_coverage.py         ← Gaussian fuzzy coverage (configurable sigma, Q_i vector)
│   ├── 05_ip.py                     ← 0-1 MILP (up to 12 versions), main IP
│   ├── 06_compare.py                ← comparison tables
│   ├── 07_reporting.py              ← final report + map
│   ├── 08_lscp.py                   ← Location Set Covering Problem
│   ├── 09_gini.py                   ← Gini inequality analysis
│   ├── 10_infra_score.py            ← infrastructure composite score
│   ├── 11_lexicographic.py          ← two-stage lexicographic (RxC → min_C)
│   ├── 12_sigma_grid.py             ← coverage sigma sensitivity grid
│   ├── 13_eps_constraint.py         ← epsilon-constraint Pareto front (AUGMECON2)
│   ├── 14_single_stage.py           ← equity-integrated single-stage MILP
│   ├── 15_compromise.py             ← compromise programming (L1/L2/Linf)
│   ├── 16_mclp.py                   ← Maximal Covering Location Problem benchmark
│   └── run_all_scenarios.py         ← experiment runner (reads config)
├── docs/
│   ├── IE492_Academic_Documentation.md  ← thesis-ready academic reference (§1–§4 + Appendices)
│   ├── 00_IE492_Sultanbeyli_Master_Plan_2026_06_07.md
│   ├── 00_academic_methods_analysis.md
│   ├── CODEBASE_ANALYSIS.md
│   ├── FINDINGS_AND_FIXES.md
│   ├── analiz_karnesi.md            ← method checklist
│   ├── sonuclar_ve_yorumlama.md     ← detailed results + interpretation
│   └── rapor/FINAL_RAPOR.md         ← final report (Turkish)
├── results/
│   ├── ahp/mcdm/fuzzy_coverage/models/ ← pipeline outputs
│   ├── lscp/lexicographic/          ← scenario-aware method outputs
│   ├── epsilon/single_stage/compromise/
│   └── gini/sigma_grid/comparison/
└── figures/
```

---

## 3. Pipeline (7 Stages)

```
01_data_prep → 02_ahp → 03a_topsis / 03b_promethee / 03c_vikor / 03d_electre → 04_fuzzy_coverage → 05_ip → 06_compare → 07_reporting
```

### Stage 1 — Data Preparation (`01_data_prep.py`)

Parses raw municipal documents (IBB earthquake report, AYDES registry, population data) into 10 processed xlsx files + scenario definitions.

### Stage 2 — AHP Weights (`02_ahp_weights.py`)

Pairwise comparison of 4 criteria (C1 Seismic Damage Risk, C2 Infrastructure Quality, C3 Gap Distance, C4 Shelter Need) across 3 scenarios:

- **Baseline**: balanced weights (C1=0.541, C2=0.254, C3=0.117, C4=0.088)
- **DamageFocused**: higher C1 weight (C1=0.609, C2=0.223, C3=0.109, C4=0.059)
- **InfrastructureFocused**: equal C1/C2 weight (C1=0.391, C2=0.391, C3=0.140, C4=0.078)

All CR < 0.10 (RI=0.90 for n=4). Eigenvalue method with column normalization → row averaging.

### Stage 3 — MCDM Scores

Parallel execution:

- `03a_topsis.py` → TOPSIS CC_j scores (3 scenarios × 140 candidates)
- `03b_promethee.py` → PROMETHEE phi_j scores (3 scenarios × 140 candidates)
- `03c_vikor.py` → VIKOR Q-benefit scores (3 scenarios × 140 candidates)
- `03d_electre.py` → ELECTRE net outranking flow scores (3 scenarios × 140 candidates)

Both with benefit direction for all 4 criteria.

### Stage 4 — Fuzzy Coverage (`04_fuzzy_coverage.py`)

Gaussian distance-decay membership with configurable sigma. Two-tier structure:

- **Core radius** (300m): Full coverage (μ=1) within 300m of container
- **Gaussian decay**: μ = exp(-(d-300)²/(2σ²)) beyond core radius
- **Truncation**: μ < 0.15 → 0 (sparsity enforcement)

Coverage modes:
- **Adaptive**: σ_m ∈ [400, 1200]m based on neighborhood population density
- **RoadNetwork**: σ adjusted by per-parcel road accessibility
- **Fixed**: Constant σ (e.g., 800m)
- **Composite**: 800m outer with 300m core (legacy)

Two matrices: candidate→mahalle (140×15) and existing→mahalle (12×15).

**Q_i Vector**: Per-mahalle road accessibility penalty (Scenario A: Q_i=1.0; Scenario B: Q_i=p_road_open ∈ [0.40, 0.99]). Multiplies entire coverage expression including existing containers.

### Stage 5 — 0-1 Integer Programming (`05_ip.py`)

Main MILP solver across up to 12 versions (4 MCDM × 3 AHP scenarios). TOPSIS and PROMETHEE are always loaded; VIKOR and ELECTRE are included when their output files exist:

```
max Z = Σ_i R_i · C_i  +  β · Σ_j q_j · X_j

where:
  C_i = Q_i · (μ_mev_i + Σ_j μ_ij · P_j · X_j)
  Q_i = 1.0 (Scenario A) or p_road_open_m (Scenario B)
  μ_ij = 1 if d_ij ≤ 300m, else exp(-(d_ij-300)²/(2σ²))
  μ_ij = 0 if μ_ij < 0.15 (truncation)

s.t. Σ_j X_j = K,  X_j ∈ {0,1}
```

Solver: PuLP with HiGHS (preferred) or CBC fallback.

### Stage 6 — Comparison (`06_compare.py`)

Cross-tabulation of all available MCDM/AHP versions, MCDM agreement, scenario sensitivity.

### Stage 7 — Reporting (`07_reporting.py`)

Consolidated FINAL_REPORT.xlsx with 18 sheets + map.

---

## 4. All Solution Methods (12 total)

| #   | Method             | File                      | Description                                                                   |
| --- | ------------------ | ------------------------- | ----------------------------------------------------------------------------- |
| 1   | MILP (up to 12 v.) | `05_ip.py`                | Main IP — 4 MCDM × 3 AHP when TOPSIS, PROMETHEE, VIKOR, ELECTRE outputs exist |
| 2   | LSCP               | `08_lscp.py`              | Location Set Covering — min K for μ ≥ 0.50                                    |
| 3   | MCLP               | `16_mclp.py`              | Maximal Covering Location Problem — binary coverage benchmark                 |
| 4   | Gini               | `09_gini.py`              | Coverage inequality across mahalle                                            |
| 5   | Infra Score        | `10_infra_score.py`       | C2 composite replacement                                                      |
| 6   | Lexicographic      | `11_lexicographic.py`     | A1: max RxC → A2: max min_C                                                   |
| 7   | Sigma Grid         | `12_sigma_grid.py`        | σ ∈ [400,1200] sensitivity                                                    |
| 8   | Eps-Constraint     | `13_eps_constraint.py`    | Pareto front (RxC vs min_C) — AUGMECON2 method                                |
| 9   | Single-Stage       | `14_single_stage.py`      | Equity-integrated (Z + α·Equity)                                              |
| 10  | Compromise         | `15_compromise.py`        | L1/L2/Linf compromise programming                                             |
| —   | **Scenarios**      | `experiments_config.json` | 12 experiment configurations                                                  |

---

## 5. Configuration-Driven Experiments

All experiments are defined in `experiments_config.json`. In this file, `K` means the number of **new** containers. The runner translates that value for scripts that expect total containers.

### Available Dimensions

| Parameter                                 | CLI flag                  | Values                                                      | Default                                              |
| ----------------------------------------- | ------------------------- | ----------------------------------------------------------- | ---------------------------------------------------- |
| Scenario                                  | `--scenario`              | A (Referans), B (Yol Kapanmasi) | A                                                    |
| Coverage sigma                            | `--sigma`                 | 800, Adaptive, RoadNetwork, 800_300                         | 800                                                  |
| Quality weight                            | `--beta`                  | 0.0 – 1.0                                                   | 0.30                                                 |
| New containers in experiment config       | `K`                       | integer                                                     | 8                                                    |
| Total containers in direct `05_ip.py` CLI | `--K`                     | integer                                                     | 20                                                   |
| Truncation                                | `--truncate` / `truncate` | 0.0 – 0.50 (mu < threshold → 0)                             | config default 0; direct `05_ip.py` CLI default 0.15 |
| No mevcut                                 | `--no-mevcut`             | flag                                                        | off                                                  |

### Quick Start

```powershell
# Full pipeline (default: Scenario A, sigma=800)
python src/01_data_prep.py
python src/02_ahp_weights.py
python src/03a_topsis.py
python src/03b_promethee.py
python src/04_fuzzy_coverage.py --sigma 800
python src/05_ip.py

# Run with road-closure scenario
python src/05_ip.py --scenario B

# Change sigma
python src/04_fuzzy_coverage.py --sigma 800_300
python src/05_ip.py --sigma 800_300

# Adaptive coverage mode
python src/04_fuzzy_coverage.py --sigma Adaptive
python src/05_ip.py --sigma Adaptive

# Direct main MILP run: --K is total containers for 05_ip.py
python src/05_ip.py --scenario B --K 20 --beta 0.5 --sigma 800_300 --truncate 0.2

# Full relocation direct run: --K is still total containers
python src/05_ip.py --scenario B --K 20 --beta 0.5 --sigma 800_300 --truncate 0.2 --no-mevcut
```

### Experiment Runner

```powershell
# List all defined experiments
python src/run_all_scenarios.py --list

# Validate commands without running solvers or writing results
python src/run_all_scenarios.py --name Baseline_SA --dry-run

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

| Experiment     | Scenario | Sigma   | Beta  | K   | Note                       |
| -------------- | -------- | ------- | ----- | --- | -------------------------- |
| Baseline_SA    | A        | 800     | 0.30  | 8   | Default reference          |
| RoadClosure_SB | B        | 800     | 0.30  | 8   | Road closure scenario      |
| TwoTier_SA     | A        | 800_300 | 0.30  | 8   | Two-tier FCM               |
| TwoTier_SB     | B        | 800_300 | 0.30  | 8   | Two-tier + road closure    |
| BetaGrid_SA    | A        | 800     | 0–1.0 | 8   | 7 beta values              |
| FullReloc_SA   | A        | 800     | 0.30  | 20  | No existing containers     |
| FullReloc_SB   | B        | 800     | 0.30  | 20  | No existing + road closure |
| Truncation_SA  | A        | 800     | 0.30  | 8   | mu < 0.20 → 0              |

---

## 6. Interactive Web UI (Streamlit)

A browser-based interface for running solvers, comparing results, and exploring maps:

```powershell
# Install dependencies first
pip install streamlit folium

# Launch the app
streamlit run app.py
# Opens at http://localhost:8501
```

### 6.1 Tab Overview

| Tab | Name                    | Purpose                                                                                                                                                          |
| --- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Deney Tasarımı**      | Select model (IP / Lexicographic / Eps-Constraint / Single-Stage / MCLP), set parameters (K, β, σ, weight type, kept mevcut, fixed aday), and run or queue a job |
| 2   | **İş Kuyruğu**          | View queued jobs, load standard thesis experiments (6 combos × 2 scenarios), run all, clear queue                                                                |
| 3   | **Çözüm Detayları**     | Browse completed runs by model/filter, inspect IP solution tables, interactive Folium maps with coverage choropleth, coverage-vs-weight charts                   |
| 4   | **Çoklu Karşılaştırma** | Side-by-side comparison of 2 runs — map overlay, metric table, bar charts                                                                                        |
| 5   | **Hassasiyet Analizi**  | Sensitivity charts across β (quality weight) and K (budget) using saved metadata                                                                                 |
| 6   | **Mahalle Profili**     | Per-neighborhood data: population, risk, shelter need, existing containers                                                                                       |

### 6.2 Running Solvers

- **"Hemen Çalıştır"** runs the selected solver in a background thread — the UI stays responsive with a live elapsed-time counter
- **"Kuyruğa Ekle"** queues the job; use the Queue tab to run all queued jobs in sequence
- **"Kuyruğu Çalıştır"** processes all queued jobs in a background thread with live progress bar
- Results (solution tables, maps, coverage charts) appear automatically in tabs 3-5 after completion

### 6.3 MCDM Method Selection (Equity Models)

`11_lexicographic.py`, `14_single_stage.py`, and `13_eps_constraint.py` now support `--mcdm` and `--mcdm-focus` flags:

```powershell
python src/11_lexicographic.py --mcdm PROMETHEE --mcdm-focus Baseline
python src/13_eps_constraint.py --mcdm ELECTRE --mcdm-focus DamageFocused
python src/14_single_stage.py --mcdm VIKOR --mcdm-focus InfrastructureFocused
```

Available methods: `TOPSIS`, `PROMETHEE`, `VIKOR`, `ELECTRE`
Available foci: `Baseline`, `DamageFocused`, `InfrastructureFocused`

---

## 7. Methods Reference (CLI)

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
python src/15_compromise.py [--scenario {A,B}] [--sigma S] [--beta B]
                             [--K K] [--weight {risk,population}] [--no-mevcut]
```

Consumes the matching scenario-specific `results/eps_constraint/pareto_results_*.xlsx` file produced by `13_eps_constraint.py`.

---

## 8. Example App Point Solution

### Selected 8 Sites (Scenario A, TOPSIS/Baseline, Adaptive Sigma)

| S_No | Alan_Adi                                                               | Mahalle         |
| ---- | ---------------------------------------------------------------------- | --------------- |
| 4    | Ali Kuscu Imam Hatip Ortaokulu Bahcesi                                 | ABDURRAHMANGAZI |
| 16   | Yunus Emre Ortaokulu Bahcesi / Yunus Emre Imam Hatip Ortaokulu Bahcesi | ADIL            |
| 25   | Sehit Erdem Diker Imam Hatip Ortaokulu Bahcesi                         | AHMET YESEVI    |
| 55   | Golet Ilkokulu Bahcesi                                                 | FATIH           |
| 59   | Esref Bitlis Parki                                                     | HAMIDIYE        |
| 60   | Ibrahim Dede Parki                                                     | HAMIDIYE        |
| 70   | Ahmet Yesevi Ilkokulu Bahcesi                                          | MECIDIYE        |
| 83   | Mehmet Akif Ersoy Parki                                                | MEHMET AKIF     |

### KPI (12 → 20 containers)

| Metric                        | Before | After | Change     |
| ----------------------------- | ------ | ----- | ---------- |
| Total fuzzy service intensity | 37.32  | 62.40 | +67.2%     |
| Mahalle min coverage          | 0.473  | 0.995 | +110.3%    |
| Mahalle below 0.50            | 1      | 0     | eliminated |

---

## 9. Dependencies

`pandas`, `numpy`, `openpyxl`, `pulp`, `matplotlib`, `scipy`, `python-docx`, `tabulate`, `fpdf2`, `streamlit`, `folium`, `plotly`, `seaborn`, `osmnx`, `networkx`

Install all dependencies:
```powershell
pip install -r requirements.txt
```

## 10. Academic Documentation

The comprehensive academic documentation is available at `docs/IE492_Academic_Documentation.md` (985 lines, ~10,000 words). This thesis-ready document covers:

| Section | Content |
|---------|---------|
| §1 Problem Formulation | Sets, indices, parameters, Gaussian fuzzy coverage model, main IP with 6 alternative models, MCDM pipeline (AHP + TOPSIS), Gini equity metric |
| §2 System Architecture | High-level data flow, 15 module descriptions with function signatures, file dependency tree |
| §3 Parameter Deep-Dive | 5 tuning parameters (β, σ, α, ε_trunc, τ), Q_i road accessibility deep-dive, OAT sensitivity, tornado diagrams |
| §4 Literature Review | 25+ academic references with inline citations |
| Appendix A | Full notation summary |
| Appendix B | Worked numerical examples (AHP computation, Gaussian coverage, Q_i effect) |

---

## 11. License & Attribution

Course: IE 492 — Industrial Engineering Senior Project
Team: Elif Keles, Zumra Sancakli, Doga Yardemir, Semanur Aydin
Advisor: Dr. Ahmet Yekta Kayman
Date: June 2026
Data: IBB (Istanbul Metropolitan Municipality), Sultanbeyli Municipality, AFAD / AYDES

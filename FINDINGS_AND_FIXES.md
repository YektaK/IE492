# IE492 Codebase — Findings & Fixes Tracker

> Last updated: 2026-06-08
> Methodology: Deep code review by 3 parallel agents (solver scripts, Streamlit app/data flow, data pipeline/tests)

---

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| CRITICAL | Active bug that breaks functionality or produces wrong results | Fix immediately |
| HIGH | Systematic design flaw causing incorrect behavior or data loss | Fix next |
| MODERATE | Correctness issue, misleading output, or missing validation | Schedule |
| LOW | Code quality, test gaps, minor inconsistencies | Track |

---

## CRITICAL

| # | File | Lines | Issue | Status | Fix |
|---|------|-------|-------|--------|-----|
| 1 | `src/sensitivity.py` | 52,124,197 | **TRUNCATE mismatch — silent no-op.** `run_ip_model` called without `TRUNCATE` (defaults to 0.0), but glob searches for `_t0.15` suffix. No file ever matches → empty results, empty plots, no error. | ✅ FIXED | Passed `TRUNCATE=0.15` to all 3 `run_ip_model()` calls |
| 2 | `src/12_sigma_grid.py` | 74 | **Wrong column name crashes startup.** Reads `CC_Baseline` but actual column is `CC_Baseline_MinMax`. `KeyError` on any run. | ✅ FIXED | Changed to `CC_Baseline_MinMax` |
| 3 | `src/08_lscp.py` | 78-82,145-148 | **Double Q_i multiplication on mevcut contribution.** `mev_cov[mh]` already includes Q_i, then constraint applies `qi * (sum + mev_cov)`, squaring Q_i on mevcut term. | ✅ FIXED | Moved `base` outside `qi * (...)` in constraint |
| 4 | `app.py` | 71-79 | **`jobs.json` race condition.** `load_jobs()`/`save_jobs()` have zero concurrency protection. Queue runner + user add job can overwrite each other. | ✅ FIXED | Atomic write (tmp → rename) |
| 5 | `app.py` | 414-468 | **`completed_jobs_log.json` race condition.** Same TOCTOU pattern as #4. Concurrent queue runs overwrite completion logs. | ✅ FIXED | Replaced writes with `_atomic_write_json()` |
| 6 | `src/03d_electre.py` | 27-35 | **Discordance ignored — not real ELECTRE.** Only concordance computed; no veto threshold. Alternative catastrophically bad on 1 criterion can still outrank. | ✅ FIXED | Added discordance matrix + penalty term |

## HIGH

| # | File | Lines | Issue | Status | Fix |
|---|------|-------|-------|--------|-----|
| 7 | `src/11_lexicographic.py` | 57,88 | **Hardcoded TOPSIS only.** Ignore PROMETHEE/VIKOR/ELECTRE scores. | ✅ FIXED | Added `--mcdm` arg, `load_mcdm_column()` from `scenario_utils.py`, MCDM in filename |
| 8 | `src/14_single_stage.py` | 56,86 | **Hardcoded TOPSIS only.** Same as #7. | ✅ FIXED | Same as #7 |
| 9 | `src/13_eps_constraint.py` | 71,90 | **Hardcoded VIKOR only.** | ✅ FIXED | Same pattern as #7 (defaults to VIKOR for backward compat) |
| 10 | `app.py` | 994,1307,476 | **`st.rerun()` hides success messages.** After minutes of waiting, user sees only a refreshed page. | ✅ FIXED | Session state notification pattern (`_set_notification`/`_show_notification`) across 7 sites |
| 11 | `app.py` | 188-189 | **Silent `except Exception: pass`.** Visualization failures produce no warning to user. | ✅ FIXED | Now logs `logger.warning(...)` with error message |
| 12 | `src/app_runner.py` | 56-58 | **`latest_match()` uses mtime.** Unreliable for duplicate-param runs; NTFS ~100ms granularity. | ✅ FIXED | Changed to filename-based sort (timestamps in names) |
| 13 | `src/config.py` | 70-77 | **`get_mevcut_indices()` over-broad except.** Catches all exceptions, silently defaults. | ✅ FIXED | Narrowed to `except (FileNotFoundError, ImportError)` |

## MODERATE

| # | File | Lines | Issue | Status | Fix |
|---|------|-------|-------|--------|-----|
| 14 | `src/solver_core.py` | 50 | **K_TOTAL < len(KEPT_MEVCUT) silent infeasibility.** Constraint `sum(X) == negative` causes cryptic failure. | ✅ FIXED | Added `ValueError` validation before model build |
| 15 | `src/05_ip.py` | 195,210 | **Z_quality missing β factor.** Reports raw `sum(q_j)` without BETA_QUALITY multiplier. | ✅ FIXED | Computes `Z_quality_val = BETA_QUALITY * Z_quality_raw` |
| 16 | `src/16_mclp.py` | 36-37 | **Hardcoded distance paths.** Bypasses `fuzzy_coverage_paths()`. | ✅ FIXED | Uses `fuzzy_coverage_paths(str(S))` for S-respecting paths |
| 17 | `src/01_data_prep.py` +6 more | 23-26 | **Doesn't use `config.py` paths.** Own `PROCESSED` definition won't propagate changes. | ✅ FIXED | Import from config (also fixed in 03a, 03b, 03c, 03d, 12b, 11_master, 01b, 02b) |
| 18 | Multiple | 222,205,198,143,43 | **Hardcoded `+12`.** `args.K + 12` ignores actual row count. | ✅ FIXED | Replaced with `len(get_mevcut_indices())` in 5 files |
| 19 | `app.py` | 319,408 | **App freezes 600s during solver.** No async/threading; all UI blocked. | ✅ FIXED | Background thread + session state polling with `st.rerun()` |
| 20 | `app.py` | 149,730 | **`fixed_df` always empty.** Fixed aday flags never visualized on map. | ✅ FIXED | Populated from `yeni_df` filtered by job's `fixed_aday` list |

## LOW

| # | File | Lines | Issue | Status | Fix |
|---|------|-------|-------|--------|-----|
| 21 | `tests/test_core.py` | 546-549 | **`test_excel_report_generation` silently skips.** CI passes but exercises nothing on fresh checkout. | ✅ FIXED | Synthetic metadata created inline instead of looking for real files |
| 22 | Multiple | — | **Haversine duplicated in 5 active files.** Addition in `archive/` neglected. | ✅ FIXED | Added `haversine_m()` to `scenario_utils.py` |
| 23 | `src/03b_promethee.py` | 51-59 | **Arbitrary q threshold (20%).** No sensitivity analysis. | ✅ FIXED | Added `--q-frac` CLI arg (default 0.20 preserves old behavior) |
| 24 | `src/01b_entropy_weights.py` | 82 | **`P <= 0` masks negative values.** `>=` catches corruption silently. | ✅ FIXED | `P <= 0` → `P == 0`; `warnings.warn()` on negative values |
| 25 | `src/04_fuzzy_coverage.py` | 212-213 | **Distance vs mu file suffix inconsistency.** Distance files lack `_sAdaptive` suffix; docstring wrong. | ✅ FIXED | Distance files now always include `_140x17{SUFFIX}` matching mu file pattern |
| 26 | `src/02b_bwm_weights.py` | 98-99 | **Consistency ratio not computed.** ξ* shown but no ξ*/max_ξ ratio. | ✅ FIXED | Added CR = ξ* / CI(a_BW) per Rezaei (2015) |
| 27 | `app.py` | multiple | **Repeated imports.** `components`, `plotly.graph_objects`, `matplotlib.pyplot` imported inside functions. | ✅ FIXED | Hoisted `go`, `px`, `plt` to top-level |

---

## Fix Log

| Date | # | Description | Status |
|------|---|-------------|--------|
| 2026-06-08 | — | Initial findings document created | ✅ |
| 2026-06-08 | 1 | `sensitivity.py`: Added `TRUNCATE=0.15` to all 3 `run_ip_model()` calls | ✅ FIXED |
| 2026-06-08 | 2 | `12_sigma_grid.py`: Changed `CC_Baseline` → `CC_Baseline_MinMax` | ✅ FIXED |
| 2026-06-08 | 3 | `08_lscp.py`: Fixed double Q_i multiplication — moved `base` outside `qi * (...)` | ✅ FIXED |
| 2026-06-08 | 4 | `app.py`: `jobs.json` atomic write (tmp → rename) | ✅ FIXED |
| 2026-06-08 | 5 | `app.py`: `completed_jobs_log.json` atomic write | ✅ FIXED |
| 2026-06-08 | 6 | `03d_electre.py`: Added discordance matrix + penalty | ✅ FIXED |
| 2026-06-08 | 7-9 | Multi-MCDM: Added `--mcdm` arg to 3 equity models, shared `load_mcdm_column()` | ✅ FIXED |
| 2026-06-08 | 10 | `app.py`: `st.rerun()` → session state notifications | ✅ FIXED |
| 2026-06-08 | 11 | `app.py`: `except Exception: pass` → `logger.warning()` | ✅ FIXED |
| 2026-06-08 | 12 | `app_runner.py`: `latest_match()` → filename sort | ✅ FIXED |
| 2026-06-08 | 13 | `config.py`: `get_mevcut_indices()` narrow except | ✅ FIXED |
| 2026-06-08 | 14 | `solver_core.py`: K_TOTAL validation | ✅ FIXED |
| 2026-06-08 | 15 | `05_ip.py`: Z_quality beta factor | ✅ FIXED |
| 2026-06-08 | 16 | `16_mclp.py`: Hardcoded distance paths → `fuzzy_coverage_paths()` | ✅ FIXED |
| 2026-06-08 | 18 | 5 files: Hardcoded `+12` → `len(get_mevcut_indices())` | ✅ FIXED |
| 2026-06-08 | 20 | `app.py`: `fixed_df` populated from job params | ✅ FIXED |
| 2026-06-08 | 22 | `scenario_utils.py`: Added shared `haversine_m()` | ✅ FIXED |
| 2026-06-08 | 19 | `app.py`: Background thread + polling for solver (no more UI freeze) | ✅ FIXED |
| 2026-06-08 | 17 | `01_data_prep.py` + 6 more: Use config.py paths instead of hardcoded | ✅ FIXED |
| 2026-06-08 | 21 | `test_core.py`: Synthetic metadata instead of silent skip | ✅ FIXED |
| 2026-06-08 | 23 | `03b_promethee.py`: Added `--q-frac` CLI arg | ✅ FIXED |
| 2026-06-08 | 24 | `01b_entropy_weights.py`: `P <= 0` → `P == 0` + warning on negatives | ✅ FIXED |
| 2026-06-08 | 25 | `04_fuzzy_coverage.py`: Distance files now consistent with mu naming | ✅ FIXED |
| 2026-06-08 | 26 | `02b_bwm_weights.py`: Added CR = ξ* / CI(a_BW) | ✅ FIXED |
| 2026-06-08 | 27 | `app.py`: Hoisted `go`, `px`, `plt` to top-level imports | ✅ FIXED |

## Additional Improvements

| Area | Description |
|------|-------------|
| Hardcoded `range(12)` | Replaced 20 occurrences across 8 files with `get_mevcut_indices()` |
| Structured logging | Added file handler (`logs/ie492.log`), `JobLoggerAdapter`, `job_logger()` factory |
| `requirements.txt` | Created with all 14 packages and compatible version ranges |
| Type hints | Added to `solver_core.py`, `visualization.py`, `config.py`, `app_runner.py` |
| `load_mcdm_scores()` | Extracted from `05_ip.py` to `scenario_utils.py`; new `load_mcdm_column()` for single-vector lookup |

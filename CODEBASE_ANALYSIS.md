# IE492 Codebase Analysis: Errors & Improvement Areas

## Project Overview

This is a sophisticated **multi-criteria optimization system** for disaster response container location selection in Sultanbeyli, Istanbul. It combines MCDM methods (TOPSIS, PROMETHEE, VIKOR, ELECTRE), integer programming (MILP), fuzzy coverage modeling, and scenario analysis. The codebase spans ~38 Python source files with a Streamlit dashboard frontend (~1686 lines).

---

## 🔴 Critical Issues (Potential Runtime Errors)

### 1. `seaborn-v0_8-whitegrid` style deprecated — `visualization.py:19`, `07_reporting.py:48`

```python
plt.style.use("seaborn-v0_8-whitegrid")
sns.set_context("paper", font_scale=1.2)
```

**Problem:** In seaborn ≥0.12, the `seaborn-v0_8-*` style names were removed. This will raise `ValueError: style 'seaborn-v0_8-whitegrid' is not found`. Also, `sns.set_context()` at module level is a side effect on import (present in both files).

**Fix:** Use `plt.style.use("seaborn-v0_8")` → `plt.style.use("seaborn-whitegrid")` for older seaborn, or wrap in try/except for compatibility.

### 2. Bare `except Exception` silently swallows errors — 11 locations

Files affected: `config.py:10`, `06_compare.py:22`, `07_reporting.py:33,162`, `09_gini.py:20`, `10_infra_score.py:19`, `11_lexicographic.py:23`, `13_eps_constraint.py:24`, `14_single_stage.py:20`, `15_compromise.py:24`, `sensitivity.py:11`

**Problem:** These catch-all handlers silently swallow errors, making debugging extremely difficult. While wrapping `sys.stdout.reconfigure` in bare `except Exception` (config.py:10, 07_reporting.py:33) is acceptable, others hide real failures.

**Note:** `excel_report_generator.py:41,126,150` and `road_network.py:27` also catch `Exception` but bind to `e` and log the error — these are acceptable patterns.

**Fix:** Log the exception:
```python
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
```

### 3. `visualization.py` imports `seaborn` at module level — side effect

```python
import seaborn as sns
# ...
sns.set_context("paper", font_scale=1.2)  # module-level side effect
```

**Problem:** Simply importing `visualization` changes global matplotlib/seaborn state, affecting any other module that imports it.

**Fix:** Move `sns.set_context()` into a function or use `with sns.plotting_context(...)`.

---

## 🟡 Code Quality Issues

### 4. `haversine_m()` duplicated in 6 files

- `01_data_prep.py:204`
- `04_fuzzy_coverage.py:34`
- `12b_sigma_calibration.py:23`
- `12_sigma_grid.py:30`
- `road_network.py:12`
- `scenario_utils.py:109`

**Problem:** 6 identical (or near-identical) copies of the same function. Any bug fix or optimization must be applied in 6 places.

**Fix:** Centralize in `solver_core.py` or `scenario_utils.py` and import from there.

### 5. Inconsistent `sys.path` manipulation across 11 files

Every solver script does:
```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
```

This is fragile and makes the codebase sensitive to execution context.

**Fix:** Install the package in editable mode (`pip install -e .`) with a `pyproject.toml` or `setup.py`, or use a consistent entry point.

### 6. Inconsistent config imports across modules

Some files import from `config`:
- `from config import DATA_DIR as PROCESSED, RESULTS_DIR` (05_ip.py)
- `from config import DATA_DIR as DATA, RESULTS_DIR as RES` (11_lexicographic.py)
- `from config import norm_mahalle, DATA_DIR as PROCESSED, RESULTS_DIR` (04_fuzzy_coverage.py)

The same constants are aliased differently in different files, making cross-module refactoring error-prone.

### 7. `app.py` mixes UI, business logic, and subprocess management

The `app.py` file is **1686 lines** (not ~700 as previously estimated), combining Streamlit UI rendering, subprocess job execution, background thread management, file I/O for job queue, and visualization orchestration.

**Problem:** This violates single-responsibility principle. Testing any individual concern is nearly impossible.

**Fix:** Extract job management, visualization, and data loading into separate modules.

### 8. `run_all_scenarios.py` — `exp.pop("_beta_sweep", None)` mutates config

At line 167, `_beta_sweep` is popped from the experiment config dict (restored at line 176). If an exception occurs between pop and restore, the config stays mutated. Also, the same dict is mutated for side effect rather than copied.

### 9. No input validation in solver scripts

Most `main()` functions accept parameters without validation:
- No check that `K_TOTAL > 0`
- No check that `0 <= BETA <= 1`
- No check that `SCENARIO in ("A", "B")`
- No check that sigma files exist before solving

---

## 🟠 Architectural / Design Issues

### 10. No `__init__.py` in `src/` directory

The `src/` folder lacks an `__init__.py`, so it's not a proper Python package. This forces every script to manually manipulate `sys.path`.

### 11. Circular import risk between `config.py` and `scenario_utils.py`

`scenario_utils.py` imports `norm_mahalle` from `config` at line 71 (lazy import inside `load_mcdm_scores()`), and `config.py` doesn't import from `scenario_utils`. Currently safe, but the lazy import inside `load_mcdm_scores()` is a code smell indicating tight coupling.

### 12. Test coverage is minimal relative to codebase size

Only **16 test functions** in `tests/test_core.py` covering: string normalization, path existence, input file schema, truncation runtime, Gini calculation, Haversine distance, fuzzy coverage symmetry, MCDM score ranges, IP loading, LSCP imports, and run_all_scenarios integration.

**Missing tests:**
- No tests for solver/optimization logic (05_ip MILP solve, 08_lscp, 16_mclp, etc.)
- No tests for MCDM scoring logic (TOPSIS, PROMETHEE, VIKOR, ELECTRE solve paths)
- No tests for the Streamlit app
- No integration tests for the end-to-end pipeline

### 13. Temporary files left in `src/`

`src/_tmp_docx.py` and `src/_tmp_inspect.py` are in the production source directory. These should be removed or moved to `scratch/`.

### 14. Hardcoded magic numbers throughout

- `15` hardcoded as mahalle count in `scenario_utils.py:32`
- `0.50` coverage threshold in 2 files in `src` (plus references in archive)
- `0.15` truncation threshold in multiple files
- `0.20` equity alpha in `14_single_stage.py`
- `0.30` default beta everywhere
- `6_371_000.0` Earth radius in 6 files

**Fix:** Centralize all magic numbers in `config.py` as named constants.

### 15. No type hints on public APIs

While **21 of 36** source files use `from __future__ import annotations`, most function signatures still lack full type annotations (especially return types on solver entry points). This reduces IDE support and makes refactoring risky.

### 16. No `pyproject.toml` or `setup.py`

The project has no package configuration file. This prevents:
- Installing in editable mode (`pip install -e .`)
- Declaring dependencies and entry points
- Publishing or sharing as a standard Python package
- Using modern Python packaging tooling

**Fix:** Add `pyproject.toml` with build-system config and project metadata.

---

## 🔵 Minor Issues

### 17. Turkish-language code mixed with English

Variable names, comments, and log messages are in Turkish while the codebase structure and some docstrings are in English. This is fine for a Turkish academic project but could hinder international collaboration.

### 18. `requirements.txt` has no upper bounds

No upper version bounds means a future `pandas` or `pulp` major version upgrade could silently break the codebase.

### 19. `jobs.json` starts empty but `completed_jobs_log.json` is referenced but never created

`COMPLETED_JOBS_FILE` is referenced in `config.py:21` and `app.py` but there's no code that creates it if it doesn't exist — the code only checks `if COMPLETED_JOBS_FILE.exists()`. The file itself does not exist in the repository.

### 20. `06_compare.py` uses `phi_{s}` but the actual column may be `phi01_{s}`

At line 66: `y2 = p[f"phi_{s}"]` — but the MCDM columns in `scenario_utils.py` use `phi01_{focus}` naming (line 51). This **will** cause a `KeyError` at runtime — `06_compare.py:66` references `phi_{s}` but `scenario_utils.py:51` defines the column template as `phi01_{focus}`.

---

## Summary Table

| Severity | Count | Key Areas |
|----------|-------|-----------|
| 🔴 Critical | 3 | Deprecated seaborn style, silent error swallowing, module side effects |
| 🟡 Quality | 6 | Code duplication, sys.path hacks, no input validation, config mutation, app.py bloat, inconsistent imports |
| 🟠 Architectural | 7 | No package structure, minimal tests, magic numbers, temp files, no type hints, circular import risk, missing pyproject.toml |
| 🔵 Minor | 4 | Language mixing, version bounds, orphaned file ref, column name mismatch |

---

## Recommended Priority Actions

1. **Fix seaborn compatibility** — wrap `plt.style.use()` in try/except
2. **Centralize `haversine_m()`** — move to `scenario_utils.py`, update all imports (6 files)
3. **Add error logging** — replace bare `except Exception` with logged warnings across 11 locations
4. **Add `pyproject.toml`** — eliminate `sys.path` hacks across all modules
5. **Centralize magic numbers** — add named constants to `config.py`
6. **Add `__init__.py`** — make `src/` a proper Python package
7. **Expand test coverage** — add solver, MCDM, and integration tests
8. **Refactor `app.py`** — separate UI, job management, and visualization concerns
9. **Clean up temp files** — move or delete `src/_tmp_*.py`

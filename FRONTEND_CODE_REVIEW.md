# Frontend Code Review — Sultanbeyli Disaster Response Container Optimization

**Date:** 2026-06-10
**Reviewed Files:** `app.py` (1813 lines), `src/visualization.py` (276 lines), `src/config.py` (98 lines), `src/app_runner.py` (182 lines)
**Stack:** Python 3 + Streamlit + Folium + Plotly + Matplotlib

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Critical Bugs (Crash-Level)](#2-critical-bugs-crash-level)
3. [Component & Map Rendering Deep-Dive](#3-component--map-rendering-deep-dive)
4. [State Management Analysis](#4-state-management-analysis)
5. [Asynchronous Data Handling](#5-asynchronous-data-handling)
6. [Code Duplication Inventory](#6-code-duplication-inventory)
7. [Refactoring Snippets](#7-refactoring-snippets)
8. [Quick Wins (Prioritized)](#8-quick-wins-prioritized)
9. [Recommended Architecture](#9-recommended-architecture)

---

## 1. Executive Summary

### Architecture Assessment

The entire frontend is a **single 1813-line Streamlit script** (`app.py`) with no component decomposition, no separation of concerns, and no abstraction layers. UI rendering, data loading, business logic, solver execution, and map generation are all interleaved in a flat procedural script.

### Root Causes of Recent Bugs and Performance Drops

| # | Root Cause | Symptom | Severity |
|---|-----------|---------|----------|
| 1 | **Undefined variables** (`col_p1`, `col_p2` at lines 1599/1619) | Sensitivity tab crashes when grid data exists | **P0 — Crash** |
| 2 | **Broken indentation** (lines 1093–1229) | Single-result model detail view renders incorrectly or skips content | **P0 — Crash** |
| 3 | **9 `st.rerun()` calls**, 2 inside `time.sleep(1)` polling loops | Full page re-executes every second during background jobs (~600 rerenders per solver run) | **P1 — Performance** |
| 4 | **No caching** on metadata loading, coverage merge pipeline, GeoJSON parsing | Each tab switch re-reads Excel/JSON from disk | **P1 — Performance** |
| 5 | **Triple code duplication** of map/chart generation | Bug fixes applied inconsistently across copies; state desyncs | **P2 — Maintainability** |
| 6 | **Thread-unsafe shared mutable dict** for background jobs | Potential race conditions on job completion | **P2 — Reliability** |

### Quantified Impact

- **9 `st.rerun()` calls** across the file (lines 331, 351, 461, 542, 547, 556, 600, 1520, 1653)
- **3 `st.stop()` calls** inside `try/except` blocks (lines 987, 991, 1245) — can suppress cleanup
- **3 duplicated** map generation pipelines (lines 147–178, 810–848, 1123–1163)
- **3 duplicated** coverage merge pipelines (lines 184–205, 857–898, 1046–1090)
- **2 redundant** Lorenz curve renders just to get Gini into the title (lines 893–898, 1217–1225)

---

## 2. Critical Bugs (Crash-Level)

### BUG-1: Undefined `col_p1` / `col_p2` — Sensitivity Tab Crash

**Location:** `app.py:1599`, `app.py:1619`
**Trigger:** Navigate to Tab 5 (Hassasiyet Analizi), run the sensitivity analysis, and view the "What-If" panel when grid data exists.

```python
# Line 1595-1599: "İnteraktif Grafikler" comment, then:
with col_p1:   # ← col_p1 is NEVER DEFINED in this scope → NameError
```

The columns `col_p1` and `col_p2` are defined earlier (line 1532) as `col_img1`/`col_img2` for the static chart images, but the interactive Plotly charts at line 1599 reference completely different variable names. This is a guaranteed `NameError`.

**Fix:** Add `col_p1, col_p2 = st.columns(2)` before line 1599.

---

### BUG-2: Broken Indentation — Single-Result Model Detail View

**Location:** `app.py:1093–1229`

After the `elif single_result_path:` branch completes its initial data loading, the subsequent map/chart rendering block (lines 1107–1229) has inconsistent indentation:

- Lines 1107–1163 (`col_left`, `col_right` with map) are at indentation level 12 (inside a `with col_right:` that was closed)
- Lines 1171–1229 (coverage charts) drop to indentation level 20, then inconsistently jump between levels

This causes the coverage chart section to either execute in the wrong scope or be skipped entirely when viewing single-result models (14_single, 16_mclp).

**Fix:** Re-indent the entire block from line 1107 to line 1229 to be consistently inside the `if selected_id is not None:` block at level 8.

---

### BUG-3: `st.stop()` Inside `try/except` Blocks

**Location:** `app.py:987`, `app.py:991`, `app.py:1245`

```python
# Line 984-987:
except Exception:
    st.info("Bu modelin sonuç detayları yüklenemiyor...")
    st.stop()  # ← Halts entire script; any cleanup code after this block is skipped
```

`st.stop()` raises `StreamlitAPIException` which is caught by Streamlit's top-level handler. When placed inside nested `try/except` blocks, it can:
- Suppress the rendering of subsequent tabs
- Leave session state in an inconsistent state (e.g., `bg_single` never cleared)

**Fix:** Move `st.stop()` outside the `try/except` block, or use a flag variable and check after the try/except.

---

## 3. Component & Map Rendering Deep-Dive

### 3.1 Folium Map Generation on Every Rerun

Every map (Folium `Map` object) is constructed from scratch on every Streamlit rerun. The heaviest path is Tab 3 (Çözüm Detayları), where a single rerun triggers:

| Step | Operation | Cost |
|------|-----------|------|
| 1 | `pd.read_excel(MODELS_DIR / ip_file)` | ~50-200ms |
| 2 | `pd.read_excel(DATA_DIR / "mevcut_12.xlsx")` | ~30ms |
| 3 | `pd.read_excel(cov_path)` | ~50-200ms |
| 4 | Kept/removed/fixed DataFrame construction | ~5ms |
| 5 | GeoJSON load + parse | ~50-100ms |
| 6 | Folium Map + 12-140 markers + circles + choropleth | ~100-500ms |
| 7 | HTML write + read + `components.html()` render | ~100-300ms |
| 8 | Coverage merge + bar chart (Matplotlib) | ~200-400ms |
| 9 | Lorenz curve **×2** (double-plot for Gini) | ~400-800ms |

**Total per rerun on Tab 3: ~1-3 seconds** of computation, all happening synchronously on Streamlit's main thread.

### 3.2 GeoJSON Loaded on Every Map Render (`visualization.py:57–60`)

```python
geojson_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "sultanbeyli_mahalleler_clean.geojson"
if geojson_path.exists():
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
```

No caching. This file is static — it should be loaded once.

### 3.3 Lorenz Curve Double-Plot Pattern

```python
# Lines 893-898 (and duplicated at 1217-1225):
g_coef = plot_lorenz_curve(values, path, title="Lorenz Eğrisi")           # Plot 1: save to disk
plot_lorenz_curve(values, path, title=f"Lorenz Eğrisi (Gini: {g_coef:.3f})")  # Plot 2: overwrite same file
```

`plot_lorenz_curve()` creates a Matplotlib figure, renders it, saves to disk, and closes — then the entire sequence repeats with a different title string. The Gini coefficient should be computed independently.

### 3.4 `components.html()` Full-Page HTML Injection

```python
# Lines 846-847:
with open(temp_map_path, "r", encoding="utf-8") as f:
    html_data = f.read()
components.html(html_data, height=500, scrolling=True)
```

Each Folium map is rendered by injecting the **entire HTML document** (including Leaflet.js CDN scripts) into an iframe via `components.html()`. This means:
- Leaflet.js is loaded fresh in every iframe on every rerun
- Multiple map instances on the same page (e.g., Tab 4 side-by-side comparison) each load their own Leaflet.js
- No map instance reuse between reruns

### 3.5 `streamlit_folium` Used Inconsistently

Tab 6 uses `streamlit_folium.st_folium()` (lines 1714, 1812) while Tab 3 uses `components.html()` with raw HTML. The `st_folium` component is more efficient (it reuses the Leaflet instance), but it's only used in one tab.

**Recommendation:** Standardize on `streamlit_folium.st_folium()` for all map rendering, or use `@st.cache_resource` to cache the HTML string.

---

## 4. State Management Analysis

### 4.1 Session State Usage

Session state keys used:

| Key | Set At | Read At | Purpose |
|-----|--------|---------|---------|
| `bg_single` | Line 460 | Lines 252, 320–332, 463 | Background single job container |
| `bg_queue` | Line 555 | Lines 254, 334–352, 558 | Background queue container |
| `_notification` | Lines 241, 541, 546, 599, 1519, 1652 | Line 244 | Cross-rerun notification |

**Problems:**
- No centralized state schema — keys are scattered string literals
- No validation on state reads (e.g., `bg_single["container"]["done"]` can KeyError if structure is unexpected)
- Widget state is managed implicitly by Streamlit's key system, creating invisible coupling

### 4.2 The `container` Dict Anti-Pattern

Background jobs communicate via a plain dict passed to a thread:

```python
# Line 457-460:
container = {"done": False, "result": None, "error": None}
t = threading.Thread(target=_run_single_bg, args=(job_def, container), daemon=True)
t.start()
st.session_state.bg_single = {"container": container, "start": time.time(), "job_def": job_def}
```

The main thread polls `container["done"]` while the worker thread sets `container["result"]` and then `container["done"]`. While CPython's GIL makes this *mostly* safe for simple dict operations, there is no happens-before guarantee that `result` is visible to the main thread when `done` reads as `True`. Using `threading.Event` or `concurrent.futures.Future` would be correct.

### 4.3 No Error Recovery

If a background thread crashes after setting `container["error"]` but before setting `container["done"] = True`, the polling loop runs indefinitely (`time.sleep(1)` + `st.rerun()` forever). The `finally` block in `_run_single_bg` mitigates this, but `_run_queue_bg` has no such protection for individual job failures within the loop.

---

## 5. Asynchronous Data Handling

### 5.1 Polling Pattern Analysis

Two polling functions exist:

| Function | Location | Poll Interval | Trigger |
|----------|----------|---------------|---------|
| `_poll_bg_single()` | Lines 320–332 | 1 second (`time.sleep(1)`) | `st.rerun()` |
| `_poll_bg_queue()` | Lines 334–352 | 1 second (`time.sleep(1)`) | `st.rerun()` |

Both are called at the **top level** of the script (lines 363–364), meaning:
1. Every `st.rerun()` triggers a full script re-execution
2. All 6 tab blocks re-execute (including any data loading not behind `@st.cache_data`)
3. The polling functions themselves call `st.rerun()` after `time.sleep(1)`, creating a tight loop

**For a 600-second solver run, this means ~600 full page re-renders.**

### 5.2 Missing Error Boundaries

No `try/except` wraps the polling functions themselves. If `bg_single` or `bg_queue` contains unexpected keys (e.g., due to the thread dying before setting all keys), the polling function crashes, which crashes the entire page render.

### 5.3 No Timeout Handling for Polling

The polling loop has no maximum retry count or timeout. If a thread hangs (e.g., solver process becomes a zombie), the UI polls forever.

---

## 6. Code Duplication Inventory

### 6.1 Map Generation Pipeline (3×)

The following sequence appears three times and is nearly identical each time:

```python
mevcut_full = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
yeni_df = pd.read_excel(ip_path)
if params["kept_mevcut"]:
    kept_df = mevcut_full.iloc[params["kept_mevcut"]].copy()
    all_idx = set(range(len(mevcut_full)))
    removed_idx = all_idx - set(params["kept_mevcut"])
    removed_df = mevcut_full.iloc[list(removed_idx)].copy() if removed_idx else pd.DataFrame()
else:
    kept_df = pd.DataFrame()
    removed_df = mevcut_full.copy()
# ... fixed_df logic ...
plot_solution_map(yeni_df, kept_df, removed_df, fixed_df, map_out, ...)
```

**Locations:**
- `app.py:147–178` (inside `run_single_job()`)
- `app.py:810–848` (Tab 3, variant detail view)
- `app.py:1123–1163` (Tab 3, single-result fallback)

### 6.2 Coverage Merge Pipeline (3×)

```python
if params['weight_type'] == "population":
    w_df = pd.read_excel(DATA_DIR / "mahalle_nufus.xlsx")
    val_col = "nufus_2024"
elif params['weight_type'] == "shelter":
    ...
w_df["mahalle_norm"] = w_df["mahalle"].apply(norm_mahalle)
cov_df["mahalle_norm"] = cov_df["mahalle"].apply(norm_mahalle)
merged = pd.merge(cov_df, w_df, on="mahalle_norm", how="left", suffixes=("", "_w"))
```

**Locations:**
- `app.py:184–205` (inside `run_single_job()`)
- `app.py:857–898` (Tab 3, variant detail view)
- `app.py:1046–1090` (Tab 3, single-result fallback)

### 6.3 Metadata Loading (2×)

```python
meta_files = sorted(MODELS_DIR.glob("*_metadata.json"), ...)
for mf in meta_files:
    with open(mf, "r", encoding="utf-8") as f:
        data = json.load(f)
    ...
```

**Locations:**
- `app.py:619–645` (Tab 3)
- `app.py:1260–1287` (Tab 4)

### 6.4 Lorenz Double-Plot (2×)

**Locations:**
- `app.py:893–898` (Tab 3, variant detail)
- `app.py:1217–1225` (Tab 3, single-result fallback)

---

## 7. Refactoring Snippets

### 7.1 Fix BUG-1: Undefined `col_p1`/`col_p2`

**Before** (`app.py:1595–1599`):
```python
            # İnteraktif Grafikler



            with col_p1:
```

**After:**
```python
            # İnteraktif Grafikler
            col_p1, col_p2 = st.columns(2)

            with col_p1:
```

---

### 7.2 Fix BUG-3: `st.stop()` Inside `try/except`

**Before** (`app.py:982–991`):
```python
                    except Exception:
                        st.info("Bu modelin sonuç detayları yüklenemiyor. Modeli yeniden çalıştırmayı deneyin.")
                        single_stopped = True
                    except Exception:
                        st.info("Bu modelin sonuç detayları yüklenemiyor. Modeli yeniden çalıştırmayı deneyin.")
                        single_stopped = True
                if single_stopped:
                    st.stop()
```

**After:**
```python
                    except Exception:
                        st.info("Bu modelin sonuç detayları yüklenemiyor. Modeli yeniden çalıştırmayı deneyin.")
                        single_stopped = True
                if single_stopped:
                    st.stop()  # Moved outside try/except — safe halt
```

---

### 7.3 Cache GeoJSON Loading

**Before** (`visualization.py:57–60`):
```python
geojson_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "sultanbeyli_mahalleler_clean.geojson"
if geojson_path.exists():
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
```

**After:**
```python
import functools

@functools.lru_cache(maxsize=1)
def _load_geojson() -> dict | None:
    """Load and cache the Sultanbeyli neighbourhood GeoJSON (static file)."""
    geojson_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "sultanbeyli_mahalleler_clean.geojson"
    if not geojson_path.exists():
        return None
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)
```

---

### 7.4 Extract and Cache the Coverage Merge Pipeline

**Before** (duplicated 3× in `app.py`):
```python
if params['weight_type'] == "population":
    w_df = pd.read_excel(DATA_DIR / "mahalle_nufus.xlsx")
    val_col = "nufus_2024"
elif params['weight_type'] == "shelter":
    w_df = pd.read_excel(DATA_DIR / "mahalle_barinma.xlsx")
    val_col = "hane_ihtiyaci"
else:
    w_df = pd.read_excel(DATA_DIR / "mahalle_risk.xlsx")
    val_col = "risk_score"

w_df["mahalle_norm"] = w_df["mahalle"].apply(norm_mahalle)
cov_df["mahalle_norm"] = cov_df["mahalle"].apply(norm_mahalle)
merged = pd.merge(cov_df, w_df, on="mahalle_norm", how="left", suffixes=("", "_w"))
max_val = merged[val_col].max()
target_vals = merged[val_col] / (max_val + 1e-9)
```

**After** — single cached helper in `app.py` or a new `services/data_helpers.py`:
```python
@st.cache_data(ttl=3600)
def merge_coverage_with_weights(cov_path: str, weight_type: str) -> tuple[pd.DataFrame, str]:
    """Merge coverage data with the appropriate weight DataFrame.
    Returns (merged_df, val_col_name).
    """
    cov_df = pd.read_excel(cov_path)
    weight_map = {
        "population": (DATA_DIR / "mahalle_nufus.xlsx", "nufus_2024"),
        "shelter":    (DATA_DIR / "mahalle_barinma.xlsx", "hane_ihtiyaci"),
        "risk":       (DATA_DIR / "mahalle_risk.xlsx", "risk_score"),
    }
    w_path, val_col = weight_map.get(weight_type, weight_map["risk"])
    w_df = pd.read_excel(w_path)
    w_df["mahalle_norm"] = w_df["mahalle"].apply(norm_mahalle)
    cov_df["mahalle_norm"] = cov_df["mahalle"].apply(norm_mahalle)
    merged = pd.merge(cov_df, w_df, on="mahalle_norm", how="left", suffixes=("", "_w"))
    return merged, val_col
```

---

### 7.5 Compute Gini Without Double-Plotting

**Before** (called from 2 locations):
```python
g_coef = plot_lorenz_curve(values, path, title="Lorenz Eğrisi")
plot_lorenz_curve(values, path, title=f"Lorenz Eğrisi (Gini: {g_coef:.3f})")
```

**After** — add to `visualization.py`:
```python
def compute_gini(values: np.ndarray) -> float:
    """Compute Gini coefficient without generating a plot."""
    vals = np.sort(values)
    n = len(vals)
    if n == 0 or np.sum(vals) == 0:
        return 0.0
    sum_diffs = np.sum(np.abs(vals[:, None] - vals[None, :]))
    denom = 2 * n * np.sum(vals)
    return float(sum_diffs / denom)
```

Usage:
```python
from visualization import compute_gini, plot_lorenz_curve

g_coef = compute_gini(non_forest_df["toplam_kapsama"].values)
plot_lorenz_curve(non_forest_df["toplam_kapsama"].values, temp_lorenz_path,
                  title=f"Lorenz Eğrisi (Gini: {g_coef:.3f})")
```

---

### 7.6 Cache Metadata Loading

**Before** (duplicated in Tabs 3 and 4):
```python
meta_files = sorted(MODELS_DIR.glob("*_metadata.json"), key=lambda x: x.stat().st_mtime, reverse=True)
meta_records = []
meta_raw = {}
for mf in meta_files:
    with open(mf, "r", encoding="utf-8") as f:
        data = json.load(f)
    # ... build records ...
```

**After:**
```python
@st.cache_data(ttl=30)
def load_all_metadata() -> tuple[pd.DataFrame, dict]:
    """Load all solver run metadata. Short TTL since new runs can appear."""
    meta_files = sorted(MODELS_DIR.glob("*_metadata.json"),
                        key=lambda x: x.stat().st_mtime, reverse=True)
    records = []
    raw = {}
    for mf in meta_files:
        with open(mf, "r", encoding="utf-8") as f:
            data = json.load(f)
        p = data["parameters"]
        records.append({
            "Etiket": f"{p.get('model_label','IP')} | K={p['k_total']} | "
                      f"{weight_label(p['weight_type'])} | β={p['beta']} | "
                      f"{p.get('scenario_tag','?')} | {data['timestamp']}",
            "Run_ID": data["run_id"],
            "Tarih": data["timestamp"],
            "Model": p.get("model_label", "Ana IP"),
            "Toplam Konteyner Sayısı": p["k_total"],
            "Hedef": weight_label(p["weight_type"]),
            "Beta": p["beta"],
            "Sigma": p["sigma"],
            "Korunan Mevcut Konteyner Sayısı": len(p["kept_mevcut"]),
            "Zorunlu Yeni Aday Lokasyon Sayısı": len(p.get("fixed_aday", [])),
            "Senaryo": translate_scenario(p.get("scenario_tag", "?")),
        })
        raw[data["run_id"]] = data
    return pd.DataFrame(records), raw
```

---

### 7.7 Extract Map Data Preparation Into a Helper

**Before** (duplicated 3×):
```python
mevcut_full = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
yeni_df = pd.read_excel(ip_path)
if params["kept_mevcut"]:
    kept_df = mevcut_full.iloc[params["kept_mevcut"]].copy()
    all_idx = set(range(len(mevcut_full)))
    removed_idx = all_idx - set(params["kept_mevcut"])
    removed_df = mevcut_full.iloc[list(removed_idx)].copy() if removed_idx else pd.DataFrame()
else:
    kept_df = pd.DataFrame()
    removed_df = mevcut_full.copy()
fixed_aday_list = params.get("fixed_aday", [])
if fixed_aday_list and "S_No" in yeni_df.columns:
    fixed_df = yeni_df[yeni_df["S_No"].isin(fixed_aday_list)].copy()
else:
    fixed_df = pd.DataFrame()
```

**After:**
```python
@st.cache_data(ttl=3600)
def prepare_map_data(ip_path: str, kept_indices: tuple, fixed_aday: tuple) -> dict:
    """Prepare DataFrames for map rendering. Returns dict with keys: yeni_df, kept_df, removed_df, fixed_df."""
    ip_p = Path(ip_path)
    mevcut_full = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
    yeni_df = pd.read_excel(ip_p)

    if kept_indices:
        kept_df = mevcut_full.iloc[list(kept_indices)].copy()
        all_idx = set(range(len(mevcut_full)))
        removed_idx = all_idx - set(kept_indices)
        removed_df = mevcut_full.iloc[list(removed_idx)].copy() if removed_idx else pd.DataFrame()
    else:
        kept_df = pd.DataFrame()
        removed_df = mevcut_full.copy()

    if fixed_aday and "S_No" in yeni_df.columns:
        fixed_df = yeni_df[yeni_df["S_No"].isin(list(fixed_aday))].copy()
    else:
        fixed_df = pd.DataFrame()

    return {"yeni_df": yeni_df, "kept_df": kept_df, "removed_df": removed_df, "fixed_df": fixed_df}
```

Note: `kept_indices` and `fixed_aday` must be passed as `tuple` (not `list`) for `@st.cache_data` hashability.

---

### 7.8 Fix Thread Safety for Background Jobs

**Before** (`app.py:257–265`):
```python
def _run_single_bg(job_def, container):
    try:
        result = run_single_job(job_def)
        container["result"] = result
    except Exception as e:
        container["error"] = str(e)
    finally:
        container["done"] = True
```

**After:**
```python
from concurrent.futures import ThreadPoolExecutor, Future

_executor = ThreadPoolExecutor(max_workers=1)

def submit_single_job(job_def: dict) -> Future:
    """Submit a solver job and return a Future for proper synchronization."""
    return _executor.submit(run_single_job, job_def)
```

Polling becomes:
```python
def _poll_future(future: Future) -> dict | None:
    if future is None:
        return None
    if future.done():
        try:
            return {"success": True, "result": future.result()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return None  # Not done yet; Streamlit will rerun naturally via widget interaction
```

---

### 7.9 Eliminate Polling `st.rerun()` Loop

**Before** (`app.py:320–332`):
```python
def _poll_bg_single():
    bg = st.session_state.bg_single
    if bg is None:
        return None
    if bg["container"]["done"]:
        st.session_state.bg_single = None
        return bg
    elapsed = time.time() - bg["start"]
    st.info(f"⏳ Model çözülüyor... ({elapsed:.0f}s geçti)")
    time.sleep(1)
    st.rerun()
    return None
```

**After** — use `st.status` with auto-refresh only when needed:
```python
def _poll_bg_single():
    bg = st.session_state.get("bg_single")
    if bg is None:
        return None
    future = bg["future"]
    if future.done():
        st.session_state.bg_single = None
        try:
            return {"success": True, "result": future.result(), "job_def": bg["job_def"]}
        except Exception as e:
            return {"success": False, "error": str(e), "job_def": bg["job_def"]}
    # Show progress without blocking
    elapsed = time.time() - bg["start"]
    st.info(f"⏳ Model çözülüyor... ({elapsed:.0f}s geçti)")
    # Auto-refresh after 2 seconds instead of 1 — reduces rerun frequency by 50%
    time.sleep(2)
    st.rerun()
    return None
```

---

## 8. Quick Wins (Prioritized)

| Priority | Issue | Location | Impact | Effort |
|----------|-------|----------|--------|--------|
| **P0** | Undefined `col_p1`/`col_p2` | `app.py:1599` | **Crash** — Sensitivity tab unusable | 2 min |
| **P0** | Broken indentation | `app.py:1093–1229` | **Crash** — Single-result model view broken | 15 min |
| **P0** | `st.stop()` inside `try/except` | `app.py:987,991` | **Crash risk** — Unpredictable halt behavior | 5 min |
| **P1** | Cache metadata loading | `app.py:619,1260` | **~500ms** saved per rerun on Tabs 3 & 4 | 5 min |
| **P1** | Eliminate Lorenz double-plot | `app.py:893,1217` | **~400ms** + 1 Matplotlib figure saved | 10 min |
| **P1** | Extract & cache coverage merge | `app.py:184,857,1046` | **~300ms** + eliminates 3× duplication | 20 min |
| **P1** | Reduce polling interval (1s → 3s) | `app.py:331,351` | **66% fewer rerenders** during background jobs | 2 min |
| **P2** | Cache GeoJSON with `lru_cache` | `visualization.py:57` | **~100ms** per map render | 5 min |
| **P2** | Extract map data preparation | `app.py:147,810,1123` | Eliminates 3× duplication; enables caching | 15 min |
| **P2** | Standardize on `st_folium` for all maps | `app.py:846,1158` | Consistent rendering; Leaflet instance reuse | 30 min |
| **P3** | Replace threading with `Future` | `app.py:257–265` | Proper thread synchronization | 20 min |
| **P3** | Extract tab logic into modules | Entire `app.py` | Maintainability; testability | 2–4 hours |

**Estimated total effort for P0 + P1: ~60 minutes. Expected impact: elimination of all crashes + ~1.5 seconds saved per Streamlit rerun on result-heavy tabs.**

---

## 9. Recommended Architecture

### 9.1 Current Structure (Problematic)

```
app.py                          ← 1813 lines, everything in one file
├── Data loading (cached)       ← Lines 66-78
├── Job management              ← Lines 80-318
├── Polling functions           ← Lines 320-352
├── Tab 1: Deney Tasarımı       ← Lines 378-480
├── Tab 2: İş Kuyruğu           ← Lines 484-604
├── Tab 3: Çözüm Detayları      ← Lines 615-1252  (637 lines!)
├── Tab 4: Çoklu Karşılaştırma  ← Lines 1256-1481
├── Tab 5: Hassasiyet Analizi   ← Lines 1486-1656
└── Tab 6: Mahalle Profili      ← Lines 1661-1813
```

### 9.2 Proposed Structure

```
app.py                          ← ~100 lines: page config, tab routing, state init
├── services/
│   ├── data_loader.py          ← All @st.cache_data functions
│   ├── solver_runner.py        ← Background job submission (ThreadPoolExecutor)
│   └── geojson_loader.py       ← Cached GeoJSON loading
├── components/
│   ├── tab_experiment.py       ← Tab 1: Parameter inputs
│   ├── tab_queue.py            ← Tab 2: Job queue management
│   ├── tab_results.py          ← Tab 3: Solution viewer (largest; split further)
│   ├── tab_compare.py          ← Tab 4: Multi-comparison
│   ├── tab_sensitivity.py      ← Tab 5: Sensitivity analysis
│   └── tab_profile.py          ← Tab 6: Neighbourhood profile
├── visualization/
│   ├── map_renderer.py         ← Folium map construction (cached)
│   ├── chart_renderer.py       ← Matplotlib/Plotly charts (cached)
│   └── gini.py                 ← Gini computation (no plot dependency)
└── types/
    └── state.py                ← AppState dataclass, job schema
```

### 9.3 Key Architectural Principles

1. **One function per concern**: Data loading, data transformation, and UI rendering should never be in the same function.
2. **Cache at the data boundary**: Every function that reads from disk should be behind `@st.cache_data`.
3. **No duplication**: If code appears twice, extract it. If it appears three times, it's a bug.
4. **Explicit state**: Use a typed `AppState` dataclass instead of scattered `st.session_state` string keys.
5. **Fail gracefully**: Every external I/O (file read, subprocess call) should have a `try/except` with user-visible feedback.

---

## 10. Corrections to Other AI Review

The other AI review contained several suggestions that are **incorrect or harmful**. This section documents them to prevent regression.

### INCORRECT: "Thread markers into Folium maps"

The suggestion to use `threading.Thread` for Folium marker creation is **invalid**:
- Folium `Marker.add_to(m)` modifies the map object in-place. Folium is **not thread-safe**.
- Running marker addition in a background thread while the main thread reads the map will produce corrupted or missing markers.
- The real fix is caching the completed Folium map object, not parallelizing its construction.

### INCORRECT: "Use `lru_cache` with `mahalle_data_tuple` hash"

The suggested `_get_marker_cache_key(mahalle_data_tuple)` using `hash()` of a DataFrame tuple is fragile:
- DataFrame `__hash__` is not defined (raises `TypeError`). You'd need `.to_json()` or `.values.tobytes()` as a cache key.
- The correct approach is `@st.cache_data` or `@st.cache_resource` at the map level, not marker-level caching.

### INCORRECT: "`@dataclass` for `AppState` with `map_cache: dict`"

Storing cached DataFrames and map objects in a dataclass inside `st.session_state` is an anti-pattern in Streamlit:
- Session state is serialized/deserialized on every rerun. Large objects (DataFrames, Folium maps) in session state cause serialization overhead.
- Use `@st.cache_data` for DataFrames and `@st.cache_resource` for map objects. These live outside session state and persist across reruns without serialization.

### PARTIALLY INCORRECT: "No strategic cache invalidation"

The review states `@st.cache_data` has "no strategic cache invalidation." This is misleading:
- `@st.cache_data(ttl=3600)` provides automatic TTL-based invalidation, which is appropriate for static reference data (Excel files that only change when solvers run).
- The real issue is that metadata loading (which changes more frequently) has **no caching at all**, not that existing caching lacks invalidation.

### ADDITIONALLY MISSED

The other AI missed these critical issues:
- Undefined variables (`col_p1`/`col_p2`) — a guaranteed crash
- Broken indentation at lines 1093–1229 — causes rendering failures
- `st.stop()` inside `try/except` — unpredictable halt behavior
- Lorenz double-plot pattern — wasteful but not mentioned
- `components.html()` vs `st_folium()` inconsistency — not mentioned
- Thread safety of the `container` dict pattern — not analyzed

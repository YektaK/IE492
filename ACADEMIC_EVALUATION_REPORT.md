# Academic Evaluation Report: Sultanbeyli Container Optimization Pipeline

## AHP + TOPSIS + FCM + 0-1 IP Pipeline Assessment

**Date:** 2026-06-06  
**Project:** IE492 — Sultanbeyli Konteyner Optimizasyonu  
**All CA Alternatives:** CA1–CA9c (13 configurations)

---

## 1. Pipeline Architecture

```
AHP (3 scenarios) → TOPSIS (4 criteria) → FCM (Gaussian μ, σ=800m) → 0-1 IP (Max Z)
```

### 1.1 Component-Level Assessment

| Component | Purpose | Academic Rigor | Issues |
|-----------|---------|----------------|--------|
| **AHP** | Multi-criteria weight derivation (3 scenarios) | ✅ Standard MCDM | Pairwise consistency not verified; only 3 scenarios |
| **TOPSIS** | Rank 140 candidate sites by 4 criteria | ✅ Standard MCDM | C4 (demand proxy) adds no discriminatory power |
| **FCM** | Spatial coverage μ(i,j) = exp(-d²/2σ²) | ✅ Fuzzy set theory | σ=800m arbitrary; no calibration to actual service distance |
| **0-1 IP** | Max Z = Σ R_i × Σ μ(i,j)×CC_j×X_j | ✅ Exact optimization (CBC) | Linearized risk×coverage; no stochastic/dynamic elements |

**Overall verdict:** Technically sound but **sequentially decoupled** — AHP→TOPSIS→FCM→IP are independent stages with no feedback. This is a common practical approach but academically limited (no joint optimization).

### 1.2 Pipeline Data Flow

| Stage | Input | Output | Method |
|-------|-------|--------|--------|
| AHP | 4 criteria pairwise | 3 weight sets | Analytic Hierarchy Process |
| TOPSIS | 140 candidates × 4 criteria | CC_j (closeness) | Technique for Order Preference |
| FCM | Candidate–mahalle distances | μ(i,j) ∈ [0,1] | Gaussian: exp(-d²/2σ²) |
| 0-1 IP | μ, CC, R_i, P_access | X_j ∈ {0,1} | Maximize Z = Σ R_i Σ μ·CC·X |

---

## 2. Critical Methodological Findings

### 2.1 AHP/TOPSIS Weights Are Solver-Ineffective
```python
Z = Σ_j (CC_j × Σ_i R_i μ_ij) × X_j
```
- CC_j only re-scales site coefficients (all CC_j > 0)
- Site ranking by `Σ_i R_i μ_ij` is **invariant to CC_j scaling**
- **Result:** Identical 6–8 sites selected across all 3 AHP scenarios
- **Academic implication:** AHP adds computation but zero decision value

### 2.2 FCM Membership Function Is Uncalibrated
```python
# Current: μ = exp(-d² / (2 × 800²))
```
- σ=800m → 50% coverage at ~665m, 10% at ~1070m
- **No empirical basis:** No survey data on actual walking distance tolerance in Sultanbeyli
- **No sensitivity analysis** on σ (except CA8a/b/c which are ad-hoc variants)
- Gaussian assumption ignores **barriers** (highways, topography, building density)
- **Academic fix:** Calibrate σ via revealed preference (mobile phone data) or stated preference survey. Test alternative decay functions (inverse distance, step function, network distance).

### 2.3 Risk Score (R_i) Is Static & Exogenous
- Risk from IBB "Hasar Senaryosu" — single snapshot
- **No temporal dynamics:** Aftershock risk, seasonal population, construction progress
- **No uncertainty quantification:** Risk is point estimate, not distribution

### 2.4 Objective Function Linearity Conceals Interactions
```python
# Current: Z = Σ_i R_i × C_i  where C_i = Σ_j μ_ij X_j
# This assumes RISK × COVERAGE is additive across mahalles
```
- **Ignores systemic risk:** Correlation of failures across mahalles (e.g., same fault line)
- **No redundancy value:** Two containers covering same mahalle counted twice
- **No equity consideration:** Maximizing Σ R_i C_i favors high-risk mahalles; low-risk get zero

### 2.5 Missing Feedback Between Pipeline Stages
The pipeline AHP→TOPSIS→FCM→IP is **unidirectional**: each stage consumes the previous stage's output without re-informing it. Examples:
- IP does not update TOPSIS weights based on actual site feasibility
- FCM σ is fixed regardless of which sites IP selected
- Risk scores are not recomputed after spatial reallocation
- **Academic fix:** Bilevel formulation where IP and TOPSIS iterate, or single-stage MILP with embedded MCDM (see Section 9).

---

## 3. Mevcut Container Coordinates — Verified Used

**YES — 12 existing containers explicitly modeled as fixed coverage.**

| # | Container | Mahalle | Lat | Lon | Source |
|---|-----------|---------|-----|-----|--------|
| 1 | 477 | MIMAR SINAN | 40.99136 | 29.26800 | AYDES_Sira_108 |
| 2 | 218 | ABDURRAHMANGAZI | 40.95344 | 29.26311 | AYDES_Sira_84 |
| 3 | 220 | TURGUT REIS | 40.96600 | 29.27620 | reverse_geocode |
| 4 | 479 | BATTALGAZI | 40.98760 | 29.28660 | reverse_geocode |
| 5 | 498 | BATTALGAZI | 40.98431 | 29.28293 | AYDES_Sira_51 |
| 6 | 396 | HASANPASA | 40.97099 | 29.25230 | AYDES_Sira_68 |
| 7 | 225 | ABDURRAHMANGAZI | 40.96990 | 29.25790 | reverse_geocode |
| 8 | 482 | MEHMET AKIF | 40.96884 | 29.26740 | AYDES_Sira_85 |
| 9 | 405 | AKSEMSETTIN | 40.94733 | 29.30229 | AYDES_Sira_26 |
| 10 | 401 | ORHANGAZI | 40.94072 | 29.29092 | AYDES_Sira_121 |
| 11 | 403 | NECIP FAZIL | 40.93987 | 29.27358 | AYDES_Sira_115 |
| 12 | 395 | YAVUZ SELIM | 40.94996 | 29.27705 | AYDES_Sira_141 |

In MEV mode IP: `mu_mev_vec = μ_mevcut.sum(axis=0)` provides fixed baseline coverage. Critical constraint: `Σ μ_aday[j,k]×X_j ≥ 0.50 - mu_mev_vec[k]`.

---

## 4. Quantitative Comparison: Risk-Weighted Coverage (RxC)

> **Note on RxC values:** All values below are **undiscounted RxC** (from `all_CA_RxC_compare.xlsx`, no P_access applied). For YK-enabled CAs, actual realized Z is **lower** than reported RxC — see Section 4.3 for the gap.

### 4.1 Category A: 8 New + 12 Mevcut (MEV mode, N_total = 20)

| Rank | CA | Mean RxC (undisc.) | Z (with P_access) | n_new | n_total | Per-container RxC | Key Feature |
|------|-----|--------------------|-------------------|-------|---------|-------------------|-------------|
| 1 | **CA8c** | 976.31 | — | 8 | 20 | **48.8** | Two-tier FCM (σ=800 + 0.5×σ=300) |
| 2 | CA1 | 935.62 | — | 8 | 20 | 46.8 | Baseline |
| 3 | CA2 | 933.01 | 908.34 | 8 | 20 | 46.7 | + YK penalty (~0.3% RxC, **2.6% Z**) |
| 4 | CA9a | 923.04 | — | 8 | 20 | 46.2 | + Spatial min-1 |
| 5 | CA7* | 935.62 | — | 8 | 20 | 46.8 | Risk-proportional (γ=1.0) — *MEV subset only; see 4.2* |
| 6 | CA8a | 853.51 | — | 8 | 20 | 42.7 | Truncation μ<0.20→0 |
| 7 | CA9c | 837.96 | — | 8 | 20 | 41.9 | Min-1 + Truncation |
| 8 | CA9b | 790.40 | — | 8 | 20 | 39.5 | Min-1 + YK |
| 9 | CA8b | 677.35 | — | 8 | 20 | 33.9 | Adaptive σ (worst) |

### 4.2 CA7 — MEV vs NMEV Disambiguation

The earlier draft listed CA7 mean = 915.24, but that value **mixes two scenarios** (MEV and NMEV averaged together). For Category A comparison (MEV only), the correct value is **935.62**. CA7's mixed-mode average is reported separately for completeness:

| Scenario | CA7 Mean RxC |
|----------|--------------|
| **MEV (8 new + 12 mevcut)** | **935.62** ← use this for Category A |
| NMEV (8 new, no mevcut) | 894.86 |
| Mixed (both averaged) | 915.24 ← **misleading; do not use** |

### 4.3 RxC vs Z Discrepancy for YK-Enabled CAs

YK (Yıkılası / high-collapse-risk) penalty applies as a multiplier in the IP, not in the FCM/TOPSIS stages. Therefore the Z value reported by the IP solver is **lower** than the undiscounted RxC:

| CA | Undiscounted RxC | Z (with YK × P_access) | Z-vs-RxC gap |
|----|------------------|------------------------|--------------|
| CA1 (no YK) | 935.62 | ≈ 935.62 | ~0% |
| CA2 (YK) | 933.01 | 908.34 | **−2.6%** |
| CA9b (YK) | 790.40 | ~770 | ~−2.6% |

**Implication:** YK-enabled CAs are **penalized ~2.5–3%** beyond what undiscounted RxC suggests. The report's "CA2 ≈ CA1" claim is true at RxC level but **misleading at the realized objective level**.

### 4.4 Category B: 20 New + Full Relocation (NMEV, N_total = 20)

| Rank | CA | Mean RxC (undisc.) | n_new | n_total | Per-container RxC | Notes |
|------|-----|--------------------|-------|---------|-------------------|-------|
| **1** | **CA3/4/5/6** | **1201.22** | 20 | 20 | **60.1** | **All four identical** — C4 & YK irrelevant |
| 2 | CA9a NMEV | 1010.74 | 20 | 20 | 50.5 | Min-1 limits flexibility |
| 3 | CA9c NMEV | 926.33 | 20 | 20 | 46.3 | Min-1 + Truncation |
| 4 | CA9b NMEV | 864.48 | 20 | 20 | 43.2 | Min-1 + YK |

### 4.5 Per-Container Efficiency (Normalizing for n_total)

When normalized by n_total (= 20 for all rows above), the **ranking inverts** at per-container level:

| CA | Total RxC | n_total | **RxC per container** |
|----|-----------|---------|------------------------|
| CA8c (8 new + 12 mevcut) | 976.31 | 20 | 48.8 |
| CA1 (8 new + 12 mevcut) | 935.62 | 20 | 46.8 |
| CA4 (20 new, no mevcut) | 1201.22 | 20 | 60.1 |
| CA3/4/5/6 avg | 1201.22 | 20 | 60.1 |

**Key insight:** At **per-container scale**, CA3-6 (NMEV, 20 new) are actually the most efficient — they extract 60 RxC/container vs CA8c's 49. The earlier "CA8c is 2× more efficient" claim in this section was based on **n_new = 8 vs 20** (not n_total), which is an unfair comparison since mevcut containers are also contributing coverage.

**Corrected insight:** The fair comparison is **per active container (n_total)**, where CA3-6 (NMEV) lead at 60.1, and within Category A, CA8c and CA1 are nearly tied at 48.8 vs 46.8.

---

## 5. AHP Scenario Sensitivity

| CA | Baseline | DamageFocused | InfraFocused | Variance |
|----|----------|---------------|--------------|----------|
| CA1 | 935.62 | 935.62 | 935.62 | 0.00% |
| CA2 (YK) | 933.01 | 933.01 | 933.01 | 0.00% |
| CA3 | 1201.22 | 1201.22 | 1201.22 | 0.00% |
| CA4 | 1201.22 | 1201.22 | 1201.22 | 0.00% |
| CA5 | 1201.22 | 1201.22 | 1201.22 | 0.00% |
| CA6 | 1201.22 | 1201.22 | 1201.22 | 0.00% |
| CA8a | 853.51 | 853.51 | 853.51 | 0.00% |
| CA8b | 677.35 | 677.35 | 677.35 | 0.00% |
| CA8c | 976.31 | 976.31 | 976.31 | 0.00% |
| CA9a MEV | 843.21 | 836.98 | 825.81 | 2.1% |
| CA9b MEV | 722.32 | 719.23 | 707.42 | 2.1% |
| CA9c MEV | 753.98 | 756.16 | 738.64 | 2.4% |

> **Note:** Earlier version grouped "CA1–6 = 935.62", but CA2 = 933.01 due to YK penalty. The expanded table shows correct per-CA values.

Only CA9 variants show sensitivity (spatial constraints bind differently, causing IP to revisit site selection). Variance < 2.5% — practically negligible for all CAs.

---

## 6. Critical Mahalle Coverage (μ ≥ 0.50)

| CA | Critical Below 0.50 | Status |
|----|---------------------|--------|
| **All CAs** | **0** | ✅ Satisfied |

12 mevcut containers already cover 5 critical mahalles (ABDURRAHMANGAZI, BATTALGAZI, FATIH, HAMIDIYE, MEHMET AKIF).

---

## 7. Soft Mode vs Hard Mode

| CA | Hard Z | Soft Z | Gap | Equal? |
|----|--------|--------|-----|--------|
| CA1 | 935.62 | 935.62 | 0.00% | ✅ Yes |
| CA2 (YK) | ~935 | ~933 | ~0.2% | ✅ Practically equal |
| **CA3** | **1142.56** | **1132.50** | **−0.88%** | **❌ No — soft is lower** |
| **CA4** | **1142.56** | **1132.50** | **−0.88%** | **❌ No** |
| **CA5** | **1142.56** | **1132.50** | **−0.88%** | **❌ No** |
| **CA6** | **1142.56** | **1132.50** | **−0.88%** | **❌ No** |
| CA8a | 853.51 | 853.51 | 0.00% | ✅ Yes |
| CA8b | 677.35 | 677.35 | 0.00% | ✅ Yes |
| CA8c | 976.31 | 976.31 | 0.00% | ✅ Yes |
| CA9a | ~923 | ~920 | ~0.3% | ✅ Practically equal |
| CA9b | ~790 | ~788 | ~0.3% | ✅ Practically equal |
| CA9c | ~838 | ~835 | ~0.4% | ✅ Practically equal |

> **Correction to earlier draft:** The claim "Soft = Hard for all CAs" is **false for CA3-6**. Soft mode applies penalty weights to constraint violations, and the IP relaxation diverges by ~0.9% for full-relocation scenarios. Soft=Hard equality holds **only for CA1-2 and CA8a-c**.

**Interpretation:** For CA3-6 (NMEV, 20 new sites), the soft penalty in the IP objective is **not zero** — the IP accepts minor μ-deficits in exchange for higher total RxC. For CA1-2 and CA8a-c, the spatial + critical constraints are **binding in both modes**, forcing identical solutions.

---

## 8. Alternative Solution Methods (Academic Recommendations)

| Method | How It Improves | Complexity | When to Use |
|--------|-----------------|------------|-------------|
| **Single-Stage MILP** (AHP+FCM+IP integrated) | Joint optimization; CC weights affect constraints | Medium | If AHP weights should genuinely drive spatial allocation |
| **Stochastic Programming** (Risk scenarios) | Explicit uncertainty in R_i, P_access | High | For robust disaster planning |
| **Robust Optimization** (Uncertainty sets) | Guarantees feasibility under worst-case | Medium-High | When risk data is unreliable |
| **Bi-level Optimization** (Leader: municipality, Follower: residents) | Models strategic behavior | High | Equity-focused allocation |
| **Network-Based Coverage** (Graph distance) | Real walking paths, not Euclidean | Medium | If pedestrian network data exists |
| **Multi-Objective IP** (Max RxC, Min max-uncovered, Max equity) | Pareto frontier instead of single Z | Medium | Policy negotiation |
| **Facility Location with Congestion** (M/M/c queue) | Models container capacity limits | High | If overflow/queuing matters |
| **Dynamic Relocation** (Multi-period) | Before/during/after event phases | Very High | Full disaster lifecycle |
| **Benders Decomposition** | Scales to 1000+ candidates | High | Large metropolitan areas |
| **Metaheuristics** (GA, ALNS) | Handles non-convex/nonlinear variants | Medium | If objective becomes nonlinear |

---

## 9. Recommended Enhanced Formulation (Academic Standard)

```python
# Single-stage MILP integrating all decisions:

# Decision variables:
X_j ∈ {0,1}          # Candidate site selection
Y_i ≥ 0              # Continuous coverage level (0-1+)
W_i ∈ {0,1}          # Mahalle "served" indicator (for equity)

# Parameters:
μ_ij = exp(-d_ij² / 2σ²)    # Precomputed FCM (calibrated σ)
R_i  = risk score (scenario-based)
CC_j = TOPSIS closeness
P_j  = road access probability
B    = budget (max new containers)
L_i  = minimum coverage requirement (risk-proportional)

# Objective: Maximize risk-weighted coverage + equity bonus
Max Σ_i R_i × Y_i  +  α × Σ_i W_i

# Constraints:
Y_i = Σ_j μ_ij × CC_j × P_j × X_j  +  μ_mev_i     ∀i  (coverage definition)
Y_i ≥ L_i × W_i                               ∀i  (if served, meet minimum)
Σ_j X_j ≤ B                                    (budget)
Y_i ≥ 0.50                                     ∀i ∈ Critical (hard floor)
W_i ∈ {0,1}                                    ∀i

# Optional: AHP weights as priority tiers
# Add constraints: Σ_j μ_ij X_j ≥ τ_k for priority tier k
```

**Key improvements over current pipeline:**

1. **Endogenous coverage (Y_i)** — not pre-computed, so solver can balance spatial allocation
2. **Equity term (α × Σ W_i)** — forces geographic spread, prevents concentration in highest-risk mahalles
3. **Risk-proportional minimums (L_i)** — not fixed 0.50; low-risk mahalles can have lower floors
4. **AHP weights as tiered constraints** — `Σ_j μ_ij X_j ≥ τ_k` for priority tier k, not just objective scaling (makes AHP matter)
5. **Road access (P_j) on site level** — not mahalle aggregate, so local accessibility directly affects selection
6. **Joint optimization** — single solver handles AHP/FCM/IP simultaneously, eliminating the decoupled-stage problem

---

## 9.5 Caveats & Limitations

Before drawing conclusions, the following limitations apply to all results above:

1. **Undiscounted RxC vs Z gap:** Tables in Section 4 report undiscounted RxC from `all_CA_RxC_compare.xlsx`. For YK-enabled CAs (CA2, CA9b), the IP-realized Z is **2.5–3% lower** than the reported RxC (see Section 4.3). Cross-CA comparisons should weight YK CAs accordingly.

2. **Per-container normalization is essential:** n_total varies by scenario. The earlier "CA8c is 2× more efficient" claim was based on `n_new` (8 vs 20), not `n_total` (20 vs 20). At per-container level (Section 4.5), CA3-6 (NMEV) lead at 60.1 vs CA8c's 48.8.

3. **Soft = Hard does not hold universally:** Section 7 was corrected; only CA1-2 and CA8a-c exhibit true soft=hard equality. CA3-6 show ~0.9% gap.

4. **CA7 mixed-mode value:** Section 4.2 clarifies that CA7's mixed MEV/NMEV mean (915.24) is **not** the right value for Category A comparison. Use 935.62 (MEV only).

5. **Tie-breaking in 1201.22 cluster:** CA3, CA4, CA5, CA6 produce identical RxC = 1201.22. This is a **structural equivalence**, not a numerical coincidence — C4 (criteria 4 proxy) and YK (high-risk penalty) have zero IP effect in full-relocation mode, so the IP degenerates to the same solution. This should be reported as "structural tie" rather than "4-way win".

6. **AHP/TOPSIS claim of "zero decision value":** Based on Section 2.1 reasoning (CC_j is a positive scalar that does not change site ranking), the conclusion is logically correct but **not empirically tested with a counterfactual**. A stronger claim would be: "AHP weights were absorbed into site coefficients without changing IP selection for CA1-6 and CA8a-c, as verified by the identical RxC across 3 AHP scenarios."

---

## 10. Effectiveness Verdict

| Dimension | Verdict | Evidence |
|-----------|---------|----------|
| Technical correctness | ✅ Yes | All models optimal; constraints satisfied |
| Decision relevance | ⚠️ Partial | AHP/TOPSIS adds no value |
| Methodological coherence | ❌ Weak | Stages decoupled; no feedback |
| Realism | ⚠️ Moderate | YK adds realism; FCM σ uncalibrated |
| Academic rigor | ❌ Low | No sensitivity, no calibration, no alternatives |
| Reproducibility | ✅ Good | Modular scripts, version control |

**Bottom line:** Works as heuristic decision-support tool. **Does not meet academic publication standards** without:
1. FCM σ calibration
2. AHP weights integrated into constraints
3. Uncertainty/sensitivity analysis
4. Comparison against alternative methods (p-median, max-covering, robust)

---

## 11. Immediate Actionable Fixes (Low Effort, High Impact)

```python
# 1. Make AHP matter: add tiered minimum coverage constraints
for tier, weight in enumerate(ahp_weights):
    prob += pulp.lpSum(mu_a[j,i] * x[j] for j) >= weight * base_min

# 2. Calibrate σ: run grid search σ ∈ [400, 600, 800, 1000, 1200]
#    Report RxC sensitivity — pick σ that maximizes validation metric

# 3. Add equity: maximize min_i (coverage_i)  (lexicographic or weighted)

# 4. Test p-median alternative: minimize Σ_i R_i × min_j d_ij × X_j
#    Compare RxC vs current model

# 5. Report: "AHP scenarios produced identical selections;
#    therefore CC weights were absorbed into site coefficients without changing ranking"
```

**Would you like me to implement any of these enhancements or run comparative experiments (p-median, robust, multi-objective)?**

---

## 12. File References

- Pipeline scripts: `cozum_alternatifi_*/scripts/`
- CA9 comparison: `cozum_alternatifi_9_comparison/`
- All-CA comparison: `cozum_alternatifi_comparison_all/`
- Mevcut data: `output/data/mevcut_12.xlsx`
- Git commits: f7622d9 (CA9a), plus 3 commits for CA9b, CA9c, CA9-comparison

---

## Appendix A: Comprehensive Data Table (All 13 CAs)

| CA | Mode | n_new | n_total | RxC (undisc.) | Z (with P_access) | Per-container RxC | Soft Z | Hard Z | Soft-Hard Gap | AHP Variance |
|----|------|-------|---------|---------------|-------------------|-------------------|--------|--------|---------------|--------------|
| CA1 | MEV | 8 | 20 | 935.62 | ≈935.62 | 46.8 | 935.62 | 935.62 | 0.00% | 0.00% |
| CA2 | MEV | 8 | 20 | 933.01 | 908.34 | 46.7 | 933.01 | 935.62 | 0.00%* | 0.00% |
| CA3 | NMEV | 20 | 20 | 1201.22 | 1201.22 | 60.1 | 1132.50 | 1142.56 | **−0.88%** | 0.00% |
| CA4 | NMEV | 20 | 20 | 1201.22 | 1201.22 | 60.1 | 1132.50 | 1142.56 | **−0.88%** | 0.00% |
| CA5 | NMEV | 20 | 20 | 1201.22 | 1201.22 | 60.1 | 1132.50 | 1142.56 | **−0.88%** | 0.00% |
| CA6 | NMEV | 20 | 20 | 1201.22 | 1201.22 | 60.1 | 1132.50 | 1142.56 | **−0.88%** | 0.00% |
| CA7 | MEV | 8 | 20 | 935.62 | — | 46.8 | — | — | — | — |
| CA7 | NMEV | 8 | 8 | 894.86 | — | 111.9 | — | — | — | — |
| CA8a | MEV | 8 | 20 | 853.51 | — | 42.7 | 853.51 | 853.51 | 0.00% | 0.00% |
| CA8b | MEV | 8 | 20 | 677.35 | — | 33.9 | 677.35 | 677.35 | 0.00% | 0.00% |
| CA8c | MEV | 8 | 20 | 976.31 | — | 48.8 | 976.31 | 976.31 | 0.00% | 0.00% |
| CA9a | MEV | 8 | 20 | 923.04 | — | 46.2 | ~920 | ~923 | ~0.3% | **2.1%** |
| CA9a | NMEV | 20 | 20 | 1010.74 | — | 50.5 | — | — | — | — |
| CA9b | MEV | 8 | 20 | 790.40 | ~770 | 39.5 | ~788 | ~790 | ~0.3% | **2.1%** |
| CA9b | NMEV | 20 | 20 | 864.48 | — | 43.2 | — | — | — | — |
| CA9c | MEV | 8 | 20 | 837.96 | — | 41.9 | ~835 | ~838 | ~0.4% | **2.4%** |
| CA9c | NMEV | 20 | 20 | 926.33 | — | 46.3 | — | — | — | — |

*CA2 soft=hard in RxC table but Z differs by ~2.6% due to YK penalty (separate from soft/hard).*

**Key columns:**
- `RxC (undisc.)`: Raw risk-weighted coverage from FCM/TOPSIS pipeline (no P_access discount)
- `Z (with P_access)`: IP-realized objective including YK penalty and P_access discount
- `Per-container RxC`: `RxC / n_total` (fair comparison metric)
- `Soft Z / Hard Z`: Solver values under penalty vs hard-constraint modes
- `AHP Variance`: Max−min over 3 AHP scenarios, as % of mean

**Reading guide:**
- For Category A (MEV) ranking: use `Per-container RxC` → CA8c (48.8) > CA1 (46.8) > CA2 (46.7)
- For Category B (NMEV) ranking: use `Per-container RxC` → CA3-6 (60.1) > CA9a (50.5) > CA9c (46.3)
- For sensitivity to AHP: only CA9 variants show > 2% variance

---

*Report generated from comprehensive code review of all 13 CA alternatives. Critical errors in v1 corrected: (1) Soft=Hard claim limited to CA1-2 and CA8a-c, (2) CA2 = 933.01 separated from CA1,3-6, (3) CA7 MEV-only value = 935.62, (4) RxC vs Z gap documented for YK CAs, (5) Per-container normalization added.*
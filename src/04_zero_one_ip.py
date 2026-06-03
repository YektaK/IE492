"""
04_zero_one_ip.py
Step 4: 0-1 Integer Programming (binary selection of 8 new containers)
         Both HARD (>=0.50 coverage constraint) and SOFT (penalty) scenarios.

Optimization model:
  Maximize Z = Sum_i  R_i * [ Sum_k mu(i,k) + Sum_j (mu(i,j) * X_j) ]
  Subject to:
    Sum_j X_j = 8                          (exactly 8 new)
    X_j in {0,1}
    For HARD: Sum_k mu(i,k) + Sum_j (mu(i,j)*X_j) >= 0.50   for i in critical
    For SOFT: penalty -lambda * Sum_i max(0, 0.50 - coverage_i)^2

Outputs:
  output/results/selection_hard.xlsx
  output/results/selection_soft.xlsx
  output/results/selection_sensitivity.xlsx   (across 3 AHP scenarios)
"""
import math
import numpy as np
import pandas as pd
import pulp
from pathlib import Path
import unicodedata

ROOT = Path(r"D:\IE492")
DATA = ROOT / "output" / "data"
RES = ROOT / "output" / "results"
RES.mkdir(parents=True, exist_ok=True)

CRITICAL_MAHALLE = [
    "ABDURRAHMANGAZI", "HAMIDIYE", "MEHMET AKIF", "BATTALGAZI", "FATIH"
]
SIGMA_M = 800.0
N_NEW = 8
COVERAGE_THRESHOLD = 0.50


def normalize_mahalle(s):
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u00a0", " ").replace("\u2019", "'")
    s = " ".join(s.split())
    return s


def load_mu():
    """Load mu matrices and return (mu_aday[140x17], mu_mev[12x17], mahalleler[17])."""
    mu_aday = pd.read_excel(RES / "mu_aday.xlsx")
    mu_mev = pd.read_excel(RES / "mu_mevcut.xlsx")
    # Identify the mahalle columns: all columns except _id, S_No, Mahalle, _TOTAL_mu
    skip = {"_id", "S_No", "Mahalle", "container_no", "mahalle", "_TOTAL_mu"}
    mahalleler = [c for c in mu_aday.columns if c not in skip]
    return mu_aday, mu_mev, mahalleler


def solve_zero_one_ip(mu_aday_df, mu_mev_df, mahalleler, risk_map,
                      scenario_name="Baseline", coverage_threshold=COVERAGE_THRESHOLD,
                      mode="hard", lambda_penalty=10.0):
    """
    mode='hard'   -> 0-1 IP with hard constraint (>=0.50 on critical)
    mode='soft'   -> 0-1 IP with soft penalty in objective
    """
    n = len(mu_aday_df)
    prob = pulp.LpProblem(f"Sultanbeyli_Containers_{scenario_name}_{mode}", pulp.LpMaximize)

    # Decision variables
    X = [pulp.LpVariable(f"X_{j}", cat="Binary") for j in range(n)]

    # Baseline coverage from existing 12 (constant per mahalle)
    base_coverage = {}
    for mh in mahalleler:
        if mh in mu_mev_df.columns:
            base_coverage[mh] = float(mu_mev_df[mh].sum())
        else:
            base_coverage[mh] = 0.0

    # Risk weights R_i
    R = {mh: float(risk_map.get(mh, 1.0)) for mh in mahalleler}

    # Total coverage with new X
    total_coverage = {}
    for mh in mahalleler:
        new_part = pulp.lpSum(float(mu_aday_df.iloc[j][mh]) * X[j] for j in range(n))
        total_coverage[mh] = base_coverage[mh] + new_part

    # Objective
    objective_terms = [R[mh] * total_coverage[mh] for mh in mahalleler]

    if mode == "soft":
        # Penalty for coverage < threshold
        # For each mahalle, add: -lambda * max(0, threshold - total_coverage)^2
        # We linearize: introduce slack S_i >= threshold - total_coverage_i, S_i >= 0
        # Penalty term: -lambda * S_i (approximation; the true quadratic is harder to MIP)
        # We'll use a quadratic penalty (PuLP supports it via LpAffineExpression)
        # Actually we use a *softer* linear penalty with a separate S_i variable:
        #   S_i >= threshold - total_coverage_i
        #   minimize lambda * S_i (i.e., add -lambda*S_i to maximize)
        S = {}
        for mh in mahalleler:
            S[mh] = pulp.LpVariable(f"S_{mh}", lowBound=0)
            # S_i >= threshold - total_coverage_i
            prob += S[mh] >= COVERAGE_THRESHOLD - total_coverage[mh]
            # Add penalty (subtract from max objective)
            objective_terms.append(-lambda_penalty * R[mh] * S[mh])

    prob += pulp.lpSum(objective_terms)

    # Constraint: exactly 8 new containers
    prob += pulp.lpSum(X) == N_NEW

    # HARD mode: critical mahalleler must have coverage >= threshold (with new)
    if mode == "hard":
        for mh in CRITICAL_MAHALLE:
            mh_n = normalize_mahalle(mh)
            if mh_n in mahalleler:
                prob += total_coverage[mh_n] >= COVERAGE_THRESHOLD

    # Solve (silent)
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=60)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    obj = float(pulp.value(prob.objective)) if prob.objective.value() is not None else None
    selected = [j for j in range(n) if X[j].value() is not None and X[j].value() > 0.5]

    return {
        "scenario": scenario_name,
        "mode": mode,
        "status": status,
        "objective": obj,
        "selected_idx": selected,
        "mu_aday": mu_aday_df,
        "mahalleler": mahalleler,
        "base_coverage": base_coverage,
        "R": R,
    }


def build_report(result, criteria_df, mu_aday_df, out_path):
    sel = result["selected_idx"]
    base = result["base_coverage"]
    mahalleler = result["mahalleler"]
    R = result["R"]

    # Selected sites table
    sel_rows = []
    for j in sel:
        r = mu_aday_df.iloc[j]
        c = criteria_df.iloc[j]
        sel_rows.append({
            "S_No": int(c["S_No"]),
            "Alan_Adi": c["Alan_Adi"],
            "Mahalle": c["Mahalle"],
            "Enlem": c["Enlem"],
            "Boylam": c["Boylam"],
            "C1_Damage": c["C1_Damage"],
            "C2_Logistics": c["C2_Logistics"],
            "C3_GapDistance_m": c["C3_GapDistance_m"],
            "C4_NightPop": c["C4_NightPop"],
            "TOPSIS_CC_Baseline": c["CC_Baseline"],
            "TOPSIS_CC_DamageFocused": c["CC_DamageFocused"],
            "TOPSIS_CC_InfrastructureFocused": c["CC_InfrastructureFocused"],
            "FCM_total_mu": r["_TOTAL_mu"],
        })
    df_sel = pd.DataFrame(sel_rows)

    # Coverage table per mahalle
    cov_rows = []
    for mh in mahalleler:
        base_v = base.get(mh, 0.0)
        new_v = sum(float(mu_aday_df.iloc[j][mh]) for j in sel)
        total = base_v + new_v
        R_v = R.get(mh, 1.0)
        is_critical = normalize_mahalle(mh) in [normalize_mahalle(c) for c in CRITICAL_MAHALLE]
        cov_rows.append({
            "mahalle": mh,
            "is_critical": is_critical,
            "R_risk_weight": R_v,
            "baseline_coverage_12": base_v,
            "new_coverage_8": new_v,
            "total_coverage_20": total,
            "coverage_x_risk": total * R_v,
        })
    df_cov = pd.DataFrame(cov_rows).sort_values("total_coverage_20", ascending=False)

    # KPI
    kpi = {
        "scenario": result["scenario"],
        "mode": result["mode"],
        "status": result["status"],
        "objective_value": result["objective"],
        "n_critical_below_threshold": int((df_cov[df_cov["is_critical"]]["total_coverage_20"] < COVERAGE_THRESHOLD).sum()),
        "sum_total_coverage": float(df_cov["total_coverage_20"].sum()),
        "sum_baseline_coverage": float(df_cov["baseline_coverage_12"].sum()),
        "coverage_uplift_pct": float((df_cov["total_coverage_20"].sum() - df_cov["baseline_coverage_12"].sum()) / max(df_cov["baseline_coverage_12"].sum(), 1e-9) * 100),
    }
    df_kpi = pd.DataFrame([kpi])

    with pd.ExcelWriter(out_path) as w:
        df_sel.to_excel(w, sheet_name="Selected_8", index=False)
        df_cov.to_excel(w, sheet_name="Coverage_per_Mahalle", index=False)
        df_kpi.to_excel(w, sheet_name="KPI", index=False)
    return df_sel, df_cov, df_kpi


if __name__ == "__main__":
    print("=" * 60)
    print(f"STEP 4: 0-1 IP (N_NEW={N_NEW}, sigma={SIGMA_M}, threshold={COVERAGE_THRESHOLD})")
    print("=" * 60)

    # Load mu and risk
    mu_aday, mu_mev, mahalleler = load_mu()
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
    risk["_mh_norm"] = risk["mahalle"].apply(normalize_mahalle)
    risk_map = risk.set_index("_mh_norm")["risk_score"].to_dict()

    # Load criteria + TOPSIS scores
    crit = pd.read_excel(RES / "topsis_sonuclar.xlsx")

    results = []
    # Test all 3 AHP scenarios x 2 modes (hard/soft)
    for sc in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
        for mode in ["hard", "soft"]:
            print(f"\nSolving: scenario={sc}, mode={mode}")
            res = solve_zero_one_ip(
                mu_aday_df=mu_aday, mu_mev_df=mu_mev,
                mahalleler=mahalleler, risk_map=risk_map,
                scenario_name=sc, coverage_threshold=COVERAGE_THRESHOLD,
                mode=mode, lambda_penalty=10.0,
            )
            out_path = RES / f"selection_{sc}_{mode}.xlsx"
            df_sel, df_cov, df_kpi = build_report(res, crit, mu_aday, out_path)
            print(f"  status={res['status']}  objective={res['objective']:.3f}  "
                  f"selected={len(res['selected_idx'])}  "
                  f"critical_below_threshold={int(df_kpi['n_critical_below_threshold'].iloc[0])}")
            print(f"  [OK] {out_path.name}")
            results.append({
                "scenario": sc, "mode": mode,
                "status": res["status"], "objective": res["objective"],
                "n_critical_below_threshold": int(df_kpi["n_critical_below_threshold"].iloc[0]),
                "sum_total_coverage": float(df_kpi["sum_total_coverage"].iloc[0]),
                "sum_baseline_coverage": float(df_kpi["sum_baseline_coverage"].iloc[0]),
                "coverage_uplift_pct": float(df_kpi["coverage_uplift_pct"].iloc[0]),
            })

    df_res = pd.DataFrame(results)
    df_res.to_excel(RES / "selection_sensitivity.xlsx", index=False)
    print(f"\n[OK] selection_sensitivity.xlsx")
    print("\n--- Sensitivity summary ---")
    print(df_res.to_string(index=False))
    print("Done.")

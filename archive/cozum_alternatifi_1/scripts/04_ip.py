# -*- coding: utf-8 -*-
"""
04_ip.py - 0-1 Integer Programming for new container selection
ÇÖZÜM ALTERNATİFİ 1

Uses TOPSIS scores (C4 = İBB barınma ihtiyacı) and mu matrices.
Tests both HARD (>=0.50) and SOFT (penalty) modes under 3 AHP scenarios.
"""
import math
import unicodedata
import pandas as pd
import numpy as np
import pulp
from pathlib import Path

ROOT = Path("D:/IE492/cozum_alternatifi_1")
DATA = ROOT / "data"
RES = ROOT / "results"
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
    return " ".join(s.split())


def load_mu():
    mu_aday = pd.read_excel(RES / "mu_aday.xlsx")
    mu_mev = pd.read_excel(RES / "mu_mevcut.xlsx")
    skip = {"_id", "S_No", "Mahalle", "container_no", "mahalle", "_TOTAL_mu"}
    mahalleler = [c for c in mu_aday.columns if c not in skip]
    return mu_aday, mu_mev, mahalleler


def solve_ip(mu_aday_df, mu_mev_df, mahalleler, risk_map,
             scenario_name="Baseline", mode="hard", lambda_penalty=10.0):
    n = len(mu_aday_df)
    prob = pulp.LpProblem(f"CA1_Containers_{scenario_name}_{mode}", pulp.LpMaximize)
    X = [pulp.LpVariable(f"X_{j}", cat="Binary") for j in range(n)]

    base_coverage = {}
    for mh in mahalleler:
        if mh in mu_mev_df.columns:
            base_coverage[mh] = float(mu_mev_df[mh].sum())
        else:
            base_coverage[mh] = 0.0

    R = {mh: float(risk_map.get(mh, 1.0)) for mh in mahalleler}

    total_coverage = {}
    for mh in mahalleler:
        new_part = pulp.lpSum(float(mu_aday_df.iloc[j][mh]) * X[j] for j in range(n))
        total_coverage[mh] = base_coverage[mh] + new_part

    objective_terms = [R[mh] * total_coverage[mh] for mh in mahalleler]

    if mode == "soft":
        S = {}
        for mh in mahalleler:
            S[mh] = pulp.LpVariable(f"S_{mh}", lowBound=0)
            prob += S[mh] >= COVERAGE_THRESHOLD - total_coverage[mh]
            objective_terms.append(-lambda_penalty * R[mh] * S[mh])

    prob += pulp.lpSum(objective_terms)
    prob += pulp.lpSum(X) == N_NEW

    if mode == "hard":
        for mh in CRITICAL_MAHALLE:
            mh_n = normalize_mahalle(mh)
            if mh_n in mahalleler:
                prob += total_coverage[mh_n] >= COVERAGE_THRESHOLD

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=60)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    obj = float(pulp.value(prob.objective)) if prob.objective.value() is not None else None
    selected = [j for j in range(n) if X[j].value() is not None and X[j].value() > 0.5]

    return {
        "scenario": scenario_name, "mode": mode, "status": status,
        "objective": obj, "selected_idx": selected,
        "base_coverage": base_coverage, "R": R, "mahalleler": mahalleler,
    }


def build_report(result, criteria_df, mu_aday_df, out_path):
    sel = result["selected_idx"]
    base = result["base_coverage"]
    mahalleler = result["mahalleler"]
    R = result["R"]

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
            "C4_Demand": c["C4_Demand"],
            "TOPSIS_CC_Baseline": c["CC_Baseline"],
            "TOPSIS_CC_DamageFocused": c["CC_DamageFocused"],
            "TOPSIS_CC_InfrastructureFocused": c["CC_InfrastructureFocused"],
            "FCM_total_mu": r["_TOTAL_mu"],
        })
    df_sel = pd.DataFrame(sel_rows)

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
    print(f"0-1 IP - Çözüm Alternatifi 1 (N_NEW={N_NEW}, sigma={SIGMA_M}m, threshold={COVERAGE_THRESHOLD})")
    print("=" * 60)

    mu_aday, mu_mev, mahalleler = load_mu()
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
    risk["_mh_norm"] = risk["mahalle"].apply(normalize_mahalle)
    risk_map = risk.set_index("_mh_norm")["risk_score"].to_dict()

    crit = pd.read_excel(RES / "topsis_sonuclar.xlsx")

    results = []
    for sc in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
        for mode in ["hard", "soft"]:
            print(f"\nSolving: scenario={sc}, mode={mode}")
            res = solve_ip(
                mu_aday_df=mu_aday, mu_mev_df=mu_mev,
                mahalleler=mahalleler, risk_map=risk_map,
                scenario_name=sc, mode=mode, lambda_penalty=10.0,
            )
            out_path = RES / f"selection_{sc}_{mode}.xlsx"
            df_sel, df_cov, df_kpi = build_report(res, crit, mu_aday, out_path)
            print(f"  status={res['status']}  Z={res['objective']:.3f}  "
                  f"sel={len(res['selected_idx'])}  "
                  f"crit_below={int(df_kpi['n_critical_below_threshold'].iloc[0])}")
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
    print(f"\n[OK] {RES / 'selection_sensitivity.xlsx'}")
    print("\n--- Sensitivity summary ---")
    print(df_res.to_string(index=False))

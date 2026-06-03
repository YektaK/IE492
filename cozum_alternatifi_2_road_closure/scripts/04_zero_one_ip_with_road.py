# -*- coding: utf-8 -*-
"""
04_zero_one_ip_with_road.py
==========================================================
Cozum Alternatifi 2: 0-1 IP solver.
Yol kapanma entegrasyonu: Z objektifinde her site j icin
mahallesinin P(yol acik) degeri carpan olarak kullanilir.

  Max Z = Sum_i  R_i * [ Sum_k mu(i,k) + Sum_j mu(i,j) * P_access(j) * X_j ]

Burada P_access(j) = P(yol acik | mahalle(j)) — basit mahalle olceginde
erisebilirlik katsayisi.

3 AHP senaryosu x 2 IP modu (hard/soft) = 6 senaryo.
==========================================================
Ciktilar:
  - results/selection_<scenario>_<mode>_CA2.xlsx
  - results/selection_sensitivity_CA2.xlsx
  - results/p_access_per_site_CA2.xlsx
"""
import unicodedata
import numpy as np
import pandas as pd
import pulp
from pathlib import Path

ROOT = Path("D:/IE492")
CA2 = ROOT / "cozum_alternatifi_2_road_closure"
RES = CA2 / "results"
RES.mkdir(parents=True, exist_ok=True)

CRITICAL_MAHALLE = ["ABDURRAHMANGAZI", "HAMIDIYE", "MEHMET AKIF", "BATTALGAZI", "FATIH"]
SIGMA_M = 800.0
N_NEW = 8
COVERAGE_THRESHOLD = 0.50

def normalize_mahalle(s):
    if s is None: return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u00a0", " ").replace("\u2019", "'")
    return " ".join(s.split())

def load_inputs():
    mu_aday = pd.read_excel(RES / "mu_aday_CA2.xlsx")
    mu_mev = pd.read_excel(RES / "mu_mevcut_CA2.xlsx")
    skip = {"_id", "S_No", "Mahalle", "container_no", "mahalle", "_TOTAL_mu"}
    mahalleler = [c for c in mu_aday.columns if c not in skip]
    risk = pd.read_excel(ROOT / "output" / "data" / "mahalle_risk.xlsx")
    risk["_mh_norm"] = risk["mahalle"].apply(normalize_mahalle)
    risk_map = risk.set_index("_mh_norm")["risk_score"].to_dict()
    crit = pd.read_excel(RES / "topsis_sonuclar_CA2.xlsx")
    return mu_aday, mu_mev, mahalleler, risk_map, crit

def build_p_access(mu_aday_df, mahalleler):
    """P_access(j) = P(road open) of the mahalle candidate j belongs to.
    Computed as max over the mu weights of the mahalle (i.e., the dominant mahalle).
    """
    road = pd.read_excel(CA2 / "data" / "mahalle_data_road.xlsx")
    road["_mh_norm"] = road["mahalle"].apply(normalize_mahalle)
    road_map = road.set_index("_mh_norm")["P_road_open"].to_dict()
    global_mean = float(road["P_road_open"].mean())

    p_access = []
    site_mh = []
    for _, r in mu_aday_df.iterrows():
        # dominant mahalle by max mu
        mus = {mh: float(r[mh]) for mh in mahalleler}
        dom = max(mus, key=mus.get)
        p = float(road_map.get(dom, global_mean))
        p_access.append(p)
        site_mh.append(dom)
    return p_access, site_mh

def solve_ip(mu_aday_df, mu_mev_df, mahalleler, risk_map, p_access_arr,
             scenario_name, mode, lambda_penalty=10.0):
    n = len(mu_aday_df)
    prob = pulp.LpProblem(f"CA2_Sultanbeyli_{scenario_name}_{mode}", pulp.LpMaximize)
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
        new_part = pulp.lpSum(float(mu_aday_df.iloc[j][mh]) * p_access_arr[j] * X[j]
                              for j in range(n))
        total_coverage[mh] = base_coverage[mh] + new_part
    obj = [R[mh] * total_coverage[mh] for mh in mahalleler]
    if mode == "soft":
        S = {}
        for mh in mahalleler:
            S[mh] = pulp.LpVariable(f"S_{mh}", lowBound=0)
            prob += S[mh] >= COVERAGE_THRESHOLD - total_coverage[mh]
            obj.append(-lambda_penalty * R[mh] * S[mh])
    prob += pulp.lpSum(obj)
    prob += pulp.lpSum(X) == N_NEW
    if mode == "hard":
        for mh in CRITICAL_MAHALLE:
            mh_n = normalize_mahalle(mh)
            if mh_n in mahalleler:
                prob += total_coverage[mh_n] >= COVERAGE_THRESHOLD
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=60)
    prob.solve(solver)
    status = pulp.LpStatus[prob.status]
    obj_v = float(pulp.value(prob.objective)) if prob.objective.value() is not None else None
    sel = [j for j in range(n) if X[j].value() is not None and X[j].value() > 0.5]
    return {"scenario": scenario_name, "mode": mode, "status": status,
            "objective": obj_v, "selected_idx": sel,
            "base_coverage": base_coverage, "R": R}

def build_report(result, mu_aday_df, crit_df, p_access_arr, site_mh, out_path):
    sel = result["selected_idx"]
    base = result["base_coverage"]
    mahalleler = [c for c in mu_aday_df.columns
                  if c not in {"_id", "S_No", "Mahalle", "container_no", "mahalle", "_TOTAL_mu"}]
    R = result["R"]
    sel_rows = []
    for j in sel:
        c = crit_df.iloc[j]
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
            "C5_P_road_open": float(c["C5_P_road_open"]),
            "P_access_applied": p_access_arr[j],
            "dominant_mahalle": site_mh[j],
            "TOPSIS_CC_Baseline": c["CC_Baseline"],
            "TOPSIS_CC_DamageFocused": c["CC_DamageFocused"],
            "TOPSIS_CC_InfrastructureFocused": c["CC_InfrastructureFocused"],
            "FCM_total_mu": float(mu_aday_df.iloc[j]["_TOTAL_mu"]),
        })
    df_sel = pd.DataFrame(sel_rows)
    cov_rows = []
    for mh in mahalleler:
        base_v = base.get(mh, 0.0)
        new_v = sum(float(mu_aday_df.iloc[j][mh]) * p_access_arr[j] for j in sel)
        total = base_v + new_v
        R_v = R.get(mh, 1.0)
        is_crit = normalize_mahalle(mh) in [normalize_mahalle(c) for c in CRITICAL_MAHALLE]
        cov_rows.append({
            "mahalle": mh, "is_critical": is_crit,
            "R_risk_weight": R_v,
            "baseline_coverage_12": base_v,
            "new_coverage_8_weighted": new_v,
            "total_coverage_20_weighted": total,
            "coverage_x_risk_weighted": total * R_v,
        })
    df_cov = pd.DataFrame(cov_rows).sort_values("total_coverage_20_weighted", ascending=False)
    kpi = {
        "scenario": result["scenario"], "mode": result["mode"],
        "status": result["status"], "objective_value": result["objective"],
        "n_critical_below_threshold": int((df_cov[df_cov["is_critical"]]["total_coverage_20_weighted"] < COVERAGE_THRESHOLD).sum()),
        "sum_total_coverage_weighted": float(df_cov["total_coverage_20_weighted"].sum()),
        "sum_baseline_coverage": float(df_cov["baseline_coverage_12"].sum()),
        "coverage_uplift_pct": float((df_cov["total_coverage_20_weighted"].sum() - df_cov["baseline_coverage_12"].sum()) / max(df_cov["baseline_coverage_12"].sum(), 1e-9) * 100),
    }
    df_kpi = pd.DataFrame([kpi])
    with pd.ExcelWriter(out_path) as w:
        df_sel.to_excel(w, sheet_name="Selected_8", index=False)
        df_cov.to_excel(w, sheet_name="Coverage_per_Mahalle", index=False)
        df_kpi.to_excel(w, sheet_name="KPI", index=False)
    return df_sel, df_cov, df_kpi

if __name__ == "__main__":
    print("=" * 60)
    print(f"STEP 4: 0-1 IP with P_access weight (CA2)")
    print("=" * 60)
    mu_aday, mu_mev, mahalleler, risk_map, crit = load_inputs()
    p_access, site_mh = build_p_access(mu_aday, mahalleler)
    print(f"P_access araligi: {min(p_access):.4f} - {max(p_access):.4f}  (ortalama {np.mean(p_access):.4f})")
    p_access_df = pd.DataFrame({
        "S_No": mu_aday["S_No"], "Mahalle_display": mu_aday["Mahalle"],
        "dominant_mahalle_norm": site_mh, "P_access": p_access
    })
    p_access_df.to_excel(RES / "p_access_per_site_CA2.xlsx", index=False)
    print(f"[OK] p_access_per_site_CA2.xlsx")

    results = []
    for sc in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
        for mode in ["hard", "soft"]:
            print(f"\nSolving: scenario={sc}, mode={mode}")
            res = solve_ip(mu_aday, mu_mev, mahalleler, risk_map, p_access,
                           sc, mode, lambda_penalty=10.0)
            out_path = RES / f"selection_{sc}_{mode}_CA2.xlsx"
            df_sel, df_cov, df_kpi = build_report(res, mu_aday, crit, p_access,
                                                  site_mh, out_path)
            print(f"  status={res['status']}  obj={res['objective']:.3f}  "
                  f"selected={len(res['selected_idx'])}  "
                  f"crit_below={int(df_kpi['n_critical_below_threshold'].iloc[0])}")
            results.append({
                "scenario": sc, "mode": mode, "status": res["status"],
                "objective": res["objective"],
                "n_critical_below_threshold": int(df_kpi["n_critical_below_threshold"].iloc[0]),
                "sum_total_coverage_weighted": float(df_kpi["sum_total_coverage_weighted"].iloc[0]),
                "sum_baseline_coverage": float(df_kpi["sum_baseline_coverage"].iloc[0]),
                "coverage_uplift_pct": float(df_kpi["coverage_uplift_pct"].iloc[0]),
            })
    df_res = pd.DataFrame(results)
    df_res.to_excel(RES / "selection_sensitivity_CA2.xlsx", index=False)
    print(f"\n[OK] selection_sensitivity_CA2.xlsx")
    print()
    print("--- CA2 Sensitivity Summary ---")
    print(df_res.to_string(index=False))

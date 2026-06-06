"""
CA8c - IP (3 AHP x 2 mode = 6 senaryo)
Two-tier FCM mu matrisini kullanir.
"""
import os
import pandas as pd
import pulp

ROOT = "D:/IE492"
CA = "cozum_alternatifi_8c_fcm_two_tier"
DATA = os.path.join(ROOT, CA, "data")
RES = os.path.join(ROOT, CA, "results")
os.makedirs(RES, exist_ok=True)

CRITICAL_MAHALLE = [
    "ABDURRAHMANGAZI", "HAMIDIYE", "MEHMET AKIF", "BATTALGAZI", "FATIH"
]
N_NEW = 8
COVERAGE_THRESHOLD = 0.50


def normalize_mahalle(s):
    if s is None: return ""
    return str(s).strip().upper()


def load_inputs():
    mu_aday = pd.read_excel(os.path.join(DATA, "mu_aday_two_tier.xlsx"))
    mu_mev = pd.read_excel(os.path.join(DATA, "mu_mevcut_two_tier.xlsx"))
    risk = pd.read_excel(os.path.join(DATA, "mahalle_risk.xlsx"))
    skip = {"_id", "S_No", "container_no", "Mahalle", "mahalle", "_TOTAL_mu"}
    mahalleler = [c for c in mu_aday.columns if c not in skip]
    risk["_n"] = risk["mahalle"].apply(normalize_mahalle)
    risk_map = dict(zip(risk["_n"], risk["risk_score"].astype(float)))
    return mu_aday, mu_mev, mahalleler, risk_map


def solve_ip(mu_aday, mu_mev, mahalleler, risk_map, scenario_name, mode, threshold=COVERAGE_THRESHOLD):
    n = len(mu_aday)
    prob = pulp.LpProblem(f"CA8c_{scenario_name}_{mode}", pulp.LpMaximize)
    X = [pulp.LpVariable(f"X_{j}", cat="Binary") for j in range(n)]
    base = {mh: float(mu_mev[mh].sum()) if mh in mu_mev.columns else 0.0 for mh in mahalleler}
    R = {mh: float(risk_map.get(mh, 1.0)) for mh in mahalleler}
    total = {}
    for mh in mahalleler:
        new_part = pulp.lpSum(float(mu_aday.iloc[j][mh]) * X[j] for j in range(n))
        total[mh] = base[mh] + new_part
    obj = pulp.lpSum(R[mh] * total[mh] for mh in mahalleler)
    if mode == "soft":
        S = {mh: pulp.LpVariable(f"S_{mh}", lowBound=0) for mh in CRITICAL_MAHALLE}
        for mh in CRITICAL_MAHALLE:
            prob += S[mh] >= threshold - total[mh]
        obj = obj - 50.0 * pulp.lpSum(S[mh] for mh in CRITICAL_MAHALLE)
    prob += obj
    prob += pulp.lpSum(X) == N_NEW
    if mode == "hard":
        for mh in CRITICAL_MAHALLE:
            prob += total[mh] >= threshold
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]
    selected = [j for j in range(n) if X[j].varValue is not None and X[j].varValue > 0.5]
    z_val = pulp.value(prob.objective)
    cov_per_mh = {mh: float(pulp.value(total[mh])) for mh in mahalleler}
    return {"scenario": scenario_name, "mode": mode, "status": status, "Z": z_val,
            "selected": selected, "coverage_per_mahalle": cov_per_mh}


def main():
    mu_aday, mu_mev, mahalleler, risk_map = load_inputs()
    scenarios = ["Baseline", "DamageFocused", "InfrastructureFocused"]
    modes = ["hard", "soft"]
    all_results = []
    coverage_table = []
    for scen in scenarios:
        for mode in modes:
            r = solve_ip(mu_aday, mu_mev, mahalleler, risk_map, scen, mode)
            row = {
                "scenario": r["scenario"], "mode": r["mode"], "status": r["status"],
                "Z": r["Z"], "n_selected": len(r["selected"]),
                "selected_snos": ",".join(str(int(mu_aday.iloc[j]["S_No"])) for j in r["selected"]),
            }
            for mh in mahalleler:
                row[f"cov_{mh}"] = r["coverage_per_mahalle"].get(mh, 0.0)
            all_results.append(row)
            for mh in mahalleler:
                coverage_table.append({
                    "scenario": r["scenario"], "mode": r["mode"], "mahalle": mh,
                    "coverage": r["coverage_per_mahalle"].get(mh, 0.0),
                    "R_risk": risk_map.get(mh, 0.0),
                })
            sel = mu_aday.iloc[r["selected"]][["S_No", "_id", "Mahalle"]].copy() if r["selected"] else pd.DataFrame()
            sel["scenario"] = r["scenario"]
            sel["mode"] = r["mode"]
            sel["Z"] = r["Z"]
            sel.to_excel(os.path.join(RES, f"selection_{r['scenario']}_{mode}.xlsx"), index=False)
            print(f"  {scen:25s} {mode:5s} Z={r['Z']:.2f} status={r['status']:10s} sites={len(r['selected'])}")
    sens = pd.DataFrame(all_results)
    sens.to_excel(os.path.join(RES, "selection_sensitivity.xlsx"), index=False)
    cov_df = pd.DataFrame(coverage_table)
    cov_df.to_excel(os.path.join(RES, "coverage_per_mahalle.xlsx"), index=False)
    print(f"[OK] selection_sensitivity.xlsx  rows={len(sens)}")
    print(f"[OK] coverage_per_mahalle.xlsx  rows={len(cov_df)}")


if __name__ == "__main__":
    main()

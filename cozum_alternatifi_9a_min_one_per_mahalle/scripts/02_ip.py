"""
02_ip.py - CA9a: spatial constraint IP, 12 senaryo (3 AHP x 2 mod x hard/soft)
- n_sites = 20 (MEV: 12+8, NMEV: 20)
- Constraint: her 15 konutlu mahallede en az 1 site
- Kritik 5 mahalle icin mu >= 0.50
"""
import os
import json
import numpy as np
import pandas as pd
import pulp
from itertools import product

ROOT = "D:/IE492"
CA = "cozum_alternatifi_9a_min_one_per_mahalle"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

mu_aday = pd.read_excel(os.path.join(DATA_DIR, "mu_aday.xlsx"))
mu_mev = pd.read_excel(os.path.join(DATA_DIR, "mu_mevcut.xlsx"))
risk = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk.xlsx"))
sp140 = pd.read_excel(os.path.join(DATA_DIR, "spatial_assignment_140.xlsx"))
sp12 = pd.read_excel(os.path.join(DATA_DIR, "spatial_assignment_12.xlsx"))
ahp = pd.read_excel(os.path.join(ROOT, "output/results/ahp_weights.xlsx"))

def _norm(s):
    if not isinstance(s, str):
        return s
    return (s.replace("\u0130", "I").replace("\u0131", "I")
             .replace("\u00dc", "U").replace("\u00fc", "U")
             .replace("\u015e", "S").replace("\u015f", "S")
             .replace("\u00c7", "C").replace("\u00e7", "C")
             .replace("\u00d6", "O").replace("\u00f6", "O")
             .replace("\u011e", "G").replace("\u011f", "G").upper())

mahalle_cols = [c for c in mu_aday.columns if c in [
    "ABDURRAHMANGAZI", "ADIL", "AHMET YESEVI", "AKSEMSETTIN", "BATTALGAZI",
    "FATIH", "HAMIDIYE", "HASANPASA", "MECIDIYE", "MEHMET AKIF",
    "MIMAR SINAN", "NECIP FAZIL", "ORHANGAZI",
    "TURGUT REIS", "YAVUZ SELIM"]]
if len(mahalle_cols) != 15:
    mahalle_cols = [c for c in mu_aday.columns if c in [m for m in _norm(m) for m in [
        "ABDURRAHMANGAZI", "ADIL", "AHMET YESEVI", "AKSEMSETTIN", "BATTALGAZI",
        "FATIH", "HAMIDIYE", "HASANPASA", "MECIDIYE", "MEHMET AKIF",
        "MIMAR SINAN", "NECIP FAZIL", "ORHANGAZI", "TURGUT REIS", "YAVUZ SELIM"]]]

mu_a = mu_aday.set_index("S_No")[mahalle_cols]
mu_m_sub = mu_mev[mahalle_cols].copy()
for c in mu_m_sub.columns:
    mu_m_sub[c] = pd.to_numeric(mu_m_sub[c], errors="coerce").fillna(0.0)
mu_m = mu_m_sub

risk_mah_col = next((c for c in risk.columns if c.lower() == "mahalle"), None)
risk_R = None
for c in risk.columns:
    if "r_risk" in c.lower() or "risk_weight" in c.lower() or c.lower() == "risk_score":
        risk_R = risk.set_index(risk_mah_col)[c]
        break
if risk_R is None:
    for c in risk.columns:
        if "risk" in c.lower() and c != risk_mah_col:
            risk_R = risk.set_index(risk_mah_col)[c]
            break
if risk_R is None:
    raise RuntimeError("risk kolonu bulunamadi")
risk_R = risk_R.apply(lambda v: float(v) if pd.notna(v) else 0.0)
critical_mah = ["ABDURRAHMANGAZI", "BATTALGAZI", "FATIH", "HAMIDIYE", "MEHMET AKIF"]
critical_idx = [mahalle_cols.index(m) for m in critical_mah if m in mahalle_cols]
mu_a_arr = mu_a.values
mu_m_arr = mu_m.values

mu_mev_vec = mu_m_arr.sum(axis=0) if mu_m_arr.size > 0 else np.zeros(len(mahalle_cols))

S_list = mu_a.index.tolist()
sp_map = dict(zip(sp140["S_No"], sp140["mahalle_of_site"]))
sp_map.update({int(r["S_No"]): r["mahalle_norm"] for _, r in sp12.iterrows()})

mah_to_sites = {m: [] for m in mahalle_cols}
for j, s in enumerate(S_list):
    m_norm = sp_map.get(s, None)
    if m_norm and m_norm in mahalle_cols:
        mah_to_sites[m_norm].append(j)

nonempty = {m: idxs for m, idxs in mah_to_sites.items() if len(idxs) > 0}
missing_mah = [m for m in mahalle_cols if m not in nonempty]
print(f"Mahalle dagilimi (aday 140):")
for m in mahalle_cols:
    print(f"  {m}: {len(mah_to_sites[m])} site")
print(f"  Toplam non-empty: {len(nonempty)}/15")
if missing_mah:
    print(f"  BOS: {missing_mah}")

AHP_SCEN = ["Baseline", "DamageFocused", "InfrastructureFocused"]
MODES = ["MEV", "NMEV"]
N_NEW = 20
N_NEW_MEV = 8
N_TOTAL = 20

all_results = []
cov_per_mahalle_rows = []
sel_detail = {}

for ahp_name in AHP_SCEN:
    w_row = ahp[ahp["scenario"] == ahp_name].iloc[0]
    w = np.array([float(w_row["w_C1_Damage"]), float(w_row["w_C2_Logistics"]),
                  float(w_row["w_C3_GapDistance"]), float(w_row["w_C4_NightPop"])])
    w_topsis = w / w.sum()
    print(f"\n=== AHP: {ahp_name} (w={w_topsis.round(3).tolist()}) ===")

    cm = pd.read_excel(os.path.join(DATA_DIR, "topsis_sonuclar.xlsx"))
    cc_col = "CC_" + ahp_name if "CC_" + ahp_name in cm.columns else None
    if cc_col is None:
        for c in cm.columns:
            if ahp_name in c:
                cc_col = c
                break
    if cc_col is None:
        cc_col = "CC_Baseline"
    s_col = "S_No" if "S_No" in cm.columns else cm.columns[0]
    cm = cm.set_index(s_col)
    if cc_col not in cm.columns:
        for c in cm.columns:
            if c.startswith("CC_"):
                cc_col = c
                break
    cc = cm[cc_col].reindex(S_list).fillna(0.0).values

    for mode in MODES:
        for soft in [False, True]:
            tag = f"{ahp_name}_{mode}_{'soft' if soft else 'hard'}"
            n_new = N_NEW_MEV if mode == "MEV" else N_NEW
            n_total = N_TOTAL

            prob = pulp.LpProblem(f"CA9a_{tag}", pulp.LpMaximize)
            x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(len(S_list))]

            objective_terms = []
            for j in range(len(S_list)):
                site_contrib = 0.0
                for i, m in enumerate(mahalle_cols):
                    site_contrib += float(risk_R.get(m, 0.0)) * mu_a_arr[j, i] * cc[j]
                objective_terms.append(cc[j] * site_contrib * x[j])
            prob += pulp.lpSum(objective_terms)

            if not soft:
                prob += pulp.lpSum(x) == n_new
            else:
                min_new = max(0, 15 - 12) if mode == "MEV" else 15
                max_new = n_new
                prob += pulp.lpSum(x) >= min_new
                prob += pulp.lpSum(x) <= max_new

            mevcut_mahalles_set = set(sp12["mahalle_norm"].dropna().unique()) if mode == "MEV" else set()
            for m in nonempty:
                if mode == "MEV" and m in mevcut_mahalles_set:
                    continue
                idxs = nonempty[m]
                if not idxs:
                    continue
                prob += pulp.lpSum(x[j] for j in idxs) >= 1

            if mode == "MEV":
                mu_mev_const = mu_mev_vec
            else:
                mu_mev_const = np.zeros_like(mu_mev_vec)
            for k_i in critical_idx:
                i = k_i
                m_name = mahalle_cols[i]
                rhs = 0.50 - mu_mev_const[i]
                if mode == "NMEV" or rhs > 0:
                    prob += (
                        pulp.lpSum(mu_a_arr[j, i] * x[j] for j in range(len(S_list)))
                        >= (0.50 - mu_mev_const[i])
                    )

            solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=120)
            status = prob.solve(solver)
            status_s = pulp.LpStatus[status]
            Z = float(pulp.value(prob.objective)) if prob.objective.value() is not None else 0.0

            chosen = [int(S_list[j]) for j in range(len(S_list)) if pulp.value(x[j]) > 0.5]
            cov_vec = np.zeros(len(mahalle_cols))
            for j_pos, j in enumerate(range(len(S_list))):
                if pulp.value(x[j]) > 0.5:
                    cov_vec += mu_a_arr[j]
            cov_vec = cov_vec + mu_mev_const
            cov_x_risk = sum(cov_vec[i] * float(risk_R.get(mahalle_cols[i], 0.0)) for i in range(len(mahalle_cols)))
            n_crit_ok = sum(1 for k in critical_idx if cov_vec[k] >= 0.50)

            mahalle_coverage = {mahalle_cols[i]: float(cov_vec[i]) for i in range(len(mahalle_cols))}
            sel_detail[tag] = {
                "chosen_sites": chosen,
                "mahalle_coverage": mahalle_coverage,
                "Z": Z,
                "n_new": sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5),
            }

            for i, m in enumerate(mahalle_cols):
                cov_per_mahalle_rows.append({
                    "scenario": tag,
                    "ahp": ahp_name,
                    "mode": mode,
                    "soft": soft,
                    "mahalle": m,
                    "coverage": float(cov_vec[i]),
                    "R_risk": float(risk_R.get(m, 0.0)),
                    "R_x_C": float(cov_vec[i]) * float(risk_R.get(m, 0.0)),
                })

            all_results.append({
                "scenario": tag,
                "ahp": ahp_name,
                "mode": mode,
                "soft": soft,
                "status": status_s,
                "Z": Z,
                "n_chosen_new": sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5),
                "n_total": (12 + sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5)) if mode == "MEV" else sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5),
                "n_critical_below_0.50": len(critical_idx) - n_crit_ok,
                "sum_R_x_C": cov_x_risk,
                "chosen_sites": ",".join(str(s) for s in chosen),
            })
            print(f"  {tag}: status={status_s}, Z={Z:.2f}, n={sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5)}, R*x={cov_x_risk:.2f}")

results_df = pd.DataFrame(all_results)
results_df.to_excel(os.path.join(RESULTS_DIR, "ip_all_scenarios.xlsx"), index=False)
print(f"\n[OK] ip_all_scenarios.xlsx ({len(results_df)} senaryo)")

cov_df = pd.DataFrame(cov_per_mahalle_rows)
cov_df.to_excel(os.path.join(RESULTS_DIR, "coverage_per_mahalle.xlsx"), index=False)
print(f"[OK] coverage_per_mahalle.xlsx ({len(cov_df)} satir)")

sel_rows = []
for tag, d in sel_detail.items():
    for s in d["chosen_sites"]:
        sel_rows.append({"scenario": tag, "S_No": s, "mahalle_of_site": sp_map.get(s, "")})
sel_df = pd.DataFrame(sel_rows)
sel_df.to_excel(os.path.join(RESULTS_DIR, "selected_sites.xlsx"), index=False)
print(f"[OK] selected_sites.xlsx")

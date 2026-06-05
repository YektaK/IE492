"""
02_ip.py - CA9c: min 1 spatial + CA8a truncation (mu < 0.20 → 0)
"""
import os
import numpy as np
import pandas as pd
import pulp

ROOT = "D:/IE492"
CA = "cozum_alternatifi_9c_min_one_truncation"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

mu_aday = pd.read_excel(os.path.join(DATA_DIR, "mu_aday.xlsx"))
mu_mev = pd.read_excel(os.path.join(DATA_DIR, "mu_mevcut.xlsx"))
risk = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk.xlsx"))
sp140 = pd.read_excel(os.path.join(DATA_DIR, "spatial_assignment_140.xlsx"))
sp12 = pd.read_excel(os.path.join(DATA_DIR, "spatial_assignment_12.xlsx"))
ahp = pd.read_excel(os.path.join(ROOT, "output/results/ahp_weights.xlsx"))

mahalle_cols = ["ABDURRAHMANGAZI","ADIL","AHMET YESEVI","AKSEMSETTIN","BATTALGAZI","FATIH",
                "HAMIDIYE","HASANPASA","MECIDIYE","MEHMET AKIF","MIMAR SINAN","NECIP FAZIL",
                "ORHANGAZI","TURGUT REIS","YAVUZ SELIM"]
mu_a = mu_aday.set_index("S_No")[mahalle_cols].copy()
for c in mu_a.columns:
    mu_a[c] = pd.to_numeric(mu_a[c], errors="coerce").fillna(0.0)

mu_m_sub = mu_mev[mahalle_cols].copy()
for c in mu_m_sub.columns:
    mu_m_sub[c] = pd.to_numeric(mu_m_sub[c], errors="coerce").fillna(0.0)

# Truncation: mu < 0.20 → 0
TRUNC = 0.20
mu_a[mu_a < TRUNC] = 0.0
mu_m_sub[mu_m_sub < TRUNC] = 0.0
print(f"[OK] Truncation: mu < {TRUNC} -> 0 (CA8a ile ayni)")

risk_R = risk.set_index("mahalle")["risk_score"].apply(lambda v: float(v) if pd.notna(v) else 0.0)
critical_mah = ["ABDURRAHMANGAZI", "BATTALGAZI", "FATIH", "HAMIDIYE", "MEHMET AKIF"]
critical_idx = [mahalle_cols.index(m) for m in critical_mah]
mu_a_arr = mu_a.values
mu_m_arr = mu_m_sub.values
mu_mev_vec = mu_m_arr.sum(axis=0)
S_list = mu_a.index.tolist()
sp_map = dict(zip(sp140["S_No"], sp140["mahalle_of_site"]))
sp_map.update({int(r["S_No"]): r["mahalle_norm"] for _, r in sp12.iterrows()})

mah_to_sites = {m: [] for m in mahalle_cols}
for j, s in enumerate(S_list):
    m_norm = sp_map.get(s, None)
    if m_norm and m_norm in mahalle_cols:
        mah_to_sites[m_norm].append(j)
nonempty = {m: idxs for m, idxs in mah_to_sites.items() if len(idxs) > 0}
mevcut_mahalles_set = set(sp12["mahalle_norm"].dropna().unique())

AHP_SCEN = ["Baseline", "DamageFocused", "InfrastructureFocused"]
all_results = []
cov_per_mahalle_rows = []
sel_detail = {}

for ahp_name in AHP_SCEN:
    cm = pd.read_excel(os.path.join(DATA_DIR, "topsis_sonuclar.xlsx"))
    cc_col = "CC_" + ahp_name
    if cc_col not in cm.columns:
        for c in cm.columns:
            if ahp_name in c: cc_col = c; break
    s_col = "S_No" if "S_No" in cm.columns else cm.columns[0]
    cm = cm.set_index(s_col)
    cc = cm[cc_col].reindex(S_list).fillna(0.0).values
    print(f"\n=== AHP: {ahp_name} ===")
    for mode in ["MEV", "NMEV"]:
        for soft in [False, True]:
            tag = f"{ahp_name}_{mode}_{'soft' if soft else 'hard'}"
            n_new = 8 if mode == "MEV" else 20
            prob = pulp.LpProblem(f"CA9c_{tag}", pulp.LpMaximize)
            x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(len(S_list))]
            obj_terms = []
            for j in range(len(S_list)):
                site_contrib = sum(float(risk_R.get(m, 0.0)) * mu_a_arr[j, i] * cc[j] for i, m in enumerate(mahalle_cols))
                obj_terms.append(cc[j] * site_contrib * x[j])
            prob += pulp.lpSum(obj_terms)
            if not soft:
                prob += pulp.lpSum(x) == n_new
            else:
                min_new = (15 - 12) if mode == "MEV" else 15
                prob += pulp.lpSum(x) >= min_new
                prob += pulp.lpSum(x) <= n_new
            mev_set = mevcut_mahalles_set if mode == "MEV" else set()
            for m in nonempty:
                if mode == "MEV" and m in mev_set: continue
                idxs = nonempty[m]
                if not idxs: continue
                prob += pulp.lpSum(x[j] for j in idxs) >= 1
            mu_mev_const = mu_mev_vec if mode == "MEV" else np.zeros_like(mu_mev_vec)
            for k_i in critical_idx:
                prob += pulp.lpSum(mu_a_arr[j, k_i] * x[j] for j in range(len(S_list))) >= (0.50 - mu_mev_const[k_i])
            status = prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=120))
            Z = float(pulp.value(prob.objective)) if prob.objective.value() is not None else 0.0
            chosen = [int(S_list[j]) for j in range(len(S_list)) if pulp.value(x[j]) > 0.5]
            cov_vec = np.zeros(len(mahalle_cols))
            for j in range(len(S_list)):
                if pulp.value(x[j]) > 0.5:
                    cov_vec += mu_a_arr[j]
            cov_vec = cov_vec + mu_mev_const
            cov_x_risk = sum(cov_vec[i] * float(risk_R.get(mahalle_cols[i], 0.0)) for i in range(len(mahalle_cols)))
            n_crit_ok = sum(1 for k in critical_idx if cov_vec[k] >= 0.50)
            sel_detail[tag] = {"chosen_sites": chosen, "mahalle_coverage": {mahalle_cols[i]: float(cov_vec[i]) for i in range(len(mahalle_cols))}, "Z": Z}
            for i, m in enumerate(mahalle_cols):
                cov_per_mahalle_rows.append({"scenario": tag, "ahp": ahp_name, "mode": mode, "soft": soft, "mahalle": m,
                                              "coverage": float(cov_vec[i]), "R_risk": float(risk_R.get(m, 0.0)),
                                              "R_x_C": float(cov_vec[i]) * float(risk_R.get(m, 0.0))})
            all_results.append({"scenario": tag, "ahp": ahp_name, "mode": mode, "soft": soft, "status": pulp.LpStatus[status],
                                "Z": Z, "n_chosen_new": sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5),
                                "n_total": (12 + sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5)) if mode == "MEV" else sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5),
                                "n_critical_below_0.50": len(critical_idx) - n_crit_ok, "sum_R_x_C": cov_x_risk,
                                "chosen_sites": ",".join(str(s) for s in chosen)})
            print(f"  {tag}: {pulp.LpStatus[status]}, Z={Z:.2f}, n={sum(1 for j in range(len(S_list)) if pulp.value(x[j]) > 0.5)}, RxC={cov_x_risk:.2f}")

pd.DataFrame(all_results).to_excel(os.path.join(RESULTS_DIR, "ip_all_scenarios.xlsx"), index=False)
pd.DataFrame(cov_per_mahalle_rows).to_excel(os.path.join(RESULTS_DIR, "coverage_per_mahalle.xlsx"), index=False)
sel_rows = []
for tag, d in sel_detail.items():
    for s in d["chosen_sites"]:
        sel_rows.append({"scenario": tag, "S_No": s, "mahalle_of_site": sp_map.get(s, "")})
pd.DataFrame(sel_rows).to_excel(os.path.join(RESULTS_DIR, "selected_sites.xlsx"), index=False)
print(f"\n[OK] 3 dosya results/ icinde")

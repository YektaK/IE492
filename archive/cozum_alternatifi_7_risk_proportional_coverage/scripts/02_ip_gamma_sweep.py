"""
02_ip_gamma_sweep.py — CA7a: Proportional Lower Bound, 5 gamma

Her gamma icin IP:
  max Z = sum_i R_i * sum_j mu(i,j) * x_j
  s.t.  sum_j x_j = 8
        sum_j mu(i,j) * x_j >= L_i(gamma)   for i critical
        x_j in {0, 1}

Cikti:
  - results/gamma_sweep_results.xlsx (her gamma: Z, secim, coverage, rho)
  - results/selected_gamma_1.0.xlsx (secim detay)
  - results/coverage_per_mahalle_gamma_*.xlsx (her gamma icin)
"""
import os
import numpy as np
import pandas as pd
import pulp

ROOT = "D:/IE492"
CA = "cozum_alternatifi_7_risk_proportional_coverage"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

mu_df = pd.read_excel(os.path.join(DATA_DIR, "mu_aday.xlsx"))
sn_col = "S_No" if "S_No" in mu_df.columns else mu_df.columns[1]
mah_cols = [c for c in mu_df.columns if c not in ("_id", sn_col, "Mahalle", "_kaynak", "_TOTAL_mu")]
J = mu_df[sn_col].astype(int).tolist()
mu = mu_df[mah_cols].values.astype(float)
mahalleler = list(mah_cols)
I = list(range(len(mahalleler)))

mu_mevcut_df = pd.read_excel(os.path.join(DATA_DIR, "mu_mevcut.xlsx"))
mc_mah_cols = [c for c in mu_mevcut_df.columns if c in mahalleler]
mu_mevcut_vec = mu_mevcut_df[mc_mah_cols].sum(axis=0).reindex(mahalleler).fillna(0.0).values
print(f"mu_mevcut (sabit ofset) = {mu_mevcut_vec.round(3).tolist()}")

risk_df = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk_CA7.xlsx"))
risk_map = {str(r["mahalle"]).upper(): float(r["R_risk"]) for _, r in risk_df.iterrows()}
critical_map = {str(r["mahalle"]).upper(): bool(r["is_critical"]) for _, r in risk_df.iterrows()}
R_vec = np.array([risk_map.get(m.upper(), 0.0) for m in mahalleler])
R_max = R_vec.max()
R_norm = R_vec / R_max if R_max > 0 else R_vec
I_critical = [i for i, m in enumerate(mahalleler) if critical_map.get(m.upper(), False)]
print(f"Havuz: {len(J)} site, {len(I)} mahalle, kritik: {len(I_critical)}")
print(f"R_max = {R_max:.2f}, R_min(critical) = {R_vec[I_critical].min():.2f}")

N_SELECT = 8
gammas = [0.0, 0.25, 0.50, 0.75, 1.0]


def L_for(gamma):
    return np.array([0.50 + gamma * 0.50 * R_norm[i] if i in I_critical else 0.0
                     for i in I])


def solve_ip(gamma, L_i, use_mevcut=True):
    prob = pulp.LpProblem(f"CA7_gamma_{gamma:.2f}_{'mev' if use_mevcut else 'nmev'}", pulp.LpMaximize)
    x = {j: pulp.LpVariable(f"x_{j}", cat="Binary") for j in J}
    muT = mu.T
    const_offset = float(np.sum(R_vec * mu_mevcut_vec)) if use_mevcut else 0.0
    prob += pulp.lpSum(R_vec[i] * muT[i, k] * x[J[k]] for i in I for k in range(len(J)))
    prob += pulp.lpSum(x[j] for j in J) == N_SELECT
    if use_mevcut:
        for i in I_critical:
            prob += pulp.lpSum(muT[i, k] * x[J[k]] for k in range(len(J))) >= max(0.0, L_i[i] - mu_mevcut_vec[i])
    else:
        for i in I_critical:
            prob += pulp.lpSum(muT[i, k] * x[J[k]] for k in range(len(J))) >= L_i[i]
    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=120)
    prob.solve(solver)
    status = pulp.LpStatus[prob.status]
    Z_var = pulp.value(prob.objective) or 0.0
    Z = Z_var + const_offset
    selected = sorted([j for j in J if pulp.value(x[j]) > 0.5])
    if use_mevcut:
        cov = mu_mevcut_vec + np.array([sum(muT[i, k] for k, j in enumerate(J) if j in selected) for i in I])
    else:
        cov = np.array([sum(muT[i, k] for k, j in enumerate(J) if j in selected) for i in I])
    return {
        "gamma": gamma,
        "status": status,
        "Z": Z,
        "Z_var": Z_var,
        "selected": selected,
        "coverage": cov,
        "L_i": L_i,
        "use_mevcut": use_mevcut,
    }


def spearman_rho(x, y):
    mask = (np.asarray(x) > 0) & (np.asarray(y) > 0)
    if mask.sum() < 3:
        return float("nan")
    rx = pd.Series(x[mask]).rank().values
    ry = pd.Series(y[mask]).rank().values
    rho = np.corrcoef(rx, ry)[0, 1]
    return float(rho)


results = []
all_coverages = {}
for use_mevcut in (True, False):
    print(f"\n========== USE_MEVCUT = {use_mevcut} ==========")
    for g in gammas:
        L_i = L_for(g)
        print(f"\n--- gamma = {g:.2f} (use_mevcut={use_mevcut}) ---")
        print(f"L_i (kritik): {[f'{L_i[i]:.3f}' for i in I_critical]}")
        r = solve_ip(g, L_i, use_mevcut=use_mevcut)
        print(f"  status = {r['status']}, Z = {r['Z']:.4f}")
        print(f"  selected = {r['selected']}")
        rho = spearman_rho(R_vec, r["coverage"])
        print(f"  Spearman rho(R, coverage) = {rho:.4f}")
        results.append({
            "use_mevcut": use_mevcut,
            "gamma": g,
            "status": r["status"],
            "Z": r["Z"],
            "n_selected": len(r["selected"]),
            "selected": r["selected"],
            "sum_coverage": r["coverage"].sum(),
            "sum_RxC": float(np.sum(R_vec * r["coverage"])),
            "spearman_rho": rho,
        })
        all_coverages[(use_mevcut, g)] = (r["selected"], r["coverage"], r["L_i"])

res_df = pd.DataFrame([
    {k: v for k, v in row.items() if k != "selected"} for row in results
])
res_df.to_excel(os.path.join(RESULTS_DIR, "gamma_sweep_results.xlsx"), index=False)
print(f"\n[OK] gamma_sweep_results.xlsx")

with pd.ExcelWriter(os.path.join(RESULTS_DIR, "gamma_sweep_results.xlsx"), engine="openpyxl", mode="w") as w:
    summary = pd.DataFrame([
        {k: v for k, v in row.items() if k != "selected"} for row in results
    ])
    summary.to_excel(w, sheet_name="summary", index=False)
    for row in results:
        sels = row["selected"]
        gd = mu_df[mu_df[sn_col].astype(int).isin(sels)].copy()
        if "Mahalle" in gd.columns:
            gd["R_dominant"] = gd["Mahalle"].map(lambda m: risk_map.get(str(m).upper(), 0.0))
        tag = ("mev" if row["use_mevcut"] else "nmev") + f"_g{int(row['gamma']*100):03d}"
        gd.to_excel(w, sheet_name=tag, index=False)

cov_rows = []
for (use_mevcut, g), (sels, cov, L_i) in all_coverages.items():
    for i, m in enumerate(mahalleler):
        cov_rows.append({
            "use_mevcut": use_mevcut,
            "gamma": g,
            "mahalle": m,
            "R_risk": R_vec[i],
            "is_critical": i in I_critical,
            "L_i_proportional": L_i[i],
            "coverage": cov[i],
            "gap_to_L": max(0.0, L_i[i] - cov[i]),
            "R_x_C": R_vec[i] * cov[i],
        })
cov_df = pd.DataFrame(cov_rows)
cov_df.to_excel(os.path.join(RESULTS_DIR, "coverage_per_mahalle_gamma_sweep.xlsx"), index=False)
print(f"[OK] coverage_per_mahalle_gamma_sweep.xlsx: {len(cov_df)} satir")

g_main = 1.0
sels_main, cov_main, L_main = all_coverages[(False, g_main)]
sel_df = mu_df[mu_df[sn_col].astype(int).isin(sels_main)].copy()
if "Mahalle" in sel_df.columns:
    sel_df["R_dominant"] = sel_df["Mahalle"].map(lambda m: risk_map.get(str(m).upper(), 0.0))
sel_df.to_excel(os.path.join(RESULTS_DIR, "selected_gamma_1.0_nmev.xlsx"), index=False)
print(f"[OK] selected_gamma_1.0_nmev.xlsx: {len(sel_df)} site")

muT_for_save = mu.T
for i, m in enumerate(mahalleler):
    col = f"mu_{m}"
    sel_df[col] = sel_df[sn_col].map(lambda s: float(muT_for_save[i, J.index(int(s))]) if int(s) in J else 0.0)
sel_df.to_excel(os.path.join(RESULTS_DIR, "selected_gamma_1.0_nmev.xlsx"), index=False)
print(f"[OK] selected_gamma_1.0_nmev.xlsx updated with mu_* cols")

print("\n=== GAMMA SWEEP OZET ===")
print(f"{'mev':>4} {'gamma':>6} | {'Z':>9} | {'sum_RxC':>9} | {'rho(R,C)':>9} | {'status':>10} | secim")
for row in results:
    mev_str = "MEV" if row["use_mevcut"] else "NMEV"
    print(f"{mev_str:>4} {row['gamma']:>6.2f} | {row['Z']:>9.2f} | {row['sum_RxC']:>9.2f} | {row['spearman_rho']:>9.4f} | {row['status']:>10} | {row['selected']}")

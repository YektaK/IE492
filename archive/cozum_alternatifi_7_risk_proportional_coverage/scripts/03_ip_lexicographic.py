"""
03_ip_lexicographic.py — CA7b: 2-stage lexicographic IP

Stage 1: max Z  (orijinal amac)
Stage 2: Stage 1 Z* korunur; max E = sum_i (R_i/R_max) * mu_covered(i)
         (yani risk-oranti coverage toplami)
"""
import os
import numpy as np
import pandas as pd
import pulp

ROOT = "D:/IE492"
CA = "cozum_alternatifi_7_risk_proportional_coverage"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")

mu_df = pd.read_excel(os.path.join(DATA_DIR, "mu_aday.xlsx"))
sn_col = "S_No" if "S_No" in mu_df.columns else mu_df.columns[1]
mah_cols = [c for c in mu_df.columns if c not in ("_id", sn_col, "Mahalle", "_kaynak", "_TOTAL_mu")]
J = mu_df[sn_col].astype(int).tolist()
mu = mu_df[mah_cols].values.astype(float)
mahalleler = list(mah_cols)
I = list(range(len(mahalleler)))
muT = mu.T

mu_mevcut_df = pd.read_excel(os.path.join(DATA_DIR, "mu_mevcut.xlsx"))
mu_mevcut_vec = mu_mevcut_df[[c for c in mu_mevcut_df.columns if c in mahalleler]].sum(axis=0).reindex(mahalleler).fillna(0.0).values

risk_df = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk_CA7.xlsx"))
risk_map = {str(r["mahalle"]).upper(): float(r["R_risk"]) for _, r in risk_df.iterrows()}
critical_map = {str(r["mahalle"]).upper(): bool(r["is_critical"]) for _, r in risk_df.iterrows()}
R_vec = np.array([risk_map.get(m.upper(), 0.0) for m in mahalleler])
R_max = R_vec.max() if R_vec.max() > 0 else 1.0
R_norm = R_vec / R_max
I_critical = [i for i, m in enumerate(mahalleler) if critical_map.get(m.upper(), False)]
N_SELECT = 8
EPS = 1e-3


def stage1(use_mevcut=True):
    prob = pulp.LpProblem("CA7b_stage1", pulp.LpMaximize)
    x = {j: pulp.LpVariable(f"x_{j}", cat="Binary") for j in J}
    const_offset = float(np.sum(R_vec * mu_mevcut_vec)) if use_mevcut else 0.0
    prob += pulp.lpSum(R_vec[i] * muT[i, k] * x[J[k]] for i in I for k in range(len(J)))
    prob += pulp.lpSum(x[j] for j in J) == N_SELECT
    for i in I_critical:
        if use_mevcut:
            prob += pulp.lpSum(muT[i, k] * x[J[k]] for k in range(len(J))) >= max(0.0, 0.50 - mu_mevcut_vec[i])
        else:
            prob += pulp.lpSum(muT[i, k] * x[J[k]] for k in range(len(J))) >= 0.50
    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=120))
    Z_var = pulp.value(prob.objective) or 0.0
    Z = Z_var + const_offset
    sels = [j for j in J if pulp.value(x[j]) > 0.5]
    return Z, sels


def stage2(Z_star, use_mevcut=True):
    prob = pulp.LpProblem("CA7b_stage2", pulp.LpMaximize)
    x = {j: pulp.LpVariable(f"x_{j}", cat="Binary") for j in J}
    const_offset = float(np.sum(R_vec * mu_mevcut_vec)) if use_mevcut else 0.0
    prob += pulp.lpSum(R_norm[i] * muT[i, k] * x[J[k]] for i in I for k in range(len(J)))
    prob += pulp.lpSum(x[j] for j in J) == N_SELECT
    for i in I_critical:
        if use_mevcut:
            prob += pulp.lpSum(muT[i, k] * x[J[k]] for k in range(len(J))) >= max(0.0, 0.50 - mu_mevcut_vec[i])
        else:
            prob += pulp.lpSum(muT[i, k] * x[J[k]] for k in range(len(J))) >= 0.50
    if use_mevcut:
        prob += pulp.lpSum(R_vec[i] * muT[i, k] * x[J[k]] for i in I for k in range(len(J))) >= Z_star - const_offset - EPS
    else:
        prob += pulp.lpSum(R_vec[i] * muT[i, k] * x[J[k]] for i in I for k in range(len(J))) >= Z_star - EPS
    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=120))
    Z_var = pulp.value(prob.objective) or 0.0
    Z_actual_var = None
    if use_mevcut:
        v = pulp.value(pulp.lpSum(R_vec[i] * muT[i, k] * x[J[k]] for i in I for k in range(len(J))))
        Z_actual_var = v
    else:
        v = pulp.value(pulp.lpSum(R_vec[i] * muT[i, k] * x[J[k]] for i in I for k in range(len(J))))
        Z_actual_var = v
    Z_actual = Z_actual_var + const_offset
    E = Z_var
    sels = sorted([j for j in J if pulp.value(x[j]) > 0.5])
    if use_mevcut:
        cov = mu_mevcut_vec + np.array([sum(muT[i, k] for k, j in enumerate(J) if j in sels) for i in I])
    else:
        cov = np.array([sum(muT[i, k] for k, j in enumerate(J) if j in sels) for i in I])
    return E, Z_actual, sels, cov


def spearman(x, y):
    mask = (np.asarray(x) > 0) & (np.asarray(y) > 0)
    if mask.sum() < 3:
        return float("nan")
    rx = pd.Series(x[mask]).rank().values
    ry = pd.Series(y[mask]).rank().values
    return float(np.corrcoef(rx, ry)[0, 1])


results = []
for use_mevcut in (True, False):
    tag = "MEV" if use_mevcut else "NMEV"
    print(f"\n========== {tag} ==========")
    Z_star, sels1 = stage1(use_mevcut)
    print(f"Stage 1: Z* = {Z_star:.4f}, secim = {sels1}")
    if use_mevcut:
        cov1 = mu_mevcut_vec + np.array([sum(muT[i, k] for k, j in enumerate(J) if j in sels1) for i in I])
    else:
        cov1 = np.array([sum(muT[i, k] for k, j in enumerate(J) if j in sels1) for i in I])
    E1 = float(np.sum(R_norm * cov1))
    rho1 = spearman(R_vec, cov1)
    print(f"  E (stage 1) = {E1:.4f}, rho = {rho1:.4f}")

    E2, Z2, sels2, cov2 = stage2(Z_star, use_mevcut)
    rho2 = spearman(R_vec, cov2)
    print(f"Stage 2: Z_actual = {Z2:.4f} (kontrol Z >= {Z_star:.4f}), E = {E2:.4f}, rho = {rho2:.4f}")
    print(f"  secim = {sels2}")

    results.append({
        "use_mevcut": use_mevcut,
        "tag": tag,
        "Z_star": Z_star,
        "Z_stage2": Z2,
        "E_stage1": E1,
        "E_stage2": E2,
        "delta_E": E2 - E1,
        "rho_stage1": rho1,
        "rho_stage2": rho2,
        "sels_stage1": sels1,
        "sels_stage2": sels2,
        "cov_stage1": cov1,
        "cov_stage2": cov2,
    })

with pd.ExcelWriter(os.path.join(RESULTS_DIR, "lexicographic_results.xlsx"), engine="openpyxl") as w:
    summary = pd.DataFrame([{
        "use_mevcut": r["use_mevcut"],
        "Z_star": r["Z_star"],
        "Z_stage2": r["Z_stage2"],
        "E_stage1": r["E_stage1"],
        "E_stage2": r["E_stage2"],
        "delta_E": r["delta_E"],
        "rho_stage1": r["rho_stage1"],
        "rho_stage2": r["rho_stage2"],
        "sels_stage1": r["sels_stage1"],
        "sels_stage2": r["sels_stage2"],
    } for r in results])
    summary.to_excel(w, sheet_name="summary", index=False)
    for r in results:
        for stage, sels, cov in [
            ("stage1", r["sels_stage1"], r["cov_stage1"]),
            ("stage2", r["sels_stage2"], r["cov_stage2"]),
        ]:
            df = mu_df[mu_df[sn_col].astype(int).isin(sels)].copy()
            if "Mahalle" in df.columns:
                df["R_dominant"] = df["Mahalle"].map(lambda m: risk_map.get(str(m).upper(), 0.0))
            sheet = f"{r['tag']}_{stage}"
            df.to_excel(w, sheet_name=sheet, index=False)
            cov_row = pd.DataFrame([{
                "mahalle": m, "R_risk": R_vec[i], "is_critical": i in I_critical,
                "coverage": cov[i], "R_x_C": R_vec[i] * cov[i],
            } for i, m in enumerate(mahalleler)])
            cov_row.to_excel(w, sheet_name=f"{sheet}_cov", index=False)
print(f"\n[OK] lexicographic_results.xlsx")

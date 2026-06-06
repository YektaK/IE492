# -*- coding: utf-8 -*-
"""
13_alt_c4_shelter.py
Alternative C4 (demand proxy) test: replace night population with
IBB's Table 5-4 shelter demand. Re-run TOPSIS+IP and compare selection.

Output:
  output/results/alt_C4_shelter_selection.xlsx  (selected 8 with alt C4)
  output/results/alt_C4_shelter_topsis.xlsx     (TOPSIS scores under alt C4)
  output/figures/alt_C4_comparison.png         (side-by-side: original 8 vs alt 8)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pulp import (
    LpProblem, LpMaximize, LpVariable, lpSum, LpBinary, LpStatus, value, PULP_CBC_CMD
)

ROOT = Path("D:/IE492")
RES = ROOT / "output" / "results"
FIG = ROOT / "output" / "figures"

# Load
adaylar = pd.read_excel(ROOT / "output" / "data" / "adaylar.xlsx")
mevcut = pd.read_excel(ROOT / "output" / "data" / "mevcut_12.xlsx")
criteria = pd.read_excel(RES / "criteria_matrix.xlsx")
mu_aday = pd.read_excel(RES / "mu_aday.xlsx")
mu_mevcut = pd.read_excel(RES / "mu_mevcut.xlsx")
risk = pd.read_excel(ROOT / "output" / "data" / "mahalle_risk.xlsx")
shelter = pd.read_excel(RES / "shelter_demand.xlsx")

# Mahalle list (without extra cols)
mahalle_cols = [c for c in mu_aday.columns
                if c not in ("S_No", "Mahalle", "_TOTAL_mu", "container_no")]

# Replace C4 with shelter demand (normalize to 0-1 by max)
shelter_max = shelter["hane_ihtiyaci"].max()
mah_to_shelter = dict(zip(shelter["mahalle"], shelter["hane_ihtiyaci"] / shelter_max))

criteria_alt = criteria.copy()
# Get night pop max for normalization (original C4 was raw counts, see build_criteria_matrix)
nightpop_max = criteria_alt["C4_NightPop"].max()
criteria_alt["C4_orig"] = criteria_alt["C4_NightPop"]
criteria_alt["C4_NightPop"] = criteria_alt["Mahalle"].map(mah_to_shelter).fillna(0)
# Note: shelter is already 0-1 normalized (divided by max)
# Now apply vector normalization to all 4 criteria
M = criteria_alt[["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_NightPop"]].values.astype(float)
norms = np.sqrt((M ** 2).sum(axis=0))
norms[norms == 0] = 1
N = M / norms

# AHP weights Baseline
w = np.array([0.541, 0.254, 0.117, 0.088])

# TOPSIS
V = N * w
ideal = V.max(axis=0)
anti = V.min(axis=0)
d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
d_minus = np.sqrt(((V - anti) ** 2).sum(axis=1))
cc_alt = d_minus / (d_plus + d_minus + 1e-12)

topsis_alt = criteria_alt[["S_No", "Alan_Adi", "Mahalle"]].copy()
topsis_alt["TOPSIS_CC_alt_C4"] = cc_alt
topsis_alt = topsis_alt.sort_values("TOPSIS_CC_alt_C4", ascending=False).reset_index(drop=True)
topsis_alt["rank_alt"] = range(1, len(topsis_alt) + 1)
topsis_alt.to_excel(RES / "alt_C4_shelter_topsis.xlsx", index=False)
print("[OK] alt_C4_shelter_topsis.xlsx")
print("Top-10 under alt C4 (shelter):")
print(topsis_alt.head(10)[["S_No", "Alan_Adi", "Mahalle", "TOPSIS_CC_alt_C4"]].to_string(index=False))

# Build mu matrices
mahalle_cols = [c for c in mu_aday.columns
                if c not in ("S_No", "Mahalle", "_TOTAL_mu", "container_no", "_id")]
muA = mu_aday.set_index("S_No")[mahalle_cols]
# mu_mevcut has _id column - drop it before summing
muM_num = mu_mevcut[mahalle_cols]
muM_base = muM_num.sum(axis=0)  # Series of total baseline coverage per mahalle

# Risk
mah_to_risk = dict(zip(risk["mahalle"], risk["risk_score"]))
R = np.array([mah_to_risk.get(m, 0) for m in mahalle_cols])
# Only critical mahalle get the >= 0.50 hard constraint
THRESHOLD = 0.50
critical = ["ABDURRAHMANGAZI", "HAMIDIYE", "MEHMET AKIF", "BATTALGAZI", "FATIH"]
critical = sorted(critical)
print(f"Critical mahalle: {critical}")

# IP with same constraints
prob = LpProblem("Alt_C4_Shelter", LpMaximize)
n = len(adaylar)
S_No_to_idx = {sid: i for i, sid in enumerate(adaylar["S_No"])}
x = [LpVariable(f"x_{i}", cat=LpBinary) for i in range(n)]
x_idx = {S_No_to_idx[sid]: x[S_No_to_idx[sid]] for sid in adaylar["S_No"]}

# Objective: sum_i R_i * (sum_k mu_M[i,k] + sum_j mu_A[j,k] * x_j)
obj_terms = []
for k, mh in enumerate(mahalle_cols):
    Rk = float(R[k])
    base_val = float(muM_base.get(mh, 0))
    obj_terms.append(Rk * base_val)
    for j in range(n):
        obj_terms.append(Rk * float(muA.iloc[j, k]) * x[j])
prob += lpSum(obj_terms), "Z"

# Choose exactly 8
prob += lpSum(x) == 8, "choose_8"

# Hard constraint: critical mahalle >= 0.50
for mh in critical:
    base_val = float(muM_base.get(mh, 0))
    prob += base_val + lpSum(float(muA.iloc[j, mahalle_cols.index(mh)]) * x[j] for j in range(n)) >= THRESHOLD, f"cov_{mh}"

prob.solve(PULP_CBC_CMD(msg=0))
print(f"Status: {LpStatus[prob.status]}  Z = {value(prob.objective):.4f}")

sel_idx = [j for j in range(n) if x[j].value() > 0.5]
sel_ids_alt = adaylar.iloc[sel_idx]["S_No"].tolist()
print(f"Selected S_No (alt C4 = shelter): {sel_ids_alt}")

# Compare to original
sel_orig = pd.read_excel(RES / "selection_Baseline_hard.xlsx")["S_No"].tolist()
print(f"Selected S_No (orig C4 = nightpop): {sel_orig}")
print(f"Identical? {set(sel_ids_alt) == set(sel_orig)}")

# Save selection
sel_alt_df = adaylar[adaylar["S_No"].isin(sel_ids_alt)].copy()
sel_alt_df = sel_alt_df.merge(topsis_alt[["S_No", "TOPSIS_CC_alt_C4"]], on="S_No")
sel_alt_df.to_excel(RES / "alt_C4_shelter_selection.xlsx", index=False)
print(f"[OK] alt_C4_shelter_selection.xlsx")

# Figure: side-by-side
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
all_ids = sorted(set(sel_orig) | set(sel_ids_alt))
labels = [f"S{s}" for s in all_ids]
in_orig = [1 if s in sel_orig else 0 for s in all_ids]
in_alt = [1 if s in sel_ids_alt else 0 for s in all_ids]
x = range(len(all_ids))
w = 0.4
axes[0].bar([i - w/2 for i in x], in_orig, w, color="dodgerblue", label="Orijinal C4 (gece nüfusu)")
axes[0].bar([i + w/2 for i in x], in_alt, w, color="crimson", label="Alternatif C4 (barınma ihtiyacı)")
axes[0].set_xticks(list(x))
axes[0].set_xticklabels(labels, rotation=45)
axes[0].set_yticks([0, 1])
axes[0].set_yticklabels(["Seçilmedi", "Seçildi"])
axes[0].set_title("8 Seçim - Orijinal vs Alternatif C4")
axes[0].legend()
axes[0].grid(axis="y", linestyle="--", alpha=0.4)

# Z comparison
axes[1].bar(["Orijinal\n(nüfus)", "Alternatif\n(barınma)"],
            [935.62, value(prob.objective)],
            color=["dodgerblue", "crimson"], alpha=0.85)
axes[1].set_title("IP Objective Z")
axes[1].set_ylabel("Z (toplam risk-ağırlıklı μ kapsama)")
for i, v in enumerate([935.62, value(prob.objective)]):
    axes[1].text(i, v + 5, f"{v:.2f}", ha="center", fontweight="bold")
axes[1].grid(axis="y", linestyle="--", alpha=0.4)

plt.tight_layout()
plt.savefig(FIG / "alt_C4_comparison.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"[OK] {FIG / 'alt_C4_comparison.png'}")

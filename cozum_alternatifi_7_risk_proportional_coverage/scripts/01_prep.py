"""
01_prep.py — CA7 veri hazirligi

Orijinal output'tan temel data kopyalanir, R normalize edilir,
L_i(gamma) profili hesaplanir (5 gamma degeri icin).
"""
import os
import shutil
import pandas as pd
import numpy as np

ROOT = "D:/IE492"
CA = "cozum_alternatifi_7_risk_proportional_coverage"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

src_files = [
    ("output/data/adaylar.xlsx", "adaylar.xlsx"),
    ("output/data/mevcut_12.xlsx", "mevcut_12.xlsx"),
    ("output/data/mahalle_nufus.xlsx", "mahalle_nufus.xlsx"),
    ("output/data/mahalle_risk.xlsx", "mahalle_risk.xlsx"),
    ("output/results/mahalle_centroids.xlsx", "mahalle_centroids.xlsx"),
    ("output/results/mu_aday.xlsx", "mu_aday.xlsx"),
    ("output/results/mu_mevcut.xlsx", "mu_mevcut.xlsx"),
    ("output/results/ahp_weights.xlsx", "ahp_weights.xlsx"),
    ("output/results/criteria_matrix.xlsx", "criteria_matrix.xlsx"),
    ("output/results/topsis_sonuclar.xlsx", "topsis_sonuclar.xlsx"),
]

for src, dst in src_files:
    s = os.path.join(ROOT, src)
    d = os.path.join(DATA_DIR, dst)
    if os.path.exists(s):
        shutil.copy(s, d)
    else:
        print(f"[UYARI] {src} yok")

risk_df = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk.xlsx"))
print("mahalle_risk columns:", list(risk_df.columns))
mah_col = "mahalle" if "mahalle" in risk_df.columns else risk_df.columns[0]
r_col = None
for c in risk_df.columns:
    if "risk" in c.lower() and "score" in c.lower():
        r_col = c
        break
if r_col is None:
    for c in risk_df.columns:
        if "risk" in c.lower():
            r_col = c
            break
if r_col is None:
    r_col = risk_df.columns[1]

risk_df = risk_df[[mah_col, r_col]].rename(columns={mah_col: "mahalle", r_col: "R_risk"})
risk_df["R_normalized"] = risk_df["R_risk"] / risk_df["R_risk"].max()
risk_df["is_critical"] = risk_df["R_normalized"] >= 0.30

gammas = [0.0, 0.25, 0.50, 0.75, 1.0]
profile_rows = []
for g in gammas:
    for _, r in risk_df.iterrows():
        L_i = 0.50 + g * 0.50 * r["R_normalized"]
        profile_rows.append({
            "gamma": g,
            "mahalle": r["mahalle"],
            "R_risk": r["R_risk"],
            "R_normalized": round(r["R_normalized"], 4),
            "is_critical": bool(r["is_critical"]),
            "L_i_proportional": round(L_i, 4),
        })
profile = pd.DataFrame(profile_rows)
profile.to_excel(os.path.join(RESULTS_DIR, "L_i_profile.xlsx"), index=False)
print(f"[OK] L_i_profile.xlsx: 5 gamma x 17 mahalle = {len(profile)} satir")

risk_df.to_excel(os.path.join(DATA_DIR, "mahalle_risk_CA7.xlsx"), index=False)
print(f"[OK] data/mahalle_risk_CA7.xlsx")

print("\nL_i profili (gamma=1.0):")
g1 = profile[profile["gamma"] == 1.0].sort_values("R_risk", ascending=False)
print(g1[["mahalle", "R_risk", "L_i_proportional"]].to_string(index=False))

# -*- coding: utf-8 -*-
"""
02_topsis_CA5.py
==========================================================
Cozum Alternatifi 3: TOPSIS 4 kriter (C4 = barinma ihtiyaci).
152 aday (140 + 12 mevcut) icin CC skorlari.
==========================================================
Ciktilar:
  - results/criteria_matrix_CA5.xlsx
  - results/ahp_weights_CA5.xlsx
  - results/topsis_sonuclar_CA5.xlsx
"""
import math
import unicodedata
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("D:/IE492")
CA5 = ROOT / "cozum_alternatifi_5_full_reloc_yk"
RES = CA5 / "results"
RES.mkdir(parents=True, exist_ok=True)

# 3 AHP senaryosu (4 kriter, orijinal ile ayni)
AHPS = {
    "Baseline": [
        [1, 3, 5, 4], [1/3, 1, 3, 3], [1/5, 1/3, 1, 2], [1/4, 1/3, 1/2, 1]
    ],
    "DamageFocused": [
        [1, 5, 7, 6], [1/5, 1, 3, 3], [1/7, 1/3, 1, 2], [1/6, 1/3, 1/2, 1]
    ],
    "InfrastructureFocused": [
        [1, 1, 5, 4], [1, 1, 5, 4], [1/5, 1/5, 1, 2], [1/4, 1/4, 1/2, 1]
    ],
}

def normalize_mahalle(s):
    if s is None: return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u00a0", " ").replace("\u2019", "'")
    s = s.replace(" TEFERRUC TEPE ORMANI", "TEFERRUC TEPE ORMANI")
    s = s.replace(" SALGAMLI DEVLET ORMANI", "SALGAMLI DEVLET ORMANI")
    return " ".join(s.split())

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def ahp_weights(M):
    A = np.array(M, dtype=float)
    n = A.shape[0]
    eigvals, eigvecs = np.linalg.eig(A)
    real_eigs = np.real(eigvals)
    idx = np.argmax(real_eigs)
    lambda_max = real_eigs[idx]
    v = np.abs(np.real(eigvecs[:, idx]))
    w = v / v.sum()
    CI = (lambda_max - n) / (n - 1)
    RI = 0.90
    CR = CI / RI
    return w, float(lambda_max), float(CI), float(CR)

# --- 1. Pool'u yukle ------------------------------------------------------
pool = pd.read_excel(RES / "pool_152_CA5.xlsx")
print(f"[OK] Pool yuklendi: {len(pool)} aday")

# --- 2. Criteria matrisini olustur ----------------------------------------
# Tum 152 havuz icin 4 kriter + C5
mev_for_gap = pool[pool["_kaynak"] == "mevcut_12"][["Enlem", "Boylam"]].values

rows = []
for _, r in pool.iterrows():
    lat, lon = float(r["Enlem"]), float(r["Boylam"])
    c1 = float(r["C1_risk_score"])
    c2 = (float(r["Su_bin"]) + float(r["WC_bin"]) + float(r["Jen_bin"])) / 3.0
    # Gap distance: en yakin mevcut (12 mevcut)
    min_d = float("inf")
    for mlat, mlon in mev_for_gap:
        d = haversine(lat, lon, mlat, mlon)
        if d < min_d:
            min_d = d
    c3 = min_d
    # CA5: C4 = nufus (SB etkisi YOK)
    c4 = float(r["C4_nufus_2024"])
    c5 = float(r["P_road_open"])
    rows.append({
        "S_No": int(r["S_No"]),
        "_kaynak": r["_kaynak"],
        "AYDES_ID": r["AYDES_ID"],
        "Alan_Adi": r["Alan_Adi"],
        "Mahalle": r["Mahalle"],
        "Mahalle_norm": r["_mh_norm"],
        "Enlem": lat,
        "Boylam": lon,
        "C1_Damage": c1,
        "C2_Logistics": c2,
        "C3_GapDistance_m": c3,
        "C4_Demand": c4,
        "C5_P_road_open": c5,
    })
df = pd.DataFrame(rows)
df.to_excel(RES / "criteria_matrix_CA5.xlsx", index=False)
print(f"[OK] criteria_matrix_CA5.xlsx  rows={len(df)}")

# --- 3. AHP weights -------------------------------------------------------
print("\n--- AHP weights ---")
ahp_results = []
for name, M in AHPS.items():
    w, lm, ci, cr = ahp_weights(M)
    ahp_results.append({
        "scenario": name,
        "w_C1_Damage": float(w[0]),
        "w_C2_Logistics": float(w[1]),
        "w_C3_GapDistance": float(w[2]),
        "w_C4_Demand": float(w[3]),
        "lambda_max": lm, "CI": ci, "CR": cr,
        "CR_acceptable": "YES" if cr < 0.10 else "NO",
    })
    print(f"  {name:24s}  w=[{w[0]:.3f}, {w[1]:.3f}, {w[2]:.3f}, {w[3]:.3f}]  CR={cr:.4f}")
df_ahp = pd.DataFrame(ahp_results)
df_ahp.to_excel(RES / "ahp_weights_CA5.xlsx", index=False)
print(f"[OK] ahp_weights_CA5.xlsx")

# --- 4. TOPSIS 4 kriter ---------------------------------------------------
def topsis_4crit(df, weights):
    M = df[["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_Demand"]].values.astype(float)
    n, m = M.shape
    norms = np.sqrt((M ** 2).sum(axis=0))
    norms[norms == 0] = 1
    N = M / norms
    V = N * weights
    cols = ["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_Demand"]
    ideal = np.zeros(m)
    anti = np.zeros(m)
    for i, c in enumerate(cols):
        ideal[i] = V[:, i].max()
        anti[i] = V[:, i].min()
    d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - anti) ** 2).sum(axis=1))
    cc = d_minus / (d_plus + d_minus + 1e-12)
    return cc

print("\n--- TOPSIS scores ---")
out = df.copy()
for sc in ahp_results:
    w = np.array([sc["w_C1_Damage"], sc["w_C2_Logistics"],
                  sc["w_C3_GapDistance"], sc["w_C4_Demand"]])
    cc = topsis_4crit(df, w)
    col = f"CC_{sc['scenario']}"
    out[col] = cc
out.to_excel(RES / "topsis_sonuclar_CA5.xlsx", index=False)
print(f"[OK] topsis_sonuclar_CA5.xlsx")
print()
print("C4 (barinma ihtiyaci) istatistikleri:")
print(f"  min  = {out['C4_Demand'].min():.0f}")
print(f"  max  = {out['C4_Demand'].max():.0f}")
print(f"  ort. = {out['C4_Demand'].mean():.0f}")
print()
print("TOPSIS Baseline top-10:")
top10 = out.nlargest(10, "CC_Baseline")[["S_No", "_kaynak", "Alan_Adi", "Mahalle", "CC_Baseline"]]
print(top10.to_string(index=False))


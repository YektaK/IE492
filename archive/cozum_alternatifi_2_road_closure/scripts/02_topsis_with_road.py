# -*- coding: utf-8 -*-
"""
02_topsis_with_road.py
==========================================================
Cozum Alternatifi 2: TOPSIS 4 ozgun kritere ek olarak
P(yol acik) bilgisini de criteria_matrix'e C5 olarak ekler.
TOPSIS skoru yine 4 kritere gore hesaplanir (4 ozgun kriter
agirliklari bozulmasin); C5 degeri IP asamasinda carpan
olarak kullanilir.
==========================================================
Girdiler:
  - D:/IE492/output/data/adaylar.xlsx
  - D:/IE492/output/data/mevcut_12.xlsx
  - D:/IE492/output/data/mahalle_nufus.xlsx
  - D:/IE492/output/data/mahalle_risk.xlsx
  - D:/IE492/cozum_alternatifi_2_road_closure/data/mahalle_data_road.xlsx
Ciktilar:
  - results/criteria_matrix_CA2.xlsx    (140 aday x 4 kriter + C5 + P_road)
  - results/ahp_weights_CA2.xlsx
  - results/topsis_sonuclar_CA2.xlsx
"""
import math
import numpy as np
import pandas as pd
import unicodedata
from pathlib import Path

ROOT = Path("D:/IE492")
CA2 = ROOT / "cozum_alternatifi_2_road_closure"
DATA = CA2 / "data"
RES = CA2 / "results"
RES.mkdir(parents=True, exist_ok=True)

# --- 3 AHP senaryosu (orijinal ile ayni, 4 kriter) -----------------------
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

def norm(s):
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
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

def build_criteria_matrix():
    aday = pd.read_excel(ROOT / "output" / "data" / "adaylar.xlsx")
    mev = pd.read_excel(ROOT / "output" / "data" / "mevcut_12.xlsx")
    nuf = pd.read_excel(ROOT / "output" / "data" / "mahalle_nufus.xlsx")
    risk = pd.read_excel(ROOT / "output" / "data" / "mahalle_risk.xlsx")
    road = pd.read_excel(DATA / "mahalle_data_road.xlsx")

    aday["_mh"] = aday["Mahalle"].apply(norm)
    nuf["_mh"] = nuf["mahalle"].apply(norm)
    risk["_mh"] = risk["mahalle"].apply(norm)
    road["_mh"] = road["mahalle"].apply(norm)

    risk_map = risk.set_index("_mh")["risk_score"].to_dict()
    nuf_map = nuf.set_index("_mh")["nufus_2024"].to_dict()
    road_map = road.set_index("_mh")["P_road_open"].to_dict()
    global_mean_p = float(road["P_road_open"].mean())

    mev_coords = mev[["enlem", "boylam"]].values
    rows = []
    for _, r in aday.iterrows():
        mh = r["_mh"]
        lat, lon = float(r["Enlem"]), float(r["Boylam"])
        c1 = float(risk_map.get(mh, 0.0))
        c2 = (r["Su_bin"] + r["WC_bin"] + r["Jen_bin"]) / 3.0
        min_d = float("inf")
        for mlat, mlon in mev_coords:
            d = haversine(lat, lon, mlat, mlon)
            if d < min_d:
                min_d = d
        c3 = min_d
        c4 = float(nuf_map.get(mh, 0))
        # C5: P(road open) - mahalle bazli erisebilirlik
        c5 = float(road_map.get(mh, global_mean_p))
        rows.append({
            "S_No": int(r["S_No"]),
            "AYDES_ID": int(r["AYDES_ID"]) if pd.notna(r["AYDES_ID"]) else None,
            "Alan_Adi": r["Alan_Adi"],
            "Mahalle": r["Mahalle"],
            "Mahalle_norm": mh,
            "Enlem": lat,
            "Boylam": lon,
            "C1_Damage": c1,
            "C2_Logistics": c2,
            "C3_GapDistance_m": c3,
            "C4_NightPop": c4,
            "C5_P_road_open": c5,
        })
    df = pd.DataFrame(rows)
    df.to_excel(RES / "criteria_matrix_CA2.xlsx", index=False)
    print(f"[OK] criteria_matrix_CA2.xlsx  rows={len(df)}")
    return df

def topsis_4crit(df, weights):
    """TOPSIS with the 4 original criteria (C5 stored separately)."""
    M = df[["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_NightPop"]].values.astype(float)
    n, m = M.shape
    norms = np.sqrt((M ** 2).sum(axis=0))
    norms[norms == 0] = 1
    N = M / norms
    V = N * weights
    cols = ["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_NightPop"]
    ideal = np.zeros(m)
    anti = np.zeros(m)
    for i, c in enumerate(cols):
        ideal[i] = V[:, i].max()  # all benefit
        anti[i] = V[:, i].min()
    d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - anti) ** 2).sum(axis=1))
    cc = d_minus / (d_plus + d_minus + 1e-12)
    return cc

if __name__ == "__main__":
    print("=" * 60)
    print("STEP 2: TOPSIS + P(yol acik) entegrasyonu")
    print("=" * 60)
    df = build_criteria_matrix()

    # AHP weights
    print("\n--- AHP weights ---")
    ahp_results = []
    for name, M in AHPS.items():
        w, lm, ci, cr = ahp_weights(M)
        ahp_results.append({
            "scenario": name,
            "w_C1_Damage": float(w[0]),
            "w_C2_Logistics": float(w[1]),
            "w_C3_GapDistance": float(w[2]),
            "w_C4_NightPop": float(w[3]),
            "lambda_max": lm, "CI": ci, "CR": cr,
            "CR_acceptable": "YES" if cr < 0.10 else "NO",
        })
        print(f"  {name:24s}  w=[{w[0]:.3f}, {w[1]:.3f}, {w[2]:.3f}, {w[3]:.3f}]  CR={cr:.4f}")
    df_ahp = pd.DataFrame(ahp_results)
    df_ahp.to_excel(RES / "ahp_weights_CA2.xlsx", index=False)
    print(f"[OK] ahp_weights_CA2.xlsx")

    # TOPSIS - 4 criteria
    print("\n--- TOPSIS scores (4 criteria) ---")
    out = df.copy()
    for sc in ahp_results:
        w = np.array([sc["w_C1_Damage"], sc["w_C2_Logistics"],
                      sc["w_C3_GapDistance"], sc["w_C4_NightPop"]])
        cc = topsis_4crit(df, w)
        col = f"CC_{sc['scenario']}"
        out[col] = cc
    out.to_excel(RES / "topsis_sonuclar_CA2.xlsx", index=False)
    print(f"[OK] topsis_sonuclar_CA2.xlsx")
    print()
    print("P(yol acik) istatistikleri (aday x 140):")
    print(f"  min  = {out['C5_P_road_open'].min():.4f}")
    print(f"  max  = {out['C5_P_road_open'].max():.4f}")
    print(f"  ort. = {out['C5_P_road_open'].mean():.4f}")

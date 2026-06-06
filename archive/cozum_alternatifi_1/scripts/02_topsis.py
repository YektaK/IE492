# -*- coding: utf-8 -*-
"""
02_topsis.py - TOPSIS with C4 = İBB Tablo 5-4 barınma ihtiyacı
ÇÖZÜM ALTERNATİFİ 1

Fark: C4 sütunu gece nüfusu yerine mahalle barınma ihtiyacı (hane).
Diğer 3 kriter (C1 hasar, C2 lojistik, C3 mesafe) birebir aynı.
"""
import math
import unicodedata
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("D:/IE492/cozum_alternatifi_1")
DATA = ROOT / "data"
RES = ROOT / "results"
RES.mkdir(parents=True, exist_ok=True)


def norm(s):
    if s is None:
        return ""
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


def build_criteria_matrix():
    aday = pd.read_excel(DATA / "adaylar.xlsx")
    mev = pd.read_excel(DATA / "mevcut_12.xlsx")
    nuf = pd.read_excel(DATA / "mahalle_nufus.xlsx")
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
    shelter = pd.read_excel(DATA / "mahalle_barinma_ihtiyaci.xlsx")

    aday["_mh"] = aday["Mahalle"].apply(norm)
    nuf["_mh"] = nuf["mahalle"].apply(norm)
    risk["_mh"] = risk["mahalle"].apply(norm)
    shelter["_mh"] = shelter["mahalle"].apply(norm)

    risk_map = risk.set_index("_mh")["risk_score"].to_dict()
    mev_coords = mev[["enlem", "boylam"]].values

    mah_to_shelter = dict(zip(shelter["_mh"], shelter["hane_ihtiyaci"]))
    mah_to_shelter_norm = dict(zip(shelter["_mh"], shelter["hane_ihtiyaci"] / shelter["hane_ihtiyaci"].max()))

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

        c4 = float(mah_to_shelter.get(mh, 0))

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
            "C4_Demand": c4,
        })

    df = pd.DataFrame(rows)
    df.to_excel(RES / "criteria_matrix.xlsx", index=False)
    print(f"[OK] criteria_matrix.xlsx  rows={len(df)}")
    return df


def topsis(df, weights, benefit_cols):
    M = df[["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_Demand"]].values.astype(float)
    n, m = M.shape
    norms = np.sqrt((M ** 2).sum(axis=0))
    norms[norms == 0] = 1
    N = M / norms
    V = N * weights
    ideal = np.zeros(m)
    anti = np.zeros(m)
    cols = ["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_Demand"]
    for i, c in enumerate(cols):
        if c in benefit_cols:
            ideal[i] = V[:, i].max()
            anti[i] = V[:, i].min()
        else:
            ideal[i] = V[:, i].min()
            anti[i] = V[:, i].max()
    d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - anti) ** 2).sum(axis=1))
    cc = d_minus / (d_plus + d_minus + 1e-12)
    return cc


if __name__ == "__main__":
    print("=" * 60)
    print("TOPSIS - Çözüm Alternatifi 1")
    print("=" * 60)

    df = build_criteria_matrix()

    ahp = pd.read_excel(RES / "ahp_weights.xlsx")

    out = df.copy()
    benefit_cols = ["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_Demand"]
    for _, sc in ahp.iterrows():
        w = np.array([sc["w_C1_Damage"], sc["w_C2_Logistics"],
                      sc["w_C3_GapDistance"], sc["w_C4_Demand"]])
        cc = topsis(df, w, benefit_cols=benefit_cols)
        col = f"CC_{sc['scenario']}"
        out[col] = cc
        top3 = out.nlargest(3, col)[["S_No", "Alan_Adi", "Mahalle", col]]
        print(f"\n  Senaryo: {sc['scenario']:24s}  w=[{w[0]:.3f}, {w[1]:.3f}, {w[2]:.3f}, {w[3]:.3f}]")
        for _, r in top3.iterrows():
            adi = str(r['Alan_Adi'])[:40]
            mh = str(r['Mahalle'])[:20]
            print(f"     S{r['S_No']:3d} {adi:40s} ({mh:20s})  CC={r[col]:.4f}")

    out.to_excel(RES / "topsis_sonuclar.xlsx", index=False)
    print(f"\n[OK] {RES / 'topsis_sonuclar.xlsx'}")

# -*- coding: utf-8 -*-
"""
03_fcm_CA3.py
==========================================================
Cozum Alternatifi 3: FCM Gaussian (sigma=800m) - 152 havuz.
==========================================================
Ciktilar:
  - results/mu_pool_CA3.xlsx         (152 site x 17 mahalle)
  - results/mahalle_centroids_CA3.xlsx
  - results/mu_mevcut_zero_CA3.xlsx  (placeholder, 12 satir, hepsi 0)
"""
import math
import unicodedata
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("D:/IE492")
CA3 = ROOT / "cozum_alternatifi_3_full_reloc_sb_yk"
RES = CA3 / "results"
RES.mkdir(parents=True, exist_ok=True)

SIGMA_M = 800.0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def normalize_mahalle(s):
    if s is None: return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u00a0", " ").replace("\u2019", "'")
    s = s.replace(" TEFERRUC TEPE ORMANI", "TEFERRUC TEPE ORMANI")
    s = s.replace(" SALGAMLI DEVLET ORMANI", "SALGAMLI DEVLET ORMANI")
    return " ".join(s.split())

def compute_mu(site_df, centroids, all_mh, sigma=SIGMA_M):
    mu = pd.DataFrame(index=site_df.index)
    for mh in all_mh:
        clat, clon = centroids.get(mh, (None, None))
        if clat is None:
            mu[mh] = 0.0
            continue
        col = []
        for _, r in site_df.iterrows():
            d = haversine(float(r["Enlem"]), float(r["Boylam"]), clat, clon)
            col.append(math.exp(-(d ** 2) / (2 * sigma ** 2)))
        mu[mh] = col
    mu["_TOTAL_mu"] = mu.sum(axis=1)
    return mu

if __name__ == "__main__":
    print("=" * 60)
    print(f"STEP 3: FCM (Cozum Alternatifi 3)  sigma={SIGMA_M}m")
    print("=" * 60)

    pool = pd.read_excel(RES / "pool_152_CA3.xlsx")
    nuf = pd.read_excel(ROOT / "output" / "data" / "mahalle_nufus.xlsx")
    risk = pd.read_excel(ROOT / "output" / "data" / "mahalle_risk.xlsx")

    nuf["_mh_norm"] = nuf["mahalle"].apply(normalize_mahalle)
    risk["_mh_norm"] = risk["mahalle"].apply(normalize_mahalle)
    all_mh = sorted(set(nuf["_mh_norm"].tolist()) | set(risk["_mh_norm"].tolist()))

    centroids = {}
    for mh in all_mh:
        sub = pool[pool["_mh_norm"] == mh]
        if len(sub) > 0:
            centroids[mh] = (float(sub["Enlem"].mean()), float(sub["Boylam"].mean()))
        else:
            centroids[mh] = (None, None)
    mapped = sum(1 for v in centroids.values() if v[0] is not None)
    print(f"Centroids: {mapped}/{len(all_mh)}")

    rows = []
    for mh in all_mh:
        clat, clon = centroids.get(mh, (None, None))
        match = nuf[nuf["_mh_norm"] == mh]
        disp = match["mahalle"].iloc[0] if len(match) > 0 else mh
        nuf_v = int(match["nufus_2024"].iloc[0]) if len(match) > 0 else 0
        risk_match = risk[risk["_mh_norm"] == mh]
        risk_v = float(risk_match["risk_score"].iloc[0]) if len(risk_match) > 0 else 0.0
        rows.append({
            "mahalle_norm": mh, "mahalle_display": disp,
            "enlem": clat, "boylam": clon,
            "nufus_2024": nuf_v, "risk_score": risk_v,
        })
    df_cent = pd.DataFrame(rows)
    df_cent.to_excel(RES / "mahalle_centroids_CA3.xlsx", index=False)
    print(f"[OK] mahalle_centroids_CA3.xlsx")

    pool_id = pool[["S_No", "AYDES_ID", "Alan_Adi", "Mahalle", "Enlem", "Boylam", "_kaynak"]].copy()
    pool_id["_id"] = pool_id["S_No"].astype(str) + " - " + pool_id["Alan_Adi"].astype(str)
    mu_pool = compute_mu(pool_id, centroids, all_mh)
    mu_pool.insert(0, "_id", pool_id["_id"].values)
    mu_pool.insert(1, "S_No", pool_id["S_No"].values)
    mu_pool.insert(2, "Mahalle", pool_id["Mahalle"].values)
    mu_pool.insert(3, "_kaynak", pool_id["_kaynak"].values)
    mu_pool.to_excel(RES / "mu_pool_CA3.xlsx", index=False)
    print(f"[OK] mu_pool_CA3.xlsx  shape={mu_pool.shape}")

    # mu_mevcut_zero: 12 mevcut'un hepsi 0 (artik sabit degil)
    mev_rows = pool[pool["_kaynak"] == "mevcut_12"]
    cols_zero = ["_id"] + all_mh + ["_TOTAL_mu"]
    df_zero = pd.DataFrame(columns=cols_zero)
    for _, r in mev_rows.iterrows():
        row = {"_id": f"M{r['S_No']} - {r['Alan_Adi']}"}
        for mh in all_mh:
            row[mh] = 0.0
        row["_TOTAL_mu"] = 0.0
        df_zero = pd.concat([df_zero, pd.DataFrame([row])], ignore_index=True)
    df_zero.to_excel(RES / "mu_mevcut_zero_CA3.xlsx", index=False)
    print(f"[OK] mu_mevcut_zero_CA3.xlsx  (12 mevcut = 0, artik sabit degil)")

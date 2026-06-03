# -*- coding: utf-8 -*-
"""
03_fcm.py
==========================================================
Cozum Alternatifi 2: FCM Gaussian uyelik matrisi (sigma=800m).
Orijinal FCM ile birebir ayni (FCM sigma=800 sabit).
==========================================================
Ciktilar:
  - results/mu_aday_CA2.xlsx         (140 aday x 17 mahalle)
  - results/mu_mevcut_CA2.xlsx       (12 mevcut x 17 mahalle)
  - results/mahalle_centroids_CA2.xlsx
"""
import math
import unicodedata
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("D:/IE492")
CA2 = ROOT / "cozum_alternatifi_2_road_closure"
RES = CA2 / "results"
RES.mkdir(parents=True, exist_ok=True)

SIGMA_M = 800.0  # walking radius for rescue equipment (sabit)

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
    s = " ".join(s.split())
    return s

def compute_mu(site_df, centroids, all_mh, sigma=SIGMA_M):
    cols_lower = {c.lower(): c for c in site_df.columns}
    lat_col = cols_lower.get("enlem") or "Enlem"
    lon_col = cols_lower.get("boylam") or "Boylam"
    mu = pd.DataFrame(index=site_df.index)
    for mh in all_mh:
        clat, clon = centroids.get(mh, (None, None))
        if clat is None:
            mu[mh] = 0.0
            continue
        col = []
        for _, r in site_df.iterrows():
            d = haversine(float(r[lat_col]), float(r[lon_col]), clat, clon)
            col.append(math.exp(-(d ** 2) / (2 * sigma ** 2)))
        mu[mh] = col
    mu["_TOTAL_mu"] = mu.sum(axis=1)
    return mu

if __name__ == "__main__":
    print("=" * 60)
    print("STEP 3: FCM (Cozum Alternatifi 2)")
    print(f"  sigma = {SIGMA_M} m (sabit)")
    print("=" * 60)

    DATA = ROOT / "output" / "data"
    aday = pd.read_excel(DATA / "adaylar.xlsx")
    mev = pd.read_excel(DATA / "mevcut_12.xlsx")
    nuf = pd.read_excel(DATA / "mahalle_nufus.xlsx")
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")

    aday["_mh_norm"] = aday["Mahalle"].apply(normalize_mahalle)
    nuf["_mh_norm"] = nuf["mahalle"].apply(normalize_mahalle)
    risk["_mh_norm"] = risk["mahalle"].apply(normalize_mahalle)
    all_mh = sorted(set(nuf["_mh_norm"].tolist()) | set(risk["_mh_norm"].tolist()))

    centroids = {}
    for mh in all_mh:
        sub = aday[aday["_mh_norm"] == mh]
        if len(sub) > 0:
            centroids[mh] = (float(sub["Enlem"].mean()), float(sub["Boylam"].mean()))
        else:
            centroids[mh] = (None, None)
    mapped = sum(1 for v in centroids.values() if v[0] is not None)
    print(f"Centroids: {mapped}/{len(all_mh)}")

    # Centroids table
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
    df_cent.to_excel(RES / "mahalle_centroids_CA2.xlsx", index=False)
    print(f"[OK] mahalle_centroids_CA2.xlsx")

    aday_id = aday[["S_No", "AYDES_ID", "Alan_Adi", "Mahalle", "Enlem", "Boylam"]].copy()
    aday_id["_id"] = aday_id["S_No"].astype(str) + " - " + aday_id["Alan_Adi"].astype(str)
    mu_aday = compute_mu(aday_id, centroids, all_mh)
    mu_aday.insert(0, "_id", aday_id["_id"].values)
    mu_aday.insert(1, "S_No", aday_id["S_No"].values)
    mu_aday.insert(2, "Mahalle", aday_id["Mahalle"].values)
    mu_aday.to_excel(RES / "mu_aday_CA2.xlsx", index=False)
    print(f"[OK] mu_aday_CA2.xlsx  shape={mu_aday.shape}")

    mev_id = mev.copy()
    mev_id["_id"] = "M" + mev_id["container_no"].astype(str) + " - " + mev_id["adres"].astype(str)
    mev_id = mev_id.rename(columns={"enlem": "Enlem", "boylam": "Boylam"})
    mu_mev = compute_mu(mev_id, centroids, all_mh)
    mu_mev.insert(0, "_id", mev_id["_id"].values)
    mu_mev.insert(1, "container_no", mev_id["container_no"].values)
    mu_mev.insert(2, "mahalle", mev_id["mahalle"].values)
    mu_mev.to_excel(RES / "mu_mevcut_CA2.xlsx", index=False)
    print(f"[OK] mu_mevcut_CA2.xlsx  shape={mu_mev.shape}")

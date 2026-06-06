"""
CA8b - FCM Adaptive Sigma
17 mahalle iki kategoriye ayrilir:
  - Kentsel (nufus_2024 >= 18000): sigma = 600m (keskin)
  - Yesil/dusuk yogunluk: sigma = 1200m (genis)
mu(mahalle_i, site_j) = exp(-d^2 / (2*sigma_i^2))

Akademik dayanak: Current & O'Kelly (2011) IJGIS
"""
import os
import math
import pandas as pd
import numpy as np

ROOT = "D:/IE492"
CA = "cozum_alternatifi_8b_fcm_adaptive_sigma"
DATA = os.path.join(ROOT, CA, "data")

KENTSEL_POP_THRESHOLD = 18000
SIGMA_KENTSEL = 600.0
SIGMA_OTHERS = 1200.0

MAHALLE_KEYS_FOREST = ("ORMAN", "FOREST", "PARK")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def main():
    aday = pd.read_excel(os.path.join(DATA, "adaylar.xlsx"))
    mev = pd.read_excel(os.path.join(DATA, "mevcut_12.xlsx"))
    nuf = pd.read_excel(os.path.join(DATA, "mahalle_nufus.xlsx"))
    centroids = pd.read_excel(os.path.join(DATA, "mahalle_centroids.xlsx"))

    cat = {}
    for _, r in centroids.iterrows():
        m = str(r["mahalle_norm"]).strip().upper()
        pop = float(r.get("nufus_2024", 0) or 0)
        is_forest = any(k in m for k in MAHALLE_KEYS_FOREST)
        if is_forest or pop < KENTSEL_POP_THRESHOLD:
            cat[m] = SIGMA_OTHERS
        else:
            cat[m] = SIGMA_KENTSEL

    aday_id = aday[["S_No", "AYDES_ID", "Alan_Adi", "Mahalle", "Enlem", "Boylam"]].copy()
    aday_id["_id"] = aday_id["S_No"].astype(str) + " - " + aday_id["Alan_Adi"].astype(str)
    aday_id["_mh_norm"] = aday_id["Mahalle"].str.strip().str.upper()

    mahalleler = list(centroids["mahalle_norm"].astype(str).str.strip().str.upper())
    skip = {"_id", "S_No", "container_no", "Mahalle", "mahalle", "_TOTAL_mu", "_mh_norm"}
    cols = [m for m in mahalleler]

    mu_aday = pd.DataFrame()
    mu_aday["_id"] = aday_id["_id"].values
    mu_aday["S_No"] = aday_id["S_No"].values
    mu_aday["Mahalle"] = aday_id["Mahalle"].values

    n_total = 0
    for _, cr in centroids.iterrows():
        m = str(cr["mahalle_norm"]).strip().upper()
        clat = float(cr["enlem"]) if pd.notna(cr["enlem"]) else None
        clon = float(cr["boylam"]) if pd.notna(cr["boylam"]) else None
        sig = cat.get(m, SIGMA_OTHERS)
        col = []
        for _, r in aday_id.iterrows():
            if clat is None or clon is None:
                col.append(0.0)
                continue
            d = haversine(float(r["Enlem"]), float(r["Boylam"]), clat, clon)
            col.append(math.exp(-(d ** 2) / (2 * sig ** 2)))
        mu_aday[m] = col
        n_total += 1
    mu_aday["_TOTAL_mu"] = mu_aday[cols].sum(axis=1)
    mu_aday.to_excel(os.path.join(DATA, "mu_aday_adaptive.xlsx"), index=False)

    mev_id = mev.copy()
    mev_id["_id"] = "M" + mev_id["container_no"].astype(str) + " - " + mev_id["adres"].astype(str)
    mev_id = mev_id.rename(columns={"enlem": "Enlem", "boylam": "Boylam"})
    mu_mev = pd.DataFrame()
    mu_mev["_id"] = mev_id["_id"].values
    mu_mev["container_no"] = mev_id["container_no"].values
    mu_mev["mahalle"] = mev_id["mahalle"].values
    for _, cr in centroids.iterrows():
        m = str(cr["mahalle_norm"]).strip().upper()
        clat = float(cr["enlem"]) if pd.notna(cr["enlem"]) else None
        clon = float(cr["boylam"]) if pd.notna(cr["boylam"]) else None
        sig = cat.get(m, SIGMA_OTHERS)
        col = []
        for _, r in mev_id.iterrows():
            if clat is None or clon is None or pd.isna(r["Enlem"]) or pd.isna(r["Boylam"]):
                col.append(0.0)
                continue
            d = haversine(float(r["Enlem"]), float(r["Boylam"]), clat, clon)
            col.append(math.exp(-(d ** 2) / (2 * sig ** 2)))
        mu_mev[m] = col
    mu_mev["_TOTAL_mu"] = mu_mev[cols].sum(axis=1)
    mu_mev.to_excel(os.path.join(DATA, "mu_mevcut_adaptive.xlsx"), index=False)

    cat_log = pd.DataFrame([
        {"mahalle": m, "sigma_m": s, "kategori": "kentsel" if s == SIGMA_KENTSEL else "yesil/dusuk"}
        for m, s in cat.items()
    ])
    cat_log.to_excel(os.path.join(DATA, "sigma_kategori.xlsx"), index=False)
    print(f"[OK] mu_aday_adaptive.xlsx shape={mu_aday.shape}")
    print(f"[OK] mu_mevcut_adaptive.xlsx shape={mu_mev.shape}")
    print(f"[OK] sigma_kategori.xlsx (n={len(cat)} mahalle)")
    print(f"  Kentsel (600m): {sum(1 for s in cat.values() if s == SIGMA_KENTSEL)}")
    print(f"  Yesil/dusuk (1200m): {sum(1 for s in cat.values() if s == SIGMA_OTHERS)}")
    print(f"  Esik: pop >= {KENTSEL_POP_THRESHOLD} -> kentsel")


if __name__ == "__main__":
    main()

"""
CA8c - Two-Tier FCM (kaskad)
Tier 1: sigma=800m, tum 140x17 (genis tarama)
Tier 2: Her site icin en yuksek Tier 1 mu'ya sahip top %20 mahallede (~3 mahalle) sigma=300m
Final mu = mu_tier1 + 0.5*mu_tier2 (sinir 1.0)

Akademik dayanak: Teich et al. (2005) "Hierarchical facility location", EJOR
"""
import os
import math
import pandas as pd
import numpy as np

ROOT = "D:/IE492"
CA = "cozum_alternatifi_8c_fcm_two_tier"
DATA = os.path.join(ROOT, CA, "data")

SIGMA_TIER1 = 800.0
SIGMA_TIER2 = 300.0
TIER2_FRACTION = 0.20
TIER2_BONUS = 0.5


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def compute_tier_matrix(site_df, centroids, sigma):
    cols = [str(m).strip().upper() for m in centroids["mahalle_norm"]]
    M = pd.DataFrame(index=site_df.index, columns=cols, dtype=float)
    for _, cr in centroids.iterrows():
        m = str(cr["mahalle_norm"]).strip().upper()
        clat = float(cr["enlem"]) if pd.notna(cr["enlem"]) else None
        clon = float(cr["boylam"]) if pd.notna(cr["boylam"]) else None
        if clat is None:
            M[m] = 0.0
            continue
        vals = []
        for _, r in site_df.iterrows():
            lat = float(r["__lat"]) if pd.notna(r["__lat"]) else None
            lon = float(r["__lon"]) if pd.notna(r["__lon"]) else None
            if lat is None or lon is None:
                vals.append(0.0)
                continue
            d = haversine(lat, lon, clat, clon)
            vals.append(math.exp(-(d ** 2) / (2 * sigma ** 2)))
        M[m] = vals
    return M


def main():
    aday = pd.read_excel(os.path.join(DATA, "adaylar.xlsx"))
    mev = pd.read_excel(os.path.join(DATA, "mevcut_12.xlsx"))
    centroids = pd.read_excel(os.path.join(DATA, "mahalle_centroids.xlsx"))

    aday_id = aday[["S_No", "AYDES_ID", "Alan_Adi", "Mahalle", "Enlem", "Boylam"]].copy()
    aday_id["_id"] = aday_id["S_No"].astype(str) + " - " + aday_id["Alan_Adi"].astype(str)
    aday_id["__lat"] = aday_id["Enlem"]
    aday_id["__lon"] = aday_id["Boylam"]

    tier1 = compute_tier_matrix(aday_id, centroids, SIGMA_TIER1)
    tier2 = compute_tier_matrix(aday_id, centroids, SIGMA_TIER2)

    n_tier2_cols = max(1, int(round(tier1.shape[1] * TIER2_FRACTION)))
    print(f"  Tier 1: sigma={SIGMA_TIER1}m, full {tier1.shape[1]} mahalle")
    print(f"  Tier 2: sigma={SIGMA_TIER2}m, top {n_tier2_cols} mahalle per site (={100*TIER2_FRACTION:.0f}%)")
    print(f"  Bonus: mu_final = mu_tier1 + {TIER2_BONUS} * mu_tier2, cap=1.0")

    tier2_kept = pd.DataFrame(0.0, index=tier2.index, columns=tier2.columns)
    for i in tier1.index:
        ranked = tier1.loc[i].sort_values(ascending=False)
        top_cols = ranked.head(n_tier2_cols).index
        tier2_kept.loc[i, top_cols] = tier2.loc[i, top_cols]

    final = (tier1 + TIER2_BONUS * tier2_kept).clip(upper=1.0)

    mu_aday = pd.DataFrame()
    mu_aday["_id"] = aday_id["_id"].values
    mu_aday["S_No"] = aday_id["S_No"].values
    mu_aday["Mahalle"] = aday_id["Mahalle"].values
    for c in final.columns:
        mu_aday[c] = final[c].values
    skip = {"_id", "S_No", "Mahalle", "mahalle", "container_no", "_TOTAL_mu"}
    mahalle_cols = [c for c in mu_aday.columns if c not in skip]
    mu_aday["_TOTAL_mu"] = mu_aday[mahalle_cols].sum(axis=1)
    mu_aday.to_excel(os.path.join(DATA, "mu_aday_two_tier.xlsx"), index=False)

    mev_id = mev.copy()
    mev_id["_id"] = "M" + mev_id["container_no"].astype(str) + " - " + mev_id["adres"].astype(str)
    mev_id = mev_id.rename(columns={"enlem": "Enlem", "boylam": "Boylam"})
    mev_id["__lat"] = mev_id["Enlem"]
    mev_id["__lon"] = mev_id["Boylam"]
    tier1_m = compute_tier_matrix(mev_id, centroids, SIGMA_TIER1)
    tier2_m = compute_tier_matrix(mev_id, centroids, SIGMA_TIER2)
    tier2_kept_m = pd.DataFrame(0.0, index=tier2_m.index, columns=tier2_m.columns)
    for i in tier1_m.index:
        ranked = tier1_m.loc[i].sort_values(ascending=False)
        top_cols = ranked.head(n_tier2_cols).index
        tier2_kept_m.loc[i, top_cols] = tier2_m.loc[i, top_cols]
    final_m = (tier1_m + TIER2_BONUS * tier2_kept_m).clip(upper=1.0)
    mu_mev = pd.DataFrame()
    mu_mev["_id"] = mev_id["_id"].values
    mu_mev["container_no"] = mev_id["container_no"].values
    mu_mev["mahalle"] = mev_id["mahalle"].values
    for c in final_m.columns:
        mu_mev[c] = final_m[c].values
    mu_mev["_TOTAL_mu"] = mu_mev[mahalle_cols].sum(axis=1)
    mu_mev.to_excel(os.path.join(DATA, "mu_mevcut_two_tier.xlsx"), index=False)

    print(f"[OK] mu_aday_two_tier.xlsx shape={mu_aday.shape}")
    print(f"[OK] mu_mevcut_two_tier.xlsx shape={mu_mev.shape}")


if __name__ == "__main__":
    main()

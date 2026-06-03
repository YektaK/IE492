"""
03_fcm.py
Step 3: Compute FCM Gaussian membership mu(i,j) for all 141 candidates + 12 existing
         containers relative to 17 mahalle centroids (sigma=800m, rescue equipment).

Output:
  output/results/mu_aday.xlsx      (140 candidates x 17 mahalle, plus row sum)
  output/results/mu_mevcut.xlsx    (12 existing x 17 mahalle)
  output/results/mahalle_centroids.xlsx  (17 mahalle with lat/lon)
"""
import math
import numpy as np
import pandas as pd
from pathlib import Path
import unicodedata

ROOT = Path(r"D:\IE492")
DATA = ROOT / "output" / "data"
RES = ROOT / "output" / "results"
RES.mkdir(parents=True, exist_ok=True)

SIGMA_M = 800.0  # meters, walking radius for rescue equipment


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def normalize_mahalle(s):
    """Normalize mahalle name to compare across data sources safely."""
    if s is None:
        return ""
    s = str(s).strip().upper()
    # Normalize Turkish chars to ASCII for cross-dataset matching
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u00a0", " ").replace("\u2019", "'")
    s = " ".join(s.split())
    return s


def build_centroids(aday, nuf, risk):
    """
    Build mahalle centroids using candidates that belong to that mahalle.
    Falls back to Aydos Kalesi (well-known Sultanbeyli landmark) for unmapped.
    """
    aday["_mh_norm"] = aday["Mahalle"].apply(normalize_mahalle)
    nuf["_mh_norm"] = nuf["mahalle"].apply(normalize_mahalle)
    risk["_mh_norm"] = risk["mahalle"].apply(normalize_mahalle)

    # All mahalle names (normalized) from nuf and risk
    all_mh = sorted(set(nuf["_mh_norm"].tolist()) | set(risk["_mh_norm"].tolist()))

    centroids = {}
    for mh in all_mh:
        sub = aday[aday["_mh_norm"] == mh]
        if len(sub) > 0:
            centroids[mh] = (float(sub["Enlem"].mean()), float(sub["Boylam"].mean()))
        else:
            centroids[mh] = (None, None)

    return all_mh, centroids, aday, nuf, risk


def compute_mu(site_df, centroids, all_mh, sigma=SIGMA_M):
    """site_df: rows with 'Enlem', 'Boylam' (or 'enlem'/'boylam'). Returns DataFrame mu[site_id, mh]."""
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
            # Gaussian membership: 1 at centroid, drops to ~0.61 at sigma, ~0.13 at 2*sigma
            col.append(math.exp(-(d ** 2) / (2 * sigma ** 2)))
        mu[mh] = col
    # Row sums: total coverage a site provides
    mu["_TOTAL_mu"] = mu.sum(axis=1)
    return mu


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 3: FCM (Fuzzy C-Means membership)")
    print(f"  sigma = {SIGMA_M} m")
    print("=" * 60)

    aday = pd.read_excel(DATA / "adaylar.xlsx")
    mev = pd.read_excel(DATA / "mevcut_12.xlsx")
    nuf = pd.read_excel(DATA / "mahalle_nufus.xlsx")
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")

    all_mh, centroids, aday, nuf, risk = build_centroids(aday, nuf, risk)
    print(f"Mahalle list (normalized): {all_mh}")
    mapped = sum(1 for v in centroids.values() if v[0] is not None)
    print(f"Centroids computed: {mapped}/{len(all_mh)}")

    # 3.1 Mahalle centroids table
    rows = []
    for mh in all_mh:
        clat, clon = centroids.get(mh, (None, None))
        # Get original (display) name from nuf
        match = nuf[nuf["_mh_norm"] == mh]
        disp = match["mahalle"].iloc[0] if len(match) > 0 else mh
        nuf_v = int(match["nufus_2024"].iloc[0]) if len(match) > 0 else 0
        risk_match = risk[risk["_mh_norm"] == mh]
        risk_v = float(risk_match["risk_score"].iloc[0]) if len(risk_match) > 0 else 0.0
        rows.append({
            "mahalle_norm": mh,
            "mahalle_display": disp,
            "enlem": clat,
            "boylam": clon,
            "nufus_2024": nuf_v,
            "risk_score": risk_v,
        })
    df_cent = pd.DataFrame(rows)
    df_cent.to_excel(RES / "mahalle_centroids.xlsx", index=False)
    print(f"[OK] mahalle_centroids.xlsx")

    # 3.2 mu matrix for 140 candidates
    aday_id = aday[["S_No", "AYDES_ID", "Alan_Adi", "Mahalle", "Enlem", "Boylam"]].copy()
    aday_id["_id"] = aday_id["S_No"].astype(str) + " - " + aday_id["Alan_Adi"].astype(str)
    mu_aday = compute_mu(aday_id, centroids, all_mh)
    mu_aday.insert(0, "_id", aday_id["_id"].values)
    mu_aday.insert(1, "S_No", aday_id["S_No"].values)
    mu_aday.insert(2, "Mahalle", aday_id["Mahalle"].values)
    mu_aday.to_excel(RES / "mu_aday.xlsx", index=False)
    print(f"[OK] mu_aday.xlsx  shape={mu_aday.shape}")

    # 3.3 mu matrix for 12 existing
    mev_id = mev.copy()
    mev_id["_id"] = "M" + mev_id["container_no"].astype(str) + " - " + mev_id["adres"].astype(str)
    mev_id = mev_id.rename(columns={"enlem": "Enlem", "boylam": "Boylam"})
    mu_mev = compute_mu(mev_id, centroids, all_mh)
    mu_mev.insert(0, "_id", mev_id["_id"].values)
    mu_mev.insert(1, "container_no", mev_id["container_no"].values)
    mu_mev.insert(2, "mahalle", mev_id["mahalle"].values)
    mu_mev.to_excel(RES / "mu_mevcut.xlsx", index=False)
    print(f"[OK] mu_mevcut.xlsx  shape={mu_mev.shape}")

    # 3.4 Quick sanity: show top-5 candidate mu for Abdurrahmangazi
    ab_n = normalize_mahalle("ABDURRAHMANGAZI")
    if ab_n in mu_aday.columns:
        top5 = mu_aday.nlargest(5, ab_n)[["_id", ab_n, "_TOTAL_mu"]]
        print(f"\nTop-5 candidates serving ABDURRAHMANGAZI (sigma={SIGMA_M}m):")
        for _, r in top5.iterrows():
            print(f"  {r['_id'][:55]:55s}  mu={r[ab_n]:.4f}  total={r['_TOTAL_mu']:.3f}")

    print("Done.")

"""
02_ahp_topsis.py
Step 2: Compute criteria matrix, AHP weights (3 scenarios), TOPSIS scores.

Outputs:
  output/results/criteria_matrix.xlsx     (141 candidates x 4 criteria + scores)
  output/results/ahp_weights.xlsx         (3 scenarios, weights + CR)
  output/results/topsis_sonuclar.xlsx     (141 ranked under 3 scenarios)
  output/results/topsis_top20.png         (top-20 bar chart)
"""
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(r"D:\IE492")
DATA = ROOT / "output" / "data"
RES = ROOT / "output" / "results"
FIG = ROOT / "output" / "figures"
RES.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)


# Haversine distance (meters) between two (lat, lon) points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


# ---------------------------------------------------------------------------
# AHP Saaty pairwise -> weights + CR
# ---------------------------------------------------------------------------
def ahp_weights(pairwise):
    """
    pairwise: n x n numpy matrix (Saaty 1-9 scale)
    returns: w (priority vector), lambda_max, CI, CR
    """
    A = np.array(pairwise, dtype=float)
    n = A.shape[0]
    # Eigenvector of largest eigenvalue
    eigvals, eigvecs = np.linalg.eig(A)
    # Largest real eigenvalue
    real_eigs = np.real(eigvals)
    idx = np.argmax(real_eigs)
    lambda_max = real_eigs[idx]
    v = np.real(eigvecs[:, idx])
    # Normalize to positive sum-1
    v = np.abs(v)
    w = v / v.sum()
    # CI = (lambda_max - n) / (n - 1)
    CI = (lambda_max - n) / (n - 1)
    # Random Index for n=4 is 0.90 (Saaty 1980)
    RI_table = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
                6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    RI = RI_table.get(n, 1.49)
    CR = CI / RI if RI > 0 else 0.0
    return w, float(lambda_max), float(CI), float(CR)


# 3 AHP scenarios (4 criteria: C1 Damage, C2 Logistics, C3 Gap, C4 NightPop)
AHPS = {
    "Baseline": [
        #        C1    C2    C3    C4
        [1,     3,    5,    4],   # C1
        [1/3,   1,    3,    3],   # C2
        [1/5, 1/3,    1,    2],   # C3
        [1/4, 1/3,  1/2,    1],   # C4
    ],
    "DamageFocused": [
        # Higher weight on damage (rescue equipment focus)
        [1,     5,    7,    6],
        [1/5,   1,    3,    3],
        [1/7, 1/3,    1,    2],
        [1/6, 1/3,  1/2,    1],
    ],
    "InfrastructureFocused": [
        # Higher weight on logistics
        [1,     1,    5,    4],
        [1,     1,    5,    4],
        [1/5, 1/5,    1,    2],
        [1/4, 1/4,  1/2,    1],
    ],
}


# ---------------------------------------------------------------------------
# Build criteria matrix for all 141 candidates
# ---------------------------------------------------------------------------
def build_criteria_matrix():
    import unicodedata
    aday = pd.read_excel(DATA / "adaylar.xlsx")
    mev = pd.read_excel(DATA / "mevcut_12.xlsx")
    nuf = pd.read_excel(DATA / "mahalle_nufus.xlsx")
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")

    def norm(s):
        s = str(s).strip().upper()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))
        return " ".join(s.split())

    aday["_mh"] = aday["Mahalle"].apply(norm)
    nuf["_mh"] = nuf["mahalle"].apply(norm)
    risk["_mh"] = risk["mahalle"].apply(norm)

    # Mahalle centroids (for FCM later too)
    mahalle_list = sorted(set(nuf["_mh"].tolist()) | set(risk["_mh"].tolist()))
    centroids = {}
    for mh in mahalle_list:
        sub = aday[aday["_mh"] == mh]
        if len(sub) > 0:
            centroids[mh] = (float(sub["Enlem"].mean()), float(sub["Boylam"].mean()))
        else:
            centroids[mh] = (None, None)

    # Existing 12: pre-compute distance to each candidate (for C3)
    mev_coords = mev[["enlem", "boylam"]].values

    # C1: damage score = risk score of the mahalle the candidate belongs to (using normalized key)
    risk_map = risk.set_index("_mh")["risk_score"].to_dict()
    nuf_map = nuf.set_index("_mh")["nufus_2024"].to_dict()

    # For each candidate compute criteria
    rows = []
    for _, r in aday.iterrows():
        mh = r["_mh"]
        lat, lon = float(r["Enlem"]), float(r["Boylam"])

        # C1: damage score (uses mahalle risk)
        c1 = float(risk_map.get(mh, 0.0))

        # C2: logistics infrastructure (0-1, mean of binary flags)
        c2 = (r["Su_bin"] + r["WC_bin"] + r["Jen_bin"]) / 3.0

        # C3: distance to nearest existing container (m) -> higher = better (gap)
        # We want LARGER c3 = better (fills a gap). So c3 = min distance.
        min_d = float("inf")
        for mlat, mlon in mev_coords:
            d = haversine(lat, lon, mlat, mlon)
            if d < min_d:
                min_d = d
        c3 = min_d

        # C4: night population (proxy = total mahalle population)
        c4 = float(nuf_map.get(mh, 0))

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
        })

    df = pd.DataFrame(rows)
    df.to_excel(RES / "criteria_matrix.xlsx", index=False)
    print(f"[OK] criteria_matrix.xlsx  rows={len(df)}")
    return df, centroids, mahalle_list


# ---------------------------------------------------------------------------
# TOPSIS
# ---------------------------------------------------------------------------
def topsis(df, weights, benefit_cols, cost_cols=None):
    """
    Standard TOPSIS:
      1) vector-normalize
      2) weight
      3) ideal (+) and anti-ideal (-)
      4) Euclidean distance
      5) CCi = d- / (d+ + d-)
    benefit_cols: criteria where MORE is better
    cost_cols: criteria where LESS is better
    """
    cost_cols = cost_cols or []
    M = df[["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_NightPop"]].values.astype(float)
    n, m = M.shape
    # Vector normalize
    norms = np.sqrt((M ** 2).sum(axis=0))
    norms[norms == 0] = 1
    N = M / norms
    # Weighted
    V = N * weights
    # Ideal/anti-ideal
    ideal = np.zeros(m)
    anti = np.zeros(m)
    cols = ["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_NightPop"]
    for i, c in enumerate(cols):
        if c in benefit_cols:
            ideal[i] = V[:, i].max()
            anti[i] = V[:, i].min()
        else:  # cost
            ideal[i] = V[:, i].min()
            anti[i] = V[:, i].max()
    # Distances
    d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - anti) ** 2).sum(axis=1))
    cc = d_minus / (d_plus + d_minus + 1e-12)
    return cc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("STEP 2: AHP + TOPSIS")
    print("=" * 60)

    # 2.1 Criteria matrix
    df, centroids, mahalle_list = build_criteria_matrix()
    print(f"     Mahalle centroids: {sum(1 for v in centroids.values() if v[0] is not None)}/{len(mahalle_list)}")

    # 2.2 AHP weights for 3 scenarios
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
            "lambda_max": lm,
            "CI": ci,
            "CR": cr,
            "CR_acceptable": "YES" if cr < 0.10 else "NO",
        })
        print(f"  {name:24s}  w=[{w[0]:.3f}, {w[1]:.3f}, {w[2]:.3f}, {w[3]:.3f}]  CR={cr:.4f} ({'OK' if cr<0.10 else 'REVIEW'})")

    df_ahp = pd.DataFrame(ahp_results)
    df_ahp.to_excel(RES / "ahp_weights.xlsx", index=False)
    print(f"[OK] ahp_weights.xlsx")

    # 2.3 TOPSIS per scenario
    print("\n--- TOPSIS scores ---")
    benefit_cols = ["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_NightPop"]
    out = df.copy()
    for sc in ahp_results:
        w = np.array([sc["w_C1_Damage"], sc["w_C2_Logistics"],
                      sc["w_C3_GapDistance"], sc["w_C4_NightPop"]])
        cc = topsis(df, w, benefit_cols=benefit_cols)
        col = f"CC_{sc['scenario']}"
        out[col] = cc
        top3 = out.nlargest(3, col)[["Alan_Adi", "Mahalle", col]]
        print(f"  {sc['scenario']:24s}  Top 3:")
        for _, r in top3.iterrows():
            adi = str(r['Alan_Adi'])[:40]
            mh = str(r['Mahalle'])[:20]
            val = float(r[col])
            print(f"     {adi:40s} ({mh:20s})  CC={val:.4f}")

    out.to_excel(RES / "topsis_sonuclar.xlsx", index=False)
    print(f"[OK] topsis_sonuclar.xlsx")

    # 2.4 Top-20 bar chart (baseline scenario)
    top20 = out.nlargest(20, "CC_Baseline")
    plt.figure(figsize=(12, 7))
    y = np.arange(len(top20))
    plt.barh(y, top20["CC_Baseline"], color="steelblue")
    plt.yticks(y, [f"{r['S_No']}. {r['Alan_Adi'][:35]}" for _, r in top20.iterrows()], fontsize=8)
    plt.gca().invert_yaxis()
    plt.xlabel("CC (Relative Closeness to Ideal)")
    plt.title("Top-20 Candidate Container Sites - TOPSIS Baseline Scenario")
    plt.tight_layout()
    plt.savefig(FIG / "topsis_top20.png", dpi=150)
    plt.close()
    print(f"[OK] topsis_top20.png")

    print("Done.")

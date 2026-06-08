# -*- coding: utf-8 -*-
"""
12_sigma_grid.py
FCM sigma duyarliligi: sigma = 400, 600, 800, 1000, 1200 m icin
mu matrislerini yeniden hesapla ve IP'yi her sigma'da kos.
RxC'nin sigma'ya gore degisimini raporla.
"""

from __future__ import annotations
import sys
import math
from pathlib import Path
import pandas as pd
import numpy as np
import pulp
from config import logger
from solver_core import get_solver

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
RES  = ROOT / "results"
OUT  = ROOT / "results" / "sigma_grid"
OUT.mkdir(parents=True, exist_ok=True)

K = 8
BETA = 0.30
SIGMAS = [400, 600, 800, 1000, 1200]


def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def compute_mu(coords_a, coords_b, sigma):
    """coords_a: [(lat,lon)], coords_b: [(lat,lon)]; mu[a,b] = exp(-d^2/(2s^2))"""
    n, m = len(coords_a), len(coords_b)
    mu = np.zeros((n, m))
    for i, (la1, lo1) in enumerate(coords_a):
        for j, (la2, lo2) in enumerate(coords_b):
            d = haversine(la1, lo1, la2, lo2)
            mu[i, j] = math.exp(-(d ** 2) / (2 * sigma ** 2))
    return mu


def main():
    logger.info("== 12_sigma_grid.py basladi ==")
    aday = pd.read_excel(DATA / "adaylar_140.xlsx")
    mev = pd.read_excel(DATA / "mevcut_12.xlsx")
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
    cc = pd.read_excel(RES / "mcdm" / "topsis_cc.xlsx")

    # Mahalle centroids (mevcut koordinatlarin mahalle ortalamasi)
    mev_geo = mev[["enlem", "boylam", "mahalle"]].copy()
    mev_centroids = mev_geo.groupby("mahalle")[["enlem", "boylam"]].mean().reset_index()
    # Aday olmayan mahalleler icin de aday parsel ortalamasi fallback
    aday_geo = aday[["Enlem", "Boylam", "Mahalle"]].copy()
    aday_centroids = aday_geo.groupby("Mahalle")[["Enlem", "Boylam"]].mean().reset_index()
    aday_centroids.columns = ["mahalle", "enlem", "boylam"]
    # Birlestir, once mevcut, sonra aday
    all_centroids = pd.concat([mev_centroids, aday_centroids]).drop_duplicates("mahalle", keep="first").reset_index(drop=True)

    mahalleler = list(all_centroids["mahalle"])
    m_coords = list(zip(all_centroids["enlem"], all_centroids["boylam"]))
    a_coords = list(zip(aday["Enlem"], aday["Boylam"]))
    mev_coords = list(zip(mev["enlem"], mev["boylam"]))
    n = len(aday)

    R = {row["mahalle"]: float(row["risk_score"]) for _, row in risk.iterrows()}
    Q = {int(cc.iloc[j]["S_No"]): float(cc.iloc[j]["CC_Baseline_MinMax"])
         for j in range(len(cc))}
    P_acc = {int(aday.iloc[j]["S_No"]): float(aday.iloc[j]["p_access_road"])
             for j in range(n)}

    rows = []
    secilen_by_sigma = {}

    for sigma in SIGMAS:
        mu_aday = compute_mu(a_coords, m_coords, sigma)
        mu_mev = compute_mu(mev_coords, m_coords, sigma)
        mu_mev_sum = mu_mev.sum(axis=0)  # (n_mahalle,)

        # IP
        prob = pulp.LpProblem(f"IP_s{sigma}", pulp.LpMaximize)
        x = [pulp.LpVariable(f"x{j}", cat="Binary") for j in range(n)]
        # Amac
        terms = []
        for mi, mh in enumerate(mahalleler):
            if mh not in R:
                continue
            cov = mu_mev_sum[mi] + pulp.lpSum(mu_aday[j, mi] * P_acc[int(aday.iloc[j]["S_No"])] * x[j] for j in range(n))
            terms.append(R[mh] * cov)
        prob += pulp.lpSum(terms) + BETA * pulp.lpSum(
            Q[int(aday.iloc[j]["S_No"])] * x[j] for j in range(n))
        prob += pulp.lpSum(x) == K
        for mi, mh in enumerate(mahalleler):
            if mh not in R:
                continue
            prob += (pulp.lpSum(mu_aday[j, mi] * x[j] for j in range(n))
                     + mu_mev_sum[mi] >= 0.50, f"cov_{mh}")

        solver = get_solver(time_limit=30, msg=0)
        prob.solve(solver)
        status = pulp.LpStatus[prob.status]
        rxc = sum(R[mh] * (mu_mev_sum[mi] + sum(
            mu_aday[j, mi] * P_acc[int(aday.iloc[j]["S_No"])] * (x[j].value() or 0)
            for j in range(n)))
            for mi, mh in enumerate(mahalleler) if mh in R)
        secilen = sorted([int(aday.iloc[j]["S_No"]) for j in range(n)
                          if (x[j].value() or 0) > 0.5])
        secilen_by_sigma[sigma] = secilen
        rows.append({
            "sigma_m": sigma, "status": status,
            "RxC": round(rxc, 4),
            "n_secilen": len(secilen),
            "secilen": ",".join(map(str, secilen))
        })
        logger.info(f"  sigma={sigma}m: status={status}, RxC={rxc:.4f}, secilen={secilen}")

    out_df = pd.DataFrame(rows)
    out_path = OUT / "sigma_grid_results.xlsx"
    out_df.to_excel(out_path, index=False)
    logger.info(f"\n  -> {out_path}")

    # Sigma duyarliligi ozeti
    rxc_values = out_df["RxC"].values
    rxc_min, rxc_max = rxc_values.min(), rxc_values.max()
    logger.info(f"\n  RxC aralik: [{rxc_min:.4f}, {rxc_max:.4f}]")
    logger.info(f"  Duyarlilik: {(rxc_max - rxc_min) / rxc_max * 100:.2f}%")

    # Site tutarliligi
    sigma_800 = set(secilen_by_sigma[800])
    for s in SIGMAS:
        if s == 800:
            continue
        diff = set(secilen_by_sigma[s]) ^ sigma_800
        logger.info(f"  sigma={s} vs 800: {len(diff)} site farkli -> {diff}")

    logger.info("== 12_sigma_grid.py tamamlandi ==")


if __name__ == "__main__":
    main()

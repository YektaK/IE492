# -*- coding: utf-8 -*-
"""
08_lscp.py
LSCP (Location Set Covering Problem) - minimum K ile tum mahalleleri
kapsayacak konteyner sayisini bul. Referans deger olarak raporlanir.

Girdi : 04_fuzzy_coverage.py ciktilari (mu_aday, mu_mevcut)
Cikti : results/lscp/lscp_result_S{scenario}.xlsx
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pulp

# Central Config & Solver Core import
from config import logger
from solver_core import get_solver

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenario_utils import load_q_vector, fuzzy_coverage_paths

ROOT = Path(__file__).resolve().parent.parent
RES  = ROOT / "results"
OUT  = ROOT / "results" / "lscp"
OUT.mkdir(parents=True, exist_ok=True)

CRITICAL_MU = 0.50


def load_mu(sigma: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    paths = fuzzy_coverage_paths(sigma)
    mev = pd.read_excel(paths["mu_mevcut"])
    aday = pd.read_excel(paths["mu_aday"])
    return mev, aday


def get_covered_pairs(aday_mu: pd.DataFrame, threshold: float) -> set:
    """Her (aday, mahalle) icin mu >= threshold olan ciftleri dondur."""
    pairs = set()
    for _, row in aday_mu.iterrows():
        for mh in aday_mu.columns[1:]:
            if row[mh] >= threshold:
                pairs.add((int(row["S_No"]), mh))
    return pairs


def solve_lscp(aday_mu: pd.DataFrame, mev_cov: dict[str, float],
               Q_i_dict: dict[str, float] | None = None,
               K_min: int = 1, K_max: int = 30) -> dict:
    """
    Min K bul: en fazla K_max aday sec, her mahallenin toplam mu'su
    >= threshold (mevcut mu dahil).
    """
    n = len(aday_mu)
    j_range = range(n)
    mahalleler = list(aday_mu.columns[1:])

    # Aday bazinda (j, mh) -> mu matrisi
    MU = {}
    for i, row in aday_mu.iterrows():
        for mh in mahalleler:
            MU[(int(row["S_No"]), mh)] = float(row[mh])

    # K araligini tara, en kucuk cozulebilir K'yi bul
    results = []
    for K in range(K_min, K_max + 1):
        prob = pulp.LpProblem(f"LSCP_K{K}", pulp.LpMinimize)
        x = [pulp.LpVariable(f"x{j}", cat="Binary") for j in j_range]
        prob += pulp.lpSum(x)

        for mh in mahalleler:
            qi = Q_i_dict.get(mh, 1.0) if Q_i_dict else 1.0
            base = mev_cov.get(mh, 0.0)
            prob += (
                qi * (pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] * x[j]
                                for j in j_range) + base) >= CRITICAL_MU,
                f"cov_{mh}"
            )
        prob += pulp.lpSum(x) == K, "tam_K"

        solver = get_solver(time_limit=30, msg=0)
        status = prob.solve(solver)
        st = pulp.LpStatus[status]
        results.append({"K": K, "status": st})

        if st == "Optimal":
            secilen = [int(aday_mu.iloc[j]["S_No"])
                       for j in j_range if x[j].value() and x[j].value() > 0.5]
            return {
                "K_min": K, "status": st,
                "secilen_adaylar": secilen,
                "tarama": results
            }

    return {"K_min": None, "status": "Infeasible",
            "secilen_adaylar": [], "tarama": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="A", choices=["A", "B"])
    parser.add_argument("--sigma", type=str, default="800",
                        help="Kapsama sigma modu: 800, Adaptive veya RoadNetwork")
    parser.add_argument("--K", type=int, default=1,
                        help="Minimum kapsanacak mahalle sayisi (varsayilan: 1)")
    parser.add_argument("--truncate", type=float, default=0.0,
                        help="Mu esik degeri: altindaki mu'ler sifirlanir (0=kapali)")
    parser.add_argument("--no-mevcut", action="store_true",
                        help="Mevcut konteynerleri yok say (tam relocation)")
    args = parser.parse_args()
    SCENARIO = args.scenario
    SIGMA = args.sigma
    K_MIN = args.K
    TRUNCATE = args.truncate
    NO_MEVCUT = args.no_mevcut

    logger.info(f"== 08_lscp.py basladi (threshold mu >= {CRITICAL_MU}, senaryo={SCENARIO}, sigma={SIGMA}) ==")
    mev_mu, aday_mu = load_mu(SIGMA)

    mahalleler = list(mev_mu.columns[1:])
    Q_i_arr = load_q_vector(SCENARIO, mahalleler)
    Q_i_dict = {mh: float(Q_i_arr[i]) for i, mh in enumerate(mahalleler)}
    logger.info(f"  Q_i ({SCENARIO}): min={Q_i_arr.min():.3f}, max={Q_i_arr.max():.3f}, mean={Q_i_arr.mean():.3f}")

    # Truncation: kucuk mu degerlerini sifirla
    if TRUNCATE > 0:
        n_zero = 0
        for j in range(len(aday_mu)):
            for mh in aday_mu.columns[1:]:
                if float(aday_mu.iloc[j][mh]) < TRUNCATE:
                    aday_mu.at[aday_mu.index[j], mh] = 0.0
                    n_zero += 1
        for j in range(len(mev_mu)):
            for mh in mev_mu.columns[1:]:
                if float(mev_mu.iloc[j][mh]) < TRUNCATE:
                    mev_mu.at[mev_mu.index[j], mh] = 0.0
                    n_zero += 1
        logger.info(f"  Truncation (mu < {TRUNCATE}): {n_zero} deger sifirlandi")

    # Mevcut konteynerlerin mahalle bazinda toplam mu'su (Q_i ile carpilmis)
    mev_cov = {}
    for mh in mev_mu.columns[1:]:
        qi = Q_i_dict.get(mh, 1.0)
        mev_cov[mh] = float(mev_mu[mh].sum()) * qi

    if NO_MEVCUT:
        for mh in mev_cov:
            mev_cov[mh] = 0.0
        logger.info(f"  No-mevcut mod: mevcut konteyner katkilari sifirlandi")

    logger.info(f"  Mevcut konteyner Q_i-scaled mu toplami (15 mahalle):")
    for mh, v in mev_cov.items():
        logger.info(f"    {mh}: {v:.4f}")

    tum_mev_yeterli = all(v >= CRITICAL_MU for v in mev_cov.values())
    if tum_mev_yeterli:
        logger.info(f"\n  TUM mahalleler zaten mevcut konteynerlerle mu>={CRITICAL_MU} - LSCP'ye gerek yok.")
        out = pd.DataFrame([{
            "K_min": 0, "status": "Mevcut yeterli",
            "scenario_code": SCENARIO,
            "secilen_adaylar": "",
            "not": f"12 mevcut (Q_i-scaled) zaten tum esikleri karsiliyor (senaryo={SCENARIO})"
        }])
    else:
        eksik = [mh for mh, v in mev_cov.items() if v < CRITICAL_MU]
        logger.info(f"\n  Esik altinda kalan mahalleler: {eksik}")

        res = solve_lscp(aday_mu, mev_cov, Q_i_dict=Q_i_dict, K_min=1, K_max=15)
        out_data = [{
            "K_min": res["K_min"],
            "status": res["status"],
            "secilen_adaylar": ", ".join(map(str, res["secilen_adaylar"])),
        }]
        for row in res["tarama"]:
            out_data.append({f"tarama_K{row['K']}": row["status"]})

        out = pd.DataFrame(out_data)

    sg_str = "" if SIGMA == "800" else f"_sg{SIGMA}"
    tr_str = f"_t{TRUNCATE}" if TRUNCATE > 0 else ""
    nm_str = "_nomez" if NO_MEVCUT else ""
    out_path = OUT / f"lscp_result_S{SCENARIO}{sg_str}{tr_str}{nm_str}.xlsx"
    out.to_excel(out_path, index=False)
    logger.info(f"\n  -> {out_path}")
    logger.info("== 08_lscp.py tamamlandi == ")


if __name__ == "__main__":
    main()

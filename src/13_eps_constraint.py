# -*- coding: utf-8 -*-
"""
13_eps_constraint.py
Pareto cephesi: min mahalle kapsamayi kisit olarak koyup RxC'yi maksimize et.
epsilon degerlerini 0.5-1.5 araliginda 9 noktada tara.

Cikti: results/eps_constraint/eps_pareto.xlsx
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pulp

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenario_utils import load_q_vector, fcm_paths

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
RES  = ROOT / "results"
OUT  = ROOT / "results" / "eps_constraint"
OUT.mkdir(parents=True, exist_ok=True)

EPS_VALUES = [0.5, 0.7, 0.9, 1.0, 1.1, 1.3, 1.5, 1.7, 2.0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="A", choices=["A", "B"])
    parser.add_argument("--sigma", type=str, default="800",
                        help="FCM sigma (metre), or '800_300' for two-tier")
    parser.add_argument("--K", type=int, default=8,
                        help="Yeni konteyner sayisi (varsayilan: 8)")
    parser.add_argument("--beta", type=float, default=0.30,
                        help="Kalite agirligi (varsayilan: 0.30)")
    parser.add_argument("--truncate", type=float, default=0.0,
                        help="Mu esik degeri: altindaki mu'ler sifirlanir (0=kapali)")
    parser.add_argument("--no-mevcut", action="store_true",
                        help="Mevcut konteynerleri yok say (tam relocation)")
    args = parser.parse_args()
    SCENARIO = args.scenario
    SIGMA = args.sigma
    K = args.K
    BETA = args.beta
    TRUNCATE = args.truncate
    NO_MEVCUT = args.no_mevcut

    print(f"== 13_eps_constraint.py basladi (senaryo={SCENARIO}, sigma={SIGMA},"
          f" K={K}, beta={BETA}) ==")
    fcm = fcm_paths(SIGMA)
    mev_mu = pd.read_excel(fcm["mu_mevcut"])
    aday_mu = pd.read_excel(fcm["mu_aday"])
    aday_data = pd.read_excel(DATA / "adaylar_140.xlsx")
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
    cc = pd.read_excel(RES / "mcdm" / "topsis_cc.xlsx")

    mahalleler = list(mev_mu.columns[1:])
    n = len(aday_mu)

    Q_i_arr = load_q_vector(SCENARIO, mahalleler)
    Q_i_dict = {mh: float(Q_i_arr[i]) for i, mh in enumerate(mahalleler)}
    print(f"  Q_i ({SCENARIO}): min={Q_i_arr.min():.3f}, max={Q_i_arr.max():.3f}, mean={Q_i_arr.mean():.3f}")

    # Truncation: kucuk mu degerlerini sifirla
    if TRUNCATE > 0:
        n_zero = 0
        for j in range(n):
            for mh in mahalleler:
                key = (int(aday_mu.iloc[j]["S_No"]), mh)
                if MU[key] < TRUNCATE:
                    MU[key] = 0.0
                    n_zero += 1
        print(f"  Truncation (mu < {TRUNCATE}): {n_zero} deger sifirlandi")

    if NO_MEVCUT:
        for mh in mahalleler:
            MU_mev[mh] = 0.0
        print(f"  No-mevcut mod: mevcut konteyner katkilari sifirlandi")

    R = {row["mahalle"]: float(row["risk_score"]) for _, row in risk.iterrows()}
    MU = {(int(aday_mu.iloc[j]["S_No"]), mh): float(aday_mu.iloc[j][mh])
          for j in range(n) for mh in mahalleler}
    MU_mev = {mh: float(mev_mu[mh].sum()) for mh in mahalleler}
    Q = {int(cc.iloc[j]["S_No"]): float(cc.iloc[j]["CC_Baseline"])
         for j in range(len(cc))}
    p_map = {int(row["S_No"]): float(row["p_access_road"])
             for _, row in aday_data.iterrows()}
    P = p_map

    rows = []
    pareto = []
    for eps in EPS_VALUES:
        prob = pulp.LpProblem(f"Eps_{eps}", pulp.LpMaximize)
        x = [pulp.LpVariable(f"x{j}", cat="Binary") for j in range(n)]
        terms = []
        for mh in mahalleler:
            if mh not in R:
                continue
            qi = Q_i_dict[mh]
            cov = qi * (MU_mev[mh] + pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
                                                P[int(aday_mu.iloc[j]["S_No"])] * x[j]
                                                for j in range(n)))
            terms.append(R[mh] * cov)
        prob += pulp.lpSum(terms) + BETA * pulp.lpSum(
            Q[int(aday_mu.iloc[j]["S_No"])] * x[j] for j in range(n))
        prob += pulp.lpSum(x) == K
        # eps kisitlamasi: her mahallenin Q_i-scaled toplam mu'su >= eps
        for mh in mahalleler:
            if mh not in R:
                continue
            qi = Q_i_dict[mh]
            prob += (qi * (pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] * x[j]
                                      for j in range(n)) + MU_mev[mh]) >= eps,
                     f"eps_{mh}")

        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
        prob.solve(solver)
        st = pulp.LpStatus[prob.status]

        if st != "Optimal":
            rows.append({"eps": eps, "status": st, "RxC": None, "min_cov": None,
                         "avg_cov": None, "secilen": ""})
            print(f"  eps={eps}: {st}")
            continue

        secilen = sorted([int(aday_mu.iloc[j]["S_No"]) for j in range(n)
                          if (x[j].value() or 0) > 0.5])
        covs = []
        rxc = 0.0
        for mh in mahalleler:
            if mh not in R:
                continue
            qi = Q_i_dict[mh]
            c = qi * (MU_mev[mh] + sum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
                                       P[int(aday_mu.iloc[j]["S_No"])] *
                                       (x[j].value() or 0) for j in range(n)))
            covs.append(c)
            rxc += R[mh] * c
        rows.append({
            "eps": eps, "status": st,
            "RxC": round(rxc, 4),
            "min_cov": round(min(covs), 4),
            "avg_cov": round(float(np.mean(covs)), 4),
            "secilen": ",".join(map(str, secilen))
        })
        pareto.append((rxc, min(covs), secilen))
        print(f"  eps={eps}: RxC={rxc:.4f}  min_C={min(covs):.4f}  n_sites={len(secilen)}")

    out = pd.DataFrame(rows)
    sg_str = "" if SIGMA == "800" else f"_sg{SIGMA}"
    tr_str = f"_t{TRUNCATE}" if TRUNCATE > 0 else ""
    nm_str = "_nomez" if NO_MEVCUT else ""
    b_str = f"_b{int(BETA*100)}" if abs(BETA - 0.30) > 0.001 else ""
    k_str = f"_K{K}" if K != 8 else ""
    out_path = OUT / f"eps_pareto_S{SCENARIO}{sg_str}{tr_str}{nm_str}{b_str}{k_str}.xlsx"
    out.to_excel(out_path, index=False)
    print(f"\n  -> {out_path}")

    # Pareto marjinali
    if len(pareto) >= 2:
        print(f"\n  Pareto bulgular (eps buyudukce min_C artar, RxC azalir):")
        for rxc, mc, _ in pareto:
            print(f"    RxC={rxc:8.4f}  min_C={mc:.4f}")

    print("== 13_eps_constraint.py tamamlandi ==")


if __name__ == "__main__":
    main()

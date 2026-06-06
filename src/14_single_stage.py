# -*- coding: utf-8 -*-
"""
14_single_stage.py
Tek-asamali MILP (Yapi 3): q + R + equity entegre.
Amac fonksiyonuna W_i (mahalle 'servis edildi' gostergesi) eklenir.
alpha * sum W_i ile equity tesvik edilir.
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
OUT  = ROOT / "results" / "single_stage"
OUT.mkdir(parents=True, exist_ok=True)

ALPHA = 0.20
L_THRESH = 0.50


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

    print(f"== 14_single_stage.py basladi (senaryo={SCENARIO}, sigma={SIGMA},"
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
    P = {int(row["S_No"]): float(row["p_access_road"])
         for _, row in aday_data.iterrows()}

    prob = pulp.LpProblem("SingleStage", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x{j}", cat="Binary") for j in range(n)]
    w = {mh: pulp.LpVariable(f"w_{mh}", cat="Binary") for mh in mahalleler if mh in R}

    terms_rxc = []
    for mh in mahalleler:
        if mh not in R:
            continue
        qi = Q_i_dict[mh]
        cov = qi * (MU_mev[mh] + pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
                                            P[int(aday_mu.iloc[j]["S_No"])] * x[j]
                                            for j in range(n)))
        terms_rxc.append(R[mh] * cov)
    Z_rxc = pulp.lpSum(terms_rxc)
    Z_quality = BETA * pulp.lpSum(
        Q[int(aday_mu.iloc[j]["S_No"])] * x[j] for j in range(n))
    Z_equity = ALPHA * pulp.lpSum(w[mh] for mh in w)

    prob += Z_rxc + Z_quality + Z_equity

    prob += pulp.lpSum(x) == K
    for mh in mahalleler:
        if mh not in R:
            continue
        qi = Q_i_dict[mh]
        base = MU_mev[mh]
        prob += (qi * (pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] * x[j]
                                  for j in range(n)) + base) >= L_THRESH * w[mh],
                 f"servis_{mh}")

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
    prob.solve(solver)
    print(f"  Status: {pulp.LpStatus[prob.status]}")

    secilen = sorted([int(aday_mu.iloc[j]["S_No"]) for j in range(n)
                      if (x[j].value() or 0) > 0.5])
    print(f"  Secilen 8: {secilen}")

    z_v = pulp.value(prob.objective)
    rxc_v = sum(R[mh] * Q_i_dict[mh] * (MU_mev[mh] + sum(
        MU[(int(aday_mu.iloc[j]["S_No"]), mh)] * P[int(aday_mu.iloc[j]["S_No"])]
        * (x[j].value() or 0) for j in range(n)))
        for mh in mahalleler if mh in R)
    q_v = BETA * sum(Q[int(aday_mu.iloc[j]["S_No"])] * (x[j].value() or 0) for j in range(n))
    e_v = ALPHA * sum(int((w[mh].value() or 0) > 0.5) for mh in w)
    print(f"  Z = {z_v:.4f}  (RxC={rxc_v:.4f}  +  q={q_v:.4f}  +  equity={e_v:.4f})")

    mahalle_rows = []
    for mh in mahalleler:
        if mh not in R:
            continue
        qi = Q_i_dict[mh]
        c = qi * (MU_mev[mh] + sum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
                                    P[int(aday_mu.iloc[j]["S_No"])] *
                                    (x[j].value() or 0) for j in range(n)))
        serv = "EVET" if (w[mh].value() or 0) > 0.5 else "HAYIR"
        mahalle_rows.append({
            "mahalle": mh, "C_i": round(c, 4),
            "servis_edildi": serv,
            "risk": R[mh]
        })
    mahalle_df = pd.DataFrame(mahalle_rows)
    print(f"\n  Mahalle kapsama (tek-asamali):")
    print(mahalle_df.to_string(index=False))

    out = pd.DataFrame({
        "Yontem": ["Tek-Asamali_MILP_V3"],
        "Z": [round(z_v, 4)],
        "RxC": [round(rxc_v, 4)],
        "Z_quality": [round(q_v, 4)],
        "Z_equity": [round(e_v, 4)],
        "K": [K],
        "alpha": [ALPHA],
        "secilen": [",".join(map(str, secilen))],
        "min_mahalle_cov": [mahalle_df["C_i"].min()],
        "avg_mahalle_cov": [mahalle_df["C_i"].mean()],
        "n_mahalle_servis": [int((mahalle_df["servis_edildi"] == "EVET").sum())]
    }, index=[0])

    sg_str = "" if SIGMA == "800" else f"_sg{SIGMA}"
    tr_str = f"_t{TRUNCATE}" if TRUNCATE > 0 else ""
    nm_str = "_nomez" if NO_MEVCUT else ""
    b_str = f"_b{int(BETA*100)}" if abs(BETA - 0.30) > 0.001 else ""
    k_str = f"_K{K}" if K != 8 else ""
    out_path = OUT / f"single_stage_result_S{SCENARIO}{sg_str}{tr_str}{nm_str}{b_str}{k_str}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as w_:
        out.to_excel(w_, sheet_name="Ozet", index=False)
        mahalle_df.to_excel(w_, sheet_name="Mahalle_Kapsama", index=False)
    print(f"\n  -> {out_path}")
    print("== 14_single_stage.py tamamlandi ==")


if __name__ == "__main__":
    main()

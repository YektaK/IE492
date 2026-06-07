# -*- coding: utf-8 -*-
"""
11_lexicographic.py
Iki asama cozum:
  1) Once RxC'yi maksimize et (orijinal IP)
  2) Sabit Z ile min C_i'yi maksimize et (equity IP)

Bu "lexicographic max-min" yaklasimi Pareto cephesinin
en "adil" noktasini bulur.
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
from scenario_utils import load_q_vector, fuzzy_coverage_paths

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
RES  = ROOT / "results"
OUT  = ROOT / "results" / "lexicographic"
OUT.mkdir(parents=True, exist_ok=True)

def main(SCENARIO="A", SIGMA="800", K_TOTAL=20, BETA=0.30, TRUNCATE=0.0, WEIGHT_TYPE="risk", KEPT_MEVCUT=None, FIXED_ADAY=None):
    if KEPT_MEVCUT is None:
        KEPT_MEVCUT = list(range(12))
    if FIXED_ADAY is None:
        FIXED_ADAY = []

    print(f"== 11_lexicographic.py basladi (senaryo={SCENARIO}, sigma={SIGMA},"
          f" K_Total={K_TOTAL}, beta={BETA}, weight={WEIGHT_TYPE}) ==")
    fcm = fuzzy_coverage_paths(SIGMA)
    mev_mu = pd.read_excel(fcm["mu_mevcut"])
    aday_mu = pd.read_excel(fcm["mu_aday"])
    
    if WEIGHT_TYPE == "risk":
        weight_df = pd.read_excel(DATA / "mahalle_risk.xlsx")
        val_col = "risk_score"
    elif WEIGHT_TYPE == "population":
        weight_df = pd.read_excel(DATA / "mahalle_nufus.xlsx")
        val_col = "nufus_2024"
    else:
        weight_df = pd.read_excel(DATA / "mahalle_risk.xlsx")
        val_col = "risk_score"
    cc = pd.read_excel(RES / "mcdm" / "topsis_cc.xlsx")

    mahalleler = list(mev_mu.columns[1:])
    n = len(aday_mu)

    # Q_i: yol erisim senaryo carpani
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

    MU_mev = {mh: sum(float(mev_mu.iloc[idx][mh]) for idx in KEPT_MEVCUT) for mh in mahalleler}

    # Parametreler (Oransal Olcekleme)
    weight_dict = {row["mahalle"]: float(row[val_col]) for _, row in weight_df.iterrows()}
    w_max = max(weight_dict.values())
    R = {mh: (weight_dict.get(mh, 1.0) / (w_max + 1e-9)) for mh in mahalleler}

    MU = {(int(aday_mu.iloc[j]["S_No"]), mh): float(aday_mu.iloc[j][mh])
          for j in range(n) for mh in mahalleler}
    Q = {int(cc.iloc[j]["S_No"]): float(cc.iloc[j]["CC_Baseline_MinMax"])
         for j in range(len(cc))}
    P = {int(aday_mu.iloc[j]["S_No"]): float(aday_mu.iloc[j]["p_access_road"]
         if "p_access_road" in aday_mu.columns else 0.7)
         for j in range(n)}

    # --------- ASAMA 1: RxC maksimize ---------
    print("  Asama 1: RxC maksimize ediliyor...")
    prob1 = pulp.LpProblem("Lexi_A1", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x{j}", cat="Binary") for j in range(n)]
    Z1_terms = []
    for mh in mahalleler:
        if mh not in R:
            continue
        qi = Q_i_dict[mh]
        cov_mh = qi * (MU_mev[mh] + pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
                                                P[int(aday_mu.iloc[j]["S_No"])] * x[j]
                                                for j in range(n)))
        Z1_terms.append(R[mh] * cov_mh)
    Z1 = pulp.lpSum(Z1_terms) + BETA * pulp.lpSum(
        Q[int(aday_mu.iloc[j]["S_No"])] * x[j] for j in range(n))
    prob1 += Z1
    prob1 += pulp.lpSum(x) == (K_TOTAL - len(KEPT_MEVCUT))
    for f_idx in FIXED_ADAY:
        prob1 += x[f_idx] == 1
    for mh in mahalleler:
        if mh not in R:
            continue
        qi = Q_i_dict[mh]
        base = MU_mev[mh]
        prob1 += (qi * (pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] * x[j]
                                   for j in range(n)) + base) >= 0.50,
                  f"cov_{mh}")

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
    prob1.solve(solver)
    print(f"  A1 status: {pulp.LpStatus[prob1.status]}")
    Z1_opt = pulp.value(prob1.objective)
    Z1_rxc = sum(R[mh] * Q_i_dict[mh] * (MU_mev[mh] + sum(
        MU[(int(aday_mu.iloc[j]["S_No"]), mh)] * P[int(aday_mu.iloc[j]["S_No"])]
        * (x[j].value() or 0) for j in range(n))) for mh in mahalleler if mh in R)
    print(f"  A1 Z_opt = {Z1_opt:.4f}, RxC = {Z1_rxc:.4f}")

    secilen1 = sorted([int(aday_mu.iloc[j]["S_No"]) for j in range(n)
                       if (x[j].value() or 0) > 0.5])

    # --------- ASAMA 2: Sabit Z ile min C_i maksimize ---------
    print("  Asama 2: min C_i maksimize ediliyor (Z_opt toleransi ile)...")
    prob2 = pulp.LpProblem("Lexi_A2", pulp.LpMaximize)
    y = [pulp.LpVariable(f"y{j}", cat="Binary") for j in range(n)]
    cov2 = {mh: Q_i_dict[mh] * (MU_mev[mh] + pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
                                                         P[int(aday_mu.iloc[j]["S_No"])] * y[j]
                                                         for j in range(n)))
            for mh in mahalleler if mh in R}
    # min cov degiskeni
    t = pulp.LpVariable("t", lowBound=0, upBound=20)
    prob2 += t
    for mh in cov2:
        prob2 += cov2[mh] >= t, f"mincov_{mh}"
    prob2 += pulp.lpSum(y) == (K_TOTAL - len(KEPT_MEVCUT))
    for f_idx in FIXED_ADAY:
        prob2 += y[f_idx] == 1
    # Z_opt - epsilon toleransi
    EPS = 0.01
    Z2_terms = []
    for mh in cov2:
        Z2_terms.append(R[mh] * cov2[mh])
    prob2 += (pulp.lpSum(Z2_terms) + BETA * pulp.lpSum(
        Q[int(aday_mu.iloc[j]["S_No"])] * y[j] for j in range(n)) >= Z1_opt - EPS,
              "Z_keep")
    # 0.50 minimum korunmali
    for mh in mahalleler:
        if mh not in R:
            continue
        qi = Q_i_dict[mh]
        prob2 += (qi * (pulp.lpSum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] * y[j]
                                   for j in range(n)) + MU_mev[mh]) >= 0.50,
                  f"cov2_{mh}")

    prob2.solve(solver)
    print(f"  A2 status: {pulp.LpStatus[prob2.status]}")
    secilen2 = sorted([int(aday_mu.iloc[j]["S_No"]) for j in range(n)
                       if (y[j].value() or 0) > 0.5])
    min_cov2 = pulp.value(t)
    print(f"  A2 min_C_i = {min_cov2:.4f}")

    # Mahalle kapsama degerleri
    rows = []
    for mh in cov2:
        qi = Q_i_dict[mh]
        c1 = qi * (MU_mev[mh] + sum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
                                    P[int(aday_mu.iloc[j]["S_No"])] *
                                    (x[j].value() or 0) for j in range(n)))
        c2 = qi * (MU_mev[mh] + sum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
                                    P[int(aday_mu.iloc[j]["S_No"])] *
                                    (y[j].value() or 0) for j in range(n)))
        rows.append({"mahalle": mh, "A1_cov": round(c1, 4), "A2_cov": round(c2, 4),
                     "delta": round(c2 - c1, 4)})

    out = pd.DataFrame({
        "Asama": ["A1_RxC_maks", "A2_minCov_maks"],
        "Status": [pulp.LpStatus[prob1.status], pulp.LpStatus[prob2.status]],
        "Z": [round(Z1_opt, 4), round(pulp.value(prob2.objective) or 0, 4)],
        "RxC": [round(Z1_rxc, 4), round(sum(R[mh] * Q_i_dict[mh] * (
            MU_mev[mh] + sum(MU[(int(aday_mu.iloc[j]["S_No"]), mh)] *
            P[int(aday_mu.iloc[j]["S_No"])] * (y[j].value() or 0) for j in range(n)))
            for mh in cov2), 4)],
        "min_C": [round(min(r["A1_cov"] for r in rows), 4), round(min_cov2, 4)],
        "secilen": [",".join(map(str, secilen1)), ",".join(map(str, secilen2))]
    }, index=[0, 1])

    sg_str = "" if SIGMA == "800" else f"_sg{SIGMA}"
    tr_str = f"_t{TRUNCATE}" if TRUNCATE > 0 else ""
    nm_str = "_nomez" if len(KEPT_MEVCUT) == 0 else ""
    b_str = f"_b{int(BETA*100)}" if abs(BETA - 0.30) > 0.001 else ""
    k_str = f"_K{K_TOTAL}"
    wt_str = f"_{WEIGHT_TYPE}" if WEIGHT_TYPE != "risk" else ""
    out_path = OUT / f"lexicographic_result_S{SCENARIO}{sg_str}{tr_str}{nm_str}{b_str}{k_str}{wt_str}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        out.to_excel(w, sheet_name="Ozet", index=False)
        pd.DataFrame(rows).to_excel(w, sheet_name="Mahalle_Karsilastirma", index=False)

    print(f"\n  -> {out_path}")
    print(f"  A1 secilen: {secilen1}")
    print(f"  A2 secilen: {secilen2}")
    print("== 11_lexicographic.py tamamlandi ==")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="A", choices=["A", "B"])
    parser.add_argument("--sigma", type=str, default="800")
    parser.add_argument("--K", type=int, default=8)
    parser.add_argument("--beta", type=float, default=0.30)
    parser.add_argument("--truncate", type=float, default=0.0)
    parser.add_argument("--no-mevcut", action="store_true")
    parser.add_argument("--weight", type=str, default="risk", choices=["risk", "population"])
    args = parser.parse_args()
    
    kept = [] if args.no_mevcut else list(range(12))
    k_tot = args.K if args.no_mevcut else args.K + 12
    main(SCENARIO=args.scenario, SIGMA=args.sigma, K_TOTAL=k_tot, BETA=args.beta, TRUNCATE=args.truncate, WEIGHT_TYPE=args.weight, KEPT_MEVCUT=kept)

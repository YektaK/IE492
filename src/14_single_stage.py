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
from scenario_utils import load_q_vector, fuzzy_coverage_paths, load_mcdm_column, MCDM_COLUMNS
from config import DATA_DIR as DATA, RESULTS_DIR as RES, logger, get_mevcut_indices
from solver_core import dict_to_matrix, add_base_constraints, get_solver
OUT  = RES / "single_stage"
OUT.mkdir(parents=True, exist_ok=True)

from config import EQUITY_ALPHA, COVERAGE_THRESHOLD
ALPHA = EQUITY_ALPHA
L_THRESH = COVERAGE_THRESHOLD


def main(SCENARIO="A", SIGMA="800", K_TOTAL=20, BETA=0.30, TRUNCATE=0.0, WEIGHT_TYPE="risk", KEPT_MEVCUT=None, FIXED_ADAY=None, MCDM_METHOD="TOPSIS", MCDM_FOCUS="Baseline"):
    if KEPT_MEVCUT is None:
        KEPT_MEVCUT = get_mevcut_indices()
    if FIXED_ADAY is None:
        FIXED_ADAY = []

    logger.info(f"== 14_single_stage.py basladi (senaryo={SCENARIO}, sigma={SIGMA},"
                f" K_Total={K_TOTAL}, beta={BETA}, weight={WEIGHT_TYPE}, mcdm={MCDM_METHOD}/{MCDM_FOCUS}) ==")
    fcm = fuzzy_coverage_paths(SIGMA)
    mev_mu = pd.read_excel(fcm["mu_mevcut"])
    aday_mu = pd.read_excel(fcm["mu_aday"])
    aday_data = pd.read_excel(DATA / "adaylar_140.xlsx")

    if WEIGHT_TYPE == "risk":
        weight_df = pd.read_excel(DATA / "mahalle_risk.xlsx")
        val_col = "risk_score"
    elif WEIGHT_TYPE == "population":
        weight_df = pd.read_excel(DATA / "mahalle_nufus.xlsx")
        val_col = "nufus_2024"
    else:
        weight_df = pd.read_excel(DATA / "mahalle_risk.xlsx")
        val_col = "risk_score"
    q_series = load_mcdm_column(MCDM_METHOD, MCDM_FOCUS)

    mahalleler = list(mev_mu.columns[1:])
    n = len(aday_mu)

    Q_i_arr = load_q_vector(SCENARIO, mahalleler)
    Q_i_dict = {mh: float(Q_i_arr[i]) for i, mh in enumerate(mahalleler)}
    logger.info(f"  Q_i ({SCENARIO}): min={Q_i_arr.min():.3f}, max={Q_i_arr.max():.3f}, mean={Q_i_arr.mean():.3f}")

    MU_mev = {mh: sum(float(mev_mu.iloc[idx][mh]) for idx in KEPT_MEVCUT) for mh in mahalleler}

    # Parametreler (Oransal Olcekleme)
    weight_dict = {row["mahalle"]: float(row[val_col]) for _, row in weight_df.iterrows()}
    w_max = max(weight_dict.values())
    R = {mh: (weight_dict.get(mh, 1.0) / (w_max + 1e-9)) for mh in mahalleler}

    MU = {(int(aday_mu.iloc[j]["S_No"]), mh): float(aday_mu.iloc[j][mh])
          for j in range(n) for mh in mahalleler}

    # Truncation: kucuk mu degerlerini sifirla
    if TRUNCATE > 0:
        n_zero = 0
        for j in range(n):
            for mh in mahalleler:
                key = (int(aday_mu.iloc[j]["S_No"]), mh)
                if MU[key] < TRUNCATE:
                    MU[key] = 0.0
                    n_zero += 1
        logger.info(f"  Truncation (mu < {TRUNCATE}): {n_zero} deger sifirlandi")

    Q = {int(sno): float(val) for sno, val in q_series.items()}
    P = {int(row["S_No"]): float(row["p_access_road"])
         for _, row in aday_data.iterrows()}

    prob = pulp.LpProblem("SingleStage", pulp.LpMaximize)
    S_Nos = [int(aday_mu.iloc[j]["S_No"]) for j in range(n)]
    MU_matrix = dict_to_matrix(MU, S_Nos, mahalleler)
    P_arr = np.array([P[s] for s in S_Nos])
    Q_arr = np.array([Q_i_dict[mh] for mh in mahalleler])
    mu_mev_arr = np.array([MU_mev[mh] for mh in mahalleler])
    R_arr = np.array([R[mh] for mh in mahalleler])

    x = [pulp.LpVariable(f"x{j}", cat="Binary") for j in range(n)]
    w = {mh: pulp.LpVariable(f"w_{mh}", cat="Binary") for mh in mahalleler if mh in R}

    coverage = [
        Q_arr[i] * (mu_mev_arr[i] + pulp.lpSum(MU_matrix[j, i] * P_arr[j] * x[j] for j in range(n)))
        for i in range(len(mahalleler))
    ]
    coverage_without_P = [
        Q_arr[i] * (mu_mev_arr[i] + pulp.lpSum(MU_matrix[j, i] * x[j] for j in range(n)))
        for i in range(len(mahalleler))
    ]

    Z_rxc = pulp.lpSum(R_arr[i] * coverage[i] for i in range(len(mahalleler)))
    Z_quality = BETA * pulp.lpSum(Q[S_Nos[j]] * x[j] for j in range(n))
    Z_equity = ALPHA * pulp.lpSum(w[mh] for mh in w)

    prob += Z_rxc + Z_quality + Z_equity

    # solver_core base constraints
    add_base_constraints(prob, x, coverage, K_TOTAL, KEPT_MEVCUT, FIXED_ADAY, 
                         None, None, None, len(mahalleler), min_one=False, risk_prop=False)

    for i, mh in enumerate(mahalleler):
        prob += (coverage_without_P[i] >= L_THRESH * w[mh], f"servis_{mh}")

    solver = get_solver(time_limit=30, msg=0)
    prob.solve(solver)
    logger.info(f"  Status: {pulp.LpStatus[prob.status]}")

    secilen = sorted([int(aday_mu.iloc[j]["S_No"]) for j in range(n)
                      if (x[j].value() or 0) > 0.5])
    logger.info(f"  Secilen: {secilen}")

    z_v = pulp.value(prob.objective)
    rxc_v = sum(R[mh] * Q_i_dict[mh] * (MU_mev[mh] + sum(
        MU[(int(aday_mu.iloc[j]["S_No"]), mh)] * P[int(aday_mu.iloc[j]["S_No"])]
        * (x[j].value() or 0) for j in range(n)))
        for mh in mahalleler if mh in R)
    q_v = BETA * sum(Q[int(aday_mu.iloc[j]["S_No"])] * (x[j].value() or 0) for j in range(n))
    e_v = ALPHA * sum(int((w[mh].value() or 0) > 0.5) for mh in w)
    logger.info(f"  Z = {z_v:.4f}  (RxC={rxc_v:.4f}  +  q={q_v:.4f}  +  equity={e_v:.4f})")

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
    logger.info(f"\n  Mahalle kapsama (tek-asamali):\n{mahalle_df.to_string(index=False)}")

    out = pd.DataFrame({
        "Yontem": ["Tek-Asamali_MILP_V3"],
        "Z": [round(z_v, 4)],
        "RxC": [round(rxc_v, 4)],
        "Z_quality": [round(q_v, 4)],
        "Z_equity": [round(e_v, 4)],
        "K": [K_TOTAL],
        "alpha": [ALPHA],
        "secilen": [",".join(map(str, secilen))],
        "min_mahalle_cov": [mahalle_df["C_i"].min()],
        "avg_mahalle_cov": [mahalle_df["C_i"].mean()],
        "n_mahalle_servis": [int((mahalle_df["servis_edildi"] == "EVET").sum())]
    }, index=[0])

    sg_str = "" if SIGMA == "800" else f"_sg{SIGMA}"
    tr_str = f"_t{TRUNCATE}" if TRUNCATE > 0 else ""
    nm_str = "_nomez" if len(KEPT_MEVCUT) == 0 else ""
    b_str = f"_b{int(BETA*100)}" if abs(BETA - 0.30) > 0.001 else ""
    k_str = f"_K{K_TOTAL}"
    wt_str = f"_{WEIGHT_TYPE}" if WEIGHT_TYPE != "risk" else ""
    mc_str = f"_{MCDM_METHOD.lower()}_{MCDM_FOCUS.lower()}"
    out_path = OUT / f"single_stage_result_S{SCENARIO}{sg_str}{tr_str}{nm_str}{b_str}{k_str}{wt_str}{mc_str}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as w_:
        out.to_excel(w_, sheet_name="Ozet", index=False)
        mahalle_df.to_excel(w_, sheet_name="Mahalle_Kapsama", index=False)
    logger.info(f"\n  -> {out_path}")

    # --------------------------------------------------
    # app.py uyumlulugu icin ip / coverage / summary dosyalari
    # --------------------------------------------------
    MODELS_DIR = (Path(__file__).resolve().parent.parent / "results" / "models")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    VER = "Tek-Asamali_MILP_V3"

    # Suffix without mcdm part (matches ip_file_suffix in app_runner.py)
    suffix = f"S{SCENARIO}{sg_str}{tr_str}{nm_str}_b{int(BETA*100)}{k_str}{wt_str}"

    # 1. ip file — selected parcel list with coordinates
    aday_data = pd.read_excel(DATA / "adaylar_140.xlsx")
    selected_df = aday_data[aday_data["S_No"].isin(secilen)].copy()
    toplam_mu = {}
    for sno in secilen:
        coverage_sum = sum(MU[(sno, mh)] * P[sno] for mh in mahalleler if mh in R)
        toplam_mu[sno] = round(coverage_sum, 4)
    selected_df["toplam_mu_saglanan"] = selected_df["S_No"].map(toplam_mu).fillna(0.0)
    ip_name = f"ip_{VER}_{MCDM_METHOD}_{MCDM_FOCUS}_{suffix}.xlsx"
    selected_df.to_excel(MODELS_DIR / ip_name, index=False)
    logger.info(f"  -> {MODELS_DIR / ip_name}")

    # 2. coverage file — per-mahalle
    cov_df = mahalle_df.rename(columns={"C_i": "toplam_kapsama"})
    cov_name = f"coverage_{VER}_{MCDM_METHOD}_{MCDM_FOCUS}_{suffix}.xlsx"
    cov_df.to_excel(MODELS_DIR / cov_name, index=False)
    logger.info(f"  -> {MODELS_DIR / cov_name}")

    # 3. summary_all — one-row variant table (app.py compatibility)
    summary_row = pd.DataFrame([{
        "version": VER,
        "mcdm": MCDM_METHOD,
        "senaryo": MCDM_FOCUS,
        "Z_total": round(z_v, 4),
        "RxC": round(rxc_v, 4),
        "min_mahalle_cov": round(mahalle_df["C_i"].min(), 4),
        "avg_mahalle_cov": round(mahalle_df["C_i"].mean(), 4),
        "sure_s": None
    }])
    sum_name = f"summary_all_{suffix}.xlsx"
    summary_row.to_excel(MODELS_DIR / sum_name, index=False)
    logger.info(f"  -> {MODELS_DIR / sum_name}")

    logger.info("== 14_single_stage.py tamamlandi ==")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="A", choices=["A", "B"])
    parser.add_argument("--sigma", type=str, default="800")
    parser.add_argument("--K", type=int, default=8)
    parser.add_argument("--beta", type=float, default=0.30)
    parser.add_argument("--truncate", type=float, default=0.0)
    parser.add_argument("--no-mevcut", action="store_true")
    parser.add_argument("--weight", type=str, default="risk", choices=["risk", "population"])
    parser.add_argument("--mcdm", type=str, default="TOPSIS", choices=list(MCDM_COLUMNS))
    parser.add_argument("--mcdm-focus", type=str, default="Baseline", choices=["Baseline", "DamageFocused", "InfrastructureFocused"])
    args = parser.parse_args()

    kept = [] if args.no_mevcut else get_mevcut_indices()
    k_tot = args.K if args.no_mevcut else args.K + len(get_mevcut_indices())
    main(SCENARIO=args.scenario, SIGMA=args.sigma, K_TOTAL=k_tot, BETA=args.beta, TRUNCATE=args.truncate, WEIGHT_TYPE=args.weight, KEPT_MEVCUT=kept, MCDM_METHOD=args.mcdm, MCDM_FOCUS=args.mcdm_focus)

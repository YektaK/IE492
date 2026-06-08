"""
05_ip.py
Sultanbeyli Konteyner Konum Secimi - 0-1 IP COZUMU

Faz 4 Guncellemesi:
- 'fuzzy_coverage' yollari ve TOPSIS(MinMax) skorlari kullaniliyor.
- Q_i yol kapanma cezasi entegre edildi.
- Batch Mode (K=8 Ekleme vs K=20 Bastan) ayni dosya icinde (veya wrapper ile) kosulabilir.

Problem:
  max Z = SUM_i R_i * C_i  +  beta * SUM_j q_j * X_j
  burada:
    C_i = Q_i[i] * (mu_mev_sum_i  +  SUM_j mu_aday[i,j] * P_j[j] * X_j)
    q_j = MCDM skoru (TOPSIS CC_MinMax  veya  PROMETHEE phi01)
    P_j = p_access_road[j]
    R_i = mahalle risk skoru
    Q_i = mahalle acik yol olasiligi penalty (Referans=1, Senaryo B=p_road_open)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pulp

# Central Config import
import config
from config import norm_mahalle, DATA_DIR as PROCESSED, RESULTS_DIR, MODELS_DIR, logger, get_mevcut_indices

MCDM_DIR = RESULTS_DIR / "mcdm"
FUZZY_COV_DIR = RESULTS_DIR / "fuzzy_coverage"

from scenario_utils import load_q_vector, fuzzy_coverage_paths, load_mcdm_scores
from solver_core import build_base_variables_and_coverage, add_base_constraints, get_solver


def run_ip_model(SCENARIO="A", K_TOTAL=20, BETA_QUALITY=0.30, SIGMA_FCM="800", TRUNCATE=0.0, WEIGHT_TYPE="risk", KEPT_MEVCUT=None, FIXED_ADAY=None):
    """Calistirma fonksiyonu"""
    if KEPT_MEVCUT is None:
        KEPT_MEVCUT = get_mevcut_indices()
    if FIXED_ADAY is None:
        FIXED_ADAY = []
        
    trunc_s = f"_{TRUNCATE}" if TRUNCATE > 0 else ""
    km_len = len(KEPT_MEVCUT)
    fa_len = len(FIXED_ADAY)
    
    logger.info(f"== 05_ip.py basladi (senaryo={SCENARIO}, K_Total={K_TOTAL}, beta={BETA_QUALITY}, sigma={SIGMA_FCM}{trunc_s}, weight={WEIGHT_TYPE}, KeptMevcut={km_len}, FixedAday={fa_len}) ==")

    # Dizinleri hazirla
    fcm = fuzzy_coverage_paths(SIGMA_FCM)
    
    adaylar_sorted = pd.read_excel(PROCESSED / "adaylar_140.xlsx")
    mevcut = pd.read_excel(PROCESSED / "mevcut_12.xlsx")
    mu_aday = pd.read_excel(fcm["mu_aday"], index_col=0)
    mu_mevcut = pd.read_excel(fcm["mu_mevcut"], index_col=0)
    
    # Agirlik vektorunu dinamik yukle
    if WEIGHT_TYPE == "risk":
        weight_df = pd.read_excel(PROCESSED / "mahalle_risk.xlsx")
        val_col = "risk_score"
    elif WEIGHT_TYPE == "population":
        weight_df = pd.read_excel(PROCESSED / "mahalle_nufus.xlsx")
        val_col = "nufus_2024"
    elif WEIGHT_TYPE == "shelter":
        weight_df = pd.read_excel(PROCESSED / "mahalle_barinma.xlsx")
        val_col = "hane_ihtiyaci"
    else:
        raise ValueError(f"Unknown weight type: {WEIGHT_TYPE}")

    for df in [adaylar_sorted, mevcut, weight_df, mu_aday, mu_mevcut]:
        for col in df.columns:
            if col.lower() in ["mahalle"] or "mahalle" in col.lower():
                df[col + "_norm"] = df[col].apply(norm_mahalle)

    mahalleler = list(mu_aday.columns)
    
    weight_dict = weight_df.set_index("mahalle_norm")[val_col].to_dict()
    R_i = np.array([weight_dict.get(m, 1.0) for m in mahalleler])
    R_max = R_i.max()
    R_i_norm = R_i / (R_max + 1e-9) # Oransal Olcekleme (0 yutan eleman engellendi)

    P_j = adaylar_sorted["p_access_road"].values

    if len(KEPT_MEVCUT) > 0:
        mu_mev_sum = mu_mevcut.iloc[KEPT_MEVCUT].sum(axis=0).values
    else:
        mu_mev_sum = np.zeros(len(mahalleler))

    MU = mu_aday.values
    n_aday, n_mah = MU.shape

    Q_i = load_q_vector(SCENARIO, mahalleler)

    if TRUNCATE > 0:
        MU = np.where(MU < TRUNCATE, 0.0, MU)

    mcdm_scores = load_mcdm_scores()

    scenarios = ["Baseline", "DamageFocused", "InfrastructureFocused"]
    mcdm_methods = list(mcdm_scores.keys())

    # Min 1 Konteyner Kisiti icin on hazirlik
    mevcut_counts = np.zeros(n_mah)
    for idx in KEPT_MEVCUT:
        m = mevcut.iloc[idx]["mahalle_norm"]
        if m in mahalleler:
            mevcut_counts[mahalleler.index(m)] += 1
                
    aday_mah_idx = []
    for m in adaylar_sorted["Mahalle_norm"]:
        if m in mahalleler:
            aday_mah_idx.append(mahalleler.index(m))
        else:
            aday_mah_idx.append(-1)

    results_all = []
    selected_details = {}

    def solve_ip(mcdm: str, scen: str, K_TOTAL: int, beta: float,
                 MU: np.ndarray, P_j: np.ndarray, R_i: np.ndarray,
                 mu_mev_sum: np.ndarray, q_j: np.ndarray,
                 n_aday: int, n_mah: int, Q_i: np.ndarray | None = None) -> dict:
        if Q_i is None:
            Q_i = np.ones(n_mah)
        prob = pulp.LpProblem(f"Sultanbeyli_{mcdm}_{scen}", pulp.LpMaximize)

        # solver_core helpers
        X, coverage = build_base_variables_and_coverage(n_aday, n_mah, MU, P_j, Q_i, mu_mev_sum)

        Z_risk = pulp.lpSum(R_i[i] * coverage[i] for i in range(n_mah))
        Z_quality = pulp.lpSum(q_j[j] * X[j] for j in range(n_aday))
        prob += Z_risk + beta * Z_quality

        # Base constraints from solver_core
        add_base_constraints(prob, X, coverage, K_TOTAL, KEPT_MEVCUT, FIXED_ADAY, 
                             aday_mah_idx, mevcut_counts, R_i, n_mah)

        t0 = time.time()
        prob.solve(get_solver(msg=0))
        dt = time.time() - t0

        selected_idx = [j for j in range(n_aday) if X[j].varValue is not None and X[j].varValue > 0.5]
        cov_vals = [Q_i[i] * (mu_mev_sum[i] + sum(MU[j, i] * P_j[j] for j in selected_idx))
                    for i in range(n_mah)]
        Z_risk_val = sum(R_i[i] * cov_vals[i] for i in range(n_mah))
        Z_quality_raw = sum(q_j[j] for j in selected_idx)
        Z_quality_val = BETA_QUALITY * Z_quality_raw
        RxC = Z_risk_val
        min_cov = min(cov_vals)
        max_cov = max(cov_vals)
        avg_cov = np.mean(cov_vals)
        n_mah_below_50 = sum(1 for c in cov_vals if c < 0.50)
        n_mah_below_20 = sum(1 for c in cov_vals if c < 0.20)

        return {
            "mcdm": mcdm,
            "senaryo": scen,
            "status": pulp.LpStatus[prob.status],
            "sure_s": round(dt, 3),
            "Z_total": round(pulp.value(prob.objective), 4),
            "Z_risk": round(Z_risk_val, 4),
            "Z_quality": round(Z_quality_val, 4),
            "RxC": round(RxC, 4),
            "min_mahalle_cov": round(min_cov, 4),
            "max_mahalle_cov": round(max_cov, 4),
            "avg_mahalle_cov": round(avg_cov, 4),
            "n_mahalle_below_050": int(n_mah_below_50),
            "n_mahalle_below_020": int(n_mah_below_20),
            "selected_idx": selected_idx,
            "coverage_vec": cov_vals,
        }

    for mcdm in mcdm_methods:
        for scen in scenarios:
            q = mcdm_scores[mcdm][scen]
            label = f"{mcdm:10s} / {scen:25s} / S{SCENARIO}"
            res = solve_ip(mcdm, scen, K_TOTAL, BETA_QUALITY, MU, P_j, R_i_norm, mu_mev_sum, q, n_aday, n_mah, Q_i=Q_i)
            logger.info(f"  -> {label} ... Z={res['Z_total']:.3f}, RxC={res['RxC']:.3f}, min_cov={res['min_mahalle_cov']:.3f}")

            idx = len(results_all) + 1
            version = f"v{idx}_S{SCENARIO}"
            results_all.append({
                "version": version,
                "mcdm": mcdm,
                "senaryo": scen,
                "scenario_code": SCENARIO,
                "K": K_TOTAL,
                "beta": BETA_QUALITY,
                **{k: v for k, v in res.items() if k not in ["selected_idx", "coverage_vec"]},
            })
            selected_details[version] = {
                "mcdm": mcdm,
                "senaryo": scen,
                "scenario_code": SCENARIO,
                "selected_idx": res["selected_idx"],
                "coverage_vec": res["coverage_vec"],
            }

    summary = pd.DataFrame(results_all)
    sg_str = "" if SIGMA_FCM == "800" else f"_sg{SIGMA_FCM}"
    tr_str = f"_t{TRUNCATE}" if TRUNCATE > 0 else ""
    nm_str = "_nomez" if len(KEPT_MEVCUT) == 0 else ""
    wt_str = f"_{WEIGHT_TYPE}"
    
    file_suffix = f"S{SCENARIO}{sg_str}_b{int(BETA_QUALITY*100)}_K{K_TOTAL}{tr_str}{nm_str}{wt_str}"
    
    summary.to_excel(MODELS_DIR / f"summary_all_{file_suffix}.xlsx", index=False)

    for vname, det in selected_details.items():
        secilen = adaylar_sorted.iloc[det["selected_idx"]][["S_No", "Alan_Adi", "Mahalle", "Enlem", "Boylam"]].copy()
        secilen["mahalle_norm"] = secilen["Mahalle"].apply(norm_mahalle)
        q_used = mcdm_scores[det["mcdm"]][det["senaryo"]]
        secilen[f"q_{det['mcdm']}"] = q_used[det["selected_idx"]]
        secilen["p_access_road"] = P_j[det["selected_idx"]]
        mu_per_parsel = MU[det["selected_idx"]].sum(axis=1)
        secilen["toplam_mu_saglanan"] = mu_per_parsel
        out_name = f"ip_{vname}_{det['mcdm']}_{det['senaryo']}_{file_suffix}.xlsx"
        secilen.to_excel(MODELS_DIR / out_name, index=False)

        cov_df = pd.DataFrame({
            "mahalle": mahalleler,
            "mu_mevcut_toplam": mu_mev_sum,
            "yeni_kapsama": [det["coverage_vec"][i] - mu_mev_sum[i] for i in range(n_mah)],
            "toplam_kapsama": det["coverage_vec"],
        })
        cov_df.to_excel(MODELS_DIR / f"coverage_{vname}_{det['mcdm']}_{det['senaryo']}_{file_suffix}.xlsx", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", action="store_true", help="Run budget scenarios: k=8 (ekleme) & k=20 (bastan)")
    parser.add_argument("--scenario", default="A")
    parser.add_argument("--K", type=int, default=20)
    parser.add_argument("--beta", type=float, default=0.30)
    parser.add_argument("--sigma", type=str, default="800")
    parser.add_argument("--truncate", type=float, default=0.15)
    parser.add_argument("--no-mevcut", action="store_true")
    parser.add_argument("--weight", type=str, default="risk", choices=["risk", "population", "shelter"])
    parser.add_argument("--kept", type=str, default="", help="Comma separated indices of kept mevcut containers")
    parser.add_argument("--fixed", type=str, default="", help="Comma separated indices of fixed aday containers")
    args = parser.parse_args()

    if args.batch:
        logger.info("==================================================")
        logger.info(f"IP BATCH MODE: K=8 & K=20 (Agirlik: {args.weight})")
        logger.info("==================================================")
        # Senaryo 1: Toplam K=20, Mevcut 12 Dahil (Yani 8 yeni eklenecek)
        logger.info("\n>>> SENARYO: K_Total=20, Mevcut 12 Dahil (K_Opt=8)")
        run_ip_model(SCENARIO="A", K_TOTAL=20, BETA_QUALITY=args.beta, SIGMA_FCM=args.sigma, TRUNCATE=args.truncate, WEIGHT_TYPE=args.weight, KEPT_MEVCUT=get_mevcut_indices(), FIXED_ADAY=[])
        
        # Senaryo 2: Toplam K=20, Mevcut Yok (Yani 20'si de yeni secilecek)
        logger.info("\n>>> SENARYO: K_Total=20, Baştan Kurulum (K_Opt=20)")
        run_ip_model(SCENARIO="A", K_TOTAL=20, BETA_QUALITY=args.beta, SIGMA_FCM=args.sigma, TRUNCATE=args.truncate, WEIGHT_TYPE=args.weight, KEPT_MEVCUT=[], FIXED_ADAY=[])
    else:
        if args.no_mevcut:
            kept = []
        elif args.kept != "":
            kept = [int(x) for x in args.kept.split(",")]
        else:
            kept = get_mevcut_indices()
            
        fixed = [int(x) for x in args.fixed.split(",")] if args.fixed != "" else []
        
        # args.K is exactly K_TOTAL in the new system
        run_ip_model(SCENARIO=args.scenario, K_TOTAL=args.K, BETA_QUALITY=args.beta, SIGMA_FCM=args.sigma, TRUNCATE=args.truncate, WEIGHT_TYPE=args.weight, KEPT_MEVCUT=kept, FIXED_ADAY=fixed)

# -*- coding: utf-8 -*-
"""
13_eps_constraint.py
Pareto cephesi: minimum mahalle kapsama esigini (epsilon) kademeli olarak artirarak 
toplam fayda (RxC) maksimizasyonu ile mekansal esitlik arasindaki trade-off'u cizer.

Faz 8 Guncellemesi:
- Adaptif Sigma, Min-1 Kısıtı ve Risk-Orantili Taban Kapsama entegre edildi.
- Pareto egrisini gorsellestiren Matplotlib entegrasyonu eklendi.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pulp
import matplotlib.pyplot as plt

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenario_utils import load_q_vector, fuzzy_coverage_paths, load_mcdm_column, MCDM_COLUMNS
from solver_core import build_base_variables_and_coverage, add_base_constraints, get_solver

# Central Config import
import config
from config import norm_mahalle, DATA_DIR as DATA, RESULTS_DIR as RES, logger, get_mevcut_indices
OUT  = RES / "eps_constraint"
OUT.mkdir(parents=True, exist_ok=True)


def pareto_suffix(SCENARIO="A", SIGMA="Adaptive", K_TOTAL=20, BETA=0.30, WEIGHT_TYPE="risk", KEPT_MEVCUT=None, MCDM_METHOD="VIKOR", MCDM_FOCUS="Baseline"):
    sg_str = "" if SIGMA == "800" else f"_sg{SIGMA}"
    b_str = f"_b{int(BETA * 100)}"
    k_str = f"_K{K_TOTAL}"
    nm_str = "_nomez" if KEPT_MEVCUT is not None and len(KEPT_MEVCUT) == 0 else ""
    wt_str = f"_{WEIGHT_TYPE}"
    mc_str = f"_{MCDM_METHOD.lower()}_{MCDM_FOCUS.lower()}"
    return f"S{SCENARIO}{sg_str}{b_str}{k_str}{nm_str}{wt_str}{mc_str}"


def main(SCENARIO="A", SIGMA="Adaptive", K_TOTAL=20, BETA=0.30, WEIGHT_TYPE="risk", KEPT_MEVCUT=None, FIXED_ADAY=None, MCDM_METHOD="VIKOR", MCDM_FOCUS="Baseline"):
    if KEPT_MEVCUT is None:
        KEPT_MEVCUT = get_mevcut_indices()
    if FIXED_ADAY is None:
        FIXED_ADAY = []

    logger.info(f"== Pareto Analizi Basliyor (K_Total={K_TOTAL}, Sigma={SIGMA}, Weight={WEIGHT_TYPE}, mcdm={MCDM_METHOD}/{MCDM_FOCUS}) ==")

    # 1. Veri Okuma
    fcm = fuzzy_coverage_paths(SIGMA)
    adaylar = pd.read_excel(DATA / "adaylar_140.xlsx")
    mevcut = pd.read_excel(DATA / "mevcut_12.xlsx")
    if WEIGHT_TYPE == "risk":
        weight_df = pd.read_excel(DATA / "mahalle_risk.xlsx")
        val_col = "risk_score"
    elif WEIGHT_TYPE == "population":
        weight_df = pd.read_excel(DATA / "mahalle_nufus.xlsx")
        val_col = "nufus_2024"
    else:
        weight_df = pd.read_excel(DATA / "mahalle_risk.xlsx")
        val_col = "risk_score"

    mu_aday = pd.read_excel(fcm["mu_aday"], index_col=0)
    mu_mevcut = pd.read_excel(fcm["mu_mevcut"], index_col=0)
    q_series = load_mcdm_column(MCDM_METHOD, MCDM_FOCUS)

    adaylar["Mahalle_norm"] = adaylar["Mahalle"].apply(norm_mahalle)
    mevcut["mahalle_norm"] = mevcut["mahalle"].apply(norm_mahalle)
    weight_df["mahalle_norm"] = weight_df["mahalle"].apply(norm_mahalle)

    mahalleler = list(mu_aday.columns)
    n_mah = len(mahalleler)
    n_aday = len(adaylar)

    # Risk skoru normalizasyonu
    weight_dict = weight_df.set_index("mahalle_norm")[val_col].to_dict()
    R_i = np.array([weight_dict.get(m, 1.0) for m in mahalleler])
    R_max = R_i.max()
    R_i_norm = R_i / (R_max + 1e-9)

    # Diger parametreler
    P_j = adaylar["p_access_road"].values
    MU = mu_aday.values
    q_j = q_series.values
    Q_i = load_q_vector(SCENARIO, mahalleler)
    
    mu_mev_sum = np.zeros(n_mah)
    mevcut_counts = np.zeros(n_mah)
    if len(KEPT_MEVCUT) > 0:
        mu_mev_sum = mu_mevcut.iloc[KEPT_MEVCUT].sum(axis=0).values
        for idx in KEPT_MEVCUT:
            m = mevcut.iloc[idx]["mahalle_norm"]
            if m in mahalleler:
                mevcut_counts[mahalleler.index(m)] += 1

    aday_mah_idx = []
    for m in adaylar["Mahalle_norm"]:
        aday_mah_idx.append(mahalleler.index(m) if m in mahalleler else -1)

    # Dinamik Epsilon Taramasi
    eps_range = np.linspace(0.80, 1.20, 20)
    
    rows = []
    pareto_points = []
    
    for eps in eps_range:
        prob = pulp.LpProblem(f"Eps_{eps:.3f}", pulp.LpMaximize)
        
        # solver_core helpers
        X, coverage = build_base_variables_and_coverage(n_aday, n_mah, MU, P_j, Q_i, mu_mev_sum)

        Z_risk = pulp.lpSum(R_i_norm[i] * coverage[i] for i in range(n_mah))
        Z_quality = pulp.lpSum(q_j[j] * X[j] for j in range(n_aday))
        
        # AUGMECON2: Epsilon kısıtları için surplus (artık) değişkenleri
        surplus = [pulp.LpVariable(f"surplus_{i}", lowBound=0) for i in range(n_mah)]
        
        # Amaç fonksiyonuna surplus değişkenlerini küçük pozitif katsayı ile ekle (weakly efficient çözümleri engellemek için)
        prob += Z_risk + BETA * Z_quality + 1e-5 * pulp.lpSum(surplus[i] for i in range(n_mah))

        # Base constraints from solver_core
        add_base_constraints(prob, X, coverage, K_TOTAL, KEPT_MEVCUT, FIXED_ADAY, 
                             aday_mah_idx, mevcut_counts, R_i_norm, n_mah)
        
        for i in range(n_mah):
            # AUGMECON2 kısıtı: cov_i - surplus_i = eps (cov_i >= eps ile eşdeğerdir)
            prob += coverage[i] - surplus[i] == eps, f"eps_con_{i}"

        solver = get_solver(time_limit=30, msg=0)
        prob.solve(solver)
        st = pulp.LpStatus[prob.status]

        if st == "Optimal":
            selected_idx = [j for j in range(n_aday) if X[j].varValue is not None and X[j].varValue > 0.5]
            cov_vals = [Q_i[i] * (mu_mev_sum[i] + sum(MU[j, i] * P_j[j] for j in selected_idx)) for i in range(n_mah)]
            Z_risk_val = sum(R_i_norm[i] * cov_vals[i] for i in range(n_mah))
            rxc = Z_risk_val
            min_c = min(cov_vals)
            avg_c = np.mean(cov_vals)
            
            rows.append({
                "eps_target": eps,
                "status": st,
                "RxC": round(rxc, 4),
                "actual_min_cov": round(min_c, 4),
                "avg_cov": round(avg_c, 4),
                "selected_sites": ",".join(map(str, sorted([int(adaylar.iloc[j]["S_No"]) for j in selected_idx])))
            })
            pareto_points.append((min_c, rxc))
            logger.info(f"  eps={eps:.3f} -> Optimal | RxC={rxc:.4f}, min_C={min_c:.4f}, avg_C={avg_c:.4f}")
        else:
            logger.info(f"  eps={eps:.3f} -> {st} (Cozumsuz)")

    # Sonuclari Kaydet
    df = pd.DataFrame(rows)
    suffix = pareto_suffix(SCENARIO, SIGMA, K_TOTAL, BETA, WEIGHT_TYPE, KEPT_MEVCUT, MCDM_METHOD, MCDM_FOCUS)
    out_file = OUT / f"pareto_results_{suffix}.xlsx"
    df.to_excel(out_file, index=False)
    
    # Pareto Grafıgini Ciz
    if len(pareto_points) > 1:
        # Tekrar eden (min_c, rxc) noktalarini filtrele
        unique_points = list(set(pareto_points))
        unique_points.sort() # min_c'ye gore sirala
        
        X_vals = [p[0] for p in unique_points]
        Y_vals = [p[1] for p in unique_points]
        
        plt.figure(figsize=(10, 6))
        plt.plot(X_vals, Y_vals, marker='o', linestyle='-', color='b', linewidth=2, markersize=8)
        
        # Noktalari etiketle
        for i, (x, y) in enumerate(unique_points):
            plt.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0,10), ha='center')
            
        plt.title(f"Pareto Cephesi (Trade-off): Mekansal Esitlik vs. Toplam Fayda (K={K_TOTAL})")
        plt.xlabel("Minimum Mahalle Kapsamasi (min_C) -> Sosyal Esitlik Artar")
        plt.ylabel("Toplam Fayda (RxC) -> Verimlilik Artar")
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plot_file = OUT / f"pareto_front_{suffix}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        logger.info(f"\n[+] Pareto grafıgi kaydedildi: {plot_file}")
        
    logger.info(f"[+] Sonuclar Excel'e kaydedildi: {out_file}")
    logger.info("== 13_eps_constraint.py tamamlandi ==")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="A", choices=["A", "B"])
    parser.add_argument("--sigma", type=str, default="Adaptive")
    parser.add_argument("--K", type=int, default=8)
    parser.add_argument("--beta", type=float, default=0.30)
    parser.add_argument("--no-mevcut", action="store_true")
    parser.add_argument("--weight", type=str, default="risk", choices=["risk", "population"])
    parser.add_argument("--mcdm", type=str, default="VIKOR", choices=list(MCDM_COLUMNS))
    parser.add_argument("--mcdm-focus", type=str, default="Baseline", choices=["Baseline", "DamageFocused", "InfrastructureFocused"])
    args = parser.parse_args()

    kept = [] if args.no_mevcut else get_mevcut_indices()
    k_tot = args.K if args.no_mevcut else args.K + len(get_mevcut_indices())
    main(SCENARIO=args.scenario, SIGMA=args.sigma, K_TOTAL=k_tot, BETA=args.beta, WEIGHT_TYPE=args.weight, KEPT_MEVCUT=kept, MCDM_METHOD=args.mcdm, MCDM_FOCUS=args.mcdm_focus)

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
from scenario_utils import load_q_vector, fuzzy_coverage_paths

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
RES  = ROOT / "results"
OUT  = ROOT / "results" / "eps_constraint"
OUT.mkdir(parents=True, exist_ok=True)

# K=8, S=Adaptive senaryosunda min_C 0.995 civarinda cikiyordu.
# K=20'de min_C 1.089 civarinda.
# Dolayisiyla epsilon taramasini buna gore dinamik yapacagiz.

def norm_mahalle(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tr = str.maketrans({"Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U", "ç": "C", "ğ": "G", "ı": "I", "ö": "O", "ş": "S", "ü": "U"})
    return s.strip().translate(tr).upper()

def main(SCENARIO="A", SIGMA="Adaptive", K_TOTAL=20, BETA=0.30, WEIGHT_TYPE="risk", KEPT_MEVCUT=None, FIXED_ADAY=None):
    if KEPT_MEVCUT is None:
        KEPT_MEVCUT = list(range(12))
    if FIXED_ADAY is None:
        FIXED_ADAY = []

    print(f"== Pareto Analizi Basliyor (K_Total={K_TOTAL}, Sigma={SIGMA}, Weight={WEIGHT_TYPE}) ==")
    
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
    vikor = pd.read_excel(RES / "mcdm" / "vikor_q.xlsx")

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
    q_j = vikor["Q_benefit_Baseline_AHP"].values
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
        X = [pulp.LpVariable(f"X_{j}", cat="Binary") for j in range(n_aday)]

        coverage = [
            Q_i[i] * (mu_mev_sum[i] + pulp.lpSum(MU[j, i] * P_j[j] * X[j] for j in range(n_aday)))
            for i in range(n_mah)
        ]

        Z_risk = pulp.lpSum(R_i_norm[i] * coverage[i] for i in range(n_mah))
        Z_quality = pulp.lpSum(q_j[j] * X[j] for j in range(n_aday))
        prob += Z_risk + BETA * Z_quality

        prob += pulp.lpSum(X) == (K_TOTAL - len(KEPT_MEVCUT))
        for f_idx in FIXED_ADAY:
            prob += X[f_idx] == 1
        
        for i in range(n_mah):
            # 1. Riske Orantili (Faz 8 Sabit Kisit)
            prob += coverage[i] >= 0.50 * R_i_norm[i]
            
            # 2. Min 1 Konteyner (Faz 8 Sabit Kisit)
            adaylar_i = [j for j in range(n_aday) if aday_mah_idx[j] == i]
            prob += pulp.lpSum(X[j] for j in adaylar_i) + mevcut_counts[i] >= 1
            
            # 3. Epsilon-Constraint (Minimum Kapsama Esitlik Kisiti)
            prob += coverage[i] >= eps

        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
        prob.solve(solver)
        st = pulp.LpStatus[prob.status]

        if st == "Optimal":
            selected_idx = [j for j in range(n_aday) if X[j].varValue is not None and X[j].varValue > 0.5]
            cov_vals = [Q_i[i] * (mu_mev_sum[i] + sum(MU[j, i] * P_j[j] for j in selected_idx)) for i in range(n_mah)]
            Z_risk_val = sum(R_i_norm[i] * cov_vals[i] for i in range(n_mah))
            rxc = Z_risk_val
            min_c = min(cov_vals)
            
            rows.append({
                "eps_target": eps,
                "status": st,
                "RxC": round(rxc, 4),
                "actual_min_cov": round(min_c, 4),
                "selected_sites": ",".join(map(str, sorted([int(adaylar.iloc[j]["S_No"]) for j in selected_idx])))
            })
            pareto_points.append((min_c, rxc))
            print(f"  eps={eps:.3f} -> Optimal | RxC={rxc:.4f}, min_C={min_c:.4f}")
        else:
            print(f"  eps={eps:.3f} -> {st} (Cozumsuz)")

    # Sonuclari Kaydet
    df = pd.DataFrame(rows)
    out_file = OUT / f"pareto_results_K{K_TOTAL}_{WEIGHT_TYPE}.xlsx"
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
        
        plot_file = OUT / f"pareto_front_K{K_TOTAL}_{WEIGHT_TYPE}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"\n[+] Pareto grafıgi kaydedildi: {plot_file}")
        
    print(f"[+] Sonuclar Excel'e kaydedildi: {out_file}")
    print("== 13_eps_constraint.py tamamlandi ==")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="A", choices=["A", "B"])
    parser.add_argument("--sigma", type=str, default="Adaptive")
    parser.add_argument("--K", type=int, default=8)
    parser.add_argument("--beta", type=float, default=0.30)
    parser.add_argument("--no-mevcut", action="store_true")
    parser.add_argument("--weight", type=str, default="risk", choices=["risk", "population"])
    args = parser.parse_args()
    
    kept = [] if args.no_mevcut else list(range(12))
    k_tot = args.K if args.no_mevcut else args.K + 12
    main(SCENARIO=args.scenario, SIGMA=args.sigma, K_TOTAL=k_tot, BETA=args.beta, WEIGHT_TYPE=args.weight, KEPT_MEVCUT=kept)

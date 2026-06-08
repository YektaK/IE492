# -*- coding: utf-8 -*-
"""
16_mclp.py
Maximal Covering Location Problem (MCLP) Benchmark Modeli

Bu model, ana IP modelimizin karsilastirilmasi (benchmark) amaciyla yazilmistir.
Klasik MCLP mantigiyla calisir:
- Eger aday alan ile mahalle arasindaki mesafe <= S ise kapsama (a_ij) 1'dir.
- Amac: Sinirli sayidaki (K) konteyneri secerek, kapsanan toplam talebi (Nufus veya Barinma) maksimize etmek.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pulp

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import norm_mahalle, DATA_DIR, MODELS_DIR as RESULTS_DIR, logger, get_mevcut_indices
from scenario_utils import fuzzy_coverage_paths
from solver_core import get_solver

def run_mclp(S=800, K_TOTAL=20, weight_type="population", KEPT_MEVCUT=None, FIXED_ADAY=None):
    if KEPT_MEVCUT is None:
        KEPT_MEVCUT = get_mevcut_indices()
    if FIXED_ADAY is None:
        FIXED_ADAY = []
    logger.info(f"--- MCLP Benchmark Basliyor ---")
    logger.info(f"Parametreler: K_Total={K_TOTAL}, S={S}m, Agirlik={weight_type}, KeptMevcut={len(KEPT_MEVCUT)}, FixedAday={len(FIXED_ADAY)}")
    
    # 1. Veri Okuma
    fcm = fuzzy_coverage_paths(str(S))
    adaylar = pd.read_excel(DATA_DIR / "adaylar_140.xlsx")
    mevcut = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
    dist_aday = pd.read_excel(fcm["dist_aday"], index_col=0)
    dist_mevcut = pd.read_excel(fcm["dist_mevcut"], index_col=0)
    
    nufus = pd.read_excel(DATA_DIR / "mahalle_nufus.xlsx")
    barinma = pd.read_excel(DATA_DIR / "mahalle_barinma.xlsx")
    risk = pd.read_excel(DATA_DIR / "mahalle_risk.xlsx")

    # Mahalle isimleri standardizasyonu
    adaylar["Mahalle_norm"] = adaylar["Mahalle"].apply(norm_mahalle)
    mevcut["mahalle_norm"] = mevcut["mahalle"].apply(norm_mahalle)
    nufus["mahalle_norm"] = nufus["mahalle"].apply(norm_mahalle)
    barinma["mahalle_norm"] = barinma["mahalle"].apply(norm_mahalle)
    risk["mahalle_norm"] = risk["mahalle"].apply(norm_mahalle)
    
    mahalleler = list(dist_aday.columns)
    n_mah = len(mahalleler)
    n_aday = len(adaylar)
    n_mevcut = len(mevcut)

    # Agirlik (Talep) Vektoru Secimi
    if weight_type == "population":
        w_dict = nufus.set_index("mahalle_norm")["nufus_2024"].to_dict()
    elif weight_type == "shelter":
        w_dict = barinma.set_index("mahalle_norm")["hane_ihtiyaci"].to_dict()
    elif weight_type == "risk":
        w_dict = risk.set_index("mahalle_norm")["risk_score"].to_dict()
    else:
        raise ValueError("Gecersiz agirlik turu: population, shelter veya risk olmali.")

    W_raw = np.array([w_dict.get(m, 0) for m in mahalleler])
    # Oransal Olcekleme
    W = W_raw / (W_raw.max() + 1e-9)
    
    # 2. Kapsama Matrisleri (a_ij)
    # Adaylarin Kapsamasi (140 x 15)
    A_aday = (dist_aday.values <= S).astype(int)
    
    # Mevcutlarin Kapsamasi
    mevcut_kapsanan_mahalleler = np.zeros(n_mah)
    if len(KEPT_MEVCUT) > 0:
        A_mevcut = (dist_mevcut.values <= S).astype(int)
        mevcut_kapsanan_mahalleler = A_mevcut[KEPT_MEVCUT, :].max(axis=0) # Sadece korunan mevcutlar kapsiyorsa 1
        
    # 3. Model Formulasyonu
    prob = pulp.LpProblem("MCLP_Sultanbeyli", pulp.LpMaximize)
    
    # Karar Degiskenleri
    X = [pulp.LpVariable(f"X_{j}", cat="Binary") for j in range(n_aday)]
    Y = [pulp.LpVariable(f"Y_{i}", cat="Binary") for i in range(n_mah)]
    
    # Amac Fonksiyonu: Kapsanan talebi maksimize et
    prob += pulp.lpSum(W[i] * Y[i] for i in range(n_mah))
    
    # Kisit 1: Toplam yeni konteyner sayisi
    prob += pulp.lpSum(X) == (K_TOTAL - len(KEPT_MEVCUT))
    
    # Kisit 1b: Zorunlu Adaylar
    for f_idx in FIXED_ADAY:
        prob += X[f_idx] == 1
    
    # Kisit 2: Kapsama Iliskisi (Mevcut veya yeni adaylardan en az 1'i kapsiyorsa Y_i 1 olabilir)
    for i in range(n_mah):
        prob += pulp.lpSum(A_aday[j, i] * X[j] for j in range(n_aday)) + mevcut_kapsanan_mahalleler[i] >= Y[i]
        
    # Cozum
    t0 = time.time()
    prob.solve(get_solver(msg=0))
    dt = time.time() - t0
    
    status = pulp.LpStatus[prob.status]
    obj_val = pulp.value(prob.objective)
    
    selected_idx = [j for j in range(n_aday) if X[j].varValue is not None and X[j].varValue > 0.5]
    covered_idx = [i for i in range(n_mah) if Y[i].varValue is not None and Y[i].varValue > 0.5]
    
    toplam_talep = W.sum()
    kapsanan_oran = obj_val / toplam_talep if toplam_talep > 0 else 0
    
    logger.info(f"Cozum Durumu: {status} ({dt:.2f} sn)")
    logger.info(f"Maksimum Kapsanan {weight_type.capitalize()}: {obj_val:,.0f} / {toplam_talep:,.0f} (%{kapsanan_oran*100:.1f})")
    logger.info(f"Kapsanan Mahalle Sayisi: {len(covered_idx)} / {n_mah}")
    logger.info(f"Secilen Aday ID'leri: {[int(adaylar.iloc[j]['S_No']) for j in selected_idx]}")
    
    # 4. Sonuclari Kaydet
    vname = f"MCLP_K{K_TOTAL}_S{S}_{weight_type}"
    if len(KEPT_MEVCUT) == 0: vname += "_nomez"
    
    secilen_df = adaylar.iloc[selected_idx][["S_No", "Alan_Adi", "Mahalle", "Enlem", "Boylam"]].copy()
    secilen_df.to_excel(RESULTS_DIR / f"{vname}_secilenler.xlsx", index=False)
    
    mahalle_sonuclar = pd.DataFrame({
        "Mahalle": mahalleler,
        "Talep": W,
        "Kapsandi_mi": [1 if i in covered_idx else 0 for i in range(n_mah)]
    })
    mahalle_sonuclar.to_excel(RESULTS_DIR / f"{vname}_mahalleler.xlsx", index=False)
    logger.info(f"Sonuclar '{vname}' önekiyle kaydedildi.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--S", type=int, default=800, help="Kapsama Yaricapi (metre)")
    parser.add_argument("--K", type=int, default=8, help="Eklenecek veya toplam konteyner")
    parser.add_argument("--weight", type=str, default="population", choices=["population", "shelter", "risk"])
    parser.add_argument("--no-mevcut", action="store_true")
    args = parser.parse_args()
    
    kept = [] if args.no_mevcut else get_mevcut_indices()
    k_tot = args.K if args.no_mevcut else args.K + len(get_mevcut_indices())
    run_mclp(S=args.S, K_TOTAL=k_tot, weight_type=args.weight, KEPT_MEVCUT=kept)

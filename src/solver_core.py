# -*- coding: utf-8 -*-
"""
solver_core.py
Merkezi PuLP IP/MILP Model Kurulum ve Çözüm Yardımcıları.
"""

import pulp
import numpy as np

def get_solver(time_limit=30, msg=0):
    """
    Sistemde HiGHS (highspy) varsa onu, yoksa CBC çözücüyü döndürür.
    """
    from config import logger
    available_solvers = pulp.listSolvers(onlyAvailable=True)
    if "HiGHS" in available_solvers:
        logger.info(f"HiGHS cozucusu secildi (timeLimit={time_limit}s, msg={msg}).")
        return pulp.HiGHS(msg=msg, timeLimit=time_limit)
    else:
        logger.info(f"HiGHS cozucusu bulunamadi, CBC cozucusune geri donuluyor (timeLimit={time_limit}s, msg={msg}).")
        return pulp.PULP_CBC_CMD(msg=msg, timeLimit=time_limit)


def dict_to_matrix(MU_dict, S_Nos, mahalleler):
    """
    Sözlük formatındaki MU matrisini (S_No, mahalle) -> float numpy array formatına çevirir (n_aday x n_mah).
    """
    n_aday = len(S_Nos)
    n_mah = len(mahalleler)
    matrix = np.zeros((n_aday, n_mah))
    for j in range(n_aday):
        for i in range(n_mah):
            matrix[j, i] = MU_dict.get((S_Nos[j], mahalleler[i]), 0.0)
    return matrix

def build_base_variables_and_coverage(n_aday, n_mah, MU_matrix, P_j, Q_i, mu_mev_sum, prefix="X"):
    """
    Aday seçim karar değişkenlerini (Binary X) ve mahalle bazlı kapsama (coverage) sembolik ifadelerini oluşturur.
    """
    X = [pulp.LpVariable(f"{prefix}_{j}", cat="Binary") for j in range(n_aday)]
    coverage = [
        Q_i[i] * (mu_mev_sum[i] + pulp.lpSum(MU_matrix[j, i] * P_j[j] * X[j] for j in range(n_aday)))
        for i in range(n_mah)
    ]
    return X, coverage

def add_base_constraints(prob, X, coverage, K_TOTAL, KEPT_MEVCUT, FIXED_ADAY, 
                         aday_mah_idx, mevcut_counts, R_i, n_mah, min_one=True, risk_prop=True):
    """
    Tüm modeller için geçerli olan temel kısıtları (Bütçe, Zorunlu Adaylar, En Az 1 Konteyner ve Risk Orantılı Kapsama) modele ekler.
    """
    # 1. Bütçe Kısıtı
    prob += pulp.lpSum(X) == (K_TOTAL - len(KEPT_MEVCUT))
    
    # 2. Zorunlu Seçilen Adaylar
    for f_idx in FIXED_ADAY:
        prob += X[f_idx] == 1
        
    # 3. Mahalle Kısıtları
    for i in range(n_mah):
        # 3a. En Az 1 Konteyner Kısıtı
        if min_one:
            adaylar_i = [j for j, idx in enumerate(aday_mah_idx) if idx == i]
            prob += pulp.lpSum(X[j] for j in adaylar_i) + mevcut_counts[i] >= 1
            
        # 3b. Esnek Riske Orantılı Kapsama Kısıtı (Risk_norm_i'nin %50'si kadar)
        if risk_prop:
            prob += coverage[i] >= 0.50 * R_i[i]

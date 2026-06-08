"""
02b_bwm_weights.py
Best-Worst Method (BWM) ile Kriter Agirliklarinin Hesaplanmasi

NOT: Buradaki Best-to-Others (BO) ve Others-to-Worst (OW) vektorleri
sistemi test etmek amaciyla SENTETIK olarak uretilmistir.
Gercek bir uygulamada karar vericilerin (uzmanlarin) 1-9 arasi
birebir degerlendirme yapmasi gerekmektedir. Karar vericiler bu degerleri
asagidaki sozluge girerek betigi tekrar calistirabilir.

Linear BWM Optimizasyon Modeli (SciPy kullanilarak) cozulmustur.
"""

import sys
import argparse
import numpy as np
import pandas as pd
from scipy.optimize import minimize

import config
from config import RESULTS_DIR

MCDM_DIR = RESULTS_DIR / "mcdm"
MCDM_DIR.mkdir(parents=True, exist_ok=True)

# Kriterler (AHP ile ayni sira)
CRITERIA = ["Nufus", "Deprem_Riski", "Erisilebilirlik", "Ulasim"]

# Sentetik BWM Verileri (Uzman Gorusleri Temsili)
# 1-9 skalasi (1: Esit, 9: Mutlak Ustunluk)
bwm_scenarios = {
    "Baseline": {
        "best": 0,    # Nufus
        "worst": 3,   # Ulasim
        "BO": [1, 2, 4, 8],      # Best (Nufus) to Others: Nufus=1, Deprem=2, Erisim=4, Ulasim=8
        "OW": [8, 4, 2, 1]       # Others to Worst (Ulasim): Nufus=8, Deprem=4, Erisim=2, Ulasim=1
    },
    "DamageFocused": {
        "best": 1,    # Deprem Riski
        "worst": 2,   # Erisilebilirlik
        "BO": [3, 1, 9, 5],      # Best (Deprem) to Others: Nufus=3, Deprem=1, Erisim=9, Ulasim=5
        "OW": [3, 9, 1, 2]       # Others to Worst (Erisim): Nufus=3, Deprem=9, Erisim=1, Ulasim=2
    },
    "InfrastructureFocused": {
        "best": 3,    # Ulasim
        "worst": 0,   # Nufus
        "BO": [7, 5, 2, 1],      # Best (Ulasim) to Others: Nufus=7, Deprem=5, Erisim=2, Ulasim=1
        "OW": [1, 2, 4, 7]       # Others to Worst (Nufus): Nufus=1, Deprem=2, Erisim=4, Ulasim=7
    }
}

def solve_linear_bwm(BO, OW, best_idx, worst_idx, n_criteria=4):
    """
    Linear BWM modelini SciPy minimize ile cozer.
    min xi
    s.t.
      w_B - a_Bj * w_j <= xi
      a_Bj * w_j - w_B <= xi
      w_j - a_jW * w_W <= xi
      a_jW * w_W - w_j <= xi
      sum(w) = 1
      w_j >= 0
    """
    # x = [w1, w2, w3, w4, xi]
    def objective(x):
        return x[-1]
        
    def const_sum(x):
        return np.sum(x[:-1]) - 1.0
        
    constraints = [{'type': 'eq', 'fun': const_sum}]
    
    # Esitsizlik kisitlari (x >= 0 uyarlandiginda: fun(x) >= 0 seklinde scipy standardi)
    for j in range(n_criteria):
        # Best-to-Others
        # xi - (w_B - a_Bj * w_j) >= 0  =>  xi - w_B + a_Bj * w_j >= 0
        constraints.append({'type': 'ineq', 'fun': lambda x, j=j: x[-1] - x[best_idx] + BO[j] * x[j]})
        # xi - (a_Bj * w_j - w_B) >= 0  =>  xi - a_Bj * w_j + w_B >= 0
        constraints.append({'type': 'ineq', 'fun': lambda x, j=j: x[-1] - BO[j] * x[j] + x[best_idx]})
        
        # Others-to-Worst
        # xi - (w_j - a_jW * w_W) >= 0  =>  xi - w_j + a_jW * x[worst_idx] >= 0
        constraints.append({'type': 'ineq', 'fun': lambda x, j=j: x[-1] - x[j] + OW[j] * x[worst_idx]})
        # xi - (a_jW * w_W - w_j) >= 0  =>  xi - OW[j] * x[worst_idx] + x[j] >= 0
        constraints.append({'type': 'ineq', 'fun': lambda x, j=j: x[-1] - OW[j] * x[worst_idx] + x[j]})

    # Sinirlar (Bounds): w_i >= 0, xi >= 0
    bounds = [(0, 1) for _ in range(n_criteria)] + [(0, None)]
    
    # Baslangic tahmini
    x0 = np.array([1/n_criteria]*n_criteria + [0.1])
    
    res = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
    
    if res.success:
        w = res.x[:-1]
        xi = res.x[-1]
        # Consistency ratio (Rezaei 2015, Omega)
        a_BW = BO[worst_idx]                     # Best-to-Worst preference
        CI_TABLE = {1: 0.00, 2: 0.44, 3: 1.00, 4: 1.63, 5: 2.30,
                    6: 3.00, 7: 3.73, 8: 4.47, 9: 5.23}
        max_xi = CI_TABLE.get(a_BW, 5.23)
        cr = xi / max_xi if max_xi > 0 else 0.0
        return w, xi, cr
    else:
        raise ValueError("BWM Optimizasyonu cozum bulamadi: " + res.message)

def main():
    print("="*60)
    print("BEST-WORST METHOD (BWM) AGIRLIK HESAPLAMASI")
    print("="*60)
    print("NOT: BO ve OW vektorleri sentetiktir (karar vericilerin ornek gridleri).")
    
    results = []
    
    for scen_name, data in bwm_scenarios.items():
        w, xi, cr = solve_linear_bwm(data["BO"], data["OW"], data["best"], data["worst"])
        print(f"\n[+] Senaryo: {scen_name}")
        print(f"    Tutarlilik: xi*={xi:.4f}, CR={cr:.4f} (CR < 0.10 kabul edilebilir)")
        for i, c in enumerate(CRITERIA):
            print(f"    - {c:15s}: {w[i]:.4f}")
            
        res_dict = {"Senaryo": scen_name, "xi_star": xi, "CR": cr}
        for i, c in enumerate(CRITERIA):
            res_dict[c] = w[i]
        results.append(res_dict)
        
    df = pd.DataFrame(results)
    out_path = MCDM_DIR / "bwm_weights.xlsx"
    df.to_excel(out_path, index=False)
    print(f"\n[+] BWM agirliklari kaydedildi: {out_path}")
    print("="*60)

if __name__ == "__main__":
    main()

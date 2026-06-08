"""
03c_vikor.py
Sultanbeyli Konteyner - VIKOR ile aday parsel puanlamasi

AHP (ve varsa BWM) agirliklarini okuyup VIKOR yontemiyle aday parselleri puanlar.
VIKOR'da Q_i 0'a yaklastikca iyidir. IP modeline (Maksimizasyon)
uygun olmasi icin (1 - Q_i) skoru da uretilir.
"""

import numpy as np
import pandas as pd

import config
from config import DATA_DIR as PROCESSED, RESULTS_DIR

AHP_DIR = RESULTS_DIR / "ahp"
MCDM_DIR = RESULTS_DIR / "mcdm"

KRITER_SUTUNLARI = ["C1_hasar_risk_amp", "C2_lojistik_amp", "C3_bosluk_amp", "C4_barinma_amp"]
# Siralama: Nufus, Deprem_Riski, Erisilebilirlik, Ulasim

def calc_vikor(mat, w, v=0.5):
    # mat: n x m (140 x 4)
    # Tum kriterler Max-yonlu (Benefit)
    f_star = mat.max(axis=0)
    f_minus = mat.min(axis=0)
    
    # Eger f_star == f_minus ise sifira bolme hatasini engelle
    denom = f_star - f_minus
    denom[denom == 0] = 1e-12
    
    # Norm matrisi
    norm_mat = (f_star - mat) / denom
    
    # S_i ve R_i
    weighted_mat = norm_mat * w
    S = weighted_mat.sum(axis=1)
    R = weighted_mat.max(axis=1)
    
    S_star = S.min()
    S_minus = S.max()
    R_star = R.min()
    R_minus = R.max()
    
    S_range = S_minus - S_star if S_minus > S_star else 1e-12
    R_range = R_minus - R_star if R_minus > R_star else 1e-12
    
    Q = v * (S - S_star) / S_range + (1 - v) * (R - R_star) / R_range
    
    # 1 - Q (Fayda skoruna cevirme)
    Q_benefit = 1 - Q
    return S, R, Q, Q_benefit

def main():
    print("="*60)
    print("VIKOR YONTEMI ILE PUANLAMA")
    print("="*60)
    
    criteria = pd.read_excel(PROCESSED / "criteria_matrix.xlsx")
    mat = criteria[KRITER_SUTUNLARI].values
    
    # Sonuclari saklayacagimiz dataframe
    sonuclar = {"S_No": criteria["S_No"].values, "Mahalle": criteria["Mahalle"].values}
    
    # 1. AHP Agirliklariyla
    print("[+] AHP-Hibrit Agirliklari Okunuyor...")
    ahp_df = pd.read_excel(AHP_DIR / "ahp_weights_hybrid.xlsx")
    
    for _, row in ahp_df.iterrows():
        scen = row["scenario"]
        w = np.array([row["C1_Nufus_hyb"], row["C2_Deprem_hyb"], row["C3_Erisim_hyb"], row["C4_Ulasim_hyb"]])
        S, R, Q, Q_ben = calc_vikor(mat, w)
        sonuclar[f"Q_{scen}_AHP"] = Q
        sonuclar[f"Q_benefit_{scen}_AHP"] = Q_ben
        print(f"  - Senaryo {scen} (AHP) tamamlandi. (Max Q_ben: {Q_ben.max():.4f})")
        
    # 2. BWM Agirliklariyla (Eger varsa)
    bwm_path = MCDM_DIR / "bwm_weights.xlsx"
    if bwm_path.exists():
        print("\n[+] BWM Agirliklari Okunuyor...")
        bwm_df = pd.read_excel(bwm_path)
        for _, row in bwm_df.iterrows():
            scen = row["Senaryo"]
            w = np.array([row["Nufus"], row["Deprem_Riski"], row["Erisilebilirlik"], row["Ulasim"]])
            S, R, Q, Q_ben = calc_vikor(mat, w)
            sonuclar[f"Q_{scen}_BWM"] = Q
            sonuclar[f"Q_benefit_{scen}_BWM"] = Q_ben
            print(f"  - Senaryo {scen} (BWM) tamamlandi. (Max Q_ben: {Q_ben.max():.4f})")
            
    res_df = pd.DataFrame(sonuclar)
    out_path = MCDM_DIR / "vikor_q.xlsx"
    res_df.to_excel(out_path, index=False)
    print(f"\n[+] Sonuclar kaydedildi: {out_path}")
    print("="*60)

if __name__ == "__main__":
    main()

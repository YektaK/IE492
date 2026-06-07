"""
03d_electre.py
Sultanbeyli Konteyner - ELECTRE (Net Outranking Flow) ile aday puanlamasi

AHP (ve varsa BWM) agirliklarini okur. Uyum (Concordance) matrisini hesaplar.
Geleneksel ELECTRE I'deki gibi kati esik (threshold) tabanli outranking grafigi yerine,
PROMETHEE benzeri bir Net Uyum Akisi (Net Concordance Flow) cikararak, IP modelinde
kullanilabilecek [0, 1] araliginda skaler bir fayda skoru (q_j) uretir.
"""

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
AHP_DIR = PROJECT_ROOT / "results" / "ahp"
MCDM_DIR = PROJECT_ROOT / "results" / "mcdm"

KRITER_SUTUNLARI = ["C1_hasar_risk_amp", "C2_lojistik_amp", "C3_bosluk_amp", "C4_barinma_amp"]

def calc_electre_net_flow(mat, w):
    n, m = mat.shape
    C = np.zeros((n, n))
    
    # Concordance matrisi (Benefit kriterleri icin i >= k)
    for i in range(n):
        for k in range(n):
            if i != k:
                # i'nin k'ya ustun veya esit oldugu kriterlerin agirliklari toplami
                c_sum = 0
                for j in range(m):
                    if mat[i, j] >= mat[k, j]:
                        c_sum += w[j]
                C[i, k] = c_sum

    # Net Outranking Flow (Net Uyum Akisi)
    # i'nin digerlerine ustunluk akisi
    phi_plus = C.sum(axis=1) / (n - 1)
    # Digerlerinin i'ye ustunluk akisi
    phi_minus = C.sum(axis=0) / (n - 1)
    
    # Net Flow
    phi_net = phi_plus - phi_minus
    
    # IP modeli icin [0, 1] araligina normalize et
    p_min = phi_net.min()
    p_max = phi_net.max()
    phi_norm = (phi_net - p_min) / (p_max - p_min + 1e-12)
    
    return phi_net, phi_norm

def main():
    print("="*60)
    print("ELECTRE (NET OUTRANKING FLOW) YONTEMI")
    print("="*60)
    
    criteria = pd.read_excel(PROCESSED / "criteria_matrix.xlsx")
    mat = criteria[KRITER_SUTUNLARI].values
    
    sonuclar = {"S_No": criteria["S_No"].values, "Mahalle": criteria["Mahalle"].values}
    
    # 1. AHP Agirliklari
    print("[+] AHP-Hibrit Agirliklari ile ELECTRE hesaplaniyor...")
    ahp_df = pd.read_excel(AHP_DIR / "ahp_weights_hybrid.xlsx")
    for _, row in ahp_df.iterrows():
        scen = row["scenario"]
        w = np.array([row["C1_Nufus_hyb"], row["C2_Deprem_hyb"], row["C3_Erisim_hyb"], row["C4_Ulasim_hyb"]])
        phi_net, phi_norm = calc_electre_net_flow(mat, w)
        sonuclar[f"NetFlow_{scen}_AHP"] = phi_net
        sonuclar[f"Q_benefit_{scen}_AHP"] = phi_norm
        print(f"  - Senaryo {scen} (AHP) tamam. (Max NetFlow: {phi_net.max():.4f})")
        
    # 2. BWM Agirliklari (Varsa)
    bwm_path = MCDM_DIR / "bwm_weights.xlsx"
    if bwm_path.exists():
        print("\n[+] BWM Agirliklari ile ELECTRE hesaplaniyor...")
        bwm_df = pd.read_excel(bwm_path)
        for _, row in bwm_df.iterrows():
            scen = row["Senaryo"]
            w = np.array([row["Nufus"], row["Deprem_Riski"], row["Erisilebilirlik"], row["Ulasim"]])
            phi_net, phi_norm = calc_electre_net_flow(mat, w)
            sonuclar[f"NetFlow_{scen}_BWM"] = phi_net
            sonuclar[f"Q_benefit_{scen}_BWM"] = phi_norm
            print(f"  - Senaryo {scen} (BWM) tamam. (Max NetFlow: {phi_net.max():.4f})")
            
    res_df = pd.DataFrame(sonuclar)
    out_path = MCDM_DIR / "electre_net_flow.xlsx"
    res_df.to_excel(out_path, index=False)
    print(f"\n[+] Sonuclar kaydedildi: {out_path}")
    print("="*60)

if __name__ == "__main__":
    main()

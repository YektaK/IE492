"""
03a_topsis.py
Sultanbeyli Konteyner - TOPSIS ile aday parsel puanlamasi

3 AHP senaryosu icin ayri ayri CC (Closeness Coefficient) hesaplar.
Girdi  : data/processed/criteria_matrix.xlsx, results/ahp/ahp_weights_hybrid.xlsx
Cikti  : results/mcdm/topsis_cc.xlsx (140 parsel x 3 senaryo x 2 normalizasyon)

Degisiklikler (Faz 2):
  1) Ham degerler yerine Faz 1'de uretilen Amplified (power-transform) sutunlari kullanilir.
  2) Sadece AHP degil, AHP-Entropy hibrit agirliklari kullanilir (w_hyb).
  3) Geleneksel L2 vektor normalizasyonunun yaninda Min-Max normalizasyonu da alternatif olarak eklendi.
     Min-Max normalizasyonu ayrik skorlarin (amplified) ozelligini daha iyi korur.
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
AHP = PROJECT_ROOT / "results" / "ahp"
MCDM = PROJECT_ROOT / "results" / "mcdm"
MCDM.mkdir(parents=True, exist_ok=True)

# Faz 1'den gelen amplified (ayriklastirilmis) kriter sutunlari
KRITER_SUTUNLARI = ["C1_hasar_risk_amp", "C2_lojistik_amp", "C3_bosluk_amp", "C4_barinma_amp"]
KRITER_ADLARI = {
    "C1_hasar_risk_amp": "C1_Nufus",
    "C2_lojistik_amp": "C2_Deprem",
    "C3_bosluk_amp": "C3_Erisim",
    "C4_barinma_amp": "C4_Ulasim",
}
# Tum amplified sutunlar 0-1 arasinda ve max-yonlu tasarlanmistir (C3 dahil, mesafenin normalizasyonunda uzak=max yapildi).

print("[1/4] Kriter matrisi ve Hibrit Agirliklar okunuyor...")
criteria = pd.read_excel(PROCESSED / "criteria_matrix.xlsx")
# AHP-Entropy Hibrit agirliklarini yukle
weights_df = pd.read_excel(AHP / "ahp_weights_hybrid.xlsx")
print(f"  criteria: {criteria.shape}")
print(f"  weights : {weights_df.shape}")

print("\n[2/4] Veri hazirligi (Amplified skorlar zaten max yonlu [0,1])...")
mat = criteria[KRITER_SUTUNLARI].copy().astype(float)
print(f"  karar matrisi: {mat.shape}")

print("\n[3/4] 3 senaryo x 2 normalizasyon icin TOPSIS hesabi...")
sonuclar = {"S_No": criteria["S_No"].values, 
            "Alan_Adi": criteria.get("Alan_Adi", pd.Series([""] * len(criteria))).values, 
            "Mahalle": criteria["Mahalle"].values}

def topsis_calc(mat_data, w_array, norm_type="L2"):
    """TOPSIS hesabi. norm_type: 'L2' veya 'MinMax'"""
    # 1) Normalizasyon
    if norm_type == "L2":
        norm = np.sqrt((mat_data ** 2).sum(axis=0))
        norm = norm.replace(0, 1)
        R = mat_data / norm
    elif norm_type == "MinMax":
        c_min = mat_data.min(axis=0)
        c_max = mat_data.max(axis=0)
        R = (mat_data - c_min) / (c_max - c_min + 1e-12)
    else:
        raise ValueError("Gecersiz norm_type")

    # 2) Agirlikli normalize
    V = R * w_array

    # 3) Ideal (A+) ve Anti-Ideal (A-) (Tum kriterler MAX yonlu)
    A_plus = V.max(axis=0)
    A_minus = V.min(axis=0)

    # 4) Oklid mesafeler
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))

    # 5) CC
    CC = D_minus / (D_plus + D_minus + 1e-12)
    return CC

for _, wrow in weights_df.iterrows():
    senaryo = wrow["scenario"]
    # Hibrit agirliklari kullan (w_hyb)
    w = np.array([wrow["C1_Nufus_hyb"], wrow["C2_Deprem_hyb"], 
                  wrow["C3_Erisim_hyb"], wrow["C4_Ulasim_hyb"]])
    print(f"\n  --- {senaryo} (Hibrit w = {w.round(4)}) ---")

    # L2 Normalizasyon (Geleneksel)
    CC_L2 = topsis_calc(mat, w, norm_type="L2")
    sonuclar[f"CC_{senaryo}_L2"] = CC_L2
    
    # Min-Max Normalizasyon (Onerilen - amplifikasyonu korur)
    CC_MinMax = topsis_calc(mat, w, norm_type="MinMax")
    sonuclar[f"CC_{senaryo}_MinMax"] = CC_MinMax

    print(f"  CC (L2)    : min={CC_L2.min():.4f}, max={CC_L2.max():.4f}, mean={CC_L2.mean():.4f}")
    print(f"  CC (MinMax): min={CC_MinMax.min():.4f}, max={CC_MinMax.max():.4f}, mean={CC_MinMax.mean():.4f}")
    
    top5_L2 = criteria.iloc[CC_L2.argsort()[::-1][:5]]["S_No"].tolist()
    top5_MM = criteria.iloc[CC_MinMax.argsort()[::-1][:5]]["S_No"].tolist()
    print(f"  top 5 (MinMax): {top5_MM} (L2: {top5_L2})")

print("\n[4/4] Kaydediliyor...")
out = pd.DataFrame(sonuclar)
out.to_excel(MCDM / "topsis_cc.xlsx", index=False)

# Sirali (rank) tablo olustur (Sadece MinMax'i baz alarak rank_df olusturalim, modelde MinMax kullanilacak)
rank_df = out.copy()
for s in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
    rank_df[f"rank_{s}"] = rank_df[f"CC_{s}_MinMax"].rank(ascending=False, method="min").astype(int)

rank_df.to_excel(MCDM / "topsis_ranked.xlsx", index=False)
print(f"  -> {MCDM / 'topsis_cc.xlsx'}")
print(f"  -> {MCDM / 'topsis_ranked.xlsx'}")

print("\n" + "=" * 60)
print("TOPSIS TAMAMLANDI")
print("=" * 60)
print("Not: IP optimizasyon modelinde CC_Senaryo_MinMax sutunlari kullanilacaktir.")

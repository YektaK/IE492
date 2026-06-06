"""
03a_topsis.py
Sultanbeyli Konteyner - TOPSIS ile aday parsel puanlamasi

3 AHP senaryosu icin ayri ayri CC (Closeness Coefficient) hesaplar.
Girdi  : data/processed/criteria_matrix.xlsx, results/ahp/ahp_weights.xlsx
Cikti  : results/mcdm/topsis_cc.xlsx (140 parsel x 3 senaryo)

Yontem:
  1) Yon normalizasyonu (TUM KRITERLER MAX)
  2) Agirlikli normalize matris: v_ij = w_j * r_ij
  3) Ideal A+ = max(v_ij), Anti-Ideal A- = min(v_ij)
  4) D+ = ||v - A+||, D- = ||v - A-||
  5) CC = D- / (D+ + D-)  -> [0, 1]
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

# Kriter sutunlari (docx sema: Nufus, Deprem, Erisim, Ulasim)
KRITER_SUTUNLARI = ["C1_hasar_risk", "C2_lojistik", "C3_bosluk_m", "C4_barinma"]
KRITER_ADLARI = {
    "C1_hasar_risk": "C1_Nufus",
    "C2_lojistik": "C2_Deprem",
    "C3_bosluk_m": "C3_Erisim",
    "C4_barinma": "C4_Ulasim",
}
# Erisim mesafesi ters cevrilmeli (uzak = iyi)
TERSINE = {"C3_bosluk_m"}

print("[1/4] Kriter matrisi ve AHP agirliklari okunuyor...")
criteria = pd.read_excel(PROCESSED / "criteria_matrix.xlsx")
weights_df = pd.read_excel(AHP / "ahp_weights.xlsx")
print(f"  criteria: {criteria.shape}")
print(f"  weights : {weights_df.shape}")

print("\n[2/4] Yon normalizasyonu (tersine cevirme) hazirligi...")
# Max yon: yuksek iyi. Erisim mesafesi icin yuksek = uzak = iyi (max yon)
# Bu nedenle TERSINE uygulanmaz. Tutarli: Hepsini max yone cevir, sonra
# normalize et.
mat = criteria[KRITER_SUTUNLARI].copy().astype(float)
print(f"  karar matrisi: {mat.shape}")

print("\n[3/4] 3 senaryo icin TOPSIS hesabi...")
sonuclar = {"S_No": criteria["S_No"].values, "Alan_Adi": criteria.get("Alan_Adi", pd.Series([""] * len(criteria))).values, "Mahalle": criteria["Mahalle"].values}

for _, wrow in weights_df.iterrows():
    senaryo = wrow["scenario"]
    w = np.array([wrow["C1_Nufus"], wrow["C2_Deprem"], wrow["C3_Erisim"], wrow["C4_Ulasim"]])
    print(f"\n  --- {senaryo} (w = {w.round(4)}) ---")

    # Adim 1: Vektor normalizasyonu (L2 norm)
    norm = np.sqrt((mat ** 2).sum(axis=0))
    norm = norm.replace(0, 1)
    R = mat / norm  # normalize matris (140 x 4)

    # Adim 2: Agirlikli normalize
    V = R * w  # V_ij = w_j * r_ij

    # Adim 3: Ideal (A+) ve Anti-Ideal (A-)
    # Tum kriterler "max" yonlu oldugu icin (yuksek = iyi)
    A_plus = V.max(axis=0)
    A_minus = V.min(axis=0)

    # Adim 4: Oklid mesafeler
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))

    # Adim 5: CC
    CC = D_minus / (D_plus + D_minus + 1e-12)

    sonuclar[f"CC_{senaryo}"] = CC
    print(f"  CC: min={CC.min():.4f}, max={CC.max():.4f}, mean={CC.mean():.4f}, std={CC.std():.4f}")
    print(f"  top 5 parsel: {criteria.iloc[CC.argsort()[::-1][:5]]['S_No'].tolist()}")

print("\n[4/4] Kaydediliyor...")
out = pd.DataFrame(sonuclar)
out.to_excel(MCDM / "topsis_cc.xlsx", index=False)

# Ayrica her senaryo icin sirali (rank) tablo
rank_df = out.copy()
for s in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
    rank_df[f"rank_{s}"] = rank_df[f"CC_{s}"].rank(ascending=False, method="min").astype(int)

rank_df.to_excel(MCDM / "topsis_ranked.xlsx", index=False)
print(f"  -> {MCDM / 'topsis_cc.xlsx'}")
print(f"  -> {MCDM / 'topsis_ranked.xlsx'}")

print("\n" + "=" * 60)
print("TOPSIS TAMAMLANDI")
print("=" * 60)
print(out.describe().to_string())

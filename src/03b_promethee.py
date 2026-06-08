"""
03b_promethee.py
Sultanbeyli Konteyner - PROMETHEE II ile aday parsel puanlamasi

3 AHP senaryosu icin ayri ayri Net Flow (phi) hesaplar.
Girdi  : data/processed/criteria_matrix.xlsx, results/ahp/ahp_weights_hybrid.xlsx
Cikti  : results/mcdm/promethee_phi.xlsx (140 parsel x 3 senaryo)

Degisiklikler (Faz 2):
  1) Ham degerler yerine Faz 1'de uretilen Amplified (power-transform) sutunlari kullanilir.
  2) Sadece AHP degil, AHP-Entropy hibrit agirliklari kullanilir (w_hyb).

Yontem (PROMETHEE II, Tip V tercih fonksiyonu = V-shape):
  1) j kriterinde a ve b alternatifleri icin d_j(a,b) = f_j(a) - f_j(b)
  2) Tercih fonksiyonu P_j(a,b):
       P_j(a,b) = 0           , d_j <= 0
       P_j(a,b) = d_j / q_j   , 0 < d_j <= q_j
       P_j(a,b) = 1           , d_j > q_j
     Burada q_j = aralik (max - min) / 5  (lineer normalize)
  3) Agirlikli tercih: pi(a,b) = Σ_j w_j * P_j(a,b)
  4) Leaving flow: phi+(a) = (1/(n-1)) Σ_b pi(a,b)
     Entering flow: phi-(a) = (1/(n-1)) Σ_b pi(b,a)
  5) Net flow: phi(a) = phi+(a) - phi-(a)
"""

from __future__ import annotations

import argparse
import numpy as np
import pandas as pd

import config
from config import DATA_DIR as PROCESSED, RESULTS_DIR

AHP = RESULTS_DIR / "ahp"
MCDM = RESULTS_DIR / "mcdm"
MCDM.mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser(description="PROMETHEE II puanlamasi")
parser.add_argument("--q-frac", type=float, default=0.20,
                    help="V-shape q threshold as fraction of range (default: 0.20 = 20 %%)")
args = parser.parse_args()

# Faz 1'den gelen amplified (ayriklastirilmis) kriter sutunlari
KRITER_SUTUNLARI = ["C1_hasar_risk_amp", "C2_lojistik_amp", "C3_bosluk_amp", "C4_barinma_amp"]

print("[1/4] Veriler okunuyor...")
criteria = pd.read_excel(PROCESSED / "criteria_matrix.xlsx")
# AHP-Entropy Hibrit agirliklarini yukle
weights_df = pd.read_excel(AHP / "ahp_weights_hybrid.xlsx")

mat = criteria[KRITER_SUTUNLARI].copy().astype(float).values  # (140, 4)
n, k = mat.shape
print(f"  karar matrisi: {mat.shape}")


def promethee_ii(M: np.ndarray, w: np.ndarray, q_frac: float = 0.20) -> np.ndarray:
    """
    PROMETHEE II, V-shape tercih fonksiyonu.
    q_j = q_frac * range(j)  (default %20'si)
    """
    n, k = M.shape
    rng = M.max(axis=0) - M.min(axis=0)
    rng = np.where(rng == 0, 1.0, rng)
    q = q_frac * rng

    phi_plus = np.zeros(n)
    phi_minus = np.zeros(n)
    for a in range(n):
        # V-shape P_j(a, b) her b icin
        # diff[a, b, j] = M[a, j] - M[b, j]  (a, b, k) tensor
        diff = M[a:a + 1, :] - M  # (n, k)  d_j(a, b)  satir=b, sutun=k
        P = np.clip(diff / q, 0, 1)  # V-shape lineer, P[a][b][j] = pref of a over b on j
        # pi[a][b] = sum_j w_j * P_j(a, b)
        pi_ab = (P * w).sum(axis=1)  # (n,) — a'nin b'ye tercih yogunlugu

        # pi_ba = a'ya dogru akan: P_j(b, a) = max(0, M[b, j] - M[a, j]) / q_j
        diff_ba = M - M[a:a + 1, :]  # (n, k)  d_j(b, a)  satir=b
        P_ba = np.clip(diff_ba / q, 0, 1)
        pi_ba = (P_ba * w).sum(axis=1)  # (n,)

        phi_plus[a] = (pi_ab.sum() - pi_ab[a]) / (n - 1)
        phi_minus[a] = (pi_ba.sum() - pi_ba[a]) / (n - 1)

    return phi_plus - phi_minus


print("\n[2/4] 3 senaryo icin PROMETHEE II hesabi...")
sonuclar = {
    "S_No": criteria["S_No"].values,
    "Alan_Adi": criteria.get("Alan_Adi", pd.Series([""] * n)).values,
    "Mahalle": criteria["Mahalle"].values,
}

for _, wrow in weights_df.iterrows():
    senaryo = wrow["scenario"]
    # Hibrit agirliklari kullan
    w = np.array([wrow["C1_Nufus_hyb"], wrow["C2_Deprem_hyb"], 
                  wrow["C3_Erisim_hyb"], wrow["C4_Ulasim_hyb"]])
    print(f"\n  --- {senaryo} (Hibrit w = {w.round(4)}) ---")

    phi = promethee_ii(mat, w, q_frac=args.q_frac)
    sonuclar[f"phi_{senaryo}"] = phi
    print(f"  phi: min={phi.min():.4f}, max={phi.max():.4f}, mean={phi.mean():.4f}, std={phi.std():.4f}")
    top5 = np.argsort(phi)[::-1][:5]
    print(f"  top 5 parsel: {criteria.iloc[top5]['S_No'].tolist()}")

print("\n[3/4] 0-1 normalize (karsilastirma icin)...")
out = pd.DataFrame(sonuclar)
for s in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
    col = f"phi_{s}"
    pmin, pmax = out[col].min(), out[col].max()
    out[f"phi01_{s}"] = (out[col] - pmin) / (pmax - pmin + 1e-12)

print("\n[4/4] Kaydediliyor...")
out.to_excel(MCDM / "promethee_phi.xlsx", index=False)

# Rank
rank_df = out.copy()
for s in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
    rank_df[f"rank_{s}"] = rank_df[f"phi_{s}"].rank(ascending=False, method="min").astype(int)
rank_df.to_excel(MCDM / "promethee_ranked.xlsx", index=False)

print(f"  -> {MCDM / 'promethee_phi.xlsx'}")
print(f"  -> {MCDM / 'promethee_ranked.xlsx'}")

print("\n" + "=" * 60)
print("PROMETHEE II TAMAMLANDI")
print("=" * 60)
print(out[[c for c in out.columns if c.startswith("phi_") or c.startswith("phi01_")]].describe().to_string())

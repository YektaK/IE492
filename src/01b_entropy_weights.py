"""
01b_entropy_weights.py
Sultanbeyli Konteyner Konum Secimi - ENTROPY AGIRLIKLANDIRMA

Amac:
  Shannon entropy tabanlı objektif kriter agirliklari hesapla.
  AHP (subjektif) ile entropy (objektif) agirliklari birlestirerek
  hibrit agirlik uret.

Yontem:
  1) Kriter matrisini [0,1] oransal formata don
  2) Her kriter icin Shannon entropy hesapla: E_j = -(1/ln n) * Sum p_ij * ln(p_ij)
  3) Ayirt edicilik: d_j = 1 - E_j  (yuksek d_j → kriter daha ayirt edici)
  4) Entropy agirligi: w_ent_j = d_j / Sum(d_j)
  5) Hibrit agirlik: w_hib_j = (w_ahp_j * w_ent_j) / Sum(w_ahp_j * w_ent_j)

Neden entropy agirligi?
  Tum adaylarin benzer oldugu bir kriter (orn. barinma talebi mahalleden geliyor,
  cogu mahallede yakin deger) az bilgi tasir → entropy yuksek → agirlik duser.
  Adaylar arasinda cok fark yaratan bir kriter (orn. C2 altyapi, 0'dan 1'e) →
  entropy dusuk → agirlik artar.

Cikti:
  results/ahp/entropy_weights.xlsx   → 4 kriterin entropy + hibrit agirliklari
  results/ahp/ahp_weights_hybrid.xlsx → 3 AHP senaryosu x hibrit agirliklar

Kullanim:
  python src/01b_entropy_weights.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

import config
from config import DATA_DIR as PROCESSED, RESULTS_DIR

AHP_OUT = RESULTS_DIR / "ahp"
AHP_OUT.mkdir(parents=True, exist_ok=True)

# Kriter sutunlari (criteria_matrix.xlsx'teki ham degerler)
KRITER_SUTUNLARI = [
    "C1_hasar_risk",
    "C2_lojistik",
    "C3_bosluk_norm",   # normalize edilmis mesafe (0-1)
    "C4_barinma",
]
KRITER_ADLARI = ["C1_Nufus/Risk", "C2_Altyapi", "C3_Erisim", "C4_Barinma"]


# ---------------------------------------------------------------------------
# 1) SHANNON ENTROPY AGIRLIK FONKSİYONLARI
# ---------------------------------------------------------------------------
def entropy_weights(matrix: np.ndarray) -> np.ndarray:
    """
    Shannon entropy tabanlı nesnel (objektif) kriter agirliklari.

    Parametre
    ---------
    matrix : np.ndarray, sekil (n, k)
        n = alternatif sayisi (parceller), k = kriter sayisi
        Ham degerler (normalize edilmemis kabul edilir — fonksiyon iceride normalize eder).

    Donus
    -----
    w_entropy : np.ndarray, sekil (k,)
        Her kriter icin entropy agirligi [0,1], toplam = 1.0
    """
    n, k = matrix.shape
    # Sutun bazinda oran matrisi (p_ij = x_ij / Sum_i x_ij)
    col_sum = matrix.sum(axis=0)
    col_sum = np.where(col_sum == 0, 1.0, col_sum)   # sifira bolme onlemi
    P = matrix / col_sum                               # (n, k)

    # p_ij=0 icin log(0)=-inf sorunu: 0 * log(0) = 0 (limit)
    if (P < 0).any():
        import warnings
        warnings.warn(f"Entropy inputte negatif deger var! {int((P < 0).sum())} adet -> 0'a clamp.")
    P_safe = np.where(P == 0, 1.0, P)                 # 0 girisleri 1 → log(1)=0
    log_P  = np.log(P_safe)
    log_P  = np.where(P == 0, 0.0, log_P)             # 0*log(0) → 0

    # Entropy: E_j = -(1/ln n) * Sum_i p_ij * ln(p_ij)
    ln_n = np.log(n) if n > 1 else 1.0
    E = -(1.0 / ln_n) * np.sum(P * log_P, axis=0)    # (k,)

    # Ayirt edicilik: d_j = 1 - E_j
    d = 1.0 - E                                        # (k,)
    d = np.clip(d, 0.0, None)                          # negatif olmasini engelle

    # Entropy agirligi: normalize d
    d_sum = d.sum()
    if d_sum == 0:
        w = np.ones(k) / k
    else:
        w = d / d_sum

    return w


def hybrid_weights(w_ahp: np.ndarray, w_entropy: np.ndarray) -> np.ndarray:
    """
    AHP (subjektif) × Entropy (objektif) hibrit agirlik.

    Birlesik agirlik: w_hib_j = (w_ahp_j * w_ent_j) / Sum_j(w_ahp_j * w_ent_j)
    → Hem uzman gorusunu hem verinin ayirt ediciliginı yansitir.

    Parametre
    ---------
    w_ahp     : np.ndarray (k,) — AHP'den gelen agirliklar
    w_entropy : np.ndarray (k,) — entropy'den gelen agirliklar

    Donus
    -----
    w_hybrid : np.ndarray (k,) — hibrit agirlik, toplam = 1.0
    """
    raw = w_ahp * w_entropy
    total = raw.sum()
    if total == 0:
        return np.ones(len(w_ahp)) / len(w_ahp)
    return raw / total


# ---------------------------------------------------------------------------
# 2) VERI YUKLEMESİ
# ---------------------------------------------------------------------------
print("=" * 60)
print("ENTROPY AGIRLANDIRMA BASLADI")
print("=" * 60)

print("\n[1/4] Kriter matrisi okunuyor...")
criteria = pd.read_excel(PROCESSED / "criteria_matrix.xlsx")
print(f"  Kriter matrisi: {criteria.shape}")

# Ham kriter degerleri (sadece surekli kriterler)
mat = criteria[KRITER_SUTUNLARI].copy().astype(float)

# Sutunlarda sifir variance kontrolu
for col in KRITER_SUTUNLARI:
    v = mat[col].var()
    if v < 1e-10:
        print(f"  [UYARI] {col} sutununda neredeyse sifir varyans (var={v:.2e}) — "
              f"entropy agirligi sifira yakin olacak")

# ---------------------------------------------------------------------------
# 3) ENTROPY AGIRLIK HESAPLAMA
# ---------------------------------------------------------------------------
print("\n[2/4] Entropy agirliklari hesaplaniyor...")
W_entropy = entropy_weights(mat.values)   # (4,)

print("\n  Entropy Analizi:")
print(f"  {'Kriter':<20}  {'Entropy':>8}  {'Ayirt.':>8}  {'W_entropy':>10}")
print("  " + "-" * 50)
for j, (col, ad) in enumerate(zip(KRITER_SUTUNLARI, KRITER_ADLARI)):
    col_sum = mat[col].sum()
    P_col = mat[col] / (col_sum if col_sum > 0 else 1)
    P_safe = np.where(P_col <= 0, 1.0, P_col)
    log_P  = np.where(P_col <= 0, 0.0, np.log(P_safe))
    ln_n   = np.log(len(mat))
    E_j    = -(1.0 / ln_n) * (P_col * log_P).sum()
    d_j    = 1.0 - E_j
    print(f"  {ad:<20}  {E_j:>8.4f}  {d_j:>8.4f}  {W_entropy[j]:>10.6f}")

print(f"\n  Toplam W_entropy = {W_entropy.sum():.6f}  (1.0 olmali)")

# ---------------------------------------------------------------------------
# 4) AHP AGIRLIKLARI ILE HIBRIT
# ---------------------------------------------------------------------------
print("\n[3/4] AHP agirliklari ile hibrit hesaplaniyor...")

ahp_df = pd.read_excel(AHP_OUT / "ahp_weights.xlsx")
ahp_cols = ["C1_Nufus", "C2_Deprem", "C3_Erisim", "C4_Ulasim"]

# Her AHP senaryosu icin hibrit
hybrid_rows = []
for _, row in ahp_df.iterrows():
    scenario = row["scenario"]
    w_ahp = np.array([row[c] for c in ahp_cols])
    w_hyb = hybrid_weights(w_ahp, W_entropy)

    print(f"\n  Senaryo: {scenario}")
    print(f"  {'Kriter':<12}  {'AHP':>8}  {'Entropy':>8}  {'Hibrit':>8}")
    for j, ad in enumerate(KRITER_ADLARI):
        print(f"  {ad:<12}  {w_ahp[j]:>8.4f}  {W_entropy[j]:>8.4f}  {w_hyb[j]:>8.4f}")
    print(f"  Toplam:       {w_ahp.sum():>8.4f}  {W_entropy.sum():>8.4f}  {w_hyb.sum():>8.4f}")

    hybrid_rows.append({
        "scenario": scenario,
        "C1_Nufus_ahp":    round(float(w_ahp[0]), 6),
        "C2_Deprem_ahp":   round(float(w_ahp[1]), 6),
        "C3_Erisim_ahp":   round(float(w_ahp[2]), 6),
        "C4_Ulasim_ahp":   round(float(w_ahp[3]), 6),
        "C1_Nufus_ent":    round(float(W_entropy[0]), 6),
        "C2_Deprem_ent":   round(float(W_entropy[1]), 6),
        "C3_Erisim_ent":   round(float(W_entropy[2]), 6),
        "C4_Ulasim_ent":   round(float(W_entropy[3]), 6),
        "C1_Nufus_hyb":    round(float(w_hyb[0]), 6),
        "C2_Deprem_hyb":   round(float(w_hyb[1]), 6),
        "C3_Erisim_hyb":   round(float(w_hyb[2]), 6),
        "C4_Ulasim_hyb":   round(float(w_hyb[3]), 6),
    })

# ---------------------------------------------------------------------------
# 5) KAYDET
# ---------------------------------------------------------------------------
print("\n[4/4] Kaydediliyor...")

# Entropy agirliklari
ent_df = pd.DataFrame({
    "kriter_kodu":  KRITER_SUTUNLARI,
    "kriter_adi":   KRITER_ADLARI,
    "w_entropy":    W_entropy.round(6),
})
ent_df.to_excel(AHP_OUT / "entropy_weights.xlsx", index=False)
print(f"  -> {AHP_OUT / 'entropy_weights.xlsx'}")

# Hibrit agirliklar (3 senaryo)
hyb_df = pd.DataFrame(hybrid_rows)
hyb_df.to_excel(AHP_OUT / "ahp_weights_hybrid.xlsx", index=False)
print(f"  -> {AHP_OUT / 'ahp_weights_hybrid.xlsx'}")

# JSON (diger scriptlerde kolayca okunmak icin)
ent_json = {
    "entropy_weights": dict(zip(KRITER_SUTUNLARI, W_entropy.round(6).tolist())),
    "note": (
        "Shannon entropy tabanli nesnel agirliklar. "
        "Yuksek w_entropy = kriter daha ayirt edici."
    ),
}
ent_json_path = AHP_OUT / "entropy_weights.json"
with open(ent_json_path, "w", encoding="utf-8") as f:
    json.dump(ent_json, f, ensure_ascii=False, indent=2)
print(f"  -> {ent_json_path}")

print("\n" + "=" * 60)
print("ENTROPY AGIRLANDIRMA TAMAMLANDI")
print("=" * 60)
print("\nOzet:")
print(f"  En ayirt edici kriter : {KRITER_ADLARI[int(W_entropy.argmax())]} "
      f"(W_ent={W_entropy.max():.4f})")
print(f"  En az ayirt edici     : {KRITER_ADLARI[int(W_entropy.argmin())]} "
      f"(W_ent={W_entropy.min():.4f})")
print(f"\n  AHP-Entropy hibrit agirliklar '{AHP_OUT / 'ahp_weights_hybrid.xlsx'}'")
print(f"  dosyasinda 3 senaryo × 4 kriter formatinda hazir.")
print(f"\n  Kullanim: TOPSIS/PROMETHEE'de 'w_hybrid' sutunlarini kullan.")

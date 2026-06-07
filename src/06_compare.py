# -*- coding: utf-8 -*-
"""
06_compare.py
TOPSIS vs PROMETHEE II + 3 AHP senaryosu karsilastirmasi + sonuc rasyoneli.

Guncelleme (Faz 2):
- L2 vs Min-Max TOPSIS normalizasyon karsilastirmasi
- AHP-Entropy hibrit agirliklarin etkisinin gosterilmesi
"""

from __future__ import annotations
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
MCDM = ROOT / "results" / "mcdm"
OUT  = ROOT / "results" / "comparison"
FIG  = ROOT / "figures"
for d in [OUT, FIG]:
    d.mkdir(parents=True, exist_ok=True)


def load_mcdm() -> dict[str, pd.DataFrame]:
    return {
        "TOPSIS":     pd.read_excel(MCDM / "topsis_cc.xlsx"),
        "PROMETHEE":  pd.read_excel(MCDM / "promethee_phi.xlsx"),
    }


def mcdm_agreement(mcdm: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """TOPSIS L2 vs MinMax ve TOPSIS MinMax vs PROMETHEE anlasmasi."""
    rows = []
    senaryolar = ["Baseline", "DamageFocused", "InfrastructureFocused"]
    
    for s in senaryolar:
        t = mcdm["TOPSIS"].set_index("S_No")
        p = mcdm["PROMETHEE"].set_index("S_No")
        
        # 1. TOPSIS L2 vs MinMax
        x = t[f"CC_{s}_L2"]
        y = t[f"CC_{s}_MinMax"]
        corr_t = float(np.corrcoef(x, y)[0, 1])
        t10_L2 = set(x.sort_values(ascending=False).head(10).index)
        t10_MM = set(y.sort_values(ascending=False).head(10).index)
        jac_t = len(t10_L2 & t10_MM) / len(t10_L2 | t10_MM)
        
        rows.append({
            "senaryo": s,
            "karsilastirma": "TOPSIS(L2) vs TOPSIS(MinMax)",
            "pearson_corr": round(corr_t, 4),
            "top10_jaccard": round(jac_t, 4),
        })
        
        # 2. TOPSIS MinMax vs PROMETHEE
        x2 = t[f"CC_{s}_MinMax"]
        y2 = p[f"phi_{s}"]
        common = x2.index.intersection(y2.index)
        corr_tp = float(np.corrcoef(x2.loc[common], y2.loc[common])[0, 1])
        t10_p = set(y2.sort_values(ascending=False).head(10).index)
        jac_tp = len(t10_MM & t10_p) / len(t10_MM | t10_p)
        
        rows.append({
            "senaryo": s,
            "karsilastirma": "TOPSIS(MinMax) vs PROMETHEE",
            "pearson_corr": round(corr_tp, 4),
            "top10_jaccard": round(jac_tp, 4),
        })
        
    return pd.DataFrame(rows)


def plot_mcdm_scatter(mcdm: dict[str, pd.DataFrame], agreement: pd.DataFrame) -> None:
    # Scatter 1: L2 vs MinMax
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    senaryolar = ["Baseline", "DamageFocused", "InfrastructureFocused"]
    for ax, s in zip(axes, senaryolar):
        t = mcdm["TOPSIS"].set_index("S_No")
        x = t[f"CC_{s}_L2"]
        y = t[f"CC_{s}_MinMax"]
        ax.scatter(x, y, s=14, alpha=0.65, color="#1f77b4")
        ax.set_xlabel("TOPSIS L2 (Geleneksel)")
        ax.set_ylabel("TOPSIS Min-Max (Amplified Korumali)")
        ax.set_title(s)
        ax.grid(alpha=0.3)
        r = agreement[(agreement["senaryo"] == s) & (agreement["karsilastirma"] == "TOPSIS(L2) vs TOPSIS(MinMax)")]["pearson_corr"].values[0]
        ax.text(0.05, 0.92, f"r = {r:.3f}", transform=ax.transAxes, fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))
    fig.suptitle("TOPSIS Normalizasyon Etkisi: L2 vs Min-Max", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIG / "compare_topsis_norm_scatter.png", dpi=150)
    plt.close(fig)

    # Scatter 2: TOPSIS(MinMax) vs PROMETHEE
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, s in zip(axes, senaryolar):
        t = mcdm["TOPSIS"].set_index("S_No")[f"CC_{s}_MinMax"]
        p = mcdm["PROMETHEE"].set_index("S_No")[f"phi_{s}"]
        common = t.index.intersection(p.index)
        ax.scatter(t.loc[common], p.loc[common], s=14, alpha=0.65, color="#2ca02c")
        ax.set_xlabel("TOPSIS CC (MinMax)")
        ax.set_ylabel("PROMETHEE φ (Net Flow)")
        ax.set_title(s)
        ax.grid(alpha=0.3)
        r = agreement[(agreement["senaryo"] == s) & (agreement["karsilastirma"] == "TOPSIS(MinMax) vs PROMETHEE")]["pearson_corr"].values[0]
        ax.text(0.05, 0.92, f"r = {r:.3f}", transform=ax.transAxes, fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))
    fig.suptitle("MCDM Tutarliligi: TOPSIS (MinMax) vs PROMETHEE", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIG / "compare_topsis_vs_promethee.png", dpi=150)
    plt.close(fig)


def main():
    print("="*50)
    print("FAZ 2: MCDM KARSILASTIRMA RAPORU")
    print("="*50)
    
    mcdm = load_mcdm()
    agreement = mcdm_agreement(mcdm)
    
    print("\n--- Korelasyon ve Jaccard Benzerlikleri ---")
    print(agreement.to_string(index=False))
    
    plot_mcdm_scatter(mcdm, agreement)
    print(f"\n[+] Gorseller {FIG} altina kaydedildi.")
    
    agreement.to_excel(OUT / "mcdm_agreement.xlsx", index=False)
    print(f"[+] Tablo {OUT / 'mcdm_agreement.xlsx'} altina kaydedildi.")
    print("="*50)

if __name__ == "__main__":
    main()

"""
04b_coverage_boundary.py
Sultanbeyli Konteyner Konum Secimi - Kapsama Siniri Haritasi (Sigma Analizi)

Farkli sigma (σ) degerleri icin mu=0.50 ve mu=0.10 (etki siniri) esik mesafelerini hesaplar ve raporlar.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FUZZY_COV_DIR = PROJECT_ROOT / "results" / "fuzzy_coverage"
FUZZY_COV_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("="*60)
    print("GAUSSIAN BULANIK KAPSAMA — SINIR HARITASI")
    print("="*60)
    
    sigmas = [400, 600, 800, 1000, 1200]
    
    # Hesaplama: mu = exp(-d^2 / 2σ^2) => d = σ * sqrt(-2 * ln(mu))
    # mu=0.50 icin: d = σ * sqrt(2 * ln(2))
    # mu=0.10 icin: d = σ * sqrt(2 * ln(10))
    
    rows = []
    for s in sigmas:
        d_50 = s * np.sqrt(2 * np.log(2))
        d_10 = s * np.sqrt(2 * np.log(10))
        
        if s == 400:
            yorum = "Cok dar — yetersiz kapsama, sadece lokal etki"
        elif s == 600:
            yorum = "Dar — mahalle-ici kapsama"
        elif s == 800:
            yorum = "Orta (Varsayilan) — dengeli mahalleler-arasi kapsama"
        elif s == 1000:
            yorum = "Genis — fazla overlap"
        elif s == 1200:
            yorum = "Cok genis — asiri overlap, sinir anlamsizlasiyor"
        else:
            yorum = "-"
            
        rows.append({
            "Sigma (m)": s,
            "mu=0.50 mesafe (m)": round(d_50, 0),
            "mu=0.10 mesafe (m)": round(d_10, 0),
            "Yorum": yorum
        })
        
    df = pd.DataFrame(rows)
    print(df.to_markdown(index=False))
    
    df.to_excel(FUZZY_COV_DIR / "coverage_boundaries.xlsx", index=False)
    print(f"\n[+] Rapor {FUZZY_COV_DIR / 'coverage_boundaries.xlsx'} altina kaydedildi.")
    print("="*60)

if __name__ == "__main__":
    main()

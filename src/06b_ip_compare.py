"""
06b_ip_compare.py
Sultanbeyli Konteyner Konum Secimi - IP Sonuclari Analizi

Farkli IP kosularini (K=8 vs K=20, TOPSIS vs PROMETHEE) okuyup karsilastirir.
"""

import pandas as pd
from pathlib import Path
import glob

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "results" / "models"
OUT_DIR = PROJECT_ROOT / "results" / "comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("="*60)
    print("FAZ 5: IP SONUCLARI KARSILASTIRMASI")
    print("="*60)

    # Tum summary_all dosyalarini bul
    files = glob.glob(str(MODELS_DIR / "summary_all_*.xlsx"))
    
    if not files:
        print("Hata: IP summary dosyalari bulunamadi.")
        return
        
    dfs = []
    for f in files:
        df = pd.read_excel(f)
        # Dosya isminden bazi metadatalari cikartalim eger df icinde yoksa
        fname = Path(f).name
        # df icinde 'K' vs olmali
        dfs.append(df)
        
    merged = pd.concat(dfs, ignore_index=True)
    
    # Eger 'nomez' (no_mevcut) varsa K=20 senaryosudur (Bastan Kurulum)
    # df icinde yoksa ekleyelim
    if "is_bastan" not in merged.columns:
        # no_mevcut kontrolu
        merged["Senaryo_Tipi"] = merged.apply(
            lambda r: "20 Baştan" if r.get("K") == 20 else "8 Ekleme", 
            axis=1
        )
        
    # Pivot tablo yapalim
    # Index: Senaryo_Tipi, mcdm, senaryo
    # Values: RxC, min_mahalle_cov, avg_mahalle_cov
    
    pivot = merged.pivot_table(
        index=["Senaryo_Tipi", "mcdm", "senaryo"],
        values=["RxC", "min_mahalle_cov", "avg_mahalle_cov", "Z_quality"],
        aggfunc="mean"
    ).round(4)
    
    print("\n[+] Birlestirilmis Sonuclar:\n")
    print(pivot.to_markdown())
    
    pivot.to_excel(OUT_DIR / "ip_comparison_summary.xlsx")
    print(f"\n[+] Tablo {OUT_DIR / 'ip_comparison_summary.xlsx'} altina kaydedildi.")
    print("="*60)

if __name__ == "__main__":
    main()

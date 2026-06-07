"""
12b_sigma_calibration.py
Sultanbeyli Konteyner Konum Secimi - Sigma (σ) Kalibrasyon Analizi

Farkli sigma degerlerinde mevcut 12 konteynerin mahalleleri kapsama oranini hesaplayarak
optimum sigma degerini belirlemek uzere kalibrasyon yapar. 
Eger sigma cok kucukse, mevcutlar cok zayif kalir. Cok buyukse, her yer %100 olur (ayrim kaybolur).
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
FUZZY_COV_DIR = PROJECT_ROOT / "results" / "fuzzy_coverage"
FUZZY_COV_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# HAVERSINE MESAFE
# ---------------------------------------------------------------------------
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def norm_mahalle(s: str) -> str:
    if not isinstance(s, str): return ""
    tr_map = str.maketrans({"Ç":"C","Ğ":"G","İ":"I","Ö":"O","Ş":"S","Ü":"U","ç":"C","ğ":"G","ı":"I","ö":"O","ş":"S","ü":"U","â":"A","î":"I","û":"U"})
    return s.strip().translate(tr_map).upper()

def main():
    print("="*60)
    print("SIGMA KALIBRASYONU (MEVCUT 12 KONTEYNER BAZLI)")
    print("="*60)
    
    mevcut = pd.read_excel(PROCESSED / "mevcut_12.xlsx")
    centroids = pd.read_excel(PROCESSED / "mahalle_centroids.xlsx")
    
    centroids["mahalle_norm"] = centroids["mahalle"].apply(norm_mahalle)
    c_clean = centroids.drop_duplicates(subset=["mahalle_norm"], keep="first")[["mahalle_norm", "lat", "lon"]]
    
    mahalleler = sorted(c_clean["mahalle_norm"].tolist())
    # Sadece ormanlari cikar
    mahalleler = [m for m in mahalleler if "ORMANI" not in m]
    
    c_clean = c_clean.set_index("mahalle_norm")
    
    mevcut_lat = mevcut["enlem"].values
    mevcut_lon = mevcut["boylam"].values
    mahalle_lat = c_clean.loc[mahalleler, "lat"].values
    mahalle_lon = c_clean.loc[mahalleler, "lon"].values
    
    D_mevcut = np.zeros((len(mevcut), len(mahalleler)))
    for j, (mlat, mlon) in enumerate(zip(mahalle_lat, mahalle_lon)):
        D_mevcut[:, j] = haversine_m(mlat, mlon, mevcut_lat, mevcut_lon)
        
    sigmas = [400, 500, 600, 700, 800, 900, 1000, 1200]
    rows = []
    
    for s in sigmas:
        # Gaussian Uyelik
        mu = np.exp(-(D_mevcut ** 2) / (2 * s ** 2))
        
        # O mahallenin herhangi bir mevcut tarafindan kapsanma orani (bagimsiz olasilik bilesimi gibi veya max)
        # Literatürde cov_j = 1 - prod(1 - mu_ij)
        # IP'de sum kullaniliyor. Biz kalibrasyon icin max(mu_ij) bakalim
        max_cov = mu.max(axis=0)
        
        # Ayrica truncation < 0.15 bakalim
        mu_trunc = mu.copy()
        mu_trunc[mu_trunc < 0.15] = 0.0
        max_cov_trunc = mu_trunc.max(axis=0)
        
        rows.append({
            "Sigma": s,
            "Min Mahalle Cov": round(max_cov.min(), 4),
            "Avg Mahalle Cov": round(max_cov.mean(), 4),
            "Max Mahalle Cov": round(max_cov.max(), 4),
            "Tam Kapsanan Mah (>0.90)": sum(max_cov > 0.90),
            "Zayif Mahalle (<0.15)": sum(max_cov < 0.15),
            "Avg Cov (Truncated)": round(max_cov_trunc.mean(), 4)
        })
        
    df = pd.DataFrame(rows)
    print(df.to_markdown(index=False))
    
    df.to_excel(FUZZY_COV_DIR / "sigma_calibration_mevcut.xlsx", index=False)
    print(f"\n[+] Rapor {FUZZY_COV_DIR / 'sigma_calibration_mevcut.xlsx'} altina kaydedildi.")
    
    # Optimum sigma secimi:
    # Avg Cov (Truncated)'in 0.50 ile 0.70 arasinda oldugu sigmalar idealdir (ne cok asiri ne cok zayif)
    
if __name__ == "__main__":
    main()

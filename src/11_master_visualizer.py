"""
11_master_visualizer.py
Sultanbeyli Konteyner Konum Secimi - Etkilesimli Harita ve Grafik Olusturucu
"""

import pandas as pd
import glob
import sys

import config
from config import DATA_DIR as PROCESSED, MODELS_DIR, MAPS_DIR, CHARTS_DIR

sys.path.insert(0, str(config.PROJECT_ROOT / "src"))

from visualization import plot_solution_map, plot_coverage_bar

MAPS_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

def visualize_ip_result(ip_file_path, cov_file_path, mevcut_df, out_prefix):
    # 1. Secilen Konteynerleri Oku
    yeni_df = pd.read_excel(ip_file_path)
    
    # 2. Mevcutlardan Korunanlari Sec (Eger nomez degilse)
    # Burada basitleştirme yapiyoruz: Eğer dosya adında "nomez" varsa kept=0.
    is_nomez = "nomez" in str(ip_file_path).lower()
    if is_nomez:
        kept_df = pd.DataFrame()
        removed_df = mevcut_df.copy()
    else:
        # Varsayilan olarak hepsi korunuyor kabul ediyoruz (örneğin ilk 12)
        kept_df = mevcut_df.copy()
        removed_df = pd.DataFrame()
        
    fixed_df = pd.DataFrame() # Eger fixed verisi olsa ayirirdik
    
    # 3. Harita Uretimi
    map_out = MAPS_DIR / f"{out_prefix}_map.html"
    title = f"Konteyner Plani: {out_prefix}"
    plot_solution_map(yeni_df, kept_df, removed_df, fixed_df, map_out, title=title)
    
    # 4. Grafik Uretimi (Eger coverage dosyasi varsa)
    if cov_file_path and Path(cov_file_path).exists():
        cov_df = pd.read_excel(cov_file_path)
        
        # Risk veya nüfus skorunu çekelim
        weight_type = "risk"
        if "population" in str(ip_file_path):
            weight_type = "population"
            w_df = pd.read_excel(PROCESSED / "mahalle_nufus.xlsx")
            val_col = "nufus_2024"
        elif "shelter" in str(ip_file_path):
            weight_type = "shelter"
            w_df = pd.read_excel(PROCESSED / "mahalle_barinma.xlsx")
            val_col = "hane_ihtiyaci"
        else:
            w_df = pd.read_excel(PROCESSED / "mahalle_risk.xlsx")
            val_col = "risk_score"
            
        # Kapsama verisine hedef veriyi birlestir
        def norm_mh(s):
            tr = str.maketrans({"Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U", "ç": "C", "ğ": "G", "ı": "I", "ö": "O", "ş": "S", "ü": "U"})
            return str(s).strip().translate(tr).upper()
            
        w_df["mahalle_norm"] = w_df["mahalle"].apply(norm_mh)
        cov_df["mahalle_norm"] = cov_df["mahalle"].apply(norm_mh)
        
        merged = pd.merge(cov_df, w_df, on="mahalle_norm", how="left", suffixes=("", "_w"))
        
        # Proportional scale for visualization relative to max
        max_val = merged[val_col].max()
        target_vals = merged[val_col] / max_val
        
        chart_out = CHARTS_DIR / f"{out_prefix}_coverage.png"
        plot_coverage_bar(merged["mahalle"], merged["toplam_kapsama"], target_vals, weight_type.capitalize(), chart_out, title=f"Kapsama vs {weight_type.capitalize()}")
        print(f"  -> Grafik kaydedildi: {chart_out}")

def main():
    print("="*60)
    print("FAZ 5: HARITA VE GRAFIK MOTORU (STANDART)")
    print("="*60)
    
    mevcut = pd.read_excel(PROCESSED / "mevcut_12.xlsx")
    
    # Ornek 1: K20 Risk (Ekleme/Kept12) - En son calistirilanlardan biri
    ip_files = glob.glob(str(MODELS_DIR / "ip_*_K20*_risk.xlsx"))
    for ip_file in ip_files:
        if "nomez" not in ip_file:
            cov_file = ip_file.replace("ip_", "coverage_")
            visualize_ip_result(ip_file, cov_file, mevcut, "K20_Mevcutlu_Risk")
            break
            
    # Ornek 2: K20 Population (Bastan Kurulum/Nomez)
    ip_files_pop = glob.glob(str(MODELS_DIR / "ip_*_K20*_nomez_population.xlsx"))
    for ip_file in ip_files_pop:
        cov_file = ip_file.replace("ip_", "coverage_")
        visualize_ip_result(ip_file, cov_file, mevcut, "K20_Bastan_Nufus")
        break

    print("="*60)

if __name__ == "__main__":
    main()

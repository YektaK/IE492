import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Proje kök dizinini ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_DIR, RESULTS_DIR, MODELS_DIR, CHARTS_DIR, get_mevcut_indices
from scenario_utils import load_q_vector, fuzzy_coverage_paths

# 05_ip modülünden çözücü fonksiyonu içe aktar
run_ip_model = None
# Python import modüllerinde sayı ile başlayanlar için importlib kullanabiliriz
import importlib
try:
    ip_module = importlib.import_module("05_ip")
    run_ip_model = ip_module.run_ip_model
except ImportError:
    # Alternatif import
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    ip_module = importlib.import_module("05_ip")
    run_ip_model = ip_module.run_ip_model

def run_beta_sensitivity(K=20, weight_type="risk", sigma="Adaptive", scenario="A"):
    """Beta parametresi (0.0 ile 1.0 arası) için hassasiyet analizi yapar."""
    betas = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    results = []
    
    print(f"[+] Beta Hassasiyet Analizi Başlıyor (K={K}, Hedef={weight_type}, Sigma={sigma})...")
    
    for b in betas:
        # IP modelini çalıştır
        run_ip_model(
            SCENARIO=scenario,
            K_TOTAL=K,
            BETA_QUALITY=b,
            SIGMA_FCM=sigma,
            WEIGHT_TYPE=weight_type,
            TRUNCATE=0.15,
            KEPT_MEVCUT=get_mevcut_indices() # Mevcutları koru
        )
        
        # En son üretilen summary dosyasını oku
        sg_str = "" if sigma == "800" else f"_sg{sigma}"
        file_suffix = f"SA{sg_str}_b{int(b*100)}_K{K}_t0.15_{weight_type}"
        sum_pattern = f"summary_all_*{file_suffix}*"
        sum_files = sorted(MODELS_DIR.glob(sum_pattern), key=lambda x: x.stat().st_mtime)
        
        if sum_files:
            df_sum = pd.read_excel(sum_files[-1])
            # Ortalama değerleri al (MCDM varyantlarının ortalaması)
            rxc_mean = df_sum["RxC"].mean()
            min_cov_mean = df_sum["min_mahalle_cov"].mean()
            avg_cov_mean = df_sum["avg_mahalle_cov"].mean()
            z_total_mean = df_sum["Z_total"].mean()
            
            results.append({
                "beta": b,
                "RxC": rxc_mean,
                "min_cov": min_cov_mean,
                "avg_cov": avg_cov_mean,
                "Z_total": z_total_mean
            })
    
    df_res = pd.DataFrame(results)
    
    # Grafik Çiz
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Sol Grafik: Z_total ve RxC
    ax1.plot(df_res["beta"], df_res["RxC"], marker='o', color='#FF6B35', linewidth=2, label="Toplam Kapsama Faydası (RxC)")
    ax1.set_xlabel("MCDM Kalite Ağırlığı (β)")
    ax1.set_ylabel("Fayda Skoru", color='#FF6B35')
    ax1.tick_params(axis='y', labelcolor='#FF6B35')
    ax1.set_title("Kalite Ağırlığı (β) vs. Kapsama Faydası (RxC)")
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Sağ Grafik: Kapsama Seviyeleri (Eşitlik)
    ax2.plot(df_res["beta"], df_res["min_cov"], marker='s', color='#2EC4B6', linewidth=2, label="Minimum Kapsama (Eşitlik)")
    ax2.plot(df_res["beta"], df_res["avg_cov"], marker='^', color='#011627', linewidth=2, label="Ortalama Kapsama")
    ax2.set_xlabel("MCDM Kalite Ağırlığı (β)")
    ax2.set_ylabel("Kapsama Oranı")
    ax2.set_title("Kalite Ağırlığı (β) vs. Kapsama Seviyeleri")
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    fig.suptitle(f"Beta (β) Hassasiyet Analizi (K={K}, Sigma={sigma})", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    out_img = CHARTS_DIR / f"sensitivity_beta_K{K}_{weight_type}.png"
    plt.savefig(out_img, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[+] Grafik kaydedildi: {out_img}")
    return df_res

def run_k_sensitivity(beta=0.3, weight_type="risk", sigma="Adaptive", scenario="A"):
    """Bütçe (K_Total) için hassasiyet analizi yapar (K=8, 12, 16, 20, 24, 28, 32)."""
    k_vals = [8, 12, 16, 20, 24, 28, 32]
    results = []
    
    print(f"[+] K (Bütçe) Hassasiyet Analizi Başlıyor (β={beta}, Hedef={weight_type}, Sigma={sigma})...")
    
    for K in k_vals:
        # IP modelini çalıştır
        run_ip_model(
            SCENARIO=scenario,
            K_TOTAL=K,
            BETA_QUALITY=beta,
            SIGMA_FCM=sigma,
            WEIGHT_TYPE=weight_type,
            TRUNCATE=0.15,
            KEPT_MEVCUT=get_mevcut_indices() # Mevcutları koru
        )
        
        # En son üretilen summary dosyasını oku
        sg_str = "" if sigma == "800" else f"_sg{sigma}"
        file_suffix = f"SA{sg_str}_b{int(beta*100)}_K{K}_t0.15_{weight_type}"
        sum_pattern = f"summary_all_*{file_suffix}*"
        sum_files = sorted(MODELS_DIR.glob(sum_pattern), key=lambda x: x.stat().st_mtime)
        
        if sum_files:
            df_sum = pd.read_excel(sum_files[-1])
            rxc_mean = df_sum["RxC"].mean()
            min_cov_mean = df_sum["min_mahalle_cov"].mean()
            avg_cov_mean = df_sum["avg_mahalle_cov"].mean()
            
            results.append({
                "K": K,
                "RxC": rxc_mean,
                "min_cov": min_cov_mean,
                "avg_cov": avg_cov_mean
            })
            
    df_res = pd.DataFrame(results)
    
    # Grafik Çiz
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Sol Grafik: RxC
    ax1.plot(df_res["K"], df_res["RxC"], marker='o', color='#E71D36', linewidth=2)
    ax1.set_xlabel("Toplam Konteyner Sayısı (K)")
    ax1.set_ylabel("Toplam Kapsama Faydası (RxC)")
    ax1.set_title("Konteyner Sayısı (K) vs. Kapsama Faydası (RxC)")
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Sağ Grafik: Kapsama Seviyeleri
    ax2.plot(df_res["K"], df_res["min_cov"], marker='s', color='#2EC4B6', linewidth=2, label="Minimum Kapsama (Eşitlik)")
    ax2.plot(df_res["K"], df_res["avg_cov"], marker='^', color='#011627', linewidth=2, label="Ortalama Kapsama")
    ax2.set_xlabel("Toplam Konteyner Sayısı (K)")
    ax2.set_ylabel("Kapsama Oranı")
    ax2.set_title("Konteyner Sayısı (K) vs. Kapsama Seviyeleri")
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    fig.suptitle(f"Bütçe (K) Hassasiyet Analizi (β={beta}, Sigma={sigma})", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    out_img = CHARTS_DIR / f"sensitivity_K_b{int(beta*100)}_{weight_type}.png"
    plt.savefig(out_img, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[+] Grafik kaydedildi: {out_img}")
    return df_res

def generate_full_grid(weight_type="risk", sigma="Adaptive", scenario="A"):
    """K=8..32 ve beta=0.0..1.0 kombinasyonlarının tamamı için grid taraması yapar ve kaydeder."""
    k_vals = [8, 12, 16, 20, 24, 28, 32]
    betas = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    results = []
    print(f"[+] Tüm Parametre Gridi Hesaplanıyor (Hedef={weight_type}, Sigma={sigma})...")
    
    total_runs = len(k_vals) * len(betas)
    run_count = 0
    
    for K in k_vals:
        for b in betas:
            run_count += 1
            print(f"  -> [{run_count}/{total_runs}] K={K}, beta={b:.1f}")
            run_ip_model(
                SCENARIO=scenario,
                K_TOTAL=K,
                BETA_QUALITY=b,
                SIGMA_FCM=sigma,
                WEIGHT_TYPE=weight_type,
                TRUNCATE=0.15,
                KEPT_MEVCUT=get_mevcut_indices() # Mevcutları koru
            )
            
            sg_str = "" if sigma == "800" else f"_sg{sigma}"
            file_suffix = f"SA{sg_str}_b{int(b*100)}_K{K}_t0.15_{weight_type}"
            sum_pattern = f"summary_all_*{file_suffix}*"
            sum_files = sorted(MODELS_DIR.glob(sum_pattern), key=lambda x: x.stat().st_mtime)
            
            if sum_files:
                df_sum = pd.read_excel(sum_files[-1])
                rxc_mean = df_sum["RxC"].mean()
                min_cov_mean = df_sum["min_mahalle_cov"].mean()
                avg_cov_mean = df_sum["avg_mahalle_cov"].mean()
                z_total_mean = df_sum["Z_total"].mean()
                
                results.append({
                    "K": K,
                    "beta": b,
                    "RxC": rxc_mean,
                    "min_cov": min_cov_mean,
                    "avg_cov": avg_cov_mean,
                    "Z_total": z_total_mean
                })
                
    df_grid = pd.DataFrame(results)
    out_path = MODELS_DIR / f"sensitivity_grid_{weight_type}.xlsx"
    df_grid.to_excel(out_path, index=False)
    print(f"[+] Grid verisi kaydedildi: {out_path}")
    return df_grid

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--K", type=int, default=20)
    parser.add_argument("--beta", type=float, default=0.3)
    parser.add_argument("--weight", type=str, default="risk", choices=["risk", "population", "shelter"])
    parser.add_argument("--sigma", type=str, default="Adaptive")
    parser.add_argument("--grid", action="store_true", help="Tüm grid taramasını hesaplar ve kaydeder")
    args = parser.parse_args()
    
    if args.grid:
        generate_full_grid(weight_type=args.weight, sigma=args.sigma)
    else:
        run_beta_sensitivity(K=args.K, weight_type=args.weight, sigma=args.sigma)
        run_k_sensitivity(beta=args.beta, weight_type=args.weight, sigma=args.sigma)

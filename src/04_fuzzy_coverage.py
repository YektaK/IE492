"""
04_fuzzy_coverage.py
Sultanbeyli Konteyner Konum Secimi - GAUSSIAN BULANIK KAPSAMA MODELI

Faz 8 Guncellemesi:
  - Adaptif Sigma: Her mahalle icin nufus yogunluguna gore (400m - 1200m arasi) esnek sigma.
  - Cift Kademeli (Two-Tier) Kapsama: 300 metreye kadar tam kapsama (mu=1.0), sonrasinda Gaussian dusus.
  - Iki Asamali Truncation (Kesme) 0.15 seviyesinde.

Girdi  : data/processed/{adaylar_140, mahalle_centroids, mevcut_12, p_road_open, mahalle_nufus}.xlsx
Cikti  : results/fuzzy_coverage/{mu_aday,mu_mevcut,distance_aday,distance_mevcut}_140x17_sAdaptive.xlsx
         results/fuzzy_coverage/Q_i_vector.xlsx
         results/fuzzy_coverage/sigma_summary_sAdaptive.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Central Config import
import config
from config import norm_mahalle, DATA_DIR as PROCESSED, RESULTS_DIR

FUZZY_COV_DIR = RESULTS_DIR / "fuzzy_coverage"
FUZZY_COV_DIR.mkdir(parents=True, exist_ok=True)

from scenario_utils import haversine_m

TRUNCATION_THRESHOLD = 0.15
CORE_DISTANCE = 300.0  # Ilk 300 metre tam kapsama

def load_coverage_inputs():
    print("[1/5] Veri okunuyor...")
    adaylar = pd.read_excel(PROCESSED / "adaylar_140.xlsx")
    mevcut = pd.read_excel(PROCESSED / "mevcut_12.xlsx")
    centroids = pd.read_excel(PROCESSED / "mahalle_centroids.xlsx")
    p_road = pd.read_excel(PROCESSED / "p_road_open.xlsx")
    nufus = pd.read_excel(PROCESSED / "mahalle_nufus.xlsx")

    adaylar["mahalle_norm"] = adaylar["Mahalle"].apply(norm_mahalle)
    mevcut["mahalle_norm"] = mevcut["mahalle"].apply(norm_mahalle)
    centroids["mahalle_norm"] = centroids["mahalle"].apply(norm_mahalle)
    p_road["mahalle_norm"] = p_road["mahalle"].apply(norm_mahalle)
    nufus["mahalle_norm"] = nufus["mahalle"].apply(norm_mahalle)

    ana_mahalleler = sorted(
        m for m in p_road["mahalle_norm"].unique()
        if "DEVLET ORMANI" not in m and "TEPE ORMANI" not in m
    )

    centroids_clean = (
        centroids.drop_duplicates(subset=["mahalle_norm"], keep="first")
        [["mahalle_norm", "lat", "lon"]]
        .rename(columns={"mahalle_norm": "mahalle"})
        .reset_index(drop=True)
    )

    mahalle_koord = centroids_clean[
        centroids_clean["mahalle"].isin(ana_mahalleler)
    ].set_index("mahalle")[["lat", "lon"]]

    if len(mahalle_koord) < len(ana_mahalleler):
        mean_lat = mahalle_koord["lat"].mean()
        mean_lon = mahalle_koord["lon"].mean()
        eksik = [m for m in ana_mahalleler if m not in mahalle_koord.index]
        for m in eksik:
            mahalle_koord.loc[m] = (mean_lat, mean_lon)

    print("[2/5] Adaptif Sigmalar hesaplaniyor...")
    nufus_dict = nufus.set_index("mahalle_norm")["nufus_2024"].to_dict()
    pop_values = np.array([nufus_dict.get(m, 20000) for m in ana_mahalleler])
    pop_min = pop_values.min()
    pop_max = pop_values.max()

    sigma_array = np.zeros(len(ana_mahalleler))
    for i, m in enumerate(ana_mahalleler):
        p = pop_values[i]
        if pop_max > pop_min:
            s = 1200 - ((p - pop_min) / (pop_max - pop_min)) * (1200 - 400)
        else:
            s = 800
        sigma_array[i] = s

    print(f"  Sigma araligi: [{sigma_array.min():.0f}m, {sigma_array.max():.0f}m]")
    return adaylar, mevcut, p_road, ana_mahalleler, mahalle_koord, sigma_array

def _parse_sigma_values(sigma: str) -> list[float]:
    try:
        return [float(part) for part in sigma.split("_")]
    except ValueError as exc:
        raise ValueError(
            f"Gecersiz sigma modu: {sigma}. 800, 800_300, Adaptive veya RoadNetwork kullanin."
        ) from exc


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sigma",
        type=str,
        default="Adaptive",
        help="Kapsama modu: Adaptive, RoadNetwork, sabit metre degeri (800) veya legacy kompozit (800_300).",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=["haversine", "road"],
        help="Geriye donuk uyumluluk icin: road secilirse --sigma RoadNetwork gibi davranir.",
    )
    args = parser.parse_args()

    sigma_mode = args.sigma
    if args.mode == "road":
        sigma_mode = "RoadNetwork"
    use_road = sigma_mode == "RoadNetwork"

    adaylar, mevcut, p_road, ana_mahalleler, mahalle_koord, sigma_array = load_coverage_inputs()
    
    print("[3/5] Mesafe matrisleri hesaplaniyor veya okunuyor...")
    aday_lat = adaylar["Enlem"].values
    aday_lon = adaylar["Boylam"].values
    mahalle_lat = mahalle_koord.loc[ana_mahalleler, "lat"].values
    mahalle_lon = mahalle_koord.loc[ana_mahalleler, "lon"].values
    
    if use_road:
        print("  [+] Gercek yol agi (Road Network) mesafeleri yukleniyor...")
        aday_path = FUZZY_COV_DIR / "distance_road_aday_140x17.xlsx"
        mevcut_path = FUZZY_COV_DIR / "distance_road_mevcut_12x17.xlsx"
        
        if not (aday_path.exists() and mevcut_path.exists()):
            print("  [-] Hata: Yol agi mesafe matrisleri bulunamadi. Lutfen once src/road_network.py calistirin.")
            sys.exit(1)
            
        df_road_aday = pd.read_excel(aday_path)
        df_road_mevcut = pd.read_excel(mevcut_path)
        
        # S_No ve container_no sutunlarini cikart
        D_aday = df_road_aday[ana_mahalleler].values
        D_mevcut = df_road_mevcut[ana_mahalleler].values
        SUFFIX = "_sRoadNetwork"
    else:
        print("  [+] Haversine (kus ucusu) mesafeleri hesaplaniyor...")
        D_aday = np.zeros((len(adaylar), len(ana_mahalleler)))
        D_mevcut = np.zeros((len(mevcut), len(ana_mahalleler)))
        
        for j, (mlat, mlon) in enumerate(zip(mahalle_lat, mahalle_lon)):
            D_aday[:, j] = haversine_m(mlat, mlon, aday_lat, aday_lon)
            D_mevcut[:, j] = haversine_m(mlat, mlon, mevcut["enlem"].values, mevcut["boylam"].values)
        SUFFIX = "_sAdaptive" if sigma_mode == "Adaptive" else f"_s{sigma_mode}"

    print("[4/5] Cift Kademeli (Two-Tier) ve Adaptif Kapsama hesaplanıyor...")
    
    def calc_coverage(D: np.ndarray, sigmas: np.ndarray, core: float, trunc: float):
        n, m = D.shape
        mu = np.zeros((n, m))
        for j in range(m):
            s = sigmas[j]
            dist = D[:, j]
            eff_dist = np.maximum(dist - core, 0)
            mu_col = np.exp(-(eff_dist ** 2) / (2 * s ** 2))
            mu_col[mu_col < trunc] = 0.0
            mu[:, j] = mu_col
        return mu

    if sigma_mode in ["Adaptive", "RoadNetwork"]:
        MU_aday = calc_coverage(D_aday, sigma_array, CORE_DISTANCE, TRUNCATION_THRESHOLD)
        MU_mevcut = calc_coverage(D_mevcut, sigma_array, CORE_DISTANCE, TRUNCATION_THRESHOLD)
        sigma_summary = "RoadNetwork" if sigma_mode == "RoadNetwork" else "Adaptive (400-1200m)"
        summary_core = CORE_DISTANCE
    else:
        sigma_values = _parse_sigma_values(sigma_mode)
        MU_aday_parts = [
            calc_coverage(D_aday, np.full(len(ana_mahalleler), sigma), 0.0, TRUNCATION_THRESHOLD)
            for sigma in sigma_values
        ]
        MU_mevcut_parts = [
            calc_coverage(D_mevcut, np.full(len(ana_mahalleler), sigma), 0.0, TRUNCATION_THRESHOLD)
            for sigma in sigma_values
        ]
        MU_aday = np.maximum.reduce(MU_aday_parts)
        MU_mevcut = np.maximum.reduce(MU_mevcut_parts)
        sigma_summary = sigma_mode
        summary_core = 0.0

    print(f"  MU_aday max: {MU_aday.max():.4f}, mean: {MU_aday.mean():.4f}")

    print("[5/5] Q_i vektoru olusturuluyor...")
    Q_i = (
        p_road[p_road["mahalle_norm"].isin(ana_mahalleler)]
        .set_index("mahalle_norm")
        .reindex(ana_mahalleler)["p_road_open"]
        .fillna(0.70)
        .values
    )

    print(f"\n[+] Kaydediliyor (suffix={SUFFIX})...")

    pd.DataFrame(D_aday, index=adaylar["S_No"], columns=ana_mahalleler).to_excel(FUZZY_COV_DIR / f"distance_aday_140x17{SUFFIX}.xlsx")
    pd.DataFrame(D_mevcut, index=mevcut["container_no"], columns=ana_mahalleler).to_excel(FUZZY_COV_DIR / f"distance_mevcut_12x17{SUFFIX}.xlsx")

    mu_aday_path = FUZZY_COV_DIR / f"mu_aday_140x17{SUFFIX}.xlsx"
    mu_mevcut_path = FUZZY_COV_DIR / f"mu_mevcut_12x17{SUFFIX}.xlsx"
    pd.DataFrame(MU_aday, index=adaylar["S_No"], columns=ana_mahalleler).to_excel(mu_aday_path)
    pd.DataFrame(MU_mevcut, index=mevcut["container_no"], columns=ana_mahalleler).to_excel(mu_mevcut_path)

    pd.DataFrame({"mahalle": ana_mahalleler, "Q_i_p_road_open": Q_i}).to_excel(FUZZY_COV_DIR / "Q_i_vector.xlsx", index=False)
    pd.DataFrame({"mahalle": ana_mahalleler, "sigma_m": sigma_array}).to_excel(FUZZY_COV_DIR / "adaptive_sigmas.xlsx", index=False)

    summary = {
        "sigma": sigma_summary,
        "two_tier_core_m": summary_core,
        "truncation_threshold": TRUNCATION_THRESHOLD,
        "n_aday": int(len(adaylar)),
        "n_mahalle": int(len(ana_mahalleler)),
        "mu_aday_mean": round(float(MU_aday.mean()), 4),
    }

    with open(FUZZY_COV_DIR / f"sigma_summary{SUFFIX}.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("GAUSSIAN BULANIK KAPSAMA HESAPLAMA TAMAMLANDI")
    print("=" * 60)

if __name__ == "__main__":
    main()

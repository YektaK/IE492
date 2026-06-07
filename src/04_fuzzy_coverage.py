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
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
FUZZY_COV_DIR = PROJECT_ROOT / "results" / "fuzzy_coverage"
FUZZY_COV_DIR.mkdir(parents=True, exist_ok=True)

TRUNCATION_THRESHOLD = 0.15
CORE_DISTANCE = 300.0  # Ilk 300 metre tam kapsama

print("[1/5] Veri okunuyor...")
adaylar = pd.read_excel(PROCESSED / "adaylar_140.xlsx")
mevcut = pd.read_excel(PROCESSED / "mevcut_12.xlsx")
centroids = pd.read_excel(PROCESSED / "mahalle_centroids.xlsx")
p_road = pd.read_excel(PROCESSED / "p_road_open.xlsx")
nufus = pd.read_excel(PROCESSED / "mahalle_nufus.xlsx")

def norm_mahalle(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tr_map = str.maketrans({
        "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U",
        "ç": "C", "ğ": "G", "ı": "I", "ö": "O", "ş": "S", "ü": "U",
        "â": "A", "î": "I", "û": "U",
    })
    return s.strip().translate(tr_map).upper()

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

# Adaptif Sigma Hesaplama (Nufus yogunluguna gore ters orantili 400m - 1200m)
print("[2/5] Adaptif Sigmalar hesaplaniyor...")
nufus_dict = nufus.set_index("mahalle_norm")["nufus_2024"].to_dict()
pop_values = np.array([nufus_dict.get(m, 20000) for m in ana_mahalleler])
pop_min = pop_values.min()
pop_max = pop_values.max()

sigma_array = np.zeros(len(ana_mahalleler))
for i, m in enumerate(ana_mahalleler):
    p = pop_values[i]
    # Ters interpolasyon: Min nufus -> 1200m, Max nufus -> 400m
    if pop_max > pop_min:
        s = 1200 - ((p - pop_min) / (pop_max - pop_min)) * (1200 - 400)
    else:
        s = 800
    sigma_array[i] = s

print(f"  Sigma araligi: [{sigma_array.min():.0f}m, {sigma_array.max():.0f}m]")

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))

print("[3/5] Mesafe matrisleri hesaplaniyor...")
aday_lat = adaylar["Enlem"].values
aday_lon = adaylar["Boylam"].values
mahalle_lat = mahalle_koord.loc[ana_mahalleler, "lat"].values
mahalle_lon = mahalle_koord.loc[ana_mahalleler, "lon"].values

D_aday = np.zeros((len(adaylar), len(ana_mahalleler)))
D_mevcut = np.zeros((len(mevcut), len(ana_mahalleler)))

for j, (mlat, mlon) in enumerate(zip(mahalle_lat, mahalle_lon)):
    D_aday[:, j] = haversine_m(mlat, mlon, aday_lat, aday_lon)
    D_mevcut[:, j] = haversine_m(mlat, mlon, mevcut["enlem"].values, mevcut["boylam"].values)

print("[4/5] Cift Kademeli (Two-Tier) ve Adaptif Kapsama hesaplanıyor...")

def calc_coverage(D: np.ndarray, sigmas: np.ndarray, core: float, trunc: float):
    n, m = D.shape
    mu = np.zeros((n, m))
    for j in range(m):
        # O mahallenin sigmasi
        s = sigmas[j]
        # Her bir parselin o mahalleye mesafesi
        dist = D[:, j]
        # Core (300m) ici 1.0, disi Gaussian
        eff_dist = np.maximum(dist - core, 0)
        mu_col = np.exp(-(eff_dist ** 2) / (2 * s ** 2))
        mu_col[mu_col < trunc] = 0.0
        mu[:, j] = mu_col
    return mu

MU_aday = calc_coverage(D_aday, sigma_array, CORE_DISTANCE, TRUNCATION_THRESHOLD)
MU_mevcut = calc_coverage(D_mevcut, sigma_array, CORE_DISTANCE, TRUNCATION_THRESHOLD)

print(f"  MU_aday max: {MU_aday.max():.4f}, mean: {MU_aday.mean():.4f}")

print("[5/5] Q_i vektoru olusturuluyor...")
Q_i = (
    p_road[p_road["mahalle_norm"].isin(ana_mahalleler)]
    .set_index("mahalle_norm")
    .reindex(ana_mahalleler)["p_road_open"]
    .fillna(0.70)
    .values
)

print("\n[+] Kaydediliyor (sigma=Adaptive)...")
SUFFIX = "_sAdaptive"

pd.DataFrame(D_aday, index=adaylar["S_No"], columns=ana_mahalleler).to_excel(FUZZY_COV_DIR / "distance_aday_140x17.xlsx")
pd.DataFrame(D_mevcut, index=mevcut["container_no"], columns=ana_mahalleler).to_excel(FUZZY_COV_DIR / "distance_mevcut_12x17.xlsx")

mu_aday_path = FUZZY_COV_DIR / f"mu_aday_140x17{SUFFIX}.xlsx"
mu_mevcut_path = FUZZY_COV_DIR / f"mu_mevcut_12x17{SUFFIX}.xlsx"
pd.DataFrame(MU_aday, index=adaylar["S_No"], columns=ana_mahalleler).to_excel(mu_aday_path)
pd.DataFrame(MU_mevcut, index=mevcut["container_no"], columns=ana_mahalleler).to_excel(mu_mevcut_path)

pd.DataFrame({"mahalle": ana_mahalleler, "Q_i_p_road_open": Q_i}).to_excel(FUZZY_COV_DIR / "Q_i_vector.xlsx", index=False)
pd.DataFrame({"mahalle": ana_mahalleler, "sigma_m": sigma_array}).to_excel(FUZZY_COV_DIR / "adaptive_sigmas.xlsx", index=False)

summary = {
    "sigma": "Adaptive (400-1200m)",
    "two_tier_core_m": CORE_DISTANCE,
    "truncation_threshold": TRUNCATION_THRESHOLD,
    "n_aday": int(len(adaylar)),
    "n_mahalle": int(len(ana_mahalleler)),
    "mu_aday_mean": round(float(MU_aday.mean()), 4),
}

with open(FUZZY_COV_DIR / f"sigma_summary{SUFFIX}.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("=" * 60)
print("GAUSSIAN BULANIK KAPSAMA (ADAPTIF + IKI KADEMELI) TAMAMLANDI")
print("=" * 60)

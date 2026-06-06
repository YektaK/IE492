"""
04_fcm.py
Sultanbeyli Konteyner Konum Secimi - FUZZY C-MEANS (Gaussian) UZAKLIK

Girdi  : data/processed/{adaylar_140, mahalle_centroids, mevcut_12, p_road_open}.xlsx
Cikti  : results/fcm/{mu_aday,mu_mevcut,distance_aday,distance_mevcut}_140x17_s{sigma}.xlsx
         results/fcm/Q_i_vector.xlsx
         results/fcm/sigma_summary_s{sigma}.json

Kullanim: python src/04_fcm.py                    (varsayilan sigma=800)
          python src/04_fcm.py --sigma 300        (sigma=300)
          python src/04_fcm.py --sigma 800_300    (iki kademeli: max(mu_800, mu_300))
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 0) YOL TANIMLARI
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
FCM_DIR = PROJECT_ROOT / "results" / "fcm"
FCM_DIR.mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--sigma", type=str, default="800",
                    help="Gaussian sigma (metre), or '800_300' for two-tier")
args = parser.parse_args()
SIGMA_STR = args.sigma
TWO_TIER = "_" in SIGMA_STR
if TWO_TIER:
    parts = SIGMA_STR.split("_")
    SIGMA_VALUES = [float(p) for p in parts]
    print(f"[+] Iki kademeli sigma: {SIGMA_VALUES}")
    SIGMA_LABEL = SIGMA_STR
else:
    SIGMA_VALUES = [float(SIGMA_STR)]
    SIGMA_LABEL = SIGMA_STR

# ---------------------------------------------------------------------------
# 1) VERIYI OKU
# ---------------------------------------------------------------------------
print("[1/5] Veri okunuyor...")
adaylar = pd.read_excel(PROCESSED / "adaylar_140.xlsx")
mevcut = pd.read_excel(PROCESSED / "mevcut_12.xlsx")
centroids = pd.read_excel(PROCESSED / "mahalle_centroids.xlsx")
p_road = pd.read_excel(PROCESSED / "p_road_open.xlsx")

print(f"  adaylar       : {adaylar.shape}")
print(f"  mevcut        : {mevcut.shape}")
print(f"  centroids     : {centroids.shape}")
print(f"  p_road_open   : {p_road.shape}")

# Mahalle isim duzeltme (encoding bozukluklarini temizle)
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

# Asil problem mahalleleri: p_road'da olan 17 mahalle (orman alanlari haric)
ana_mahalleler = sorted(
    m for m in p_road["mahalle_norm"].unique()
    if "DEVLET ORMANI" not in m and "TEPE ORMANI" not in m
)
print(f"  Ana problem mahalleleri ({len(ana_mahalleler)}): {ana_mahalleler}")

# Centroids: mahalle_norm'a gore dedup (birden fazla satır varsa ilkini al)
centroids_clean = (
    centroids.drop_duplicates(subset=["mahalle_norm"], keep="first")
    [["mahalle_norm", "lat", "lon"]]
    .rename(columns={"mahalle_norm": "mahalle"})
    .reset_index(drop=True)
)
print(f"  centroid'ler (dedup): {centroids_clean.shape}")

# Ana mahallelerin koordinatlari
mahalle_koord = centroids_clean[
    centroids_clean["mahalle"].isin(ana_mahalleler)
].set_index("mahalle")[["lat", "lon"]]
print(f"  Koordinati bulunan ana mahalle: {len(mahalle_koord)}")

# Eksik mahalleler icin ortalama koordinat
if len(mahalle_koord) < len(ana_mahalleler):
    mean_lat = mahalle_koord["lat"].mean()
    mean_lon = mahalle_koord["lon"].mean()
    eksik = [m for m in ana_mahalleler if m not in mahalle_koord.index]
    for m in eksik:
        mahalle_koord.loc[m] = (mean_lat, mean_lon)
    print(f"  {len(eksik)} mahalle icin ortalama koordinat kullanildi")

# ---------------------------------------------------------------------------
# 2) HAVERSINE MESAFE FONKSIYONU
# ---------------------------------------------------------------------------
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------------------
# 3) ADAY x MAHALLE MESAFE MATRISI
# ---------------------------------------------------------------------------
print(f"[2/5] Aday x mahalle mesafesi hesaplaniyor...")

aday_lat = adaylar["Enlem"].values
aday_lon = adaylar["Boylam"].values
mahalle_lat = mahalle_koord.loc[ana_mahalleler, "lat"].values
mahalle_lon = mahalle_koord.loc[ana_mahalleler, "lon"].values

D_aday = np.zeros((len(adaylar), len(ana_mahalleler)))
for j, (mlat, mlon) in enumerate(zip(mahalle_lat, mahalle_lon)):
    D_aday[:, j] = haversine_m(mlat, mlon, aday_lat, aday_lon)

print(f"  D_aday shape: {D_aday.shape}, mesafe: [{D_aday.min():.0f}, {D_aday.max():.0f}] m")

# ---------------------------------------------------------------------------
# 4) MEVCUT x MAHALLE MESAFE MATRISI
# ---------------------------------------------------------------------------
print("[3/5] Mevcut x mahalle mesafesi hesaplaniyor...")

mevcut_lat = mevcut["enlem"].values
mevcut_lon = mevcut["boylam"].values

D_mevcut = np.zeros((len(mevcut), len(ana_mahalleler)))
for j, (mlat, mlon) in enumerate(zip(mahalle_lat, mahalle_lon)):
    D_mevcut[:, j] = haversine_m(mlat, mlon, mevcut_lat, mevcut_lon)

print(f"  D_mevcut shape: {D_mevcut.shape}")

# ---------------------------------------------------------------------------
# 5) GAUSSIAN UYELIK HESAPLAMA (tek veya iki kademeli)
# ---------------------------------------------------------------------------
print("[4/5] Gaussian uyelik hesaplaniyor...")


def gaussian_mu(D: np.ndarray, sigma: float) -> np.ndarray:
    return np.exp(-(D ** 2) / (2 * sigma ** 2))


MU_aday = np.zeros_like(D_aday)
MU_mevcut = np.zeros_like(D_mevcut)
sigma_labels = []

if TWO_TIER:
    # Iki kademeli: her sigma icin ayri hesapla, max al
    for sigma in SIGMA_VALUES:
        sigma_labels.append(f"{sigma:.0f}")
        M_a = gaussian_mu(D_aday, sigma)
        M_m = gaussian_mu(D_mevcut, sigma)
        MU_aday = np.maximum(MU_aday, M_a)
        MU_mevcut = np.maximum(MU_mevcut, M_m)
        print(f"  sigma={sigma:.0f}: mu_aday mean={M_a.mean():.4f}, "
              f"mu_mevcut mean={M_m.mean():.4f}")
    print(f"  -> combined (max): mu_aday mean={MU_aday.mean():.4f}, "
          f"mu_mevcut mean={MU_mevcut.mean():.4f}")
    SIGMA_EFF = SIGMA_VALUES[-1]  # son sigma kritik mesafe icin
else:
    sigma = SIGMA_VALUES[0]
    sigma_labels.append(f"{sigma:.0f}")
    MU_aday = gaussian_mu(D_aday, sigma)
    MU_mevcut = gaussian_mu(D_mevcut, sigma)
    SIGMA_EFF = sigma

print(f"  MU_aday:   shape={MU_aday.shape}, "
      f"min={MU_aday.min():.4f}, max={MU_aday.max():.4f}, "
      f"mean={MU_aday.mean():.4f}")
print(f"  MU_mevcut: shape={MU_mevcut.shape}, "
      f"min={MU_mevcut.min():.4f}, max={MU_mevcut.max():.4f}, "
      f"mean={MU_mevcut.mean():.4f}")

d_50 = SIGMA_EFF * np.sqrt(2 * np.log(2))
d_10 = SIGMA_EFF * np.sqrt(2 * np.log(10))
print(f"  mu=0.50 esik mesafesi: {d_50:.0f} m (sigma referans={SIGMA_EFF:.0f})")
print(f"  mu=0.10 esik mesafesi: {d_10:.0f} m")

# ---------------------------------------------------------------------------
# 6) Q_i VEKTORU (p_road_open -> mahalle bazli)
# ---------------------------------------------------------------------------
print("[5/5] Q_i vektoru olusturuluyor...")

Q_i = (
    p_road[p_road["mahalle_norm"].isin(ana_mahalleler)]
    .set_index("mahalle_norm")
    .reindex(ana_mahalleler)["p_road_open"]
    .fillna(0.70)
    .values
)
print(f"  Q_i mean={Q_i.mean():.3f}, std={Q_i.std():.3f}, "
      f"min={Q_i.min():.3f}, max={Q_i.max():.3f}")

# ---------------------------------------------------------------------------
# 7) KAYDET (sigma-ekli dosya isimleri)
# ---------------------------------------------------------------------------
print()
print("[+] Kaydediliyor (sigma={})...".format(SIGMA_LABEL))

SUFFIX = f"_s{SIGMA_LABEL}"

# Mesafe matrisleri (sabit — mesafe sigmadan bagimsiz)
pd.DataFrame(D_aday, index=adaylar["S_No"], columns=ana_mahalleler).to_excel(
    FCM_DIR / "distance_aday_140x17.xlsx"
)
pd.DataFrame(D_mevcut, index=mevcut["container_no"], columns=ana_mahalleler).to_excel(
    FCM_DIR / "distance_mevcut_12x17.xlsx"
)

# Uyelik matrisleri (sigma-ekli)
mu_aday_path = FCM_DIR / f"mu_aday_140x17{SUFFIX}.xlsx"
mu_mevcut_path = FCM_DIR / f"mu_mevcut_12x17{SUFFIX}.xlsx"
pd.DataFrame(MU_aday, index=adaylar["S_No"], columns=ana_mahalleler).to_excel(mu_aday_path)
pd.DataFrame(MU_mevcut, index=mevcut["container_no"], columns=ana_mahalleler).to_excel(mu_mevcut_path)

# Q_i (sabit)
pd.DataFrame({"mahalle": ana_mahalleler, "Q_i_p_road_open": Q_i}).to_excel(
    FCM_DIR / "Q_i_vector.xlsx", index=False
)

# Ozet (sigma-ekli)
summary = {
    "sigma": SIGMA_LABEL,
    "sigma_values": sigma_labels,
    "two_tier": TWO_TIER,
    "d_50_m": round(d_50, 1),
    "d_10_m": round(d_10, 1),
    "n_aday": int(len(adaylar)),
    "n_mevcut": int(len(mevcut)),
    "n_mahalle": int(len(ana_mahalleler)),
    "mu_aday": {
        "min": round(float(MU_aday.min()), 4),
        "max": round(float(MU_aday.max()), 4),
        "mean": round(float(MU_aday.mean()), 4),
        "std": round(float(MU_aday.std()), 4),
    },
    "mu_mevcut": {
        "min": round(float(MU_mevcut.min()), 4),
        "max": round(float(MU_mevcut.max()), 4),
        "mean": round(float(MU_mevcut.mean()), 4),
        "std": round(float(MU_mevcut.std()), 4),
    },
    "Q_i": {
        "min": round(float(Q_i.min()), 4),
        "max": round(float(Q_i.max()), 4),
        "mean": round(float(Q_i.mean()), 4),
        "std": round(float(Q_i.std()), 4),
    },
    "mahalleler": ana_mahalleler,
}
with open(FCM_DIR / f"sigma_summary{SUFFIX}.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print()
print("=" * 60)
if TWO_TIER:
    print(f"FCM (IKI KADEMELI GAUSSIAN) TAMAMLANDI — sigma={SIGMA_LABEL}")
else:
    print(f"FCM (GAUSSIAN UZAKLIK) TAMAMLANDI — sigma={SIGMA_LABEL}")
print("=" * 60)
print(f"  Aday        : {summary['n_aday']}")
print(f"  Mevcut      : {summary['n_mevcut']}")
print(f"  Mahalle     : {summary['n_mahalle']}")
print(f"  Sigma       : {SIGMA_LABEL}")
print(f"  mu=0.50 mes : {d_50:.0f} m")
print(f"  mu=0.10 mes : {d_10:.0f} m")
print()
print("Cikti dosyalari (results/fcm/):")
for f in sorted(FCM_DIR.iterdir()):
    if f.name.startswith("mu_") or f.name.startswith("distance_") or f.name.startswith("sigma_summary"):
        print(f"  - {f.name}")

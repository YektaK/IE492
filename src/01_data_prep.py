"""
01_data_prep.py
Sultanbeyli Konteyner Konum Secimi - VERI HAZIRLIGI

Girdi  : archive/old_output/data/ icindeki 5 orijinal dosya
Cikti  : data/processed/ altinda 8 temiz xlsx + data/scenarios/ altinda 6 senaryo

Kullanim: python src/01_data_prep.py
"""

from __future__ import annotations

import os
import shutil

import numpy as np
import pandas as pd

import config
from config import PROJECT_ROOT, DATA_DIR as PROCESSED
from scenario_utils import haversine_m

# ---------------------------------------------------------------------------
# 0) YOL TANIMLARI (config'den alinmayan, sadece bu script'e ozel)
# ---------------------------------------------------------------------------
ARCHIVE_DATA = PROJECT_ROOT / "archive" / "old_output" / "data"
SCENARIOS = PROJECT_ROOT / "data" / "scenarios"
RAW_DIRS = [
    PROJECT_ROOT / "data" / "raw" / "ibb_deprem_raporu",
    PROJECT_ROOT / "data" / "raw" / "afad_konteyner",
    PROJECT_ROOT / "data" / "raw" / "toplanma_alanlari",
    PROJECT_ROOT / "data" / "raw" / "tukik_nufus",
]

# Dizinleri olustur
for d in [PROCESSED, SCENARIOS, *RAW_DIRS]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1) ORJINAL VERIYI OKU
# ---------------------------------------------------------------------------
print("[1/6] Orijinal veriler okunuyor...")

adaylar = pd.read_excel(ARCHIVE_DATA / "adaylar.xlsx")
mevcut = pd.read_excel(ARCHIVE_DATA / "mevcut_12.xlsx")
nufus = pd.read_excel(ARCHIVE_DATA / "mahalle_nufus.xlsx")
risk = pd.read_excel(ARCHIVE_DATA / "mahalle_risk.xlsx")
barinma = pd.read_excel(ARCHIVE_DATA / "mahalle_barinma_ihtiyaci.xlsx")

print(f"  adaylar   : {adaylar.shape}")
print(f"  mevcut    : {mevcut.shape}")
print(f"  nufus     : {nufus.shape}")
print(f"  risk      : {risk.shape}")
print(f"  barinma   : {barinma.shape}")

# ---------------------------------------------------------------------------
# 2) MAHALLE MERKEZ KOORDINATLARI (turetilmis)
# ---------------------------------------------------------------------------
print("[2/6] Mahalle merkez koordinatlari hesaplaniyor...")

# Her mahalle icin aday parsel koordinatlarinin ortalamasi
centroids = (
    adaylar.groupby("Mahalle")[["Enlem", "Boylam"]]
    .mean()
    .reset_index()
    .rename(columns={"Enlem": "lat", "Boylam": "lon"})
)

# Eger mevcut konteyner bir mahallede yoksa, onu da ekle (sentinel)
mevcut_extra = mevcut.groupby("mahalle")[["enlem", "boylam"]].mean().reset_index()
mevcut_extra.columns = ["Mahalle", "lat", "lon"]
centroids = (
    pd.concat([centroids, mevcut_extra], ignore_index=True)
    .drop_duplicates(subset=["Mahalle"])
    .reset_index(drop=True)
)

# Normalize mahalle isimleri (buyuk harf, tirnak temizligi)
centroids["Mahalle"] = centroids["Mahalle"].str.strip().str.upper()
centroids = centroids.rename(columns={"Mahalle": "mahalle"})
for df in [nufus, risk, barinma]:
    df["mahalle"] = df["mahalle"].str.strip().str.upper()

# Tum mahalleler
tum_mahalleler = sorted(set(nufus["mahalle"]) | set(risk["mahalle"]) | set(barinma["mahalle"]))
print(f"  {len(tum_mahalleler)} mahalle tespit edildi")
print(f"  centroid'lerde mahalle sayisi: {centroids['mahalle'].nunique()}")

# Centroid bulunmayan mahalleler icin ortalama ile doldur
if centroids["mahalle"].nunique() < len(tum_mahalleler):
    mean_lat = centroids["lat"].mean()
    mean_lon = centroids["lon"].mean()
    eksik = [m for m in tum_mahalleler if m not in centroids["mahalle"].values]
    for m in eksik:
        centroids = pd.concat(
            [centroids, pd.DataFrame([{"mahalle": m, "lat": mean_lat, "lon": mean_lon}])],
            ignore_index=True,
        )
    print(f"  {len(eksik)} mahalle icin ortalama koordinat kullanildi")

centroids.to_excel(PROCESSED / "mahalle_centroids.xlsx", index=False)

# ---------------------------------------------------------------------------
# 3) p_access_road (parsel bazli) - sentetik ama gercekci
# ---------------------------------------------------------------------------
print("[3/6] p_access_road (parsel bazli) uretiliyor...")

np.random.seed(42)
n = len(adaylar)

# Mahalle ortalama erisebilirligi (0.55 - 0.95 arasi)
mahalle_puanlari = centroids.set_index("mahalle")[["lat", "lon"]].apply(
    lambda r: 0.55 + 0.40 * (
        (r["lat"] - centroids["lat"].min())
        / (centroids["lat"].max() - centroids["lat"].min() + 1e-9)
    ),
    axis=1,
)
mahalle_puanlari = mahalle_puanlari.clip(0.55, 0.95).to_dict()

# Parsel bazli: mahalle ortalamasi + gaussian gurultu
p_access = []
for _, row in adaylar.iterrows():
    base = mahalle_puanlari.get(row["Mahalle"].strip().upper(), 0.70)
    val = np.clip(base + np.random.normal(0, 0.05), 0.30, 0.99)
    p_access.append(val)
adaylar["p_access_road"] = p_access
adaylar.to_excel(PROCESSED / "adaylar_140.xlsx", index=False)
print(f"  p_access_road: mean={np.mean(p_access):.3f}, std={np.std(p_access):.3f}")

# ---------------------------------------------------------------------------
# 4) p_road_open (mahalle bazli) - sentetik
# ---------------------------------------------------------------------------
print("[4/6] p_road_open (mahalle bazli) uretiliyor...")

p_road = []
for m in tum_mahalleler:
    base = mahalle_puanlari.get(m, 0.70)
    val = np.clip(base + np.random.normal(0, 0.05), 0.40, 0.99)
    p_road.append({"mahalle": m, "p_road_open": val})

p_road_df = pd.DataFrame(p_road)
p_road_df.to_excel(PROCESSED / "p_road_open.xlsx", index=False)
print(f"  {len(p_road_df)} mahalle icin p_road_open")

# ---------------------------------------------------------------------------
# 5) MAHALLE DUZEYINDE TEMIZ TABLOLAR
# ---------------------------------------------------------------------------
print("[5/6] Mahalle duzeyinde temiz tablolar yaziliyor...")

nufus_clean = nufus[["mahalle", "nufus_2024"]].copy()
nufus_clean.to_excel(PROCESSED / "mahalle_nufus.xlsx", index=False)

risk_clean = risk[["mahalle", "risk_score"]].copy()
risk_clean["risk_score"] = risk_clean["risk_score"].astype(float)
risk_clean.to_excel(PROCESSED / "mahalle_risk.xlsx", index=False)

barinma_clean = barinma[["mahalle", "hane_ihtiyaci"]].copy()
barinma_clean.to_excel(PROCESSED / "mahalle_barinma.xlsx", index=False)

mevcut_clean = mevcut[["container_no", "mahalle", "enlem", "boylam"]].copy()
mevcut_clean["mahalle"] = mevcut_clean["mahalle"].str.strip().str.upper()
mevcut_clean.to_excel(PROCESSED / "mevcut_12.xlsx", index=False)

# ---------------------------------------------------------------------------
# 6) KRITER MATRISI (140 parsel x 4 kriter)
# ---------------------------------------------------------------------------
print("[6/6] Kriter matrisi olusturuluyor...")

def fix_tr_chars(s):
    if not isinstance(s, str): return s
    tr_map = {'İ': 'I', 'I': 'I', 'Ş': 'S', 'Ç': 'C', 'Ö': 'O', 'Ü': 'U', 'Ğ': 'G',
              'i': 'i', 'ı': 'i', 'ş': 's', 'ç': 'c', 'ö': 'o', 'ü': 'u', 'ğ': 'g'}
    for k, v in tr_map.items():
        s = s.replace(k, v)
    return s.strip().upper()

adaylar["Mahalle"] = adaylar["Mahalle"].apply(fix_tr_chars)
nufus_clean["mahalle"] = nufus_clean["mahalle"].apply(fix_tr_chars)
risk_clean["mahalle"] = risk_clean["mahalle"].apply(fix_tr_chars)
barinma_clean["mahalle"] = barinma_clean["mahalle"].apply(fix_tr_chars)

nufus_idx = nufus_clean.set_index("mahalle")["nufus_2024"].to_dict()
risk_idx = risk_clean.set_index("mahalle")["risk_score"].to_dict()
barinma_idx = barinma_clean.set_index("mahalle")["hane_ihtiyaci"].to_dict()

# C1: hasar riski (mahalleden)
adaylar["C1_hasar_risk"] = adaylar["Mahalle"].map(risk_idx).fillna(risk_clean["risk_score"].mean())

# C2: lojistik kompozit — deprem mudahalesi oncelik siralamasina gore agirlikli bilesik
# Su (0.35): yasam icin kritik, oncelik 1
# Jenerator (0.30): enerji bagimsizligi, gece mudahale, oncelik 2
# WC (0.20): hijyen ve uzun sureli konaklama, oncelik 3
# Kamera (0.15): guvenlik/izleme, oncelik 4
W_INFRA = {"Su_bin": 0.35, "Jen_bin": 0.30, "WC_bin": 0.20, "Kamera_bin": 0.15}
print(f"  C2 altyapi agirliklari: {W_INFRA}")
adaylar["C2_lojistik"] = sum(
    adaylar[col] * w for col, w in W_INFRA.items()
)
print(f"  C2_lojistik: mean={adaylar['C2_lojistik'].mean():.3f}, "
      f"std={adaylar['C2_lojistik'].std():.3f}, "
      f"max={adaylar['C2_lojistik'].max():.3f}")

# C3: bosluk mesafesi (en yakin mevcut konteynere metre)
mesafeler = np.zeros(len(adaylar))
for i, row in adaylar.iterrows():
    d = haversine_m(
        row["Enlem"], row["Boylam"],
        mevcut_clean["enlem"].values, mevcut_clean["boylam"].values,
    )
    mesafeler[i] = d.min()
adaylar["C3_bosluk_m"] = mesafeler

# 0-1 normalize (max mesafeye oranla)
max_m = adaylar["C3_bosluk_m"].max()
adaylar["C3_bosluk_norm"] = adaylar["C3_bosluk_m"] / max_m

# C4: barinma talebi (mahalleden)
adaylar["C4_barinma"] = adaylar["Mahalle"].map(barinma_idx).fillna(barinma_clean["hane_ihtiyaci"].mean())

criteria = adaylar[
    ["S_No", "AYDES_ID", "Mahalle", "Enlem", "Boylam",
     "C1_hasar_risk", "C2_lojistik", "C3_bosluk_m", "C3_bosluk_norm", "C4_barinma",
     "p_access_road"]
].copy()

# ---------------------------------------------------------------------------
# 6b) POWER TRANSFORM AMPLIFIKASYONU (Gorev 1.2)
# ---------------------------------------------------------------------------
# Amac: Yan yana konumlarda benzer skorlari ayiriklastirmak.
# Min-max normalize → ham degerler [0,1]'e tasiniyor.
# Power transform (alpha=2): yuksek degerler daha yuksege, dusuk degerler daha dusuge cekilir.
# Ornek: 0.70 vs 0.90 farki 0.20 → amplified 0.49 vs 0.81, fark 0.32 (%60 artis)

ALPHA_POWER = 2  # Amplifikasyon katsayisi; 1=linear, 2=kare, 3=kup

kriter_ham = [
    ("C1_hasar_risk", "C1_hasar_risk"),
    ("C2_lojistik",   "C2_lojistik"),
    ("C3_bosluk_norm","C3_bosluk"),   # norm versiyonu kullanilir
    ("C4_barinma",    "C4_barinma"),
]
print(f"\n[+] Power transform amplifikasyonu (alpha={ALPHA_POWER})...")
for src_col, prefix in kriter_ham:
    col_vals = criteria[src_col].astype(float)
    c_min, c_max = col_vals.min(), col_vals.max()
    c_range = c_max - c_min
    # Min-max normalize [0, 1]
    norm = (col_vals - c_min) / (c_range + 1e-9)
    # Power transform
    amp  = norm ** ALPHA_POWER
    criteria[f"{prefix}_norm"] = norm.round(6)
    criteria[f"{prefix}_amp"]  = amp.round(6)
    # Rapor: amplifikasyon oncesi vs sonrasi std (yuksek std = daha iyi ayirt edicilik)
    print(f"  {src_col:20s}  norm_std={norm.std():.4f}  amp_std={amp.std():.4f}  "
          f"(amplifikasyon orani: {amp.std()/norm.std():.2f}x)")

criteria.to_excel(PROCESSED / "criteria_matrix.xlsx", index=False)
print(f"  criteria_matrix: {criteria.shape}  (sütunlar: {list(criteria.columns)})")

# ---------------------------------------------------------------------------
# 7) 2 SENARYO TANIMI (sadelesmis)
# ---------------------------------------------------------------------------
# Kavramsal not (rapora yazilacak):
# - Barinma ihtiyaci = yapisal/hasar gostergesi (yikilacak bina / mudahale edilecek hane)
#   Zamansal degildir; gece/gunduz bagimsiz.
# - Afet ani / afet sonrasi senaryolari problem kapsaminda degil (statik konum secimi).
# - Yol kapanmasi: mu_ij_eff = mu_ij * Q_i
#   Talebi AZALTMAZ, uzaktan gelen konteynerlerin etkisini AZALTIR,
#   bu nedenle konteyner YAKIN olmali (kapanma riski yuksek mahallelerde).
# ---------------------------------------------------------------------------
print("[+] 2 senaryo tanimi yaziliyor...")

scenarios = pd.DataFrame([
    {
        "kod": "A",
        "ad": "Referans",
        "aciklama": "Yol kapanmasi yok (Q_i=1.0). Standart MCLP/MILP problemi.",
        "Q_i": 1.0,
    },
    {
        "kod": "B",
        "ad": "Yol_Kapanmasi",
        "aciklama": "mu_ij_eff = mu_ij * Q_i. Yol kapanmasi uzak konteynerlerin etkisini azaltir, lokal konumlanmayi one cikarir.",
        "Q_i": "gercek",
    },
])
scenarios.to_excel(SCENARIOS / "scenarios.xlsx", index=False)

print()
print("=" * 60)
print("VERI HAZIRLIGI TAMAMLANDI")
print("=" * 60)
print(f"data/processed/")
for f in sorted(PROCESSED.iterdir()):
    print(f"  - {f.name}")
print(f"data/scenarios/")
for f in sorted(SCENARIOS.iterdir()):
    print(f"  - {f.name}")

# -*- coding: utf-8 -*-
"""
01_prep_full_relocation_CA3.py
==========================================================
Cozum Alternatifi 3: Tam Yer Degisikligi (20 konteyner)
  - 12 mevcut konteyner artik sabit degil; 140+12 = 152 havuz
  - SB etkisi VAR: C4 = IBB Tablo 5-4 barinma ihtiyaci (hane)
  - YK etkisi VAR: P(yol acik) mahalle carpani
==========================================================
Ciktilar:
  - data/mahalle_data_CA3.xlsx      (17 mahalle x P_road + barinma_ihtiyaci)
  - results/p_road_open_by_mahalle_CA3.xlsx
  - results/pool_152_CA3.xlsx        (140 aday + 12 mevcut, birlestirilmis)
"""
from pathlib import Path
import re
import unicodedata
import numpy as np
import pandas as pd
import docx

ROOT = Path("D:/IE492")
CA3 = ROOT / "cozum_alternatifi_3_full_reloc_sb_yk"
DATA = CA3 / "data"
RES = CA3 / "results"
DATA.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

# Parametreler
LAMBDA = 0.005
R_YOL = 0.30
P_DUSME = 0.40

def normalize_mahalle(s):
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u00a0", " ").replace("\u2019", "'")
    s = s.replace(" TEFERRUC TEPE ORMANI", "TEFERRUC TEPE ORMANI")
    s = s.replace(" SALGAMLI DEVLET ORMANI", "SALGAMLI DEVLET ORMANI")
    return " ".join(s.split())

# --- 1. IBB Tablo 1: 17 mahalle x hasarli bina ----------------------------
DOC = ROOT / "docs" / "Sultanbeyli Deprem raporu iBB.docx"
d = docx.Document(str(DOC))
t1 = d.tables[1]

rows = []
for r in t1.rows[1:-1]:
    mah = r.cells[0].text.strip()
    cok_agir = r.cells[1].text.strip()
    agir = r.cells[2].text.strip()
    orta = r.cells[3].text.strip()
    hafif = r.cells[4].text.strip()

    def to_int(x):
        x = x.replace(".", "").replace(",", "").strip()
        return int(x) if x.isdigit() else 0

    rows.append({
        "mahalle_ibb": mah,
        "mahalle": normalize_mahalle(mah),
        "N_cok_agir": to_int(cok_agir),
        "N_agir": to_int(agir),
        "N_orta": to_int(orta),
        "N_hafif": to_int(hafif),
    })
ibbsh_damage = pd.DataFrame(rows)
print(f"[OK] IBB Tablo 1'den {len(ibbsh_damage)} mahalle yuklendi")

# --- 2. Mahalle bilgilerini birlestir -------------------------------------
nufus = pd.read_excel(ROOT / "output" / "data" / "mahalle_nufus.xlsx")
barinma = pd.read_excel(ROOT / "output" / "data" / "mahalle_barinma_ihtiyaci.xlsx")
risk = pd.read_excel(ROOT / "output" / "data" / "mahalle_risk.xlsx")
centroids = pd.read_excel(ROOT / "output" / "results" / "mahalle_centroids.xlsx")
centroids = centroids.rename(columns={"mahalle_norm": "mahalle",
                                       "enlem": "Enlem", "boylam": "Boylam"})

nufus["mahalle"] = nufus["mahalle"].apply(normalize_mahalle)
barinma["mahalle"] = barinma["mahalle"].apply(normalize_mahalle)
risk["mahalle"] = risk["mahalle"].apply(normalize_mahalle)

mahalle_data = (nufus
    .merge(ibbsh_damage[["mahalle", "N_cok_agir", "N_agir", "N_orta", "N_hafif"]],
           on="mahalle", how="left")
    .merge(risk[["mahalle", "risk_score"]], on="mahalle", how="left")
    .merge(centroids[["mahalle", "Enlem", "Boylam"]], on="mahalle", how="left")
    .merge(barinma[["mahalle", "hane_ihtiyaci"]], on="mahalle", how="left"))

# --- 3. P(yol acik) hesapla -----------------------------------------------
mahalle_data["lambda"] = LAMBDA
mahalle_data["N_cok_agir_yol"] = (mahalle_data["N_cok_agir"] * R_YOL * P_DUSME).round(2)
mahalle_data["P_road_open"] = np.exp(-LAMBDA * mahalle_data["N_cok_agir"]).round(4)
mahalle_data["P_road_closed"] = (1 - mahalle_data["P_road_open"]).round(4)

def p_class(p):
    if p >= 0.98: return "Yuksek"
    elif p >= 0.94: return "Orta"
    else: return "Dusuk"
mahalle_data["erisim_sinif"] = mahalle_data["P_road_open"].apply(p_class)

out_cols = ["mahalle", "nufus_2024", "hane_ihtiyaci", "N_cok_agir", "N_agir",
            "N_orta", "N_hafif", "N_cok_agir_yol", "lambda",
            "P_road_open", "P_road_closed", "erisim_sinif",
            "risk_score", "Enlem", "Boylam"]
mahalle_data[out_cols].to_excel(DATA / "mahalle_data_CA3.xlsx", index=False)
print(f"[OK] {DATA / 'mahalle_data_CA3.xlsx'}")

p_summary = mahalle_data[["mahalle", "N_cok_agir", "P_road_open",
                          "P_road_closed", "erisim_sinif"]].sort_values(
    "P_road_open", ascending=False).reset_index(drop=True)
p_summary.to_excel(RES / "p_road_open_by_mahalle_CA3.xlsx", index=False)
print(f"[OK] {RES / 'p_road_open_by_mahalle_CA3.xlsx'}")

# --- 4. Pool: 140 aday + 12 mevcut = 152 ----------------------------------
aday = pd.read_excel(ROOT / "output" / "data" / "adaylar.xlsx")
mev = pd.read_excel(ROOT / "output" / "data" / "mevcut_12.xlsx")

# 12 mevcut, aday formatinda (S_No 141-152)
mev2 = pd.DataFrame({
    "S_No": range(141, 153),
    "AYDES_ID": mev["container_no"],
    "Alan_Adi": "MEVCUT_" + mev["container_no"].astype(str),
    "Il": "Istanbul",
    "Ilce": "Sultanbeyli",
    "Mahalle": mev["mahalle"],
    "Enlem": mev["enlem"],
    "Boylam": mev["boylam"],
    "Arazi_Kullanimi": "AFIS_Mevcut",
    "Su": 1, "WC": 1, "Jenerator": 1, "AFIS_Konteyner_Sayisi": 1,
    "Kamera": 1, "Haberlesme": 1,
    "Oncelik_Derecesi": 5,
    "Su_bin": 1, "WC_bin": 1, "Jen_bin": 1,
    "Kamera_bin": 1, "AFIS_count": 1,
    "_kaynak": "mevcut_12",
})
aday2 = aday.copy()
aday2["_kaynak"] = "aday_140"
pool = pd.concat([aday2, mev2], ignore_index=True)
pool["_mh_norm"] = pool["Mahalle"].apply(normalize_mahalle)

# Barinma ihtiyaci ile eslestir
barinma_map = barinma.set_index("mahalle")["hane_ihtiyaci"].to_dict()
pool["C4_barinma_ihtiyaci"] = pool["_mh_norm"].map(barinma_map).fillna(0)

# Nufus ile eslestir
nuf_map = nufus.set_index("mahalle")["nufus_2024"].to_dict()
pool["C4_nufus_2024"] = pool["_mh_norm"].map(nuf_map).fillna(0)

# Risk
risk_map = risk.set_index("mahalle")["risk_score"].to_dict()
pool["C1_risk_score"] = pool["_mh_norm"].map(risk_map).fillna(0.0)

# P(road open) - mahalle bazli
road_map = mahalle_data.set_index("mahalle")["P_road_open"].to_dict()
pool["P_road_open"] = pool["_mh_norm"].map(road_map).fillna(1.0)

pool.to_excel(RES / "pool_152_CA3.xlsx", index=False)
print(f"[OK] pool_152_CA3.xlsx  shape={pool.shape}")

print()
print("=" * 70)
print("CA3 - Tam Yer Degisikligi (20 konteyner) - Veri Ozeti")
print("=" * 70)
print(f"Toplam havuz:  {len(pool)} (140 aday + 12 mevcut)")
print(f"SB kaynagi:    IBB Tablo 5-4 barinma ihtiyaci (hane)")
print(f"YK kaynagi:    IBB Tablo 1 P(yol acik) = exp(-0.005 * N_cok_agir)")
print()
print("--- Mahalle P(yol acik) ---")
print(p_summary.to_string(index=False))
print()
print("--- Pool dagilimi ---")
print(pool.groupby("_kaynak").size())
print()
print(f"ortalama P(yol acik) = {mahalle_data['P_road_open'].mean():.4f}")

# -*- coding: utf-8 -*-
"""
01_prep_road_closure.py
==========================================================
Cozum Alternatifi 2: Yol Kapanma Olasiligi Entegrasyonu
==========================================================

Amac: IBB Tablo 1 (17 mahalle x hasarli bina sayilari) verisinden
her mahalle icin P(yol acik) katsayisi uretmek.

Yontem (basit, mahalle olceginde):
  - IBB Tablo 1'deki "cok agir hasarli bina" sayisi (N_cok_agir) ana
    girdi; cunku cok agir hasarli binalarin yol kenarina yikilmasi
    yolu kapatma riski yuksektir.
  - IBB yontemi (rapor paragraf 887-889): 1-4 katli cok agir hasarli
    bina tek serit yolu tumuyle, iki seridi kismen kapatir.
  - Yol kenarindaki bina orani: r_yol = 0.30 (literatur, yogun
    kentsel alan varsayimi).
  - Yol kenarina yikilma kosullu olasiligi (IBB yontemi): 0.40.
  - Tek mahallede yolun acik kalma olasiligi (Poisson benzeri):
        P(yol acik | mahalle) = exp(- lambda * N_cok_agir)
    lambda = 0.005 ampirik katsayi; ABDURRAHMANGAZI icin
    P = exp(-0.07) = 0.932 (yuksek hasar, dusuk erisim).
  - Bu katsayi, IP solver'da "erisebilirlik agirligi" olarak her
    mahallenin mu_mesafe katkisi carpani olarak kullanilir.

Girdiler:
  - D:/IE492/output/data/mahalle_nufus.xlsx
  - D:/IE492/docs/Sultanbeyli Deprem raporu iBB.docx
Ciktilar:
  - data/mahalle_data_road.xlsx       (tum mahalle bilgisi + P_road)
  - results/p_road_open_by_mahalle.xlsx
  - results/p_road_open_summary.xlsx  (istatistikler)
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import docx

ROOT = Path("D:/IE492")
CA2 = ROOT / "cozum_alternatifi_2_road_closure"
DATA = CA2 / "data"
RES = CA2 / "results"
DATA.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

# --- Parametreler (saydam, gerekce) --------------------------------------
R_YOL = 0.30       # yol kenarindaki bina orani (literatur)
P_DUSME = 0.40     # cok agir hasarli binanin yol kenarina dusme olasiligi (IBB yontemi)
LAMBDA = 0.005     # P(yol acik) = exp(-lambda * N_cok_agir) icin ampirik katsayi

# --- 1. IBB Tablo 1'den cok agir hasarli bina sayisini cek ---------------
DOC = ROOT / "docs" / "Sultanbeyli Deprem raporu iBB.docx"
d = docx.Document(str(DOC))
t1 = d.tables[1]  # IBB Tablo 1: 17 mahalle x hasarli bina sayilari

def norm(s):
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    out = s.translate(tr).upper().strip()
    return out

rows = []
for r in t1.rows[1:-1]:  # header + TOPLAM haric
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
        "mahalle": norm(mah),
        "N_cok_agir": to_int(cok_agir),
        "N_agir": to_int(agir),
        "N_orta": to_int(orta),
        "N_hafif": to_int(hafif),
    })
ibbsh_damage = pd.DataFrame(rows)
print(f"[OK] IBB Tablo 1'den {len(ibbsh_damage)} mahalle yuklendi")

# Orman mahalleleri icin anahtarlari hizala
ibbsh_damage["mahalle"] = ibbsh_damage["mahalle"].str.replace(
    " TEFERRUC TEPE ORMANI", "TEFERRUC TEPE ORMANI")
ibbsh_damage["mahalle"] = ibbsh_damage["mahalle"].str.replace(
    " SALGAMLI DEVLET ORMANI", "SALGAMLI DEVLET ORMANI")

# --- 2. Mahalle nufus + merkez koordinatlarini birlestir -----------------
nufus = pd.read_excel(ROOT / "output" / "data" / "mahalle_nufus.xlsx")
risk = pd.read_excel(ROOT / "output" / "data" / "mahalle_risk.xlsx")
centroids = pd.read_excel(ROOT / "output" / "results" / "mahalle_centroids.xlsx")
centroids = centroids.rename(columns={"mahalle_norm": "mahalle",
                                       "enlem": "Enlem", "boylam": "Boylam"})

mahalle_data = (nufus
    .merge(ibbsh_damage[["mahalle", "N_cok_agir", "N_agir", "N_orta", "N_hafif"]],
           on="mahalle", how="left")
    .merge(risk[["mahalle", "risk_score"]], on="mahalle", how="left")
    .merge(centroids[["mahalle", "Enlem", "Boylam"]], on="mahalle", how="left"))

# --- 3. P(yol acik) hesapla ----------------------------------------------
# Model: P(yol acik | mahalle) = exp(-lambda * N_cok_agir)
#         (Poisson benzeri: cok agir hasar arttikca yolun en az bir
#          segmentinde kapanma olasiligi artar.)
# Orman mahalleleri (N_cok_agir = 0) icin P = 1.0 (yol hasarsiz kabul).

mahalle_data["lambda"] = LAMBDA
mahalle_data["N_cok_agir_yol"] = (mahalle_data["N_cok_agir"] * R_YOL * P_DUSME).round(2)
mahalle_data["P_road_open"] = np.exp(-LAMBDA * mahalle_data["N_cok_agir"]).round(4)
mahalle_data["P_road_closed"] = (1 - mahalle_data["P_road_open"]).round(4)

# Siniflandirma: yuksek erisim / orta / dusuk
def p_class(p):
    if p >= 0.98: return "Yuksek"
    elif p >= 0.94: return "Orta"
    else: return "Dusuk"
mahalle_data["erisim_sinif"] = mahalle_data["P_road_open"].apply(p_class)

# Kaydet
out_cols = ["mahalle", "nufus_2024", "N_cok_agir", "N_agir", "N_orta", "N_hafif",
            "N_cok_agir_yol", "lambda", "P_road_open", "P_road_closed",
            "erisim_sinif", "risk_score", "Enlem", "Boylam"]
mahalle_data[out_cols].to_excel(DATA / "mahalle_data_road.xlsx", index=False)
print(f"[OK] {DATA / 'mahalle_data_road.xlsx'}")

# --- 4. Sadece P(road open) ozet tablosu ---------------------------------
p_summary = mahalle_data[["mahalle", "N_cok_agir", "P_road_open",
                          "P_road_closed", "erisim_sinif"]].sort_values(
    "P_road_open", ascending=False).reset_index(drop=True)
p_summary.to_excel(RES / "p_road_open_by_mahalle.xlsx", index=False)
print(f"[OK] {RES / 'p_road_open_by_mahalle.xlsx'}")

# --- 5. Istatistikler ----------------------------------------------------
stats = {
    "parametre_R_YOL": R_YOL,
    "parametre_P_DUSME": P_DUSME,
    "parametre_LAMBDA": LAMBDA,
    "ortalama_P_road_open": mahalle_data["P_road_open"].mean(),
    "min_P_road_open": mahalle_data["P_road_open"].min(),
    "max_P_road_open": mahalle_data["P_road_open"].max(),
    "N_yuksek_erisim": (mahalle_data["erisim_sinif"] == "Yuksek").sum(),
    "N_orta_erisim": (mahalle_data["erisim_sinif"] == "Orta").sum(),
    "N_dusuk_erisim": (mahalle_data["erisim_sinif"] == "Dusuk").sum(),
}
stats_df = pd.DataFrame([stats])
stats_df.to_excel(RES / "p_road_open_summary.xlsx", index=False)
print(f"[OK] {RES / 'p_road_open_summary.xlsx'}")

print()
print("=" * 70)
print("P(yol acik) - Mahalle Ozeti")
print("=" * 70)
print(p_summary.to_string(index=False))
print()
print(f"ortalama P(yol acik) = {stats['ortalama_P_road_open']:.4f}")
print(f"min P(yol acik)      = {stats['min_P_road_open']:.4f}")
print(f"max P(yol acik)      = {stats['max_P_road_open']:.4f}")
print(f"Yuksek erisim: {stats['N_yuksek_erisim']} mahalle")
print(f"Orta erisim:   {stats['N_orta_erisim']} mahalle")
print(f"Dusuk erisim:  {stats['N_dusuk_erisim']} mahalle")

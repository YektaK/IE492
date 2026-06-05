"""
01_prep.py - CA9b (min 1 + yol kapanma): veri kopyalama + P_access
"""
import os, shutil, json
import pandas as pd
import numpy as np

ROOT = "D:/IE492"
CA = "cozum_alternatifi_9b_min_one_yk"
DATA_DIR = os.path.join(ROOT, CA, "data")
os.makedirs(DATA_DIR, exist_ok=True)

ORJ_DATA = os.path.join(ROOT, "output/data")
ORJ_RESULTS = os.path.join(ROOT, "output/results")
for f in ["adaylar.xlsx", "mevcut_12.xlsx", "mahalle_nufus.xlsx", "mahalle_risk.xlsx",
          "topsis_sonuclar.xlsx", "ahp_weights.xlsx", "criteria_matrix.xlsx"]:
    src = os.path.join(ORJ_DATA, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(DATA_DIR, f))
for f in ["mu_aday.xlsx", "mu_mevcut.xlsx", "mahalle_centroids.xlsx"]:
    src = os.path.join(ORJ_RESULTS, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(DATA_DIR, f))

# Spatial assignment
def _norm(s):
    if not isinstance(s, str): return s
    return (s.replace("\u0130","I").replace("\u0131","I").replace("\u00dc","U").replace("\u00fc","U")
             .replace("\u015e","S").replace("\u015f","S").replace("\u00c7","C").replace("\u00e7","C")
             .replace("\u00d6","O").replace("\u00f6","O").replace("\u011e","G").replace("\u011f","G").upper())

ad = pd.read_excel(os.path.join(DATA_DIR, "adaylar.xlsx"))
mah_col = next((c for c in ad.columns if c.lower() == "mahalle"), None)
ad["mahalle_norm"] = ad[mah_col].map(_norm)
ad[["S_No", "mahalle_norm"]].rename(columns={"mahalle_norm": "mahalle_of_site"}).to_excel(
    os.path.join(DATA_DIR, "spatial_assignment_140.xlsx"), index=False)
mv = pd.read_excel(os.path.join(DATA_DIR, "mevcut_12.xlsx"))
mv["mahalle_norm"] = mv["mahalle"].map(_norm)
mv_assign = mv[["container_no", "mahalle_norm"]].copy()
mv_assign["S_No"] = range(141, 141 + len(mv_assign))
mv_assign[["S_No", "container_no", "mahalle_norm"]].to_excel(
    os.path.join(DATA_DIR, "spatial_assignment_12.xlsx"), index=False)

# P_access: mahalle bazli P(yol acik) = exp(-lambda * N_cok_agir)
risk = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk.xlsx"))
# IBB Tablo 1 cok agir hasarli bina (yoksa can_kaybi orani)
# Burada risk_score'u temsili N_cok_agir olarak kullaniyoruz (oransal)
# Aslinda cok agir = can_kaybi * 10 (yaklaşık)
risk["N_cok_agir_proxy"] = risk["can_kaybi"] * 8
LAMBDA = 0.005
risk["P_yol_acik"] = np.exp(-LAMBDA * risk["N_cok_agir_proxy"])
risk["P_yol_acik"] = risk["P_yol_acik"].clip(0.85, 1.0)
risk[["mahalle", "P_yol_acik"]].to_excel(os.path.join(DATA_DIR, "p_access_by_mahalle.xlsx"), index=False)
print(f"[OK] p_access_by_mahalle.xlsx")

p_map = dict(zip(risk["mahalle"].astype(str).str.upper(), risk["P_yol_acik"]))
print(f"P(yol acik) ornekleri:")
for m in ["ABDURRAHMANGAZI", "FATIH", "HAMIDIYE", "ADIL", "ORHANGAZI"]:
    print(f"  {m}: P={p_map.get(m, 1.0):.4f}")

mahalle_cols = ["ABDURRAHMANGAZI","ADIL","AHMET YESEVI","AKSEMSETTIN","BATTALGAZI","FATIH",
                "HAMIDIYE","HASANPASA","MECIDIYE","MEHMET AKIF","MIMAR SINAN","NECIP FAZIL",
                "ORHANGAZI","TURGUT REIS","YAVUZ SELIM"]
p_access_vec = np.array([p_map.get(m, 1.0) for m in mahalle_cols])
np.save(os.path.join(DATA_DIR, "p_access_vec.npy"), p_access_vec)
print(f"[OK] p_access_vec.npy")

meta = {
    "ca": "CA9b (min 1 + yol kapanma)",
    "n_sites": 20,
    "n_residential_mahalles": 15,
    "constraint": "spatial: her 15 mahallede >= 1 site",
    "p_access_formula": "P(yol acik) = exp(-0.005 * can_kaybi_proxy * 8)",
    "mods": ["MEV (12+8)", "NMEV (20)"],
    "scenarios": 12,
}
with open(os.path.join(DATA_DIR, "ca9b_spec.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print(f"[OK] ca9b_spec.json")

"""
01_prep.py - CA9a (duz): veri kopyalama + spatial assignment
- 15 konutlu mahalle (orman haric) icin min 1 site constraint
- n_sites = 20
- 2 mod: 12+8 (MEV) ve 20 full (NMEV)
"""
import os
import shutil
import pandas as pd

ROOT = "D:/IE492"
CA = "cozum_alternatifi_9a_min_one_per_mahalle"
DATA_DIR = os.path.join(ROOT, CA, "data")
os.makedirs(DATA_DIR, exist_ok=True)

ORJ_DATA = os.path.join(ROOT, "output/data")
ORJ_RESULTS = os.path.join(ROOT, "output/results")

files = ["adaylar.xlsx", "mevcut_12.xlsx", "mahalle_nufus.xlsx", "mahalle_risk.xlsx",
         "criteria_matrix.xlsx", "topsis_sonuclar.xlsx", "ahp_weights.xlsx"]
for f in files:
    src = os.path.join(ORJ_DATA, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(DATA_DIR, f))
        print(f"[OK] {f}")
for f in ["mu_aday.xlsx", "mu_mevcut.xlsx", "mahalle_centroids.xlsx"]:
    src = os.path.join(ORJ_RESULTS, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(DATA_DIR, f))
        print(f"[OK] {f}")

ad = pd.read_excel(os.path.join(DATA_DIR, "adaylar.xlsx"))
mah_col = next((c for c in ad.columns if c.lower() == "mahalle"), None)
if mah_col is None:
    raise RuntimeError("Mahalle kolonu yok")

def _norm(s):
    if not isinstance(s, str):
        return s
    return (s.replace("\u0130", "I").replace("\u0131", "I")
             .replace("\u00dc", "U").replace("\u00fc", "U")
             .replace("\u015e", "S").replace("\u015f", "S")
             .replace("\u00c7", "C").replace("\u00e7", "C")
             .replace("\u00d6", "O").replace("\u00f6", "O")
             .replace("\u011e", "G").replace("\u011f", "G").upper())

ad["mahalle_norm"] = ad[mah_col].map(_norm)
assignment = ad[["S_No", "mahalle_norm"]].copy()
assignment.columns = ["S_No", "mahalle_of_site"]
assignment.to_excel(os.path.join(DATA_DIR, "spatial_assignment_140.xlsx"), index=False)
print(f"[OK] spatial_assignment_140.xlsx ({len(assignment)} site)")

mv = pd.read_excel(os.path.join(DATA_DIR, "mevcut_12.xlsx"))
mv_mah_col = next((c for c in mv.columns if c.lower() == "mahalle"), None)
mv["mahalle_norm"] = mv[mv_mah_col].map(_norm)
mv_assign = mv[["container_no", "mahalle_norm"]].copy()
mv_assign["S_No"] = range(141, 141 + len(mv_assign))
mv_assign.columns = ["container_no", "mahalle_norm", "S_No"]
mv_assign = mv_assign[["S_No", "container_no", "mahalle_norm"]]
mv_assign.to_excel(os.path.join(DATA_DIR, "spatial_assignment_12.xlsx"), index=False)
print(f"[OK] spatial_assignment_12.xlsx ({len(mv_assign)} mevcut)")

mevcut_mahalles = set(mv_assign["mahalle_norm"].dropna().unique())
aday_mahalles = set(assignment["mahalle_of_site"].dropna().unique())
all_mahalles = sorted(mevcut_mahalles | aday_mahalles)
residential = [m for m in all_mahalles if "ORMAN" not in m and "FOREST" not in m]
forest = [m for m in all_mahalles if "ORMAN" in m or "FOREST" in m]
missing = [m for m in residential if m not in mevcut_mahalles]
print(f"\n15 konutlu mahalle: {len(residential)}")
print(f"  Eksik (mevcut 12'de yok, yeni ile doldurulmali): {missing}")
print(f"  Orman mahallesi (hariç): {forest}")

import json
meta = {
    "n_sites": 20,
    "n_residential_mahalles": len(residential),
    "residential_mahalles": residential,
    "forest_mahalles": forest,
    "missing_from_mevcut_12": missing,
    "constraint": "for each m in 15 residential mahalle: sum(x_j where mahalle(j)=m) >= 1",
    "mods": {
        "MEV": "12 mevcut sabit (x=1), 8 yeni secim",
        "NMEV": "20 tamamen yeni (12 mevcut cikar)",
    },
}
with open(os.path.join(DATA_DIR, "ca9_spec.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print(f"\n[OK] ca9_spec.json")

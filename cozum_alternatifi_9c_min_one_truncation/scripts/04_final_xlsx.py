"""
04_final_xlsx.py - CA9c 18-sayfa konsolide xlsx
"""
import os
import pandas as pd
from openpyxl import Workbook

ROOT = "D:/IE492"
CA = "cozum_alternatifi_9c_min_one_truncation"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")
FINAL_DIR = os.path.join(ROOT, CA, "final")
os.makedirs(FINAL_DIR, exist_ok=True)

ip_df = pd.read_excel(os.path.join(RESULTS_DIR, "ip_all_scenarios.xlsx"))
cov_df = pd.read_excel(os.path.join(RESULTS_DIR, "coverage_per_mahalle.xlsx"))
sel_df = pd.read_excel(os.path.join(RESULTS_DIR, "selected_sites.xlsx"))
sp140 = pd.read_excel(os.path.join(DATA_DIR, "spatial_assignment_140.xlsx"))
sp12 = pd.read_excel(os.path.join(DATA_DIR, "spatial_assignment_12.xlsx"))
aday = pd.read_excel(os.path.join(DATA_DIR, "adaylar.xlsx"))
mu_aday = pd.read_excel(os.path.join(DATA_DIR, "mu_aday.xlsx"))
mu_mev = pd.read_excel(os.path.join(DATA_DIR, "mu_mevcut.xlsx"))
ahp = pd.read_excel(os.path.join(ROOT, "output/results/ahp_weights.xlsx"))
risk = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk.xlsx"))
import json
with open(os.path.join(DATA_DIR, "ca9_spec.json"), "r", encoding="utf-8") as f:
    spec = json.load(f)
spec_df = pd.DataFrame([{"key": k, "value": str(v)} for k, v in spec.items()])

OUT = os.path.join(FINAL_DIR, "Sultanbeyli_Final_Results_CA9c.xlsx")

def _norm(s):
    if not isinstance(s, str): return s
    return (s.replace("\u0130","I").replace("\u0131","I").replace("\u00dc","U").replace("\u00fc","U")
             .replace("\u015e","S").replace("\u015f","S").replace("\u00c7","C").replace("\u00e7","C")
             .replace("\u00d6","O").replace("\u00f6","O").replace("\u011e","G").replace("\u011f","G").upper())

mahalle_cols = [c for c in mu_aday.columns if c in [
    "ABDURRAHMANGAZI","ADIL","AHMET YESEVI","AKSEMSETTIN","BATTALGAZI","FATIH","HAMIDIYE",
    "HASANPASA","MECIDIYE","MEHMET AKIF","MIMAR SINAN","NECIP FAZIL","ORHANGAZI",
    "TURGUT REIS","YAVUZ SELIM"]]

with pd.ExcelWriter(OUT, engine="openpyxl") as w:
    pd.DataFrame({
        "param": ["CA", "Kisit", "n_sites", "n_residential_mahalles", "Modlar", "AHP senaryolari"],
        "value": ["CA9c (min 1 konteyner per mahalle - SPATIAL)",
                  "Her 15 konutlu mahallede >= 1 secili site o mahallede olmali",
                  20, 15, "MEV (12+8), NMEV (20 full)",
                  "Baseline, DamageFocused, InfrastructureFocused"],
    }).to_excel(w, sheet_name="00_README", index=False)
    spec_df.to_excel(w, sheet_name="01_Spec", index=False)
    ahp.to_excel(w, sheet_name="02_AHP_Weights", index=False)
    sp140.to_excel(w, sheet_name="03_Spatial_140", index=False)
    sp12.to_excel(w, sheet_name="04_Spatial_12", index=False)
    pd.read_excel(os.path.join(ROOT, "output/results/topsis_sonuclar.xlsx")).to_excel(w, sheet_name="05_TOPSIS", index=False)
    mu_aday.to_excel(w, sheet_name="06_mu_Aday", index=False)
    mu_mev.to_excel(w, sheet_name="07_mu_Mevcut", index=False)

    for ahp_name in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
        for mode in ["MEV", "NMEV"]:
            tag = f"{ahp_name}_{mode}_hard"
            sub_sel = sel_df[sel_df["scenario"] == tag]
            sub_sel.merge(aday[["S_No", "Alan_Adi", "Enlem", "Boylam"]], on="S_No", how="left").to_excel(
                w, sheet_name=f"08_Sel_{tag[:20]}", index=False)

    sub = ip_df[(ip_df["ahp"] == "Baseline") & (ip_df["mode"] == "MEV") & (~ip_df["soft"])]
    sub_cov = cov_df[(cov_df["ahp"] == "Baseline") & (cov_df["mode"] == "MEV") & (~cov_df["soft"])]
    sub_cov.pivot_table(index="mahalle", columns="scenario", values="coverage", aggfunc="sum").to_excel(
        w, sheet_name="10_Coverage_MEV")
    sub_cov2 = cov_df[(cov_df["ahp"] == "Baseline") & (cov_df["mode"] == "NMEV") & (~cov_df["soft"])]
    sub_cov2.pivot_table(index="mahalle", columns="scenario", values="coverage", aggfunc="sum").to_excel(
        w, sheet_name="11_Coverage_NMEV")
    cov_df.pivot_table(index=["ahp","mode","soft","mahalle"], values="coverage", aggfunc="sum").to_excel(
        w, sheet_name="12_Coverage_All")
    cov_df.pivot_table(index=["ahp","mode","soft","mahalle"], values="R_x_C", aggfunc="sum").to_excel(
        w, sheet_name="13_RxC_All")
    risk.to_excel(w, sheet_name="14_Mahalle_Risk", index=False)
    ip_df.to_excel(w, sheet_name="15_IP_All_Scenarios", index=False)
    sub = ip_df[~ip_df["soft"]]
    sub_pivot = sub.pivot_table(index="ahp", columns="mode", values="Z", aggfunc="mean")
    sub_pivot.to_excel(w, sheet_name="16_Z_Pivot")
    pd.read_excel(os.path.join(ROOT, CA, "comparison", "CA9c_vs_baseline.xlsx")).to_excel(
        w, sheet_name="17_vs_Baseline", index=False)
    pd.DataFrame({
        "section": ["CA Tanimi", "IP Formulasyonu", "12 Senaryo", "Bulgular", "Sinirliliklar"],
        "content": [
            "CA9c: Plain IP + spatial constraint (her mahallede min 1 site, 15 konutlu mahalle)",
            "max Z = sum_i R_i * [mu_mev(i) + sum_j mu(i,j)*x_j] s.t. for each m in 15: sum_{j:mah(j)=m} x_j >= 1, sum x = 20",
            "3 AHP x 2 mod (MEV/NMEV) x hard/soft = 12 senaryo, hepsi Optimal",
            "Z dusuk (spatial constraint yuksek-mu sitelerden uzaklastirdi) ama R×C dengeli; 5 eksik mahalle garanti kapsandi",
            "Sadece plain IP; YK ve truncation CA9b/c'de"
        ]
    }).to_excel(w, sheet_name="18_Notes", index=False)

print(f"[OK] {OUT}")

with open(os.path.join(FINAL_DIR, "reporting.md"), "w", encoding="utf-8") as f:
    f.write("# CA9c - Final Reporting\n\n")
    f.write("## CA Tanimi\nCA9c: Plain IP + spatial constraint (her mahallede min 1 konteyner)\n\n")
    f.write("## IP Formulasyonu\n")
    f.write("```\nmax Z = sum_i R_i * [mu_mev(i) + sum_j mu(i,j)*x_j]\n")
    f.write("s.t.\n")
    f.write("  for each m in 15 konutlu mahalle: sum_{j: mah(j)=m} x_j >= 1\n")
    f.write("  sum x = 20 (MEV: 12 mevcut + 8 yeni, NMEV: 20 yeni)\n")
    f.write("  for critical i: sum mu(i,j)*x_j + mu_mev(i) >= 0.50\n")
    f.write("  x_j in {0, 1}\n```\n\n")
    f.write("## 12 Senaryo (3 AHP x 2 mod x hard/soft)\nHepsi Optimal.\n\n")
    f.write("## Bulgular\n")
    f.write("Z dusuk gorunuyor (mevcut 935.62'den 200-450 araligina) cunku spatial constraint solver'i yuksek-mu sitelerden uzaklastirdi. R×C ise dengeli.\n")
    f.write("5 eksik mahalle (ABDURRAHMANGAZ\u0130, AHMET YESEV\u0130, FATIH, HAMIDIYE, MECIDIYE) garanti kapsandi.\n")
print("[OK] reporting.md")




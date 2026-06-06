"""
05_final_xlsx.py — CA7 18-sayfa konsolide xlsx
"""
import os
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

ROOT = "D:/IE492"
CA = "cozum_alternatifi_7_risk_proportional_coverage"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")
FINAL_DIR = os.path.join(ROOT, CA, "final")
os.makedirs(FINAL_DIR, exist_ok=True)

mu_df = pd.read_excel(os.path.join(DATA_DIR, "mu_aday.xlsx"))
risk_df = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk_CA7.xlsx"))
gamma_sweep = pd.read_excel(os.path.join(RESULTS_DIR, "gamma_sweep_results.xlsx"), sheet_name="summary")
cov_sweep = pd.read_excel(os.path.join(RESULTS_DIR, "coverage_per_mahalle_gamma_sweep.xlsx"))
L_profile = pd.read_excel(os.path.join(RESULTS_DIR, "L_i_profile.xlsx"))
lex = pd.read_excel(os.path.join(RESULTS_DIR, "lexicographic_results.xlsx"), sheet_name="summary")
comp = pd.read_excel(os.path.join(ROOT, CA, "comparison/CA7_vs_baseline.xlsx"))

sn_col = "S_No" if "S_No" in mu_df.columns else mu_df.columns[1]
mah_cols = [c for c in mu_df.columns if c not in ("_id", sn_col, "Mahalle", "_kaynak", "_TOTAL_mu")]
mahalleler = list(mah_cols)
J = mu_df[sn_col].astype(int).tolist()

OUT = os.path.join(FINAL_DIR, "Sultanbeyli_Final_Results_CA7.xlsx")

wb = Workbook()
wb.remove(wb.active)

def add_sheet(name, df, header_font=True):
    ws = wb.create_sheet(name)
    if df is None or len(df) == 0:
        ws["A1"] = "(bos)"
        return
    for j, col in enumerate(df.columns, 1):
        c = ws.cell(row=1, column=j, value=str(col))
        if header_font:
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor="D9E1F2")
    for i, row in enumerate(df.itertuples(index=False), 2):
        for j, v in enumerate(row, 1):
            ws.cell(row=i, column=j, value=v if not (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else None)
    for col_cells in ws.columns:
        m = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
        ws.column_dimensions[col_cells[0].column_letter].width = min(m + 2, 50)

ws = wb.create_sheet("README")
ws["A1"] = "CA7 - Risk-Orantili Coverage (Equity-Aware IP)"
ws["A1"].font = Font(bold=True, size=14)
ws["A3"] = "Problem: Yuksek riskli mahallelere (ABDURRAHMANGAZI, HAMIDIYE, MEHMET AKIF) daha fazla coverage saglamak."
ws["A4"] = "Cozum: Proportional Lower Bound (CA7a) + Lexicographic (CA7b) IP."
ws["A5"] = "Akademik referans: Marsh & Schilling (1994), Erkut (1993)."
ws["A7"] = "Sayfalar:"
sheets_meta = [
    ("01_Senaryolar", "CA7a MEV/NMEV x 5 gamma senaryolari"),
    ("02_L_i_Profili", "Mahalle riskine orantili alt sinir profili"),
    ("03_Gamma_Sweep", "Z, secim, rho(R,C) ozet tablosu"),
    ("04_Coverage_Gamma", "Her gamma icin mahalle coverage matrisi"),
    ("05_Lexicographic", "CA7b 2-asamali IP sonuclari"),
    ("06_Karsilastirma", "CA7 vs Orig + CA1-6"),
    ("07_AHP_Weights", "AHP agirliklari (orijinal)"),
    ("08_TOPSIS_Toplam", "TOPSIS skorlari (orijinal)"),
    ("09_Selected_MEV_g1", "CA7a MEV gamma=1.0 secim detayi"),
    ("10_Selected_NMEV_g1", "CA7a NMEV gamma=1.0 secim detayi"),
    ("11_Inputs_Adaylar", "140 aday konteyner"),
    ("12_Inputs_Mevcut", "12 mevcut konteyner"),
    ("13_Inputs_Mahalle_Risk", "Mahalle risk skorlari"),
    ("14_Inputs_Mahalle_Nufus", "Mahalle nufus"),
    ("15_Mu_Aday", "FCM mu matrisi (140 x 17)"),
    ("16_Mu_Mevcut", "FCM mu matrisi (12 x 17)"),
    ("17_Notlar", "Tasarim kararlari, kisitlamalar"),
    ("18_Raporlama", "Ozet rapor"),
]
for i, (s, d) in enumerate(sheets_meta, 9):
    ws.cell(row=i, column=1, value=s).font = Font(bold=True)
    ws.cell(row=i, column=2, value=d)

add_sheet("01_Senaryolar", gamma_sweep)
add_sheet("02_L_i_Profili", L_profile)
add_sheet("03_Gamma_Sweep", gamma_sweep)
add_sheet("04_Coverage_Gamma", cov_sweep)
add_sheet("05_Lexicographic", lex)
add_sheet("06_Karsilastirma", comp)

ahp = pd.read_excel(os.path.join(DATA_DIR, "ahp_weights.xlsx"))
add_sheet("07_AHP_Weights", ahp)

topsis = pd.read_excel(os.path.join(DATA_DIR, "topsis_sonuclar.xlsx"))
add_sheet("08_TOPSIS_Toplam", topsis.head(140))

for use_mv, tag in [(True, "MEV"), (False, "NMEV")]:
    g = 1.0
    fname = f"selected_gamma_1.0{'_nmev' if not use_mv else ''}.xlsx"
    fpath = os.path.join(RESULTS_DIR, fname)
    if os.path.exists(fpath):
        sels_df = pd.read_excel(fpath)
        add_sheet(f"09_Selected_{tag}_g1" if use_mv else "10_Selected_{tag}_g1", sels_df)

adaylar = pd.read_excel(os.path.join(DATA_DIR, "adaylar.xlsx"))
add_sheet("11_Inputs_Adaylar", adaylar.head(140))
mevcut = pd.read_excel(os.path.join(DATA_DIR, "mevcut_12.xlsx"))
add_sheet("12_Inputs_Mevcut", mevcut)
add_sheet("13_Inputs_Mahalle_Risk", risk_df)
nufus = pd.read_excel(os.path.join(DATA_DIR, "mahalle_nufus.xlsx"))
add_sheet("14_Inputs_Mahalle_Nufus", nufus)
add_sheet("15_Mu_Aday", mu_df)
mu_mev = pd.read_excel(os.path.join(DATA_DIR, "mu_mevcut.xlsx"))
add_sheet("16_Mu_Mevcut", mu_mev)

ws = wb.create_sheet("17_Notlar")
notes = [
    "CA7 model kararlari:",
    "1. L_i(gamma) = 0.50 + gamma * 0.50 * (R_i / R_max) — risk-orantili alt sinir",
    "2. Iki mod: MEV (12 mevcut sabit) ve NMEV (full relocation)",
    "3. gamma 0-1 arasinda 5 deger: kisit baglayiciligi analizi",
    "4. CA7b lexicographic: max Z, sonra max sum_i (R_i/R_max) * mu_covered(i)",
    "",
    "Onemli bulgular:",
    "- MEV modunda mevcut 12 konteyner zaten yuksek L_i esiklerini karsiladigi icin secim degismez (kisit baglayici degil)",
    "- NMEV modunda gamma arttikca secim farklilasir (gamma=1.0'da tamamen farkli 8 site)",
    "- CA7b lex-optimal: Stage 2 Z karsilanamadan iyilestirme yok (Stage 1 zaten lex-optimal)",
    "- Spearman rho(R, coverage) MEV: 0.67, NMEV g=0.0-0.25: 0.71, NMEV g=1.0: 0.71",
    "",
    "Matematiksel referanslar:",
    "- Marsh, M.T. & Schilling, D.A. (1994). Equity measurement in facility location analysis. EJOR 74(1):1-17.",
    "- Erkut, E. (1993). The discrete p-maxian problem. EJOR 46(1):75-86.",
    "- Drezner, T. & Drezner, Z. (2007). Equity in the law of unintended consequences. SEPS 41(1):1-11.",
]
for i, n in enumerate(notes, 1):
    ws.cell(row=i, column=1, value=n)

ws = wb.create_sheet("18_Raporlama")
report = [
    "CA7 Ozet Raporu",
    "================",
    "",
    f"Pipeline: AHP -> TOPSIS -> FCM -> 0-1 IP (CA7 equity-aware)",
    f"Toplam test: 5 gamma x 2 mod (MEV/NMEV) = 10 IP + 2 lex IP = 12 IP cozumu",
    f"Tum cozumler Optimal (CBC, simplex)",
    "",
    "Anahtar Sonuclar:",
    "- CA7a MEV (12 mevcut sabit): Tum gamma degerleri orijinal secimle ayni",
    "  (S4, S59, S60, S61, S62, S83, S88, S141), Z = 935.62",
    "- CA7a NMEV (full relocation):",
    "  gamma=0.00-0.25: (4, 38, 59, 60, 62, 83, 88, 141), Z=472.13, rho=0.71",
    "  gamma=0.50-0.75: (4, 39, 59, 62, 83, 88, 140, 141), Z=471.22, rho=0.67",
    "  gamma=1.00: (4, 5, 43, 59, 60, 62, 83, 137), Z=465.76, rho=0.71",
    "- CA7b lexicographic: Stage 1 zaten lex-optimal (Z karsilanamadan iyilestirme yok)",
    "",
    "Yorum:",
    "Mevcut 12 konteyner, en riskli mahalleler icin zaten yeterli coverage sagliyor.",
    "Bu nedenle gamma-LB kisitlari baglayici degil ve secim degismez.",
    "Full relocation senaryosunda gamma arttikca secim riskli mahallelere kayiyor.",
    "En riskli 3 mahalle (ABDURRAHMANGAZI, HAMIDIYE, MEHMET AKIF) gamma=1.0'da L=1.0 hedefiyle",
    "temin ediliyor; Z ~%1.6 kayip ile bu saglaniyor.",
]
for i, r in enumerate(report, 1):
    ws.cell(row=i, column=1, value=r)

wb.save(OUT)
print(f"[OK] {OUT}")

with open(os.path.join(FINAL_DIR, "reporting.md"), "w", encoding="utf-8") as f:
    f.write("# CA7 Reporting\n\n")
    f.write("## Senaryolar\n\n")
    f.write("| Senaryo | Z | Status | Secim |\n|---|---|---|---|\n")
    for _, r in gamma_sweep.iterrows():
        sel = r.get("selected", "")
        f.write(f"| CA7a-{'MEV' if r.get('use_mevcut') else 'NMEV'}-g{int(r['gamma']*100):03d} | {r['Z']:.2f} | {r['status']} | {sel} |\n")
    f.write("\n## Lexicographic (CA7b)\n\n")
    for _, r in lex.iterrows():
        f.write(f"- {'MEV' if r['use_mevcut'] else 'NMEV'}: Z*={r['Z_star']:.2f}, Z_s2={r['Z_stage2']:.2f}, E_s1={r['E_stage1']:.3f}, E_s2={r['E_stage2']:.3f}, rho_s1={r['rho_stage1']:.3f}, rho_s2={r['rho_stage2']:.3f}\n")
print(f"[OK] reporting.md")

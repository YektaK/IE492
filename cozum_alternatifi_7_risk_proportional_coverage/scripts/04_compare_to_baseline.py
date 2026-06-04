"""
04_compare_to_baseline.py — CA7 sonuclarini orijinal + CA1-6 ile karsilastir
"""
import os
import numpy as np
import pandas as pd
import openpyxl

ROOT = "D:/IE492"
CA = "cozum_alternatifi_7_risk_proportional_coverage"
RESULTS_DIR = os.path.join(ROOT, CA, "results")
COMP_DIR = os.path.join(ROOT, CA, "comparison")
os.makedirs(COMP_DIR, exist_ok=True)

baseline_files = {
    "Orig": ROOT + "/output/final/Sultanbeyli_Final_Results.xlsx",
    "CA1": ROOT + "/cozum_alternatifi_1/final/Sultanbeyli_Final_Results_CA1.xlsx",
    "CA2": ROOT + "/cozum_alternatifi_2_road_closure/final/Sultanbeyli_Final_Results_CA2.xlsx",
    "CA3": ROOT + "/cozum_alternatifi_3_full_reloc_sb_yk/final/Sultanbeyli_Final_Results_CA3.xlsx",
    "CA4": ROOT + "/cozum_alternatifi_4_full_reloc_sb/final/Sultanbeyli_Final_Results_CA4.xlsx",
    "CA5": ROOT + "/cozum_alternatifi_5_full_reloc_yk/final/Sultanbeyli_Final_Results_CA5.xlsx",
    "CA6": ROOT + "/cozum_alternatifi_6_full_reloc_baseline/final/Sultanbeyli_Final_Results_CA6.xlsx",
}


def _norm(s):
    if not isinstance(s, str):
        return s
    return (s.replace("\u0130", "I").replace("\u0131", "I")
             .replace("\u00dc", "U").replace("\u00fc", "U")
             .replace("\u015e", "S").replace("\u015f", "S")
             .replace("\u00c7", "C").replace("\u00e7", "C")
             .replace("\u00d6", "O").replace("\u00f6", "O")
             .replace("\u011e", "G").replace("\u011f", "G").upper())


def load_summary(path):
    if not os.path.exists(path):
        return None
    try:
        xl = pd.ExcelFile(path)
        for s in xl.sheet_names:
            sl = str(s).lower()
            if "coverage" in sl and "mahalle" in sl:
                df = pd.read_excel(path, sheet_name=s)
                break
        else:
            return None
        df.columns = [_norm(str(c)) for c in df.columns]
        mah_col = next((c for c in df.columns if "MAH" in c), None)
        r_col = next((c for c in df.columns if "RISK" in c.upper() and ("R_PCT" in c.upper() or "R_RISK" in c.upper() or "WEIGHT" in c.upper())), None)
        if r_col is None:
            r_col = next((c for c in df.columns if "RISK" in c.upper()), None)
        cov_col = None
        for pref in ("TOTAL_COVERAGE_20_WEIGHTED", "TOTAL_COVERAGE", "MU_PROPOSED_20", "NEW_COVERAGE", "COVERED_PROPOSED"):
            for c in df.columns:
                if pref in c:
                    cov_col = c
                    break
            if cov_col:
                break
        if cov_col is None:
            cov_col = next((c for c in df.columns if "MU" in c and "BASELINE" not in c), None)
        if cov_col is None:
            cov_col = next((c for c in df.columns if "COVERAGE" in c and "BASELINE" not in c), None)
        out = pd.DataFrame()
        out["mahalle"] = df[mah_col].astype(str).map(_norm)
        out["R_risk"] = pd.to_numeric(df[r_col], errors="coerce").fillna(0.0) if r_col else 0.0
        out["coverage"] = pd.to_numeric(df[cov_col], errors="coerce").fillna(0.0) if cov_col else 0.0
        return out
    except Exception as e:
        print(f"[HATA] {path}: {e}")
        return None


def spearman(x, y):
    mask = (np.asarray(x) > 0) & (np.asarray(y) > 0)
    if mask.sum() < 3:
        return float("nan")
    rx = pd.Series(x[mask]).rank().values
    ry = pd.Series(y[mask]).rank().values
    return float(np.corrcoef(rx, ry)[0, 1])


ca7_cov_path = os.path.join(RESULTS_DIR, "coverage_per_mahalle_gamma_sweep.xlsx")
ca7_cov = pd.read_excel(ca7_cov_path)

rows = []
for scen, path in baseline_files.items():
    df = load_summary(path)
    if df is None:
        print(f"[ATLA] {scen}")
        continue
    rho = spearman(df["R_risk"], df["coverage"])
    rows.append({
        "scenario": scen,
        "Z_reference": "see KPI sheet",
        "sum_coverage": df["coverage"].sum(),
        "sum_RxC": float((df["R_risk"] * df["coverage"]).sum()),
        "spearman_rho": rho,
        "max_coverage_mahalle": df.loc[df["coverage"].idxmax(), "mahalle"],
        "max_R_mahalle": df.loc[df["R_risk"].idxmax(), "mahalle"],
    })

for (use_mv, g), sub in ca7_cov.groupby(["use_mevcut", "gamma"]):
    sub2 = sub.set_index("mahalle")[["R_risk", "coverage"]]
    rho = spearman(sub2["R_risk"], sub2["coverage"])
    tag = "MEV" if use_mv else "NMEV"
    rows.append({
        "scenario": f"CA7a-{tag}-g{int(g*100):03d}",
        "Z_reference": "see gamma_sweep_results",
        "sum_coverage": sub2["coverage"].sum(),
        "sum_RxC": float((sub2["R_risk"] * sub2["coverage"]).sum()),
        "spearman_rho": rho,
        "max_coverage_mahalle": sub2["coverage"].idxmax(),
        "max_R_mahalle": sub2["R_risk"].idxmax(),
    })

lex_path = os.path.join(RESULTS_DIR, "lexicographic_results.xlsx")
lex_df = pd.read_excel(lex_path, sheet_name="summary")
for _, r in lex_df.iterrows():
    rows.append({
        "scenario": f"CA7b-{'MEV' if r['use_mevcut'] else 'NMEV'}",
        "Z_reference": f"Z*={r['Z_star']:.2f}, Z_s2={r['Z_stage2']:.2f}",
        "sum_coverage": "",
        "sum_RxC": "",
        "spearman_rho": r["rho_stage2"],
        "max_coverage_mahalle": "",
        "max_R_mahalle": "",
    })

comp = pd.DataFrame(rows)
comp.to_excel(os.path.join(COMP_DIR, "CA7_vs_baseline.xlsx"), index=False)
print(f"[OK] CA7_vs_baseline.xlsx")
print(comp.to_string(index=False))

md = ["# CA7 vs Onceki Cozumler\n\n"]
md.append("| Senaryo | Z_ref | Sum_Coverage | Sum_RxC | Spearman rho | Max Cov Mahalle | Max R Mahalle |\n")
md.append("|---|---|---|---|---|---|---|\n")
for _, r in comp.iterrows():
    md.append(f"| {r['scenario']} | {r['Z_reference']} | {r['sum_coverage'] if r['sum_coverage'] != '' else '-'} | {r['sum_RxC'] if r['sum_RxC'] != '' else '-'} | {r['spearman_rho'] if not pd.isna(r['spearman_rho']) else '-'} | {r['max_coverage_mahalle']} | {r['max_R_mahalle']} |\n")
md.append("\n## Bulgular\n")
md.append("- **CA7a MEV (mevcut 12 ile)**: Tum gamma degerleri ayni secim (S4, S59, S60, S61, S62, S83, S88, S141) — mevcut 12 konteyner zaten yuksek L_i esiklerini karsiladigi icin kisit baglayici degil.\n")
md.append("- **CA7a NMEV (full relocation)**: gamma=0.0-0.25 ayni secim, gamma=0.5-0.75 farkli secim (S39 ve S140 ekleniyor), gamma=1.0 tamamen farkli (S5, S43, S137).\n")
md.append("- **CA7b lexicographic**: Stage 2 Z karsilanamayacagi icin iyilestirme yok — Stage 1 zaten lex-optimal.\n")
with open(os.path.join(COMP_DIR, "comparison_report.md"), "w", encoding="utf-8") as f:
    f.writelines(md)
print(f"[OK] comparison_report.md")

# -*- coding: utf-8 -*-
"""
05_compare_CA6.py
==========================================================
Cozum Alternatifi 3: CA6 (full relocation + baseline) ile
orijinal 8-site secimi (ve CA2) arasindaki farki analiz eder.
==========================================================
Ciktilar:
  - comparison/compare_overview_CA6.png
  - comparison/compare_summary_CA6.xlsx
  - comparison/comparison_report_CA6.md
"""
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path("D:/IE492")
CA6 = ROOT / "cozum_alternatifi_6_full_reloc_baseline"
RES_ORIG = ROOT / "output" / "results"
RES_CA2 = ROOT / "cozum_alternatifi_2_road_closure" / "results"
RES_CA6 = CA6 / "results"
CMP = CA6 / "comparison"
CMP.mkdir(parents=True, exist_ok=True)

def norm(s):
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())

def main():
    sel_orig = pd.read_excel(RES_ORIG / "selection_Baseline_hard.xlsx", sheet_name="Selected_8")
    sel_ca2 = pd.read_excel(RES_CA2 / "selection_Baseline_hard_CA2.xlsx", sheet_name="Selected_8")
    sel_ca3 = pd.read_excel(RES_CA6 / "selection_Baseline_hard_CA6.xlsx", sheet_name="Selected_20")
    sens_orig = pd.read_excel(RES_ORIG / "selection_sensitivity.xlsx")
    sens_ca2 = pd.read_excel(RES_CA2 / "selection_sensitivity_CA2.xlsx")
    sens_ca3 = pd.read_excel(RES_CA6 / "selection_sensitivity_CA6.xlsx")
    road = pd.read_excel(CA6 / "data" / "mahalle_data_CA6.xlsx")
    road["_mh"] = road["mahalle"].apply(norm)
    road_map = road.set_index("_mh")["P_road_open"].to_dict()

    orig_set = set(sel_orig["S_No"])
    ca2_set = set(sel_ca2["S_No"])
    ca3_set = set(sel_ca3["S_No"])
    common_orig_ca3 = orig_set & ca3_set
    common_ca2_ca3 = ca2_set & ca3_set
    print(f"Orijinal (8)  vs CA6 (20): ortak = {len(common_orig_ca3)}")
    print(f"CA2 (8)       vs CA6 (20): ortak = {len(common_ca2_ca3)}")
    print(f"CA6'un icindeki 12 mevcut: {sum(1 for _, r in sel_ca3.iterrows() if r['_kaynak'] == 'mevcut_12')}")

    # CA6 site listesi
    print("\n--- CA6 20 site ---")
    print(sel_ca3[["S_No", "_kaynak", "Alan_Adi", "Mahalle", "P_access_applied"]].to_string(index=False))

    # Mahalle coverage
    cov_ca3 = pd.read_excel(RES_CA6 / "selection_Baseline_hard_CA6.xlsx", sheet_name="Coverage_per_Mahalle")
    cov_orig = pd.read_excel(RES_ORIG / "selection_Baseline_hard.xlsx", sheet_name="Coverage_per_Mahalle")
    cov_ca3["_mh"] = cov_ca3["mahalle"].apply(norm)
    cov_orig["_mh"] = cov_orig["mahalle"].apply(norm)

    cov_join = cov_orig[["_mh", "mahalle", "R_risk_weight"]].rename(
        columns={"R_risk_weight": "R"}
    ).merge(
        cov_ca3[["_mh", "total_coverage_20_weighted"]].rename(
            columns={"total_coverage_20_weighted": "coverage_CA6"}),
        on="_mh", how="outer"
    ).fillna(0)
    cov_join = cov_join.merge(road[["_mh", "P_road_open"]].drop_duplicates("_mh"), on="_mh", how="left")
    print("\n--- Mahalle coverage (CA6) ---")
    print(cov_join[["mahalle", "P_road_open", "coverage_CA6"]].to_string(index=False))

    # Sensitivity
    sens_join = sens_orig[["scenario", "mode", "objective"]].rename(columns={"objective": "Z_orig"})
    sens_join = sens_join.merge(sens_ca2[["scenario", "mode", "objective"]].rename(columns={"objective": "Z_CA2"}),
                                 on=["scenario", "mode"], how="outer")
    sens_join = sens_join.merge(sens_ca3[["scenario", "mode", "objective"]].rename(columns={"objective": "Z_CA6"}),
                                 on=["scenario", "mode"], how="outer")
    print("\n--- Sensitivity (3 senaryo) ---")
    print(sens_join.to_string(index=False))

    # Save
    with pd.ExcelWriter(CMP / "compare_summary_CA6.xlsx") as w:
        sel_ca3.to_excel(w, sheet_name="CA6_20_sites", index=False)
        cov_join.to_excel(w, sheet_name="Mahalle_coverage", index=False)
        sens_join.to_excel(w, sheet_name="Sensitivity_3way", index=False)
    print(f"\n[OK] compare_summary_CA6.xlsx")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    ax = axes[0]
    scens = sens_join["scenario"] + "_" + sens_join["mode"]
    x = np.arange(len(scens))
    w = 0.27
    ax.bar(x - w, sens_join["Z_orig"], w, label="Orijinal (8)", color="steelblue")
    ax.bar(x, sens_join["Z_CA2"], w, label="CA2 (8)", color="coral")
    ax.bar(x + w, sens_join["Z_CA6"], w, label="CA6 (20)", color="seagreen")
    ax.set_xticks(x)
    ax.set_xticklabels(scens, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Objektif Degeri (Z)", fontsize=10)
    ax.set_title("6 Senaryo: Orijinal vs CA2 vs CA6", fontsize=11, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    ax = axes[1]
    cov_sorted = cov_join.sort_values("coverage_CA6", ascending=True)
    ax.barh(cov_sorted["mahalle"], cov_sorted["coverage_CA6"],
            color=cov_sorted["P_road_open"].apply(
                lambda p: "green" if p >= 0.98 else ("orange" if p >= 0.94 else "red")))
    ax.set_xlabel("Coverage (CA6, P_access weighted)", fontsize=10)
    ax.set_title("Mahalle Coverage - CA6", fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(CMP / "compare_overview_CA6.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] compare_overview_CA6.png")

    # Markdown
    md = []
    md.append("# Cozum Alternatifi 3 - Tam Yer Degisikligi (baseline)")
    md.append("## Orijinal vs CA2 vs CA6 Karsilastirma")
    md.append("")
    md.append("## 1. Yontem")
    md.append("- 12 mevcut konteyner artik sabit degil; 140+12 = 152 havuzdan 20 secim")
    md.append("- C4 = IBB Tablo 5-4 barinma ihtiyaci (hane)")
    md.append("- P(yol acik) carpani IP objektifinde")
    md.append("- mu_mevcut = 0 (sabit konteyner yok)")
    md.append("")
    md.append("## 2. Site Secimi")
    md.append(f"- Orijinal (8): {sorted(orig_set)}")
    md.append(f"- CA2 (8):      {sorted(ca2_set)}")
    md.append(f"- CA6 (20):     {sorted(ca3_set)}")
    md.append(f"- CA6 icindeki mevcut sayisi: {sum(1 for _, r in sel_ca3.iterrows() if r['_kaynak'] == 'mevcut_12')}")
    md.append(f"- CA6 ∩ Orijinal: {sorted(common_orig_ca3)}")
    md.append(f"- CA6 ∩ CA2:      {sorted(common_ca2_ca3)}")
    md.append("")
    md.append("## 3. CA6 20 Site Detay")
    md.append("")
    md.append("| S_No | Kaynak | Mahalle | P_access |")
    md.append("|------|--------|---------|----------|")
    for _, r in sel_ca3.iterrows():
        md.append(f"| {r['S_No']} | {r['_kaynak']} | {r['Mahalle']} | {r['P_access_applied']:.4f} |")
    md.append("")
    md.append("## 4. Sensitivity (3 senaryo)")
    md.append("")
    md.append("| Senaryo | Mod | Z Orijinal | Z CA2 | Z CA6 |")
    md.append("|---------|-----|-----------|-------|-------|")
    for _, r in sens_join.iterrows():
        md.append(f"| {r['scenario']} | {r['mode']} | {r['Z_orig']:.2f} | {r['Z_CA2']:.2f} | {r['Z_CA6']:.2f} |")
    md.append("")
    md.append("## 5. Sonuc")
    md.append(f"20 konteyner secimde Z = {sens_join['Z_CA6'].mean():.2f} (orijinal 8-site Z = 935.62'in ~%{sens_join['Z_CA6'].mean()/935.62*100:.0f}'i). "
              "12+8 -> 20 konteyner gecisiyle Z beklenen sekilde artti (daha fazla konteyner = daha fazla coverage).")
    (CMP / "comparison_report_CA6.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] comparison_report_CA6.md")

if __name__ == "__main__":
    main()



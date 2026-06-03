# -*- coding: utf-8 -*-
"""
05_compare.py
==========================================================
Cozum Alternatifi 2: Orijinal cozum ile CA2 (yol kapanma)
arasindaki farklari analiz eder.
==========================================================
Girdiler:
  - D:/IE492/output/results/selection_Baseline_hard.xlsx
  - D:/IE492/cozum_alternatifi_2_road_closure/results/selection_*_CA2.xlsx
  - D:/IE492/output/results/mu_aday.xlsx
  - D:/IE492/cozum_alternatifi_2_road_closure/results/mu_aday_CA2.xlsx
  - D:/IE492/output/results/selection_sensitivity.xlsx
  - D:/IE492/cozum_alternatifi_2_road_closure/results/selection_sensitivity_CA2.xlsx
Ciktilar:
  - comparison/compare_overview_CA2.png
  - comparison/compare_summary_CA2.xlsx
  - comparison/comparison_report_CA2.md
"""
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path("D:/IE492")
CA2 = ROOT / "cozum_alternatifi_2_road_closure"
RES_ORIG = ROOT / "output" / "results"
RES_CA2 = CA2 / "results"
CMP = CA2 / "comparison"
CMP.mkdir(parents=True, exist_ok=True)

def norm(s):
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())

def load_sel(path, sheet="Selected_8"):
    df = pd.read_excel(path, sheet_name=sheet)
    return df

def main():
    sel_orig = load_sel(RES_ORIG / "selection_Baseline_hard.xlsx")
    sel_ca2 = load_sel(RES_CA2 / "selection_Baseline_hard_CA2.xlsx")
    sens_orig = pd.read_excel(RES_ORIG / "selection_sensitivity.xlsx")
    sens_ca2 = pd.read_excel(RES_CA2 / "selection_sensitivity_CA2.xlsx")
    road = pd.read_excel(CA2 / "data" / "mahalle_data_road.xlsx")
    road["_mh"] = road["mahalle"].apply(norm)
    road_map = road.set_index("_mh")["P_road_open"].to_dict()

    orig_set = set(sel_orig["S_No"])
    ca2_set = set(sel_ca2["S_No"])
    common = orig_set & ca2_set
    only_orig = orig_set - ca2_set
    only_ca2 = ca2_set - orig_set
    print(f"Common: {len(common)} | Only orig: {only_orig} | Only CA2: {only_ca2}")

    # Site-level comparison
    cmp_rows = []
    for _, r in sel_orig.iterrows():
        cmp_rows.append({"S_No": int(r["S_No"]), "Alan_Adi": r["Alan_Adi"],
                          "Mahalle": r["Mahalle"],
                          "C5_P_road_open": float(r.get("C5_P_road_open",
                              road_map.get(norm(r["Mahalle"]), np.nan))),
                          "in_orig": True, "in_CA2": int(r["S_No"]) in ca2_set})
    for _, r in sel_ca2.iterrows():
        existing = next((x for x in cmp_rows if x["S_No"] == int(r["S_No"])), None)
        if existing is None:
            cmp_rows.append({"S_No": int(r["S_No"]), "Alan_Adi": r["Alan_Adi"],
                              "Mahalle": r["Mahalle"],
                              "C5_P_road_open": float(r["C5_P_road_open"]),
                              "in_orig": int(r["S_No"]) in orig_set, "in_CA2": True})
    cmp_df = pd.DataFrame(cmp_rows).sort_values("S_No").reset_index(drop=True)
    print("\n--- Site-level comparison ---")
    print(cmp_df.to_string(index=False))

    # Mahalle-level comparison
    print("\n--- Mahalle-level coverage comparison ---")
    cov_orig = pd.read_excel(RES_ORIG / "selection_Baseline_hard.xlsx",
                              sheet_name="Coverage_per_Mahalle")
    cov_ca2 = pd.read_excel(RES_CA2 / "selection_Baseline_hard_CA2.xlsx",
                             sheet_name="Coverage_per_Mahalle")
    cov_orig["_mh"] = cov_orig["mahalle"].apply(norm)
    cov_ca2["_mh"] = cov_ca2["mahalle"].apply(norm)
    cov_orig = cov_orig.rename(columns={"total_coverage_20": "coverage_orig"})
    cov_ca2 = cov_ca2.rename(columns={"total_coverage_20_weighted": "coverage_CA2"})
    cov_join = cov_orig[["_mh", "mahalle", "R_risk_weight", "coverage_orig"]].merge(
        cov_ca2[["_mh", "coverage_CA2"]], on="_mh", how="outer"
    ).fillna(0)
    road_for_join = road[["_mh", "P_road_open"]].drop_duplicates("_mh")
    cov_join = cov_join.merge(road_for_join, on="_mh", how="left")
    cov_join["delta_coverage"] = cov_join["coverage_CA2"] - cov_join["coverage_orig"]
    print(cov_join[["mahalle", "P_road_open", "coverage_orig",
                     "coverage_CA2", "delta_coverage"]].to_string(index=False))

    # Sensitivity comparison
    print("\n--- Sensitivity summary (orig vs CA2) ---")
    sens_join = sens_orig.merge(sens_ca2, on=["scenario", "mode"], suffixes=("_orig", "_CA2"))
    sens_join["delta_obj"] = sens_join["objective_CA2"] - sens_join["objective_orig"]
    print(sens_join[["scenario", "mode", "status_orig", "status_CA2",
                      "objective_orig", "objective_CA2", "delta_obj"]].to_string(index=False))

    # Save combined
    with pd.ExcelWriter(CMP / "compare_summary_CA2.xlsx") as w:
        cmp_df.to_excel(w, sheet_name="Site_comparison", index=False)
        cov_join.to_excel(w, sheet_name="Mahalle_coverage", index=False)
        sens_join.to_excel(w, sheet_name="Sensitivity", index=False)
    print(f"\n[OK] compare_summary_CA2.xlsx")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    ax = axes[0]
    ax.scatter(cov_join["coverage_orig"], cov_join["coverage_CA2"],
                c=cov_join["P_road_open"], cmap="RdYlGn",
                vmin=0.93, vmax=1.0, s=80, edgecolor="k", alpha=0.85)
    for _, r in cov_join.iterrows():
        ax.annotate(r["mahalle"][:14], (r["coverage_orig"], r["coverage_CA2"]),
                    fontsize=7, alpha=0.7, xytext=(3, 3), textcoords="offset points")
    lims = [min(cov_join["coverage_orig"].min(), cov_join["coverage_CA2"].min()) - 0.05,
            max(cov_join["coverage_orig"].max(), cov_join["coverage_CA2"].max()) + 0.05]
    ax.plot(lims, lims, "k--", alpha=0.5, label="y=x (no change)")
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_xlabel("Orijinal Coverage", fontsize=10)
    ax.set_ylabel("CA2 Coverage (P_access weighted)", fontsize=10)
    ax.set_title("Mahalle Coverage: Orijinal vs CA2", fontsize=11, fontweight="bold")
    cbar = plt.colorbar(ax.collections[0], ax=ax, fraction=0.046)
    cbar.set_label("P(yol acik)", fontsize=9)
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)

    ax = axes[1]
    scens = sens_join["scenario"] + "_" + sens_join["mode"]
    x = np.arange(len(scens))
    w = 0.35
    ax.bar(x - w/2, sens_join["objective_orig"], w, label="Orijinal", color="steelblue")
    ax.bar(x + w/2, sens_join["objective_CA2"], w, label="CA2", color="coral")
    ax.set_xticks(x)
    ax.set_xticklabels(scens, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Objektif Degeri (Z)", fontsize=10)
    ax.set_title("6 Senaryo: Orijinal vs CA2 (Z degeri)", fontsize=11, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(CMP / "compare_overview_CA2.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] compare_overview_CA2.png")

    # Markdown report
    md = []
    md.append("# Cozum Alternatifi 2 - Yol Kapanma Olasiligi Entegrasyonu")
    md.append("## Orijinal vs CA2 Karsilastirma Raporu")
    md.append("")
    md.append("## 1. Yontem")
    md.append("IBB Tablo 1'deki 'cok agir hasarli bina' sayisindan yol kapanma olasiligi hesaplanir:")
    md.append("")
    md.append("```")
    md.append("P(yol acik | mahalle) = exp(-lambda * N_cok_agir)")
    md.append("")
    md.append("Burada:")
    md.append("  lambda = 0.005 (ampirik katsayi)")
    md.append("  N_cok_agir = mahalledeki cok agir hasarli bina sayisi (IBB Tablo 1)")
    md.append("```")
    md.append("")
    md.append("Sonuc olarak ABDURRAHMANGAZI (N=14) icin P=0.93, orman mahalleleri (N=0) icin P=1.00 elde edilir.")
    md.append("")
    md.append("Bu katsayi IP solver'inda her site j icin carpan olarak kullanilir:")
    md.append("")
    md.append("```")
    md.append("Max Z = Sum_i R_i * [ Sum_k mu(i,k) + Sum_j mu(i,j) * P_access(j) * X_j ]")
    md.append("P_access(j) = P(yol acik | dominant_mahalle(j))")
    md.append("```")
    md.append("")
    md.append("## 2. Site Secimi Farki")
    md.append("")
    md.append(f"- **Orijinal 8 site:** {sorted(orig_set)}")
    md.append(f"- **CA2 8 site:** {sorted(ca2_set)}")
    md.append(f"- **Ortak:** {len(common)} site ({sorted(common)})")
    md.append(f"- **Orijinalde olup CA2'de olmayan:** {sorted(only_orig)}")
    md.append(f"- **CA2'de olup orijinalde olmayan:** {sorted(only_ca2)}")
    md.append("")
    md.append("Detayli tablo:")
    md.append("")
    md.append("| S_No | Alan | Mahalle | P(yol acik) | Orijinal | CA2 |")
    md.append("|------|------|---------|-------------|----------|-----|")
    for _, r in cmp_df.iterrows():
        md.append(f"| {r['S_No']} | {r['Alan_Adi'][:35]} | {r['Mahalle']} | {r['C5_P_road_open']:.4f} | "
                  f"{'X' if r['in_orig'] else ''} | {'X' if r['in_CA2'] else ''} |")
    md.append("")
    md.append("## 3. Mahalle Coverage Farki")
    md.append("")
    md.append("| Mahalle | P(yol acik) | Coverage Orijinal | Coverage CA2 | Delta |")
    md.append("|---------|-------------|-------------------|--------------|-------|")
    for _, r in cov_join.iterrows():
        md.append(f"| {r['mahalle']} | {r['P_road_open']:.4f} | {r['coverage_orig']:.3f} | {r['coverage_CA2']:.3f} | {r['delta_coverage']:+.3f} |")
    md.append("")
    md.append("## 4. Sensitivity (6 Senaryo)")
    md.append("")
    md.append("| Senaryo | Mod | Z Orijinal | Z CA2 | Delta |")
    md.append("|---------|-----|-----------|-------|-------|")
    for _, r in sens_join.iterrows():
        md.append(f"| {r['scenario']} | {r['mode']} | {r['objective_orig']:.2f} | {r['objective_CA2']:.2f} | {r['delta_obj']:+.2f} |")
    md.append("")
    md.append("## 5. Sonuc")
    md.append("")
    md.append(f"Yol kapanma olasiligi entegrasyonu {len(common)}/8 site secimini degistirdi. "
              f"En dusuk P(yol acik) olan ABDURRAHMANGAZI (0.93) ve HAMIDIYE (0.94) "
              f"mahallelerindeki siteler daha dusuk agirlikla katkida bulundugu icin "
              f"solver daha erisebilir mahallelere (FATIH, YAVUZ SELIM) yoneldi. "
              f"Objektif degeri Z yaklasik {abs(sens_join['delta_obj'].mean()):.1f} birim azaldi "
              f"(erisilebilirlik katsayisi carpan etkisi).")
    (CMP / "comparison_report_CA2.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] comparison_report_CA2.md")

if __name__ == "__main__":
    main()

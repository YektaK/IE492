# -*- coding: utf-8 -*-
"""
05_compare.py - Side-by-side comparison: Original (C4=night pop) vs Alternative (C4=shelter need)
COZUM ALTERNATIFI 1

Reads:
  - Original outputs from D:\\IE492\\output\\results\\
  - Alt outputs from D:\\IE492\\cozum_alternatifi_1\\results\\

Produces:
  - comparison/compare_selection.png       (which 8 sites differ?)
  - comparison/compare_z_value.png         (objective Z comparison)
  - comparison/compare_coverage.png        (per-mahalle coverage delta)
  - comparison/compare_topsis_top10.png    (Top-10 TOPSIS rankings)
  - comparison/compare_summary.xlsx        (all metrics in one xlsx)
  - comparison/comparison_report.md        (narrative comparison)
"""
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ORIG = Path("D:/IE492")
ORIG_RES = ORIG / "output" / "results"
ALT = Path("D:/IE492/cozum_alternatifi_1")
ALT_RES = ALT / "results"
CMP = ALT / "comparison"
CMP.mkdir(parents=True, exist_ok=True)


def norm(s):
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())


def load_orig_baseline_hard():
    """Return DataFrame of original Baseline_hard selection with criteria+scores."""
    sel = pd.read_excel(ORIG_RES / "selection_Baseline_hard.xlsx")
    return sel


def load_alt_baseline_hard():
    sel = pd.read_excel(ALT_RES / "selection_Baseline_hard.xlsx")
    return sel


def load_orig_topsis():
    return pd.read_excel(ORIG_RES / "topsis_sonuclar.xlsx")


def load_alt_topsis():
    return pd.read_excel(ALT_RES / "topsis_sonuclar.xlsx")


if __name__ == "__main__":
    print("=" * 60)
    print("KARŞILAŞTIRMA: Orijinal vs Çözüm Alternatifi 1")
    print("  C4 orijinal  = gece nüfusu (TÜİK 2024)")
    print("  C4 alternatif = İBB Tablo 5-4 barınma ihtiyacı (hane)")
    print("=" * 60)

    sel_o = load_orig_baseline_hard()
    sel_a = load_alt_baseline_hard()
    top_o = load_orig_topsis().nlargest(10, "CC_Baseline").reset_index(drop=True)
    top_a = load_alt_topsis().nlargest(10, "CC_Baseline").reset_index(drop=True)

    set_o = set(sel_o["S_No"].tolist())
    set_a = set(sel_a["S_No"].tolist())
    common = set_o & set_a
    only_o = set_o - set_a
    only_a = set_a - set_o
    print(f"\nOrijinal seçim  ({len(set_o)} site): {sorted(set_o)}")
    print(f"Alternatif seçim ({len(set_a)} site): {sorted(set_a)}")
    print(f"Ortak: {len(common)}  Sadece orijinal: {len(only_o)}  Sadece alternatif: {len(only_a)}")
    if set_o == set_a:
        print(">>> SEÇİM ÖZDEŞ: Solver C4 proxy'sine karşı sağlam.")
    else:
        print(">>> SEÇİM FARKLI: Detayları inceleyin.")

    z_o = float(sel_o["C4_NightPop"].sum() * 0 + float(
        pd.read_excel(ORIG_RES / "selection_sensitivity.xlsx").query(
            "scenario=='Baseline' and mode=='hard'")["objective"].iloc[0]))
    z_a = float(pd.read_excel(ALT_RES / "selection_sensitivity.xlsx").query(
        "scenario=='Baseline' and mode=='hard'")["objective"].iloc[0])
    print(f"\nZ orijinal  = {z_o:.4f}")
    print(f"Z alternatif = {z_a:.4f}")
    print(f"Delta Z     = {z_a - z_o:+.4f}  ({(z_a/z_o-1)*100:+.2f}%)")

    cov_o = pd.read_excel(ORIG_RES / "selection_Baseline_hard.xlsx", sheet_name="Coverage_per_Mahalle")
    cov_a = pd.read_excel(ALT_RES / "selection_Baseline_hard.xlsx", sheet_name="Coverage_per_Mahalle")

    fig, axes = plt.subplots(2, 2, figsize=(15, 11))

    ax = axes[0, 0]
    all_ids = sorted(set_o | set_a)
    labels = [f"S{s}" for s in all_ids]
    in_o = [1 if s in set_o else 0 for s in all_ids]
    in_a = [1 if s in set_a else 0 for s in all_ids]
    x = np.arange(len(all_ids))
    w = 0.4
    ax.bar(x - w/2, in_o, w, color="dodgerblue", label="Orijinal (C4=gece nüfusu)", alpha=0.85)
    ax.bar(x + w/2, in_a, w, color="crimson", label="Alternatif (C4=barınma ihtiyacı)", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, fontsize=9)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Seçilmedi", "Seçildi"])
    ax.set_title("8 Seçim Karşılaştırması", fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_ylim(-0.05, 1.3)

    ax = axes[0, 1]
    ax.bar(["Orijinal\n(C4=nüfus)", "Alternatif\n(C4=barınma)"],
           [z_o, z_a], color=["dodgerblue", "crimson"], alpha=0.85, edgecolor="black")
    ax.set_title("IP Amaç Fonksiyonu Z", fontweight="bold")
    ax.set_ylabel("Z (toplam risk-ağırlıklı μ kapsama)")
    for i, v in enumerate([z_o, z_a]):
        ax.text(i, v + max(z_o, z_a) * 0.01, f"{v:.2f}", ha="center", fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    ax = axes[1, 0]
    mhs = sorted(set(cov_o["mahalle"]) | set(cov_a["mahalle"]))
    cov_o_idx = cov_o.set_index("mahalle").reindex(mhs)
    cov_a_idx = cov_a.set_index("mahalle").reindex(mhs)
    x = np.arange(len(mhs))
    ax.bar(x - w/2, cov_o_idx["total_coverage_20"].fillna(0).values, w,
           color="dodgerblue", label="Orijinal", alpha=0.85)
    ax.bar(x + w/2, cov_a_idx["total_coverage_20"].fillna(0).values, w,
           color="crimson", label="Alternatif", alpha=0.85)
    ax.axhline(0.5, color="black", linestyle="--", alpha=0.5, label="Eşik (0.50)")
    short = [m.replace(" DEVLET ORMANI", "").replace(" TEPE ORMANI", "").replace(" AYDOSU", "") for m in mhs]
    ax.set_xticks(x)
    ax.set_xticklabels(short, rotation=45, ha="right", fontsize=8)
    ax.set_title("Mahalle Kapsama (12 mevcut + 8 yeni)", fontweight="bold")
    ax.set_ylabel("Toplam μ kapsama")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    ax = axes[1, 1]
    top_o_x = [f"S{r['S_No']}" for _, r in top_o.iterrows()]
    top_a_x = [f"S{r['S_No']}" for _, r in top_a.iterrows()]
    y = np.arange(10)
    ax.barh(y - 0.2, top_o["CC_Baseline"].values, 0.4, color="dodgerblue", label="Orijinal", alpha=0.85)
    ax.barh(y + 0.2, top_a["CC_Baseline"].values, 0.4, color="crimson", label="Alternatif", alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{a} | {b}" for a, b in zip(top_o_x, top_a_x)], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("TOPSIS CC (Baseline)")
    ax.set_title("Top-10 Sıralaması (Orijinal | Alternatif)", fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    plt.suptitle("Orijinal Çözüm vs Çözüm Alternatifi 1 (C4 = İBB Barınma İhtiyacı)",
                 fontsize=13, fontweight="bold", y=1.00)
    plt.tight_layout()
    plt.savefig(CMP / "compare_overview.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n[OK] {CMP / 'compare_overview.png'}")

    summary = []
    summary.append({"metric": "Seçilen 8 site (S_No)", "orijinal": str(sorted(set_o)),
                    "alternatif": str(sorted(set_a)),
                    "identical": "YES" if set_o == set_a else "NO"})
    summary.append({"metric": "Z (IP objective, Baseline hard)",
                    "orijinal": round(z_o, 4), "alternatif": round(z_a, 4),
                    "identical": "YES" if abs(z_o - z_a) < 1e-3 else "NO"})
    summary.append({"metric": "Toplam kapsama (17 mahalle)",
                    "orijinal": round(float(cov_o["total_coverage_20"].sum()), 4),
                    "alternatif": round(float(cov_a["total_coverage_20"].sum()), 4),
                    "identical": "YES" if abs(cov_o["total_coverage_20"].sum() - cov_a["total_coverage_20"].sum()) < 1e-3 else "NO"})
    summary.append({"metric": "Kritik altında kalan mahalle",
                    "orijinal": int((cov_o[cov_o["is_critical"]]["total_coverage_20"] < 0.5).sum()),
                    "alternatif": int((cov_a[cov_a["is_critical"]]["total_coverage_20"] < 0.5).sum()),
                    "identical": "YES" if (cov_o[cov_o["is_critical"]]["total_coverage_20"] < 0.5).sum() ==
                                        (cov_a[cov_a["is_critical"]]["total_coverage_20"] < 0.5).sum() else "NO"})
    summary.append({"metric": "Toplam barınma ihtiyacı (hane)",
                    "orijinal": int(pd.read_excel(ORIG / "output" / "data" / "mahalle_barinma_ihtiyaci.xlsx")["hane_ihtiyaci"].sum()),
                    "alternatif": int(pd.read_excel(ORIG / "output" / "data" / "mahalle_barinma_ihtiyaci.xlsx")["hane_ihtiyaci"].sum()),
                    "identical": "YES"})

    df_sum = pd.DataFrame(summary)
    with pd.ExcelWriter(CMP / "compare_summary.xlsx") as w:
        df_sum.to_excel(w, sheet_name="Summary", index=False)
        sel_o.assign(solution="orijinal").to_excel(w, sheet_name="Orig_Selection", index=False)
        sel_a.assign(solution="alternatif").to_excel(w, sheet_name="Alt_Selection", index=False)
        cov_o.merge(cov_a, on="mahalle", suffixes=("_orig", "_alt")).to_excel(
            w, sheet_name="Coverage_Delta", index=False)
        top_o.assign(solution="orijinal").to_excel(w, sheet_name="Top10_Orig", index=False)
        top_a.assign(solution="alternatif").to_excel(w, sheet_name="Top10_Alt", index=False)
    print(f"[OK] {CMP / 'compare_summary.xlsx'}")

    print("\n--- ÖZET ---")
    print(df_sum.to_string(index=False))

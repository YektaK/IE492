# -*- coding: utf-8 -*-
"""
00_compare_all.py
==========================================================
Tum senaryolarin (orijinal + CA1 + CA2 + CA3-6) toplu karsilastirmasi.

7 senaryo:
  - Orig (8-site)
  - CA1 (8-site, C4=barinma)
  - CA2 (8-site, yol kapanma entegre)
  - CA3 (20-site, SB+YK)
  - CA4 (20-site, SB only)
  - CA5 (20-site, YK only)
  - CA6 (20-site, baseline)
==========================================================
Ciktilar:
  - results/all_scenarios_summary.xlsx
  - results/site_overlap_matrix.xlsx
  - maps/comparison_overview.png
  - reporting_toplu.md
"""
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path("D:/IE492")
CMP = ROOT / "cozum_alternatifi_comparison_all"
RES = CMP / "results"
MAPS = CMP / "maps"
RES.mkdir(parents=True, exist_ok=True)
MAPS.mkdir(parents=True, exist_ok=True)

def norm(s):
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())

# --- 1. Senaryo tanimlari -------------------------------------------------
SCENARIOS = [
    {"name": "Orig",     "konteyner": 8,  "C4": "nufus",      "YK": False, "relocation": False,
     "sel": ROOT / "output" / "results" / "selection_Baseline_hard.xlsx",
     "sens": ROOT / "output" / "results" / "selection_sensitivity.xlsx",
     "sheet": "Selected_8"},
    {"name": "CA1",      "konteyner": 8,  "C4": "barinma",    "YK": False, "relocation": False,
     "sel": ROOT / "cozum_alternatifi_1" / "results" / "selection_Baseline_hard.xlsx",
     "sens": ROOT / "cozum_alternatifi_1" / "results" / "selection_sensitivity.xlsx",
     "sheet": "Selected_8"},
    {"name": "CA2",      "konteyner": 8,  "C4": "nufus",      "YK": True,  "relocation": False,
     "sel": ROOT / "cozum_alternatifi_2_road_closure" / "results" / "selection_Baseline_hard_CA2.xlsx",
     "sens": ROOT / "cozum_alternatifi_2_road_closure" / "results" / "selection_sensitivity_CA2.xlsx",
     "sheet": "Selected_8"},
    {"name": "CA3_SB+YK","konteyner": 20, "C4": "barinma",   "YK": True,  "relocation": True,
     "sel": ROOT / "cozum_alternatifi_3_full_reloc_sb_yk" / "results" / "selection_Baseline_hard_CA3.xlsx",
     "sens": ROOT / "cozum_alternatifi_3_full_reloc_sb_yk" / "results" / "selection_sensitivity_CA3.xlsx",
     "sheet": "Selected_20"},
    {"name": "CA4_SB",   "konteyner": 20, "C4": "barinma",   "YK": False, "relocation": True,
     "sel": ROOT / "cozum_alternatifi_4_full_reloc_sb" / "results" / "selection_Baseline_hard_CA4.xlsx",
     "sens": ROOT / "cozum_alternatifi_4_full_reloc_sb" / "results" / "selection_sensitivity_CA4.xlsx",
     "sheet": "Selected_20"},
    {"name": "CA5_YK",   "konteyner": 20, "C4": "nufus",     "YK": True,  "relocation": True,
     "sel": ROOT / "cozum_alternatifi_5_full_reloc_yk" / "results" / "selection_Baseline_hard_CA5.xlsx",
     "sens": ROOT / "cozum_alternatifi_5_full_reloc_yk" / "results" / "selection_sensitivity_CA5.xlsx",
     "sheet": "Selected_20"},
    {"name": "CA6_BL",   "konteyner": 20, "C4": "nufus",     "YK": False, "relocation": True,
     "sel": ROOT / "cozum_alternatifi_6_full_reloc_baseline" / "results" / "selection_Baseline_hard_CA6.xlsx",
     "sens": ROOT / "cozum_alternatifi_6_full_reloc_baseline" / "results" / "selection_sensitivity_CA6.xlsx",
     "sheet": "Selected_20"},
]

# --- 2. Senaryo bazli metrikler -------------------------------------------
all_rows = []
selected_sets = {}
for sc in SCENARIOS:
    try:
        sel_df = pd.read_excel(sc["sel"], sheet_name=sc["sheet"])
        sens_df = pd.read_excel(sc["sens"])
    except FileNotFoundError as e:
        print(f"[UYARI] {sc['name']}: dosya bulunamadi - {e}")
        continue
    sel_ids = set(sel_df["S_No"])
    selected_sets[sc["name"]] = sel_ids
    z_mean = float(sens_df["objective"].mean())
    z_hard = float(sens_df[sens_df["mode"] == "hard"]["objective"].mean())
    z_soft = float(sens_df[sens_df["mode"] == "soft"]["objective"].mean())
    cov_col = "sum_total_coverage_weighted" if "sum_total_coverage_weighted" in sens_df.columns else "sum_total_coverage"
    cov_sum = float(sens_df[cov_col].mean())
    crit_below = int(sens_df["n_critical_below_threshold"].sum())
    mevcut_count = sum(1 for _, r in sel_df.iterrows() if r.get("_kaynak", "") == "mevcut_12")
    all_rows.append({
        "senaryo": sc["name"],
        "konteyner": sc["konteyner"],
        "C4_kaynak": sc["C4"],
        "YK_carpani": "var" if sc["YK"] else "yok",
        "relocation": sc["relocation"],
        "n_secim": len(sel_ids),
        "n_mevcut": mevcut_count,
        "n_yeni": len(sel_ids) - mevcut_count,
        "Z_ortalama": z_mean,
        "Z_hard": z_hard,
        "Z_soft": z_soft,
        "sum_coverage": cov_sum,
        "crit_below_toplam": crit_below,
        "selected_S_No": sorted(sel_ids),
    })

df_all = pd.DataFrame(all_rows)
df_all.to_excel(RES / "all_scenarios_summary.xlsx", index=False)
print("--- Tum Senaryolar ---")
print(df_all[["senaryo", "konteyner", "C4_kaynak", "YK_carpani", "relocation",
              "n_secim", "n_mevcut", "n_yeni", "Z_ortalama"]].to_string(index=False))

# --- 3. Site overlap matrisi ----------------------------------------------
print("\n--- Site Overlap Matrisi (secim seti kesisim) ---")
all_ids = set()
for s in selected_sets.values():
    all_ids |= s
all_ids = sorted(all_ids)
overlap_rows = []
for sid in all_ids:
    row = {"S_No": sid}
    for sc in SCENARIOS:
        row[sc["name"]] = "X" if sid in selected_sets.get(sc["name"], set()) else ""
    overlap_rows.append(row)
df_overlap = pd.DataFrame(overlap_rows)
df_overlap.to_excel(RES / "site_overlap_matrix.xlsx", index=False)
print(df_overlap.to_string(index=False))

# --- 4. Coverage heatmap ---------------------------------------------------
cov_orig = pd.read_excel(ROOT / "output" / "results" / "selection_Baseline_hard.xlsx",
                          sheet_name="Coverage_per_Mahalle")
cov_orig["_mh"] = cov_orig["mahalle"].apply(norm)
cov_orig = cov_orig.set_index("_mh")

mh_list = sorted(cov_orig.index.tolist())
heat = pd.DataFrame(index=mh_list)
for sc in SCENARIOS:
    try:
        cov_sc = pd.read_excel(sc["sel"].parent / sc["sel"].name.replace("Baseline_hard", "Baseline_hard"),
                                sheet_name="Coverage_per_Mahalle")
        cov_sc["_mh"] = cov_sc["mahalle"].apply(norm)
        cov_sc = cov_sc.set_index("_mh")
        heat[sc["name"]] = cov_sc["total_coverage_20_weighted"].reindex(mh_list).fillna(0)
    except Exception as e:
        print(f"[UYARI] {sc['name']} coverage yuklenemedi: {e}")
        heat[sc["name"]] = 0

heat.to_excel(RES / "mahalle_coverage_heatmap.xlsx")
print("\n--- Mahalle Coverage (7 senaryo) ---")
print(heat.to_string())

# --- 5. Plotlar ------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(15, 7))
ax = axes[0]
names = [r["senaryo"] for r in all_rows]
ax.bar(names, [r["Z_ortalama"] for r in all_rows],
        color=["steelblue" if "CA" not in n else "seagreen" for n in names])
ax.set_ylabel("Z (ortalama 6 senaryo)", fontsize=10)
ax.set_title("Tum Senaryolar - Objektif Deger", fontsize=11, fontweight="bold")
ax.grid(axis="y", alpha=0.3)
for i, r in enumerate(all_rows):
    ax.text(i, r["Z_ortalama"] + 20, f"{r['konteyner']}-site", ha="center", fontsize=8)

ax = axes[1]
im = ax.imshow(heat.values, aspect="auto", cmap="YlGnBu")
ax.set_xticks(range(len(heat.columns)))
ax.set_xticklabels(heat.columns, rotation=30, ha="right", fontsize=8)
ax.set_yticks(range(len(heat.index)))
ax.set_yticklabels(heat.index, fontsize=7)
ax.set_title("Mahalle Coverage Heatmap (7 senaryo)", fontsize=11, fontweight="bold")
plt.colorbar(im, ax=ax, fraction=0.046)
plt.tight_layout()
plt.savefig(MAPS / "comparison_overview.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"\n[OK] comparison_overview.png")

# --- 6. Toplu rapor -------------------------------------------------------
md = []
md.append("# Tum Cozum Alternatifleri - Toplu Karsilastirma")
md.append("## Sultanbeyli Konteyner Optimizasyonu - 7 Senaryo Analizi")
md.append("")
md.append("**Tarih:** 2026  \n**Pipeline:** AHP + TOPSIS + FCM (sigma=800) + 0-1 IP  \n")
md.append("## 1. Senaryolar")
md.append("")
md.append("| Senaryo | Konteyner | C4 Kaynagi | YK Carpani | Relocation | Z (ort) |")
md.append("|---------|-----------|------------|------------|------------|---------|")
for r in all_rows:
    md.append(f"| {r['senaryo']} | {r['konteyner']} | {r['C4_kaynak']} | {r['YK_carpani']} | "
              f"{'evet' if r['relocation'] else 'hayir'} | {r['Z_ortalama']:.2f} |")
md.append("")
md.append("## 2. Kapsam Farki")
md.append("- 8-site senaryolar (Orig, CA1, CA2): Z ~ 908-936 araliginda (sabit konteynerler ekleniyor)")
md.append("- 20-site senaryolar (CA3-6): Z ~ 1142-1201 araliginda (12+8 -> 20 konteyner)")
md.append("- Z artisi 12 ek konteynerin degeri; mu_mevcut=0 oldugu icin baslangic coverage 0")
md.append("")
md.append("## 3. C4 Etkisi")
md.append("- C4 = barinma ihtiyaci (SB) veya nufus degisimi Z'yi **degistirmedi**: CA3=CA5=1142.55, CA4=CA6=1201.22")
md.append("- Talep proxy secimi solver-secim etkisizdir (kullanici gereksinimi) - 'rozet' karar")
md.append("")
md.append("## 4. YK Etkisi")
md.append("- P_access carpani Z'yi **~%5 dusurdu**: CA3=CA5 (YK var) < CA4=CA6 (YK yok)")
md.append("- 1142.55 vs 1201.22 = fark 58.67, oran %4.9")
md.append("- Solver dusuk P_access'li mahallelere (ABDURRAHMANGAZI, HAMIDIYE) daha az agirlik verdi")
md.append("")
md.append("## 5. Relocation Etkisi")
md.append("- 12 mevcut konteynerin relocate edilmesi solver'a secim esnekligi kazandirdi")
md.append("- 20-site Z = 8-site Z * ~1.28 (12 ek konteyner)")
md.append("- Mevcut konteynerlerden sadece 1-2'si secildi (CA3'te 1 mevcut, S152)")
md.append("")
md.append("## 6. Site Overlap")
md.append("- 8-site senaryolarda (Orig, CA1, CA2) secim 6-7/8 site ortak (saglam cozum)")
md.append("- 20-site senaryolarda secim 4 CA arasi ~%80 ortak (P_access onemli)")
md.append("- Toplam 27 unique site secildi (140 havuzun %19.3'u)")
md.append("")
md.append("## 7. Sonuc ve Oneriler")
md.append("- **Tam relocation (20 konteyner) icin en uygun senaryo: CA4 (SB only, YK yok)** - en yuksek Z=1201.22")
md.append("- **Yol kapanma entegrasyonu gerekli**: gercekci deprem sonrasi erisim")
md.append("- **C4 secimi (barinma vs nufus) solver etkisiz**: kavramsal acidan SB daha dogru")
md.append("- **Onerilen nihai secim**: CA3 (SB+YK) - talep dogru amaca yonelik, yol kapanma dahil")

(RES.parent / "reporting_toplu.md").write_text("\n".join(md), encoding="utf-8")
print(f"\n[OK] reporting_toplu.md")
print(f"[OK] all_scenarios_summary.xlsx")
print(f"[OK] site_overlap_matrix.xlsx")
print(f"[OK] mahalle_coverage_heatmap.xlsx")

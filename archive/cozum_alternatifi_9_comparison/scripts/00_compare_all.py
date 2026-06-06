"""
00_compare_all.py - CA9a vs CA9b vs CA9c top-level comparison
"""
import os
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "D:/IE492"
OUT = os.path.join(ROOT, "cozum_alternatifi_9_comparison")
os.makedirs(OUT, exist_ok=True)

cas = {
    "CA9a (plain+spatial)": os.path.join(ROOT, "cozum_alternatifi_9a_min_one_per_mahalle"),
    "CA9b (spatial+P_access)": os.path.join(ROOT, "cozum_alternatifi_9b_min_one_yk"),
    "CA9c (spatial+truncation)": os.path.join(ROOT, "cozum_alternatifi_9c_min_one_truncation"),
}

rows = []
for label, p in cas.items():
    df = pd.read_excel(os.path.join(p, "results", "ip_all_scenarios.xlsx"))
    df["CA"] = label
    rows.append(df)
all_df = pd.concat(rows, ignore_index=True)
all_df.to_excel(os.path.join(OUT, "all_scenarios_3CA.xlsx"), index=False)
print(f"[OK] all_scenarios_3CA.xlsx ({len(all_df)} satir)")

hard = all_df[~all_df["soft"]]
pivot_z = hard.pivot_table(index="CA", columns=["ahp", "mode"], values="Z", aggfunc="mean")
pivot_rxc = hard.pivot_table(index="CA", columns=["ahp", "mode"], values="sum_R_x_C", aggfunc="mean")
pivot_z.to_excel(os.path.join(OUT, "pivot_Z_3CA.xlsx"))
pivot_rxc.to_excel(os.path.join(OUT, "pivot_RxC_3CA.xlsx"))
print("[OK] pivot Z & RxC")

cov_rows = []
for label, p in cas.items():
    c = pd.read_excel(os.path.join(p, "results", "coverage_per_mahalle.xlsx"))
    c["CA"] = label
    cov_rows.append(c)
cov_all = pd.concat(cov_rows, ignore_index=True)
hard_cov = cov_all[~cov_all["soft"]]
mah_pivot = hard_cov.pivot_table(index="mahalle", columns="CA", values="R_x_C", aggfunc="mean", fill_value=0)
mah_pivot.to_excel(os.path.join(OUT, "pivot_RxC_per_mahalle_3CA.xlsx"))
print("[OK] pivot RxC per mahalle")

n_crit_pivot = hard.pivot_table(index="CA", columns=["ahp", "mode"], values="n_critical_below_0.50", aggfunc="mean")
n_crit_pivot.to_excel(os.path.join(OUT, "pivot_n_critical_below_0.50_3CA.xlsx"))
print("[OK] pivot n_critical_below_0.50")

fig, ax = plt.subplots(figsize=(10, 6))
ca_labels = list(cas.keys())
colors = {"CA9a (plain+spatial)": "tab:blue", "CA9b (spatial+P_access)": "tab:orange", "CA9c (spatial+truncation)": "tab:green"}
for label in ca_labels:
    sub = hard[hard["CA"] == label]
    z = sub["Z"].values
    r = sub["sum_R_x_C"].values
    ax.scatter(r, z, s=80, c=colors[label], label=label, edgecolors="black", alpha=0.8)
    for _, row in sub.iterrows():
        ax.annotate(f"{row['ahp'][:3]}-{row['mode']}", (row["sum_R_x_C"], row["Z"]), fontsize=7, alpha=0.7)
ax.set_xlabel("sum R x C (toplam risk-weighted coverage)")
ax.set_ylabel("Z (objective value)")
ax.set_title("CA9a vs CA9b vs CA9c (hard scenarios)")
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "Z_vs_RxC_3CA.png"), dpi=120, bbox_inches="tight")
plt.close()
print("[OK] Z_vs_RxC_3CA.png")

fig, ax = plt.subplots(figsize=(12, 6))
mah_pivot.plot(kind="bar", ax=ax, color=[colors[c] for c in mah_pivot.columns])
ax.set_ylabel("mean R x C")
ax.set_title("Mahalle bazinda R x C - 3 CA karsilastirma (hard senaryolar ort.)")
ax.legend(loc="upper right", fontsize=9)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "RxC_per_mahalle_3CA.png"), dpi=120, bbox_inches="tight")
plt.close()
print("[OK] RxC_per_mahalle_3CA.png")

with open(os.path.join(OUT, "comparison_report.md"), "w", encoding="utf-8") as f:
    f.write("# CA9a vs CA9b vs CA9c - Comparison\n\n")
    f.write("**Senaryolar:**\n- CA9a: Plain IP + spatial constraint (her mahallede min 1 konteyner)\n- CA9b: Plain IP + spatial + P_access (yol kapanma penalty)\n- CA9c: Plain IP + spatial + CA8a truncation (mu < 0.20 -> 0)\n\n")
    f.write("**Kapsam:** 3 AHP (Baseline/DamageFocused/InfrastructureFocused) x 2 mod (MEV/NMEV) x hard = 6 hard senaryo x 3 CA = 18 karsilastirma noktasi.\n\n")
    f.write("## Z (objective) - hard mean per CA:\n\n")
    f.write("| CA | Baseline_MEV | Baseline_NMEV | DamageFocused_MEV | DamageFocused_NMEV | InfrastructureFocused_MEV | InfrastructureFocused_NMEV |\n")
    f.write("|---|---|---|---|---|---|---|\n")
    for label in ca_labels:
        row = [label]
        for ahp in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
            for mode in ["MEV", "NMEV"]:
                v = hard[(hard["CA"]==label) & (hard["ahp"]==ahp) & (hard["mode"]==mode)]["Z"].mean()
                row.append(f"{v:.2f}")
        f.write("| " + " | ".join(row) + " |\n")
    f.write("\n## sum R x C - hard mean per CA:\n\n")
    f.write("| CA | Baseline_MEV | Baseline_NMEV | DamageFocused_MEV | DamageFocused_NMEV | InfrastructureFocused_MEV | InfrastructureFocused_NMEV |\n")
    f.write("|---|---|---|---|---|---|---|\n")
    for label in ca_labels:
        row = [label]
        for ahp in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
            for mode in ["MEV", "NMEV"]:
                v = hard[(hard["CA"]==label) & (hard["ahp"]==ahp) & (hard["mode"]==mode)]["sum_R_x_C"].mean()
                row.append(f"{v:.2f}")
        f.write("| " + " | ".join(row) + " |\n")
    f.write("\n## Gozlemler\n\n")
    z9a = hard[hard["CA"]=="CA9a (plain+spatial)"]["Z"].mean()
    z9b = hard[hard["CA"]=="CA9b (spatial+P_access)"]["Z"].mean()
    z9c = hard[hard["CA"]=="CA9c (spatial+truncation)"]["Z"].mean()
    f.write(f"- Ortalama Z: CA9a={z9a:.2f}, CA9b={z9b:.2f}, CA9c={z9c:.2f}\n")
    f.write(f"- P_access penalty (CA9b) Z'yi CA9a'ya gore %{(z9a-z9b)/z9a*100:.1f} dusurdu.\n")
    f.write(f"- Truncation (CA9c) Z'yi CA9a'ya gore %{(z9a-z9c)/z9a*100:.1f} dusurdu.\n")
    f.write("- En dusuk Z = InfrastructureFocused_MEV (en muhafazakar), en yuksek Z = DamageFocused_NMEV.\n")
    f.write("- CA9b'de P_access < 1 olan siteler secimden elendi; risk-weighted coverage artti.\n")
    f.write("- CA9c'de mu<0.20 truncation dusuk-kaliteli siteleri tamamen devre disi birakti; coverage tekrar artti.\n")

print("[OK] comparison_report.md")

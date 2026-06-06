"""
05_map.py - CA9b secim haritalari
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "D:/IE492"
CA = "cozum_alternatifi_9b_min_one_yk"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")
MAPS_DIR = os.path.join(ROOT, CA, "maps")
os.makedirs(MAPS_DIR, exist_ok=True)

aday = pd.read_excel(os.path.join(DATA_DIR, "adaylar.xlsx"))
mev = pd.read_excel(os.path.join(DATA_DIR, "mevcut_12.xlsx"))
sp12 = pd.read_excel(os.path.join(DATA_DIR, "spatial_assignment_12.xlsx"))
ip_df = pd.read_excel(os.path.join(RESULTS_DIR, "ip_all_scenarios.xlsx"))
sel_df = pd.read_excel(os.path.join(RESULTS_DIR, "selected_sites.xlsx"))
cov_df = pd.read_excel(os.path.join(RESULTS_DIR, "coverage_per_mahalle.xlsx"))
risk = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk.xlsx"))
risk_col = "risk_score" if "risk_score" in risk.columns else [c for c in risk.columns if "risk" in c.lower()][0]
risk_map = dict(zip(risk["mahalle"].astype(str).str.upper(), risk[risk_col].astype(float)))

for tag in ["Baseline_MEV_hard", "Baseline_NMEV_hard"]:
    fig, ax = plt.subplots(figsize=(14, 10))
    sc = None
    if "Enlem" in aday.columns and "Boylam" in aday.columns:
        valid = aday.dropna(subset=["Enlem", "Boylam"])
        ax.scatter(valid["Boylam"], valid["Enlem"], s=40, c="lightgray", alpha=0.5, label="Aday (secilmemis)")

    sub_sel = sel_df[sel_df["scenario"] == tag]
    if len(sub_sel):
        chosen = sub_sel.merge(aday[["S_No", "Enlem", "Boylam", "Alan_Adi"]], on="S_No", how="left")
        chosen = chosen.dropna(subset=["Enlem", "Boylam"])
        ax.scatter(chosen["Boylam"], chosen["Enlem"], s=220, c="red", marker="*", edgecolors="white",
                   label=f"Secilen ({len(chosen)} yeni)", zorder=5)
        for _, r in chosen.iterrows():
            ax.text(r["Boylam"], r["Enlem"]+0.0007, f"S{int(r['S_No'])}", fontsize=7, ha="center", color="red", weight="bold")

    if "enlem" in mev.columns and "boylam" in mev.columns:
        valid_mv = mev.dropna(subset=["enlem", "boylam"])
        if "mahalle" in valid_mv.columns:
            valid_mv = valid_mv[~valid_mv["mahalle"].astype(str).str.contains("ORMAN", na=False, case=False)]
        ax.scatter(valid_mv["boylam"], valid_mv["enlem"], s=80, c="lightblue", marker="s", edgecolors="navy",
                   label="Mevcut 12", zorder=4)

    sub_cov = cov_df[(cov_df["scenario"] == tag)].copy()
    sub_cov["mahalle_n"] = sub_cov["mahalle"].astype(str).str.upper()
    sub_cov["R"] = sub_cov["mahalle_n"].map(risk_map).fillna(0)
    if len(sub_cov):
        centroid = pd.read_excel(os.path.join(ROOT, "output/results/mahalle_centroids.xlsx"))
        if "mahalle_norm" in centroid.columns:
            c_dict = centroid.set_index("mahalle_norm")[["enlem", "boylam"]].to_dict("index")
            xs, ys, sizes, colors = [], [], [], []
            for _, r in sub_cov.iterrows():
                info = c_dict.get(r["mahalle_n"], None)
                if info is not None and pd.notna(info.get("enlem")):
                    xs.append(info["boylam"]); ys.append(info["enlem"])
                    sizes.append(100 + r["R"] * 20); colors.append(r["R"])
            if xs:
                sc = ax.scatter(xs, ys, s=sizes, c=colors, cmap="Reds", alpha=0.6, edgecolors="black", zorder=3)
                for x, y, m in zip(xs, ys, sub_cov["mahalle_n"].tolist()):
                    ax.text(x, y+0.0008, m[:12], fontsize=7, ha="center")
    if sc is not None:
        plt.colorbar(sc, ax=ax, label="R risk")
    ax.set_title(f"CA9b - {tag} (spatial: her mahallede >= 1)")
    ax.set_xlabel("Boylam"); ax.set_ylabel("Enlem")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(MAPS_DIR, f"selection_map_CA9b_{tag}.png")
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")

fig, ax = plt.subplots(figsize=(12, 7))
data = []
for _, r in ip_df[~ip_df["soft"]].iterrows():
    data.append({"scenario": r["scenario"], "Z": r["Z"], "R_x_C": r["sum_R_x_C"]})
df = pd.DataFrame(data)
x = np.arange(len(df))
ax.bar(x-0.2, df["Z"], width=0.4, color="#1f77b4", label="Z")
ax2 = ax.twinx()
ax2.bar(x+0.2, df["R_x_C"], width=0.4, color="#d62728", label="R x C")
ax.set_xticks(x)
ax.set_xticklabels(df["scenario"], rotation=45, ha="right", fontsize=7)
ax.set_ylabel("Z", color="#1f77b4")
ax2.set_ylabel("R x C", color="#d62728")
ax.set_title("CA9b - Z ve RxC (6 hard senaryo)")
ax.legend(loc="upper left")
ax2.legend(loc="upper right")
plt.tight_layout()
plt.savefig(os.path.join(MAPS_DIR, "z_vs_rxc.png"), dpi=120, bbox_inches="tight")
plt.close()
print(f"[OK] z_vs_rxc.png")


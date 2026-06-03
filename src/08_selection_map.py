"""
08_selection_map.py
Focused map: only the 12 existing + 8 selected, with risk-coloured mahalle,
800m coverage circles, and labels.  Goes to output/final/selection_map_focus.png.
"""
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from pathlib import Path

ROOT = Path(r"D:\IE492")
DATA = ROOT / "output" / "data"
RES = ROOT / "output" / "results"
FIG = ROOT / "output" / "final"

aday = pd.read_excel(DATA / "adaylar.xlsx")
mev = pd.read_excel(DATA / "mevcut_12.xlsx")
centroids = pd.read_excel(RES / "mahalle_centroids.xlsx")
selection = pd.read_excel(RES / "selection_Baseline_hard.xlsx", sheet_name="Selected_8")
risk = pd.read_excel(DATA / "mahalle_risk.xlsx")

# Normalize helper
def n(s):
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())

centroids["_mh"] = centroids["mahalle_norm"].fillna("")
centroids["_mh_display"] = centroids["mahalle_display"].fillna("")
centroids["_risk"] = centroids["risk_score"].fillna(0)
centroids["_nuf"] = centroids["nufus_2024"].fillna(0)

sel_pts = selection.copy()
mev_pts = mev.copy()

fig, ax = plt.subplots(figsize=(14, 11))

# Mahalle risk-coloured polygons (we have only centroids -> draw large circles
# scaled by population, coloured by risk)
max_pop = max(centroids["_nuf"].max(), 1)
for _, c in centroids.iterrows():
    if pd.isna(c["enlem"]):
        continue
    r = float(c["_risk"])
    pop = float(c["_nuf"])
    size = 200 + (pop / max_pop) * 1200
    color = plt.cm.Reds(min(0.15 + r / 40, 0.95))
    ax.scatter(c["boylam"], c["enlem"], s=size, c=[color],
               alpha=0.45, edgecolors="darkred", linewidths=1.2, zorder=1)
    label = f"{c['_mh_display']}\nR={r:.1f}  n={int(pop):,}"
    ax.annotate(label, (c["boylam"], c["enlem"]),
                textcoords="offset points", xytext=(0, -2),
                fontsize=8, ha="center", color="black")

# Existing 12 — blue squares, 800m circles
for _, m in mev_pts.iterrows():
    ax.scatter(m["boylam"], m["enlem"], s=200, c="royalblue", marker="s",
               zorder=4, edgecolors="white", linewidths=1.5)
    ax.add_patch(Circle((m["boylam"], m["enlem"]), 0.0072,
                        fill=False, edgecolor="royalblue",
                        linestyle="--", alpha=0.35, linewidth=0.8, zorder=3))

# Selected 8 — big red stars with label
for _, s in sel_pts.iterrows():
    ax.scatter(s["Boylam"], s["Enlem"], s=550, c="red", marker="*",
               zorder=6, edgecolors="white", linewidths=2.0)
    # 800m coverage
    ax.add_patch(Circle((s["Boylam"], s["Enlem"]), 0.0072,
                        fill=False, edgecolor="red",
                        linestyle="-", alpha=0.5, linewidth=1.2, zorder=5))
    label = f"S{s['S_No']}\n{s['Mahalle']}"
    ax.annotate(label, (s["Boylam"], s["Enlem"]),
                textcoords="offset points", xytext=(10, 10),
                fontsize=9, color="darkred", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="red", alpha=0.85))

# Custom legend
from matplotlib.lines import Line2D
legend_elems = [
    Line2D([0], [0], marker="*", color="w", label="Selected 8 (new)",
           markerfacecolor="red", markersize=18, markeredgecolor="white"),
    Line2D([0], [0], marker="s", color="w", label="Existing 12",
           markerfacecolor="royalblue", markersize=12, markeredgecolor="white"),
    Line2D([0], [0], marker="o", color="w", label="Mahalle centroid (size ∝ population, color ∝ risk)",
           markerfacecolor="lightcoral", markersize=14, alpha=0.5),
    Line2D([0], [0], color="red", linestyle="-", label="800m FCM radius (new)"),
    Line2D([0], [0], color="royalblue", linestyle="--", label="800m FCM radius (existing)"),
]
ax.legend(handles=legend_elems, loc="lower right", fontsize=9, framealpha=0.95)

ax.set_xlabel("Longitude", fontsize=10)
ax.set_ylabel("Latitude", fontsize=10)
ax.set_title("Sultanbeyli Container Network — Selected 8 (red stars) + Existing 12 (blue squares)\n"
             "Mahalle shaded by IBB risk × sized by population  |  800 m FCM coverage radius shown",
             fontsize=12, fontweight="bold")
ax.grid(True, alpha=0.25)
ax.set_aspect("equal", adjustable="datalim")
plt.tight_layout()

out = FIG / "selection_map_focus.png"
plt.savefig(out, dpi=180, bbox_inches="tight")
plt.close()
print(f"[OK] {out}")

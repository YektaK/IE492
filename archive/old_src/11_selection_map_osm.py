# -*- coding: utf-8 -*-
"""
11_selection_map_osm.py
Builds selection map on OpenStreetMap (real basemap).
Saves: D:/IE492/output/final/selection_map_osm.png

Layers (bottom -> top):
  1. OSM Mapnik basemap (contextily)
  2. Mahalle centroids: circles colored by shelter-need (Table 5-4), sized by population
  3. Existing 12 containers: blue squares + 800m dashed radius
  4. Selected 8 new sites: red stars + 800m solid radius
  5. Labels: S_No + Mahalle for selected
  6. Legend + scale bar + north arrow
"""
from pathlib import Path
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import contextily as cx
from PIL import Image
import requests

ROOT = Path("D:/IE492")
RES = ROOT / "output" / "results"
FINAL = ROOT / "output" / "final"
DATA = ROOT / "output" / "data"

OUT_PNG = FINAL / "selection_map_osm.png"

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
adaylar = pd.read_excel(DATA / "adaylar.xlsx")
mevcut = pd.read_excel(DATA / "mevcut_12.xlsx")
risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
sel = pd.read_excel(RES / "selection_Baseline_hard.xlsx")
sel_ids = sel["S_No"].tolist()
shelter = pd.read_excel(RES / "shelter_demand.xlsx") if (RES / "shelter_demand.xlsx").exists() else None

# Mahalle -> centroid (lat, lon) from centroids file
centroids = pd.read_excel(RES / "mahalle_centroids.xlsx")
centroids["mahalle"] = centroids["mahalle_norm"]
mh_to_lat = dict(zip(centroids["mahalle"], centroids["enlem"]))
mh_to_lon = dict(zip(centroids["mahalle"], centroids["boylam"]))

# WGS84 lon/lat -> Web Mercator (EPSG:3857)
def lonlat_to_mercator(lon, lat):
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    return tr.transform(lon, lat)

# Convert all coordinates
def to_mercator_df(df, lon_col=None, lat_col=None):
    if lon_col is None:
        lon_col = "Boylam" if "Boylam" in df.columns else "boylam"
    if lat_col is None:
        lat_col = "Enlem" if "Enlem" in df.columns else "enlem"
    out = df.copy()
    xs, ys = [], []
    for _, r in out.iterrows():
        x, y = lonlat_to_mercator(r[lon_col], r[lat_col])
        xs.append(x); ys.append(y)
    out["x_3857"] = xs
    out["y_3857"] = ys
    return out

mevcut_m = to_mercator_df(mevcut)
aday_m = to_mercator_df(adaylar)
sel_m = to_mercator_df(sel)

# Mahalle centroids
mh_list = centroids["mahalle"].tolist()
mh_lons = centroids["boylam"].values
mh_lats = centroids["enlem"].values
mh_x, mh_y = [], []
for lon, lat in zip(mh_lons, mh_lats):
    x, y = lonlat_to_mercator(lon, lat)
    mh_x.append(x); mh_y.append(y)
mh_x = np.array(mh_x); mh_y = np.array(mh_y)

# Population (for circle size)
nufus = pd.read_excel(DATA / "mahalle_nufus.xlsx")
pop_col = "nufus_2024" if "nufus_2024" in nufus.columns else "nufus"
mh_to_pop = dict(zip(nufus["mahalle"], nufus[pop_col]))
mh_pop = np.array([mh_to_pop.get(m, 5000) for m in mh_list])

# Risk for color
mh_to_risk = dict(zip(risk["mahalle"], risk["risk_score"]))
mh_risk = np.array([mh_to_risk.get(m, 0) for m in mh_list])

# Shelter demand
mh_to_shelter = {}
if shelter is not None:
    mh_to_shelter = dict(zip(shelter["mahalle"], shelter["hane_ihtiyaci"]))
mh_shelter = np.array([mh_to_shelter.get(m, 0) for m in mh_list])

# ---------------------------------------------------------------------------
# 800m radius in meters, then transform to degrees offset
# ---------------------------------------------------------------------------
RADIUS_M = 800.0

# Compute a bbox with padding
all_x = list(mevcut_m["x_3857"]) + list(aday_m["x_3857"]) + list(mh_x)
all_y = list(mevcut_m["y_3857"]) + list(aday_m["y_3857"]) + list(mh_y)
pad = 1500  # meters
xmin, xmax = min(all_x) - pad, max(all_x) + pad
ymin, ymax = min(all_y) - pad, max(all_y) + pad

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 12))

# 1. Basemap (OSM)
try:
    cx.add_basemap(ax, crs="EPSG:3857",
                   source=cx.providers.OpenStreetMap.Mapnik,
                   zoom=14, alpha=0.85)
except Exception as e:
    print(f"[WARN] Basemap failed: {e}; using blank")

# 2. Mahalle centroids (size by population, color by shelter need)
if mh_shelter.sum() > 0:
    sizes = 80 + 600 * mh_pop / mh_pop.max()
    sc = ax.scatter(mh_x, mh_y, s=sizes, c=mh_shelter, cmap="YlOrRd",
                    alpha=0.6, edgecolor="black", linewidth=1.2, zorder=3)
    cbar = plt.colorbar(sc, ax=ax, fraction=0.025, pad=0.01, shrink=0.6)
    cbar.set_label("Barınma İhtiyacı (hane)", fontsize=10)
else:
    sizes = 80 + 600 * mh_pop / mh_pop.max()
    sc = ax.scatter(mh_x, mh_y, s=sizes, c=mh_risk, cmap="YlOrRd",
                    alpha=0.6, edgecolor="black", linewidth=1.2, zorder=3)
    cbar = plt.colorbar(sc, ax=ax, fraction=0.025, pad=0.01, shrink=0.6)
    cbar.set_label("Risk Skoru", fontsize=10)

# Label mahalle names
for i, m in enumerate(mh_list):
    short = m.replace(" DEVLET ORMANI", "").replace(" TEPE ORMANI", "")[:14]
    ax.text(mh_x[i], mh_y[i] + 350, short, fontsize=7.5,
            ha="center", color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.6, pad=1),
            zorder=4)

# 3. Existing 12 containers (blue squares + dashed 800m circles)
ax.scatter(mevcut_m["x_3857"], mevcut_m["y_3857"],
           marker="s", s=140, c="dodgerblue", edgecolor="navy", linewidth=1.5,
           zorder=5, label="Mevcut 12 konteyner")
for _, r in mevcut_m.iterrows():
    circ = plt.Circle((r["x_3857"], r["y_3857"]), RADIUS_M,
                      fill=False, edgecolor="dodgerblue", linestyle="--",
                      linewidth=1, alpha=0.7, zorder=4)
    ax.add_patch(circ)

# 4. Selected 8 new sites (red stars + solid 800m circles)
ax.scatter(sel_m["x_3857"], sel_m["y_3857"],
           marker="*", s=520, c="crimson", edgecolor="darkred", linewidth=2,
           zorder=6, label="Yeni 8 konteyner (önerilen)")
for _, r in sel_m.iterrows():
    circ = plt.Circle((r["x_3857"], r["y_3857"]), RADIUS_M,
                      fill=True, facecolor="crimson", edgecolor="darkred",
                      linewidth=1.5, alpha=0.15, zorder=5)
    ax.add_patch(circ)

# 5. Labels for selected
for _, r in sel_m.iterrows():
    sid = int(r["S_No"])
    mh = r["Mahalle"][:12]
    ax.annotate(f"S{sid}\n{mh}",
                xy=(r["x_3857"], r["y_3857"]),
                xytext=(8, 8), textcoords="offset points",
                fontsize=8, fontweight="bold", color="darkred",
                bbox=dict(facecolor="white", edgecolor="darkred", alpha=0.85, pad=1.5),
                zorder=7)

# Limits
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

# Axes off (basemap shows geography)
ax.set_xticks([]); ax.set_yticks([])
ax.set_title("Sultanbeyli - 8 Yeni Konteyner Konum Önerisi (AHP+TOPSIS+FCM+0-1 IP)\n"
             "OpenStreetMap bazlı harita - 800m yarıçap, mahalle renk = barınma ihtiyacı (hane)",
             fontsize=13, fontweight="bold", pad=12)

# Scale bar (rough, 1 km)
scale_x_start = xmin + 200
scale_x_end = scale_x_start + 1000
scale_y = ymin + 200
ax.plot([scale_x_start, scale_x_end], [scale_y, scale_y],
        color="black", linewidth=3, zorder=8)
ax.text((scale_x_start + scale_x_end) / 2, scale_y + 60, "1 km",
        ha="center", fontsize=10, fontweight="bold", zorder=8)
ax.plot([scale_x_start, scale_x_start], [scale_y - 30, scale_y + 30],
        color="black", linewidth=2, zorder=8)
ax.plot([scale_x_end, scale_x_end], [scale_y - 30, scale_y + 30],
        color="black", linewidth=2, zorder=8)

# North arrow (top-right)
n_x, n_y = xmax - 400, ymax - 400
ax.annotate("N", xy=(n_x, n_y), xytext=(n_x, n_y - 700),
            arrowprops=dict(facecolor="black", width=4, headwidth=12),
            ha="center", fontsize=14, fontweight="bold", zorder=8)

# Legend
legend_elements = [
    Line2D([0], [0], marker="s", color="w", markerfacecolor="dodgerblue",
           markeredgecolor="navy", markersize=11, label="Mevcut 12 konteyner"),
    Line2D([0], [0], marker="*", color="w", markerfacecolor="crimson",
           markeredgecolor="darkred", markersize=18, label="Yeni 8 konteyner (seçilen)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="lightgray",
           markeredgecolor="black", alpha=0.6, markersize=10,
           label="Mahalle merkezi (boyut = nüfus)"),
    mpatches.Patch(facecolor="crimson", edgecolor="darkred", alpha=0.15,
                   label="Yeni konteyner 800m etki alanı"),
    mpatches.Patch(facecolor="none", edgecolor="dodgerblue", linestyle="--",
                   label="Mevcut konteyner 800m etki alanı"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=9,
          framealpha=0.95, edgecolor="black")

ax.text(0.01, 0.01,
        "Kaynak: OSM (Mapnik) baz harita + İBB Deprem Raporu (Tablo 5-4) + AYDES",
        transform=ax.transAxes, fontsize=8, color="dimgray")

plt.tight_layout()
plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print(f"[OK] {OUT_PNG}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")

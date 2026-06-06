# -*- coding: utf-8 -*-
"""
16_selection_map_web.py
Real web-map (CartoDB Positron + OSM) overlay of container positions
and 800m coverage. EPSG:3857 (Web Mercator) for accurate scaling.
No anchor-based affine guessing - all coords projected exactly.

Layers (bottom -> top):
  1. CartoDB Positron basemap (gray, low-saturation - good for thesis)
  2. Mahalle centroids: size = population, color = shelter need (Table 5-4)
  3. Existing 12: blue squares + 800m dashed
  4. Selected 8: red stars + 800m filled
  5. Labels: S_No + Mahalle, staggered with leader lines
  6. Legend + 1 km scale bar + N arrow
  7. Inset: 17-mahalle outline of Sultanbeyli

Output: output/final/selection_map_web.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
import contextily as cx
from pyproj import Transformer

ROOT = Path("D:/IE492")
RES = ROOT / "output" / "results"
FINAL = ROOT / "output" / "final"
DATA = ROOT / "output" / "data"
OUT_PNG = FINAL / "selection_map_web.png"

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
adaylar = pd.read_excel(DATA / "adaylar.xlsx")
mevcut = pd.read_excel(DATA / "mevcut_12.xlsx")
risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
sel = pd.read_excel(RES / "selection_Baseline_hard.xlsx")
shelter = pd.read_excel(RES / "shelter_demand.xlsx") if (RES / "shelter_demand.xlsx").exists() else None

centroids = pd.read_excel(RES / "mahalle_centroids.xlsx")
centroids["mahalle"] = centroids["mahalle_norm"]
# Forest mahalles (TEFERRUC TEPE ORMANI, SALGAMLI DEVLET ORMANI) lack
# coords because they are non-residential. Estimate from IBB Sekil 3-1 visual
# position (eastern forest and southern forest in Sultanbeyli).
FOREST_OVERRIDES = {
    "TEFERRUC TEPE ORMANI":   (40.948, 29.290),  # east-central forest
    "SALGAMLI DEVLET ORMANI": (40.930, 29.260),  # south forest
}
for m, (lat, lon) in FOREST_OVERRIDES.items():
    mask = centroids["mahalle"] == m
    if mask.any():
        centroids.loc[mask, "enlem"] = lat
        centroids.loc[mask, "boylam"] = lon
# Drop any remaining NaN rows
centroids = centroids.dropna(subset=["enlem", "boylam"]).reset_index(drop=True)
mh_list = centroids["mahalle"].tolist()
mh_lat = centroids["enlem"].values
mh_lon = centroids["boylam"].values

nufus = pd.read_excel(DATA / "mahalle_nufus.xlsx")
pop_col = "nufus_2024" if "nufus_2024" in nufus.columns else "nufus"
mh_to_pop = dict(zip(nufus["mahalle"], nufus[pop_col]))
mh_pop = np.array([mh_to_pop.get(m, 5000) for m in mh_list])

mh_to_risk = dict(zip(risk["mahalle"], risk["risk_score"]))
mh_risk = np.array([mh_to_risk.get(m, 0) for m in mh_list])

mh_to_shelter = dict(zip(shelter["mahalle"], shelter["hane_ihtiyaci"])) if shelter is not None else {}
mh_shelter = np.array([mh_to_shelter.get(m, 0) for m in mh_list])

# ---------------------------------------------------------------------------
# Reproject lon/lat -> Web Mercator (EPSG:3857)
# ---------------------------------------------------------------------------
tr = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def project(df, lon_col=None, lat_col=None):
    lon_c = lon_col or ("Boylam" if "Boylam" in df.columns else "boylam")
    lat_c = lat_col or ("Enlem" if "Enlem" in df.columns else "enlem")
    xs, ys = tr.transform(df[lon_c].values, df[lat_c].values)
    out = df.copy()
    out["x_3857"] = xs; out["y_3857"] = ys
    return out

mevcut_m = project(mevcut)
sel_m = project(sel)
aday_m = project(adaylar)
mh_x, mh_y = tr.transform(mh_lon, mh_lat)

# ---------------------------------------------------------------------------
# Bbox (with 1.2 km padding around all markers)
# ---------------------------------------------------------------------------
RADIUS_M = 800.0
all_x = np.concatenate([mevcut_m["x_3857"], aday_m["x_3857"], mh_x])
all_y = np.concatenate([mevcut_m["y_3857"], aday_m["y_3857"], mh_y])
pad = 1200
xmin, xmax = all_x.min() - pad, all_x.max() + pad
ymin, ymax = all_y.min() - pad, all_y.max() + pad
print(f"Bbox: x[{xmin:.0f}, {xmax:.0f}] y[{ymin:.0f}, {ymax:.0f}]")
print(f"Width/height: {(xmax-xmin)/1000:.2f} km x {(ymax-ymin)/1000:.2f} km")

# ---------------------------------------------------------------------------
# Label staggering: 8-direction radial fan from cluster centroid
# ---------------------------------------------------------------------------
def assign_offsets(df, key_x="x_3857", key_y="y_3857"):
    coords = np.column_stack([df[key_x].values, df[key_y].values])
    cx, cy = coords[:, 0].mean(), coords[:, 1].mean()
    dists = np.sqrt(((coords - [cx, cy]) ** 2).sum(axis=1))
    OFFSETS = [
        ( 60, -60), ( 90, -30), ( 90,  30), ( 60,  60),
        (-60,  60), (-90,  30), (-90, -30), (-60, -60),
    ]
    order = np.argsort(dists)
    used = [False] * len(OFFSETS)
    out = [None] * len(coords)
    for new_i, orig_i in enumerate(order):
        dx, dy = coords[orig_i] - [cx, cy]
        ang = np.degrees(np.arctan2(dy, dx))
        slot = int(((ang + 180) / 45)) % 8
        if used[slot]:
            free = [j for j, u in enumerate(used) if not u]
            slot = min(free, key=lambda j: min((j - slot) % 8, (slot - j) % 8))
        used[slot] = True
        out[orig_i] = OFFSETS[slot]
    return out

off_sel = assign_offsets(sel_m)

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(15, 13))
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

# 1. Basemap - explicit bounds2img + imshow (more reliable than add_basemap)
tr_back = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
lon_min, lat_min = tr_back.transform(xmin, ymin)
lon_max, lat_max = tr_back.transform(xmax, ymax)
print(f"Basemap bbox lon/lat: ({lon_min:.4f}, {lat_min:.4f}) - ({lon_max:.4f}, {lat_max:.4f})")
src_used = None

def is_blank_tile(img, white_pct_threshold=0.995):
    """Return True if tile is mostly white (i.e. failed/blocked download)."""
    arr = np.asarray(img)
    if arr.ndim == 2:
        return (arr > 240).mean() > white_pct_threshold
    rgb = arr[..., :3]
    return ((rgb > 240).all(axis=-1)).mean() > white_pct_threshold

SOURCES = [
    (cx.providers.OpenStreetMap.HOT, 14),
    (cx.providers.CartoDB.Voyager, 14),
    (cx.providers.OpenTopoMap, 14),
    (cx.providers.CartoDB.Positron, 14),
    (cx.providers.Esri.WorldImagery, 14),
    (cx.providers.OpenStreetMap.Mapnik, 14),
]
for src, z in SOURCES:
    try:
        img, ext = cx.bounds2img(lon_min, lat_min, lon_max, lat_max,
                                 zoom=z, source=src, ll=True)
        if is_blank_tile(img):
            print(f"  {src} returned blank/white tiles, trying next source")
            continue
        ax.imshow(img, extent=[ext[0], ext[2], ext[1], ext[3]],
                  alpha=0.85, zorder=1, interpolation="bilinear")
        src_used = f"{src} (zoom={z})"
        print(f"Basemap rendered: {src_used} | shape={img.shape}")
        break
    except Exception as e:
        print(f"  source failed ({src}): {e}")

if src_used is None:
    print("WARNING: no basemap source succeeded; using plain white background")

# 2. Mahalle centroids: size = pop, color = shelter need
if mh_shelter.sum() > 0:
    sizes = 80 + 600 * mh_pop / mh_pop.max()
    sc = ax.scatter(mh_x, mh_y, s=sizes, c=mh_shelter, cmap="YlOrRd",
                    alpha=0.55, edgecolor="black", linewidth=1.0, zorder=3)
    cbar = plt.colorbar(sc, ax=ax, fraction=0.025, pad=0.01, shrink=0.6)
    cbar.set_label("Barınma ihtiyacı (hane)", fontsize=10)
else:
    sizes = 80 + 600 * mh_pop / mh_pop.max()
    sc = ax.scatter(mh_x, mh_y, s=sizes, c=mh_risk, cmap="YlOrRd",
                    alpha=0.55, edgecolor="black", linewidth=1.0, zorder=3)
    cbar = plt.colorbar(sc, ax=ax, fraction=0.025, pad=0.01, shrink=0.6)
    cbar.set_label("Risk Skoru", fontsize=10)

# Mahalle name labels (above each centroid)
for i, m in enumerate(mh_list):
    short = m.replace(" DEVLET ORMANI", "").replace(" TEPE ORMANI", "")[:14]
    ax.text(mh_x[i], mh_y[i] + 220, short, fontsize=7.5, ha="center",
            color="black", zorder=4,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1))

# 3. Existing 12: blue squares + dashed 800m circles
ax.scatter(mevcut_m["x_3857"], mevcut_m["y_3857"],
           marker="s", s=120, c="dodgerblue", edgecolor="navy", linewidth=1.5,
           zorder=5, label="Mevcut 12 konteyner")
for _, r in mevcut_m.iterrows():
    ax.add_patch(plt.Circle((r["x_3857"], r["y_3857"]), RADIUS_M,
                            fill=False, edgecolor="dodgerblue", linestyle="--",
                            linewidth=1, alpha=0.7, zorder=4))

# 4. Selected 8: red stars + filled 800m circles
ax.scatter(sel_m["x_3857"], sel_m["y_3857"],
           marker="*", s=500, c="crimson", edgecolor="darkred", linewidth=2,
           zorder=6, label="Yeni 8 konteyner (seçilen)")
for _, r in sel_m.iterrows():
    ax.add_patch(plt.Circle((r["x_3857"], r["y_3857"]), RADIUS_M,
                            fill=True, facecolor="crimson", edgecolor="darkred",
                            linewidth=1.5, alpha=0.18, zorder=5))

# 5. Staggered labels with leader lines
for (_, r), (ox, oy) in zip(sel_m.iterrows(), off_sel):
    sid = int(r["S_No"])
    mh = r["Mahalle"].replace(" DEVLET ORMANI", "").replace(" TEPE ORMANI", "")[:12]
    px, py = r["x_3857"], r["y_3857"]
    lx, ly = px + ox, py + oy
    ax.add_patch(FancyArrowPatch((px, py), (lx, ly), arrowstyle="-",
                                 color="darkred", linewidth=0.7, alpha=0.75,
                                 zorder=6))
    ax.text(lx, ly, f"S{sid} {mh}", fontsize=8.5, fontweight="bold",
            color="darkred", ha="center", va="center", zorder=7,
            bbox=dict(facecolor="white", edgecolor="darkred",
                      alpha=0.92, pad=1.5, linewidth=0.8))

# Scale bar (1 km)
sb_x0 = xmin + 250
sb_x1 = sb_x0 + 1000
sb_y = ymin + 250
ax.plot([sb_x0, sb_x1], [sb_y, sb_y], color="black", linewidth=3.5, zorder=8)
ax.plot([sb_x0, sb_x0], [sb_y - 50, sb_y + 50], color="black", linewidth=2, zorder=8)
ax.plot([sb_x1, sb_x1], [sb_y - 50, sb_y + 50], color="black", linewidth=2, zorder=8)
ax.text((sb_x0 + sb_x1) / 2, sb_y + 80, "1 km", ha="center", fontsize=10,
        fontweight="bold", zorder=8,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1))

# North arrow
n_x, n_y = xmax - 500, ymax - 500
ax.annotate("", xy=(n_x, n_y), xytext=(n_x, n_y - 1000),
            arrowprops=dict(facecolor="black", width=5, headwidth=14,
                            edgecolor="black"), zorder=8)
ax.text(n_x, n_y + 200, "N", ha="center", fontsize=14, fontweight="bold", zorder=8)

# Legend
legend_elements = [
    Line2D([0], [0], marker="s", color="w", markerfacecolor="dodgerblue",
           markeredgecolor="navy", markersize=11, label="Mevcut 12 konteyner"),
    Line2D([0], [0], marker="*", color="w", markerfacecolor="crimson",
           markeredgecolor="darkred", markersize=18, label="Yeni 8 konteyner (seçilen)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="lightgray",
           markeredgecolor="black", alpha=0.6, markersize=10,
           label="Mahalle merkezi (boyut = nüfus)"),
    mpatches.Patch(facecolor="crimson", edgecolor="darkred", alpha=0.18,
                   label="Yeni konteyner 800m etki alanı"),
    mpatches.Patch(facecolor="none", edgecolor="dodgerblue", linestyle="--",
                   label="Mevcut konteyner 800m etki alanı"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=9,
          framealpha=0.95, edgecolor="black", bbox_to_anchor=(0.01, 0.01))

ax.set_xticks([]); ax.set_yticks([])
ax.set_title("Sultanbeyli - 8 Yeni + 12 Mevcut Konteyner Konum Önerisi\n"
             "AHP+TOPSIS+FCM+0-1 IP | Gerçek Web Haritası (EPSG:3857) | 800m yarıçap",
             fontsize=13, fontweight="bold", pad=12)
ax.text(0.5, 0.005,
        "Baz harita: OSM HOT/Voyager (Web Mercator EPSG:3857) | Risk: İBB Deprem Raporu (Tablo 5-2/5-4) | "
        "Not: 'HAMIDIYE' etiketli konteynerler İBB idari sınırına göre konumlandırılmıştır; "
        "alanın büyük kısmı Teferrüç Tepe Ormanı olup yüksek risklidir.",
        transform=ax.transAxes, fontsize=7, color="dimgray", ha="center")

plt.tight_layout()
plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print(f"[OK] {OUT_PNG}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")

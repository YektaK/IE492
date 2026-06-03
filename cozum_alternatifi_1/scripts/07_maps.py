# -*- coding: utf-8 -*-
"""
07_maps.py - Web map (OSM basemap) for alternative solution
ÇÖZÜM ALTERNATİFİ 1

Mirrors src/16_selection_map_web.py but with alternative selection.
Since solver selected the SAME 8 sites under alt C4, the map is identical
in geometry. Mahalle centroids colored by İBB shelter need (hane).
"""
import math
import unicodedata
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import contextily as ctx
from pyproj import Transformer

ROOT = Path("D:/IE492/cozum_alternatifi_1")
DATA = ROOT / "data"
RES = ROOT / "results"
MAPS = ROOT / "maps"
MAPS.mkdir(parents=True, exist_ok=True)

FOREST_OVERRIDES = {
    "TEFERRUC TEPE ORMANI": (40.948, 29.290),
    "SALGAMLI DEVLET ORMANI": (40.930, 29.260),
}

to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def norm(s):
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())


if __name__ == "__main__":
    print("=" * 60)
    print(f"Web map - Çözüm Alternatifi 1")
    print("=" * 60)

    aday = pd.read_excel(DATA / "adaylar.xlsx")
    mev = pd.read_excel(DATA / "mevcut_12.xlsx")
    sel = pd.read_excel(RES / "selection_Baseline_hard.xlsx")
    centroids = pd.read_excel(RES / "mahalle_centroids.xlsx")
    shelter = pd.read_excel(DATA / "mahalle_barinma_ihtiyaci.xlsx")

    sel_ids = set(sel["S_No"].tolist())
    sel_df = aday[aday["S_No"].isin(sel_ids)].copy()
    print(f"Selected sites: {sorted(sel_ids)}")

    centroids["_mh"] = centroids["mahalle_norm"].apply(norm)
    forest_mask = centroids["enlem"].isna()
    for i, r in centroids[forest_mask].iterrows():
        key = r["_mh"]
        for fk, (lat, lon) in FOREST_OVERRIDES.items():
            if norm(fk) == key:
                centroids.at[i, "enlem"] = lat
                centroids.at[i, "boylam"] = lon
                print(f"  Override forest: {r['mahalle_display']} -> ({lat}, {lon})")
                break

    valid = centroids.dropna(subset=["enlem", "boylam"])
    lat_min, lat_max = valid["enlem"].min() - 0.005, valid["enlem"].max() + 0.005
    lon_min, lon_max = valid["boylam"].min() - 0.005, valid["boylam"].max() + 0.005
    print(f"BBox: lat [{lat_min:.4f}, {lat_max:.4f}]  lon [{lon_min:.4f}, {lon_max:.4f}]")

    fig, ax = plt.subplots(figsize=(13, 13))
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    mev_x, mev_y = transformer.transform(mev["boylam"].values, mev["enlem"].values)
    ax.scatter(mev_x, mev_y, marker="s", s=110, c="royalblue", edgecolors="navy",
               linewidths=1.2, label="Mevcut 12 konteyner", zorder=4)
    for x, y, lab in zip(mev_x, mev_y, mev["container_no"].astype(str)):
        ax.annotate(f"M{lab}", (x, y), xytext=(4, 4), textcoords="offset points",
                    fontsize=7, color="navy", zorder=5)

    sel_x, sel_y = transformer.transform(sel_df["Boylam"].values, sel_df["Enlem"].values)
    ax.scatter(sel_x, sel_y, marker="*", s=320, c="crimson", edgecolors="darkred",
               linewidths=1.5, label="Yeni seçilen 8 konteyner", zorder=5)
    for x, y, sid in zip(sel_x, sel_y, sel_df["S_No"].astype(str)):
        ax.annotate(f"S{sid}", (x, y), xytext=(8, 8), textcoords="offset points",
                    fontsize=10, fontweight="bold", color="darkred", zorder=6)

    for x, y in zip(mev_x, mev_y):
        circle = plt.Circle((x, y), 800, fill=False, edgecolor="royalblue",
                            linestyle="--", alpha=0.35, linewidth=1)
        ax.add_patch(circle)
    for x, y in zip(sel_x, sel_y):
        circle = plt.Circle((x, y), 800, fill=False, edgecolor="crimson",
                            linestyle="-", alpha=0.6, linewidth=1.3)
        ax.add_patch(circle)

    centroids_valid = centroids.dropna(subset=["enlem", "boylam"])
    cen_x, cen_y = transformer.transform(centroids_valid["boylam"].values, centroids_valid["enlem"].values)
    shelter_map = dict(zip(shelter["mahalle"].apply(norm), shelter["hane_ihtiyaci"]))
    shelter_vals = np.array([shelter_map.get(norm(m), 0) for m in centroids_valid["mahalle_display"]])
    sizes = 60 + shelter_vals / max(shelter_vals.max(), 1) * 280
    sc = ax.scatter(cen_x, cen_y, s=sizes, c=shelter_vals, cmap="YlOrRd",
                    edgecolors="black", linewidths=0.7, alpha=0.85,
                    label="Mahalle (boyut = barınma ihtiyacı)", zorder=3)
    plt.colorbar(sc, ax=ax, label="İBB Barınma İhtiyacı (hane)", shrink=0.7)

    for x, y, name, hane in zip(cen_x, cen_y, centroids_valid["mahalle_display"], shelter_vals):
        short = str(name).replace(" DEVLET ORMANI", "").replace(" TEPE ORMANI", "").replace(" AYDOSU", "")
        if hane > 0 or "OR" in str(name).upper():
            ax.annotate(short, (x, y), xytext=(0, -14), textcoords="offset points",
                        ha="center", fontsize=7, color="black",
                        bbox=dict(boxstyle="round,pad=0.18", facecolor="white", alpha=0.75, edgecolor="none"))

    try:
        ctx.add_basemap(ax, crs="EPSG:3857", source=ctx.providers.OpenStreetMap.Mapnik, zoom=14)
    except Exception as e:
        print(f"  Basemap uyari: {e}")

    x_min, x_max = transformer.transform(lon_min, lat_min)[0], transformer.transform(lon_max, lat_max)[0]
    y_min, y_max = transformer.transform(lon_min, lat_min)[1], transformer.transform(lon_max, lat_max)[1]
    pad_x = (x_max - x_min) * 0.05
    pad_y = (y_max - y_min) * 0.05
    ax.set_xlim(x_min - pad_x, x_max + pad_x)
    ax.set_ylim(y_min - pad_y, y_max + pad_y)
    ax.set_xlabel("Easting (m, EPSG:3857)")
    ax.set_ylabel("Northing (m, EPSG:3857)")

    ax.set_title("Sultanbeyli - Konteyner Optimizasyonu (Çözüm Alternatifi 1)\n"
                 "C4 = İBB Tablo 5-4 Barınma İhtiyacı  •  Mevcut 12 (mavi) + Yeni 8 (kırmızı)  •  σ = 800 m",
                 fontsize=11, fontweight="bold")

    bar_x0 = x_min - pad_x + (x_max - x_min) * 0.02
    bar_y = y_min - pad_y + (y_max - y_min) * 0.04
    ax.plot([bar_x0, bar_x0 + 1000], [bar_y, bar_y], color="black", linewidth=3)
    ax.text(bar_x0 + 500, bar_y + (y_max - y_min) * 0.015, "1 km",
            ha="center", fontsize=9, fontweight="bold")

    ax.annotate("N", xy=(x_max - pad_x * 0.3, y_max - pad_y * 0.3),
                xytext=(x_max - pad_x * 0.3, y_max - pad_y * 0.7),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="black"),
                ha="center", fontsize=12, fontweight="bold")

    ax.legend(loc="lower right", fontsize=8, framealpha=0.85)
    ax.grid(visible=True, linestyle=":", alpha=0.3)
    plt.tight_layout()
    out = MAPS / "selection_map_CA1.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")

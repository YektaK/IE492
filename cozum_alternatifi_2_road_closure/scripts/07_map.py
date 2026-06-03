# -*- coding: utf-8 -*-
"""
07_map.py
==========================================================
Cozum Alternatifi 2: Secim haritasi.
- 12 mevcut + 8 yeni konteyner
- Mahalle merkezleri P(yol acik) ile renklendirilmis
- Coverage cemberleri 800m
- Web Mercator (EPSG:3857)
==========================================================
"""
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import unicodedata

ROOT = Path("D:/IE492")
CA2 = ROOT / "cozum_alternatifi_2_road_closure"
RES = CA2 / "results"
MAPS = CA2 / "maps"
MAPS.mkdir(parents=True, exist_ok=True)

def norm(s):
    if s is None: return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())

# Web Mercator forward (lon/lat -> x/y in meters)
LON0 = math.radians(29.25)
def lonlat_to_xy(lon, lat):
    x = math.radians(lon) * 6378137.0
    y = math.log(math.tan(math.pi/4 + math.radians(lat)/2)) * 6378137.0
    return x, y

def main():
    sel = pd.read_excel(RES / "selection_Baseline_hard_CA2.xlsx", sheet_name="Selected_8")
    mev = pd.read_excel(ROOT / "output" / "data" / "mevcut_12.xlsx")
    road = pd.read_excel(CA2 / "data" / "mahalle_data_road.xlsx")
    centroids = pd.read_excel(RES / "mahalle_centroids_CA2.xlsx")
    centroids = centroids.rename(columns={"mahalle_norm": "_mh", "mahalle_display": "mahalle",
                                          "enlem": "Enlem", "boylam": "Boylam"})
    road["_mh"] = road["mahalle"].apply(norm)
    road_map = road.set_index("_mh")["P_road_open"].to_dict()
    centroids["P_road"] = centroids["_mh"].map(road_map)
    centroids = centroids.dropna(subset=["Enlem", "Boylam"])

    fig, ax = plt.subplots(figsize=(13, 11))
    # 12 mevcut
    for _, r in mev.iterrows():
        x, y = lonlat_to_xy(float(r["boylam"]), float(r["enlem"]))
        ax.add_patch(plt.Rectangle((x-30, y-30), 60, 60, color="steelblue", alpha=0.7, zorder=3))
        circ = plt.Circle((x, y), 800, color="steelblue", fill=False, linestyle="--", alpha=0.4, zorder=2)
        ax.add_patch(circ)
    # 8 secili
    for _, r in sel.iterrows():
        x, y = lonlat_to_xy(float(r["Boylam"]), float(r["Enlem"]))
        ax.plot(x, y, marker="*", color="crimson", markersize=22, markeredgecolor="k",
                markeredgewidth=0.8, zorder=5)
        circ = plt.Circle((x, y), 800, color="crimson", fill=False, linestyle="-", alpha=0.5, zorder=4)
        ax.add_patch(circ)
        ax.annotate(f"S{int(r['S_No'])}", (x, y), xytext=(8, 8), textcoords="offset points",
                    fontsize=9, fontweight="bold", color="crimson",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7, edgecolor="crimson"))
    # Mahalle merkezleri (P_road ile renk)
    sc = ax.scatter([lonlat_to_xy(float(r["Boylam"]), float(r["Enlem"]))[0] for _, r in centroids.iterrows()],
                     [lonlat_to_xy(float(r["Boylam"]), float(r["Enlem"]))[1] for _, r in centroids.iterrows()],
                     c=centroids["P_road"], cmap="RdYlGn", vmin=0.93, vmax=1.0,
                     s=180, edgecolor="k", linewidth=0.8, zorder=4)
    for _, r in centroids.iterrows():
        x, y = lonlat_to_xy(float(r["Boylam"]), float(r["Enlem"]))
        ax.annotate(r["mahalle"][:14], (x, y), xytext=(0, 12), textcoords="offset points",
                    fontsize=8, ha="center",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.6, edgecolor="none"))
    plt.colorbar(sc, ax=ax, label="P(yol acik)", fraction=0.04)
    ax.set_xlabel("Web Mercator X (m)", fontsize=10)
    ax.set_ylabel("Web Mercator Y (m)", fontsize=10)
    ax.set_title("Sultanbeyli - CA2 Secim Haritasi (Yol Kapanma Entegreli)\n"
                  "Mavi: mevcut 12 konteyner, Kirmizi yildiz: yeni secilen 8 konteyner",
                  fontsize=12, fontweight="bold")
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out = MAPS / "CA2_selection_map.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
07_map_CA4.py
==========================================================
Cozum Alternatifi 3: Secim haritasi (matplotlib tabanli).
20 secili konteyner + mevcut 12 + mahalle risk overlay.
==========================================================
"""
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path("D:/IE492")
CA4 = ROOT / "cozum_alternatifi_4_full_reloc_sb"
RES = CA4 / "results"
MAPS = CA4 / "maps"
MAPS.mkdir(parents=True, exist_ok=True)

def normalize_mahalle(s):
    if s is None: return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u00a0", " ").replace("\u2019", "'")
    return " ".join(s.split())

if __name__ == "__main__":
    print("=" * 60)
    print("STEP 7: CA4 Secim Haritasi")
    print("=" * 60)

    sel = pd.read_excel(RES / "selection_Baseline_hard_CA4.xlsx", sheet_name="Selected_20")
    centroids = pd.read_excel(RES / "mahalle_centroids_CA4.xlsx")
    centroids["mahalle_norm"] = centroids["mahalle_norm"].astype(str)
    road = pd.read_excel(CA4 / "data" / "mahalle_data_CA4.xlsx")
    road["mahalle"] = road["mahalle"].apply(normalize_mahalle)

    fig, ax = plt.subplots(figsize=(12, 11))
    # Mahalle P(road) arka plan
    cmap_bg = plt.cm.RdYlGn
    for _, r in centroids.iterrows():
        if pd.isna(r["enlem"]) or pd.isna(r["boylam"]): continue
        mh_norm = r["mahalle_norm"]
        p = road[road["mahalle"] == mh_norm]["P_road_open"]
        if len(p) == 0: continue
        p = float(p.iloc[0])
        color = cmap_bg(0.0 if p < 0.94 else (0.5 if p < 0.98 else 1.0))
        ax.scatter(r["boylam"], r["enlem"], c=[color], s=200, alpha=0.6, edgecolor="k", linewidth=0.5)

    # 20 secili konteyner
    for _, r in sel.iterrows():
        ax.scatter(r["Boylam"], r["Enlem"], marker="*", s=200, c="red",
                   edgecolor="k", linewidth=0.7, zorder=5)
        ax.annotate(f"S{int(r['S_No'])}", (r["Boylam"], r["Enlem"]),
                    fontsize=7, xytext=(5, 5), textcoords="offset points", zorder=6)

    ax.set_xlabel("Boylam")
    ax.set_ylabel("Enlem")
    ax.set_title("CA4 - Tam Yer Degisikligi (SB, 20 konteyner)", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out = MAPS / "CA4_selection_map.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")


# -*- coding: utf-8 -*-
"""
15_ibbsh_overlay.py
Overlays container positions and 800m coverage circles on
IBB Sekil 3-1 (base map) and Sekil 5-2 (heavy damage heatmap),
plus a side-by-side composite for jury view.

Pixel-to-coordinate mapping uses 3 anchor points (mahal labels)
to compute an affine transformation. Approximate but consistent.

Outputs (all under output/final/):
  selection_on_ibb_sekil_3_1.png
  selection_on_ibb_sekil_5_2.png
  selection_on_ibb_composite.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch, FancyArrowPatch
from matplotlib.lines import Line2D
from PIL import Image

ROOT = Path("D:/IE492")
RES = ROOT / "output" / "results"
FINAL = ROOT / "output" / "final"
IBBMAPS = FINAL / "ibbsh_maps"

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
adaylar = pd.read_excel(ROOT / "output" / "data" / "adaylar.xlsx")
mevcut = pd.read_excel(ROOT / "output" / "data" / "mevcut_12.xlsx")
sel = pd.read_excel(RES / "selection_Baseline_hard.xlsx")
sel_ids = sel["S_No"].tolist()

centroids = pd.read_excel(RES / "mahalle_centroids.xlsx")
centroids["mahalle"] = centroids["mahalle_norm"]
mh_to_lat = dict(zip(centroids["mahalle"], centroids["enlem"]))
mh_to_lon = dict(zip(centroids["mahalle"], centroids["boylam"]))

# ---------------------------------------------------------------------------
# Anchor-based pixel mapping (3 points, exact affine)
# ---------------------------------------------------------------------------
ANCHORS_3_1 = {
    "MIMAR SINAN":      (40.973, 29.272,  640,  375),
    "ABDURRAHMANGAZI":  (40.960, 29.255,  415, 1175),
    "NECIP FAZIL":      (40.934, 29.272,  650, 1800),
}
ANCHORS_5_2 = {
    "MIMAR SINAN":      (40.973, 29.272,  750,  430),
    "ABDURRAHMANGAZI":  (40.960, 29.255,  485, 1390),
    "NECIP FAZIL":      (40.934, 29.272,  755, 2120),
}

def fit_affine(anchors):
    pts = np.array([(lat, lon, px, py) for (lat, lon, px, py) in anchors.values()])
    A = np.column_stack([pts[:, 0], pts[:, 1], np.ones(3)])
    a_lat, a_lon, c = np.linalg.solve(A, pts[:, 2])
    d_lat, e_lon, f = np.linalg.solve(A, pts[:, 3])
    return (a_lat, a_lon, c, d_lat, e_lon, f)

def to_px(lat, lon, params):
    a_lat, a_lon, c, d_lat, e_lon, f = params
    return (a_lat * lat + a_lon * lon + c,
            d_lat * lat + e_lon * lon + f)

params_3_1 = fit_affine(ANCHORS_3_1)
params_5_2 = fit_affine(ANCHORS_5_2)

# ---------------------------------------------------------------------------
# Pixels per km (use anchor-derived horizontal + vertical)
# ---------------------------------------------------------------------------
def ppkm(params, lat0=40.955, lon0=29.273):
    px0, py0 = to_px(lat0, lon0, params)
    px_n, py_n = to_px(lat0 + 1/111.0, lon0, params)  # 1 km N
    px_e, py_e = to_px(lat0, lon0 + 1/85.3, params)  # 1 km E
    dpx_n = ((px_n - px0)**2 + (py_n - py0)**2) ** 0.5
    dpx_e = ((px_e - px0)**2 + (py_e - py0)**2) ** 0.5
    return (dpx_n + dpx_e) / 2.0

ppkm_3_1 = ppkm(params_3_1)
ppkm_5_2 = ppkm(params_5_2)
RADIUS_M = 800.0
radius_px_3_1 = ppkm_3_1 * RADIUS_M / 1000.0
radius_px_5_2 = ppkm_5_2 * RADIUS_M / 1000.0
print(f"Pixels per km - 3-1: {ppkm_3_1:.1f}, 5-2: {ppkm_5_2:.1f}")
print(f"800m radius (px) - 3-1: {radius_px_3_1:.1f}, 5-2: {radius_px_5_2:.1f}")

# ---------------------------------------------------------------------------
# Label placement: assign unique offset directions to avoid collisions
# ---------------------------------------------------------------------------
# Sort selected sites by pixel-x then by pixel-y; assign angular offsets around
# the cluster centroid so labels fan out radially.
def assign_label_offsets(sel_df, params, radius_px):
    coords = []
    for _, r in sel_df.iterrows():
        px, py = to_px(r["Enlem"], r["Boylam"], params)
        coords.append((px, py))
    coords = np.array(coords)
    cx, cy = coords[:, 0].mean(), coords[:, 1].mean()
    # Distance of each point from cluster centroid in pixel space
    dists = np.sqrt((coords[:, 0] - cx)**2 + (coords[:, 1] - cy)**2)
    # Label offset in pixels (8-direction fanning)
    OFFSETS = [( 0, -32), ( 30, -16), ( 30,  16), ( 0,  32),
               (-30,  16), (-30, -16), ( 45,   0), (-45,   0)]
    order = np.argsort(dists)  # farthest first → keeps inner labels clean
    slot_used = [False] * len(OFFSETS)
    offsets = []
    for i in order:
        px, py = coords[i]
        dx, dy = px - cx, py - cy
        ang = np.degrees(np.arctan2(dy, dx))
        # Choose slot by angle quadrant
        slot = int(((ang + 180) / 45)) % 8
        if slot_used[slot]:
            # Find nearest free
            free = [j for j, u in enumerate(slot_used) if not u]
            slot = min(free, key=lambda j: min((j - slot) % 8, (slot - j) % 8))
        slot_used[slot] = True
        offsets.append(OFFSETS[slot])
    # Restore original order
    out = [None] * len(offsets)
    for new_i, orig_i in enumerate(order):
        out[orig_i] = offsets[new_i]
    return out

off_3_1 = assign_label_offsets(sel, params_3_1, radius_px_3_1)
off_5_2 = assign_label_offsets(sel, params_5_2, radius_px_5_2)

# ---------------------------------------------------------------------------
# Overlay function
# ---------------------------------------------------------------------------
def overlay_ibbsh(base_img_path, params, radius_px, out_path, title, offsets):
    fig, ax = plt.subplots(figsize=(11, 15))
    img = Image.open(base_img_path)
    ax.imshow(img, extent=[0, img.size[0], img.size[1], 0])

    # Existing 12 (blue squares + 800m dashed)
    for _, r in mevcut.iterrows():
        px, py = to_px(r["enlem"], r["boylam"], params)
        ax.add_patch(Circle((px, py), radius_px, fill=False,
                            edgecolor="dodgerblue", linestyle="--",
                            linewidth=1.2, alpha=0.85, zorder=3))
        ax.scatter([px], [py], marker="s", s=110, c="dodgerblue",
                   edgecolor="navy", linewidth=1.5, zorder=5)

    # Selected 8 (red stars + 800m filled)
    for (_, r), (ox, oy) in zip(sel.iterrows(), offsets):
        px, py = to_px(r["Enlem"], r["Boylam"], params)
        ax.add_patch(Circle((px, py), radius_px, facecolor="crimson",
                            edgecolor="darkred", linewidth=1.5,
                            alpha=0.22, zorder=4))
        ax.scatter([px], [py], marker="*", s=460, c="crimson",
                   edgecolor="darkred", linewidth=2, zorder=6)
        mh = str(r["Mahalle"]).replace(" DEVLET ORMANI", "").replace(" TEPE ORMANI", "")[:12]
        label = f"S{int(r['S_No'])} {mh}"
        lx, ly = px + ox, py + oy
        # Leader line
        ax.add_patch(FancyArrowPatch((px, py), (lx, ly),
                                     arrowstyle="-", color="darkred",
                                     linewidth=0.7, alpha=0.7, zorder=6))
        ax.text(lx, ly, label, fontsize=8.5, fontweight="bold",
                color="darkred", ha="center", va="center", zorder=7,
                bbox=dict(facecolor="white", edgecolor="darkred",
                          alpha=0.92, pad=1.5, linewidth=0.8))

    # Legend
    legend_elements = [
        Line2D([0], [0], marker="s", color="w", markerfacecolor="dodgerblue",
               markeredgecolor="navy", markersize=11, label="Mevcut 12 konteyner"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor="crimson",
               markeredgecolor="darkred", markersize=18, label="Yeni 8 konteyner"),
        Patch(facecolor="crimson", edgecolor="darkred", alpha=0.22,
              label="800m kapsama alani (yeni)"),
        Patch(facecolor="none", edgecolor="dodgerblue", linestyle="--",
              label="800m kapsama alani (mevcut)"),
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=9,
              framealpha=0.95, edgecolor="black", bbox_to_anchor=(0.02, 0.02))
    ax.set_xlim(0, img.size[0])
    ax.set_ylim(img.size[1], 0)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
    ax.text(0.5, 0.985,
            "Kaynak baz harita: IBB Deprem Raporu (Sultanbeyli Ilcesi)",
            transform=ax.transAxes, fontsize=8, color="dimgray", ha="center")
    plt.tight_layout()
    plt.savefig(out_path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] {out_path}")

overlay_ibbsh(
    IBBMAPS / "image23.jpeg", params_3_1, radius_px_3_1,
    FINAL / "selection_on_ibb_sekil_3_1.png",
    "Sultanbeyli - IBB Sekil 3-1 Baz Harita Uzerinde 8 Yeni + 12 Mevcut Konteyner\n"
    "(800m etki alani, mahalle sinirlari IBB raporundan alindi)",
    off_3_1,
)

overlay_ibbsh(
    IBBMAPS / "image59.jpeg", params_5_2, radius_px_5_2,
    FINAL / "selection_on_ibb_sekil_5_2.png",
    "Sultanbeyli - IBB Sekil 5-2 Cok Agir Hasarli Bina Dagilimi Uzerinde Secim\n"
    "(Mw=7.5 senaryo, 800m etki alani)",
    off_5_2,
)

# ---------------------------------------------------------------------------
# Side-by-side composite (Şekil 3-1 + Şekil 5-2) for jury view
# ---------------------------------------------------------------------------
def composite(base_left, params_l, rad_l, base_right, params_r, rad_r, out):
    fig, axes = plt.subplots(1, 2, figsize=(22, 15))
    for ax, base, params, radius_px, title, offsets in [
        (axes[0], base_left, params_l, rad_l,
         "Sol: IBB Sekil 3-1 Baz Harita + 8 Yeni + 12 Mevcut Konteyner", off_3_1),
        (axes[1], base_right, params_r, rad_r,
         "Sag: IBB Sekil 5-2 Cok Agir Hasarli Bina Dagilimi + Secim", off_5_2),
    ]:
        img = Image.open(base)
        ax.imshow(img, extent=[0, img.size[0], img.size[1], 0])
        for _, r in mevcut.iterrows():
            px, py = to_px(r["enlem"], r["boylam"], params)
            ax.add_patch(Circle((px, py), radius_px, fill=False,
                                edgecolor="dodgerblue", linestyle="--",
                                linewidth=1.0, alpha=0.85, zorder=3))
            ax.scatter([px], [py], marker="s", s=80, c="dodgerblue",
                       edgecolor="navy", linewidth=1.3, zorder=5)
        for (_, r), (ox, oy) in zip(sel.iterrows(), offsets):
            px, py = to_px(r["Enlem"], r["Boylam"], params)
            ax.add_patch(Circle((px, py), radius_px, facecolor="crimson",
                                edgecolor="darkred", linewidth=1.3,
                                alpha=0.22, zorder=4))
            ax.scatter([px], [py], marker="*", s=380, c="crimson",
                       edgecolor="darkred", linewidth=2, zorder=6)
            mh = str(r["Mahalle"]).replace(" DEVLET ORMANI", "").replace(" TEPE ORMANI", "")[:12]
            lx, ly = px + ox, py + oy
            ax.add_patch(FancyArrowPatch((px, py), (lx, ly),
                                         arrowstyle="-", color="darkred",
                                         linewidth=0.6, alpha=0.7, zorder=6))
            ax.text(lx, ly, f"S{int(r['S_No'])} {mh}", fontsize=7.5,
                    fontweight="bold", color="darkred", ha="center", va="center",
                    zorder=7,
                    bbox=dict(facecolor="white", edgecolor="darkred",
                              alpha=0.92, pad=1.2, linewidth=0.7))
        ax.set_xlim(0, img.size[0])
        ax.set_ylim(img.size[1], 0)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, fontsize=11, fontweight="bold")
    legend_elements = [
        Line2D([0], [0], marker="s", color="w", markerfacecolor="dodgerblue",
               markeredgecolor="navy", markersize=11, label="Mevcut 12 konteyner"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor="crimson",
               markeredgecolor="darkred", markersize=18, label="Yeni 8 konteyner"),
        Patch(facecolor="crimson", edgecolor="darkred", alpha=0.22,
              label="800m kapsama alani (yeni)"),
        Patch(facecolor="none", edgecolor="dodgerblue", linestyle="--",
              label="800m kapsama alani (mevcut)"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=4,
               fontsize=10, framealpha=0.95, edgecolor="black",
               bbox_to_anchor=(0.5, -0.01))
    fig.suptitle(
        "Sultanbeyli Ilcesi Konteyner Konum Secimi - IBB Deprem Raporu Uzerine Yerlestirme",
        fontsize=14, fontweight="bold", y=0.995)
    plt.tight_layout(rect=[0, 0.02, 1, 0.98])
    plt.savefig(out, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] {out}")

composite(
    IBBMAPS / "image23.jpeg", params_3_1, radius_px_3_1,
    IBBMAPS / "image59.jpeg", params_5_2, radius_px_5_2,
    FINAL / "selection_on_ibb_composite.png",
)

print("\nDone. Three overlays written to output/final/.")

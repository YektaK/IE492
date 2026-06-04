"""
06_map.py - CA7 secim haritalari ve L_i profili gorseli (v2)

Ciktilar:
  - selection_map_CA7a_MEV_g1.png
  - selection_map_CA7a_NMEV_g1.png
  - gamma_sweep_curves_NMEV.png
  - gamma_sweep_curves_MEV.png
  - L_i_profile_chart.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "D:/IE492"
CA = "cozum_alternatifi_7_risk_proportional_coverage"
DATA_DIR = os.path.join(ROOT, CA, "data")
RESULTS_DIR = os.path.join(ROOT, CA, "results")
MAPS_DIR = os.path.join(ROOT, CA, "maps")
os.makedirs(MAPS_DIR, exist_ok=True)

mu_df = pd.read_excel(os.path.join(DATA_DIR, "mu_aday.xlsx"))
mevcut_df = pd.read_excel(os.path.join(DATA_DIR, "mevcut_12.xlsx"))
risk_df = pd.read_excel(os.path.join(DATA_DIR, "mahalle_risk_CA7.xlsx"))
cov_sweep = pd.read_excel(os.path.join(RESULTS_DIR, "coverage_per_mahalle_gamma_sweep.xlsx"))
centroids = pd.read_excel(os.path.join(ROOT, "output/results/mahalle_centroids.xlsx"))
L_profile = pd.read_excel(os.path.join(RESULTS_DIR, "L_i_profile.xlsx"))
adaylar = pd.read_excel(os.path.join(ROOT, "output/data/adaylar.xlsx"))

sel_mev_path = os.path.join(RESULTS_DIR, "selected_gamma_1.0.xlsx")
sel_nmev_path = os.path.join(RESULTS_DIR, "selected_gamma_1.0_nmev.xlsx")
sel_mev = pd.read_excel(sel_mev_path) if os.path.exists(sel_mev_path) else None
sel_nmev = pd.read_excel(sel_nmev_path) if os.path.exists(sel_nmev_path) else None


def _norm(s):
    if not isinstance(s, str):
        return s
    return (s.replace("\u0130", "I").replace("\u0131", "I")
             .replace("\u00dc", "U").replace("\u00fc", "U")
             .replace("\u015e", "S").replace("\u015f", "S")
             .replace("\u00c7", "C").replace("\u00e7", "C")
             .replace("\u00d6", "O").replace("\u00f6", "O")
             .replace("\u011e", "G").replace("\u011f", "G").upper())


risk_col = None
for c in risk_df.columns:
    if "risk" in c.lower():
        risk_col = c
        break
mah_col = None
for c in risk_df.columns:
    if "mahalle" in c.lower():
        mah_col = c
        break
risk_map = {str(r[mah_col]).upper(): float(r[risk_col]) for _, r in risk_df.iterrows()}

cent_idx_col = None
for c in ("mahalle_norm", "Mahalle_norm"):
    if c in centroids.columns:
        cent_idx_col = c
        break
cent = centroids.set_index(cent_idx_col) if cent_idx_col else centroids.copy()
lat_col = "enlem" if "enlem" in cent.columns else ("Enlem" if "Enlem" in cent.columns else None)
lon_col = "boylam" if "boylam" in cent.columns else ("Boylam" if "Boylam" in cent.columns else None)

lat_map = {}
lon_map = {}
for m, row in cent.iterrows():
    if lat_col and lon_col and pd.notna(row[lat_col]) and pd.notna(row[lon_col]):
        lat_map[str(m).upper()] = float(row[lat_col])
        lon_map[str(m).upper()] = float(row[lon_col])

def get_xy_from_sno(df):
    if df is None or "S_No" not in df.columns:
        return None, None, []
    xs, ys, lbls = [], [], []
    for _, r in df.iterrows():
        s = int(r["S_No"])
        match = adaylar[adaylar["S_No"] == s] if "S_No" in adaylar.columns else None
        if match is None or len(match) == 0:
            continue
        lat = float(match.iloc[0]["enlem"]) if "enlem" in adaylar.columns else None
        lon = float(match.iloc[0]["boylam"]) if "boylam" in adaylar.columns else None
        if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
            continue
        xs.append(lon)
        ys.append(lat)
        lbls.append(f"S{s}")
    return xs, ys, lbls

def get_mevcut_xy(df):
    xs, ys, lbls = [], [], []
    for _, r in df.iterrows():
        lat = float(r["enlem"]) if "enlem" in df.columns and pd.notna(r["enlem"]) else None
        lon = float(r["boylam"]) if "boylam" in df.columns and pd.notna(r["boylam"]) else None
        if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
            continue
        mah = str(r.get("mahalle", "")).upper()
        if "ORMAN" in mah or "FOREST" in mah:
            continue
        xs.append(lon)
        ys.append(lat)
        lbls.append(str(r.get("container_no", "")))
    return xs, ys, lbls


fig, ax = plt.subplots(figsize=(14, 10))
mappable_set = False
if lat_col and lon_col:
    valid_idx = [m for m in cent.index if m in lat_map]
    if valid_idx:
        xs = [lon_map[m] for m in valid_idx]
        ys = [lat_map[m] for m in valid_idx]
        Rs = [risk_map.get(str(m).upper(), 0.0) for m in valid_idx]
        sc = ax.scatter(xs, ys, s=220, c=Rs, cmap="Reds", alpha=0.75, edgecolors="black", zorder=3)
        for m, x, y in zip(valid_idx, xs, ys):
            ax.text(x, y + 0.0010, str(m)[:12], fontsize=7, ha="center", zorder=4)
        plt.colorbar(sc, ax=ax, label="R risk")
        mappable_set = True

xs, ys, lbls = get_mevcut_xy(mevcut_df)
if xs:
    ax.scatter(xs, ys, s=70, c="lightblue", marker="s", edgecolors="navy", label="Mevcut 12", zorder=4)

xs, ys, lbls = get_xy_from_sno(sel_mev)
if xs:
    ax.scatter(xs, ys, s=220, c="blue", marker="*", edgecolors="white", label="CA7a secim (gamma=1.0, MEV)", zorder=6)
    for x, y, l in zip(xs, ys, lbls):
        ax.text(x, y + 0.0007, l, fontsize=7, ha="center", color="blue", weight="bold", zorder=7)

ax.set_title("CA7 - Risk-Orantili Coverage (MEV gamma=1.0)")
ax.set_xlabel("Boylam")
ax.set_ylabel("Enlem")
ax.legend(loc="lower right")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(MAPS_DIR, "selection_map_CA7a_MEV_g1.png"), dpi=120, bbox_inches="tight")
plt.close()
print("[OK] selection_map_CA7a_MEV_g1.png")

fig, ax = plt.subplots(figsize=(14, 10))
mappable_set = False
if lat_col and lon_col:
    valid_idx = [m for m in cent.index if m in lat_map]
    if valid_idx:
        xs = [lon_map[m] for m in valid_idx]
        ys = [lat_map[m] for m in valid_idx]
        Rs = [risk_map.get(str(m).upper(), 0.0) for m in valid_idx]
        sc = ax.scatter(xs, ys, s=220, c=Rs, cmap="Reds", alpha=0.75, edgecolors="black", zorder=3)
        for m, x, y in zip(valid_idx, xs, ys):
            ax.text(x, y + 0.0010, str(m)[:12], fontsize=7, ha="center", zorder=4)
        plt.colorbar(sc, ax=ax, label="R risk")
        mappable_set = True

xs, ys, lbls = get_mevcut_xy(mevcut_df)
if xs:
    ax.scatter(xs, ys, s=70, c="lightblue", marker="s", edgecolors="navy", label="Mevcut 12 (referans)", zorder=4)

xs, ys, lbls = get_xy_from_sno(sel_nmev)
if xs:
    ax.scatter(xs, ys, s=220, c="purple", marker="*", edgecolors="white", label="CA7a NMEV (gamma=1.0)", zorder=6)
    for x, y, l in zip(xs, ys, lbls):
        ax.text(x, y + 0.0007, l, fontsize=7, ha="center", color="purple", weight="bold", zorder=7)

ax.set_title("CA7 - Risk-Orantili Coverage (NMEV gamma=1.0)")
ax.set_xlabel("Boylam")
ax.set_ylabel("Enlem")
ax.legend(loc="lower right")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(MAPS_DIR, "selection_map_CA7a_NMEV_g1.png"), dpi=120, bbox_inches="tight")
plt.close()
print("[OK] selection_map_CA7a_NMEV_g1.png")


def plot_curves(use_mev, fname, title):
    gammas = sorted(cov_sweep["gamma"].unique())
    sub_mode = cov_sweep[cov_sweep["use_mevcut"] == use_mev]
    if sub_mode.empty:
        return
    base = sub_mode[sub_mode["gamma"] == gammas[0]].sort_values("R_risk", ascending=False)
    if base.empty:
        return
    fig, ax = plt.subplots(figsize=(12, 7))
    for g in gammas:
        sub = sub_mode[sub_mode["gamma"] == g].sort_values("R_risk", ascending=False)
        ax.plot(range(len(sub)), sub["coverage"].values, marker="o", label=f"gamma={g:.2f}")
    ax.set_xticks(range(len(base)))
    ax.set_xticklabels([str(m)[:10] for m in base["mahalle"]], rotation=70, fontsize=7)
    ax.set_ylabel("Coverage")
    ax.set_xlabel("Mahalle (R_risk azalan)")
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(MAPS_DIR, fname), dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] {fname}")


plot_curves(False, "gamma_sweep_curves_NMEV.png", "CA7a NMEV - Coverage profili (mahalle R azalan)")
plot_curves(True, "gamma_sweep_curves_MEV.png", "CA7a MEV - Coverage profili (mahalle R azalan)")

g1 = L_profile[L_profile["gamma"] == 1.0].copy().sort_values("R_risk", ascending=False)
if not g1.empty:
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(g1))
    rmax = g1["R_risk"].max()
    ax.bar(x - 0.2, g1["R_risk"], width=0.4, color="#d62728", label="R_risk", alpha=0.8)
    ax.bar(x + 0.2, g1["L_i_proportional"] * rmax, width=0.4, color="#1f77b4", label="L_i * R_max (hedef coverage)", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([str(m)[:12] for m in g1["mahalle"]], rotation=60, fontsize=8)
    ax.set_ylabel("Skor")
    ax.set_title("CA7 L_i Proportional (gamma=1.0) - Mahalle Risk vs Hedef Alt Sinir")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(MAPS_DIR, "L_i_profile_chart.png"), dpi=120, bbox_inches="tight")
    plt.close()
    print("[OK] L_i_profile_chart.png")

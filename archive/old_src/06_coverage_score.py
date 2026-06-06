"""
06_coverage_score.py
Compute the 'Total Coverage Score (%)' (mahalle-level, threshold=0.50)
- Baseline: 12 mevcut konteyner
- Proposed: 12 mevcut + 8 secilen yeni

Update reporting.md and the final Excel workbook.
"""
from __future__ import annotations
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
from pathlib import Path

OUT = Path(r"D:\IE492\output")
RESULTS = OUT / "results"
FINAL = OUT / "final"
FIGURES = OUT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# ---------- Load FCM mu matrices ----------
mu_mevcut_raw = pd.read_excel(RESULTS / "mu_mevcut.xlsx", index_col=0)   # 12 x 20 (has container_no, mahalle, 17 mu, _TOTAL_mu)
mu_aday_raw   = pd.read_excel(RESULTS / "mu_aday.xlsx",   index_col=0)   # 141 x ?
selected  = pd.read_excel(RESULTS / "selection_Baseline_hard.xlsx")  # has S_No column
mahalle   = pd.read_excel(OUT / "data" / "mahalle_risk.xlsx")
risk      = mahalle.set_index("mahalle")["risk_score"].to_dict()

# Extract only the 17 mahalle mu columns (drop label cols + _TOTAL_mu)
NON_MAHALLE = {"container_no", "mahalle", "_id", "_TOTAL_mu", "S_No", "Alan_Adi", "Mahalle", "AYDES_ID", "Il", "Ilce", "Enlem", "Boylam", "Arazi_Kullanimi", "Su", "WC", "Jenerator", "AFIS_Konteyner_Sayisi", "Kamera", "Haberlesme", "Oncelik_Derecesi", "Su_bin", "WC_bin", "Jen_bin", "Kamera_bin", "AFIS_count"}
def extract_mu(df):
    cols = [c for c in df.columns if c not in NON_MAHALLE]
    return df[cols].astype(float)
mu_mevcut = extract_mu(mu_mevcut_raw)
mu_aday   = extract_mu(mu_aday_raw)
print("mu_mevcut shape:", mu_mevcut.shape, "cols:", list(mu_mevcut.columns)[:3], "...", list(mu_mevcut.columns)[-2:])
print("mu_aday shape:", mu_aday.shape)

mahalleler = list(mu_mevcut.columns)  # 17 mahalle names
S = selected["S_No"].astype(int).tolist()
print("Selected 8 S_No:", S)

# Map S_No -> mu_aday row using S_No column
S_int = [int(s) for s in S]
S_mask = mu_aday_raw["S_No"].astype(int).isin(S_int)
print(f"Found {S_mask.sum()} selected sites in mu_aday: {mu_aday_raw.loc[S_mask, 'S_No'].astype(int).tolist()}")
mu_aday_selected = mu_aday_raw.loc[S_mask].drop(columns=[c for c in NON_MAHALLE if c in mu_aday_raw.columns]).astype(float)
print("mu_aday_selected shape:", mu_aday_selected.shape)

# ---------- Build per-mahalle MAX mu (binary coverage) ----------
# Baseline: only 12 mevcut
max_mu_baseline = mu_mevcut.max(axis=0)   # Series indexed by mahalle

# Proposed: mevcut UNION selected 8 aday
mu_combined = pd.concat([mu_mevcut, mu_aday_selected], axis=0)
max_mu_proposed = mu_combined.max(axis=0)

THRESHOLD = 0.50
n_total = len(mahalleler)
n_covered_baseline = int((max_mu_baseline >= THRESHOLD).sum())
n_covered_proposed = int((max_mu_proposed >= THRESHOLD).sum())
pct_baseline = n_covered_baseline / n_total * 100
pct_proposed = n_covered_proposed / n_total * 100
uplift_pp    = pct_proposed - pct_baseline

# Exclude the 2 forest mahalleler (they have 0 candidates, structurally 0)
URBAN = [m for m in mahalleler if m not in ("TEFERRUC TEPE ORMANI", "SALGAMLI DEVLET ORMANI")]
n_urban     = len(URBAN)
n_b_urban   = int((max_mu_baseline[URBAN] >= THRESHOLD).sum())
n_p_urban   = int((max_mu_proposed[URBAN] >= THRESHOLD).sum())
pct_b_urban = n_b_urban / n_urban * 100
pct_p_urban = n_p_urban / n_urban * 100

# Mean coverage (continuous) - more informative
mean_b = max_mu_baseline.mean()
mean_p = max_mu_proposed.mean()

# Per-mahalle detailed table
rows = []
for m in mahalleler:
    mb = float(max_mu_baseline[m])
    mp = float(max_mu_proposed[m])
    r  = float(risk.get(m, 0.0))
    rows.append({
        "Mahalle": m,
        "Risk_R_pct": round(r, 1),
        "Mu_Baseline_12": round(mb, 3),
        "Mu_Proposed_20": round(mp, 3),
        "Covered_Baseline": mb >= THRESHOLD,
        "Covered_Proposed": mp >= THRESHOLD,
        "Improvement": round(mp - mb, 3),
    })
df_det = pd.DataFrame(rows).sort_values(["Covered_Baseline", "Covered_Proposed", "Mu_Proposed_20"], ascending=[True, True, False]).reset_index(drop=True)

print("\n=== TOTAL COVERAGE SCORE ===")
print(f"District-wide  (17 mahalle):  Baseline 12 = {pct_baseline:5.1f}%  ({n_covered_baseline}/17)")
print(f"                              Proposed 20 = {pct_proposed:5.1f}%  ({n_covered_proposed}/17)")
print(f"                              Uplift      = +{uplift_pp:.1f} pp")
print(f"Urban-only     (15 mahalle):  Baseline 12 = {pct_b_urban:5.1f}%  ({n_b_urban}/15)")
print(f"                              Proposed 20 = {pct_p_urban:5.1f}%  ({n_p_urban}/15)")
print(f"Mean μ (continuous):           Baseline    = {mean_b:.3f}")
print(f"                              Proposed    = {mean_p:.3f}")

# ---------- Save detailed per-mahalle table ----------
df_det.to_excel(RESULTS / "coverage_score_detailed.xlsx", index=False)

# ---------- Build a comparison figure ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Bar chart of max_mu per mahalle: baseline vs proposed
order = df_det.sort_values("Mu_Proposed_20", ascending=False)["Mahalle"].tolist()
baseline_vals = [df_det.set_index("Mahalle").loc[m, "Mu_Baseline_12"] for m in order]
proposed_vals = [df_det.set_index("Mahalle").loc[m, "Mu_Proposed_20"] for m in order]

fig, ax = plt.subplots(figsize=(13, 7))
x = np.arange(len(order))
w = 0.4
b1 = ax.bar(x - w/2, baseline_vals, w, label=f"Mevcut 12 (Toplam Skor: {pct_baseline:.1f}%)", color="#bdc3c7", edgecolor="#7f8c8d")
b2 = ax.bar(x + w/2, proposed_vals, w, label=f"Önerilen 20 (Toplam Skor: {pct_proposed:.1f}%)", color="#27ae60", edgecolor="#1e8449")

# Threshold line
ax.axhline(THRESHOLD, color="#e74c3c", linestyle="--", linewidth=1.5, label=f"Eşik μ = {THRESHOLD}")

# Highlight critical mahalleler
for i, m in enumerate(order):
    if risk.get(m, 0) >= 25:
        ax.text(x[i], 1.02, "*", ha="center", va="bottom", fontsize=14, color="#c0392b", fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(order, rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Maksimum FCM Üyelik Katsayısı (μ)", fontsize=11)
ax.set_title(f"Sultanbeyli Mahalle Bazında Kapsama Karşılaştırması\n12 Mevcut Konteyner vs 20 Önerilen Konteyner (Eşik = {THRESHOLD})", fontsize=12, fontweight="bold")
ax.set_ylim(0, 1.15)
ax.legend(loc="upper right", fontsize=10)
ax.grid(axis="y", linestyle=":", alpha=0.5)

# Annotate uplift on right
ax.text(0.02, 0.96, f"İyileşme: +{uplift_pp:.1f} yüzde puan\nMahalle sayısı: {n_covered_baseline}/17 → {n_covered_proposed}/17",
        transform=ax.transAxes, fontsize=10, verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff9e6", edgecolor="#f39c12"))
plt.tight_layout()
fig.savefig(FIGURES / "toplam_kapsama_skoru.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"\nFigure saved: {FIGURES / 'toplam_kapsama_skoru.png'}")

# ---------- KPI summary as one-row df ----------
kpi = pd.DataFrame([{
    "Metrik": "Toplam Kapsama Skoru (17 mahalle, eşik μ≥0.50)",
    "Baseline 12": f"{pct_baseline:.1f}%",
    "Proposed 20": f"{pct_proposed:.1f}%",
    "Iyilesme_pp": f"+{uplift_pp:.1f}",
    "Kapsanan_Mahalle_Baseline": f"{n_covered_baseline}/17",
    "Kapsanan_Mahalle_Proposed": f"{n_covered_proposed}/17",
}, {
    "Metrik": "Toplam Kapsama Skoru (15 kentsel mahalle, eşik μ≥0.50)",
    "Baseline 12": f"{pct_b_urban:.1f}%",
    "Proposed 20": f"{pct_p_urban:.1f}%",
    "Iyilesme_pp": f"+{pct_p_urban - pct_b_urban:.1f}",
    "Kapsanan_Mahalle_Baseline": f"{n_b_urban}/15",
    "Kapsanan_Mahalle_Proposed": f"{n_p_urban}/15",
}, {
    "Metrik": "Ortalama FCM μ (sürekli, 17 mahalle)",
    "Baseline 12": f"{mean_b:.3f}",
    "Proposed 20": f"{mean_p:.3f}",
    "Iyilesme_pp": f"+{(mean_p-mean_b)*100:.1f}%",
    "Kapsanan_Mahalle_Baseline": "-",
    "Kapsanan_Mahalle_Proposed": "-",
}])
kpi.to_excel(RESULTS / "coverage_score_kpi.xlsx", index=False)
print("\nKPI summary saved.")
print(kpi.to_string(index=False))

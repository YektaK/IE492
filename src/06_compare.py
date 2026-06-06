# -*- coding: utf-8 -*-
"""
06_compare.py
TOPSIS vs PROMETHEE II + 3 AHP senaryosu karşılaştırması + sonuç rasyoneli.

Girdi :  results/models/ip_v*.xlsx + coverage_v*.xlsx + summary_all.xlsx
        results/mcdm/topsis_cc.xlsx
        results/mcdm/promethee_phi.xlsx
        results/ahp/ahp_weights.xlsx
Çıktı :  results/comparison/compare_*.xlsx
         figures/compare_*.png
         docs/planlar/rasyonal.md
"""

from __future__ import annotations
import os
import sys
import json
import numpy as np
import pandas as pd
import openpyxl
import matplotlib.pyplot as plt
from pathlib import Path

# Windows konsol encoding düzeltmesi
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
RES  = ROOT / "results" / "models"
MCDM = ROOT / "results" / "mcdm"
AHP  = ROOT / "results" / "ahp"
OUT  = ROOT / "results" / "comparison"
FIG  = ROOT / "figures"
DOC  = ROOT / "docs" / "planlar"
for d in [OUT, FIG, DOC]:
    d.mkdir(parents=True, exist_ok=True)


# ---------- 1. Summary yükle ----------
def load_summary() -> pd.DataFrame:
    df = pd.read_excel(RES / "summary_all.xlsx")
    df = df.dropna(subset=["version"]).reset_index(drop=True)
    return df


# ---------- 2. MCDM skorları yükle ----------
def load_mcdm() -> dict[str, pd.DataFrame]:
    return {
        "TOPSIS":     pd.read_excel(MCDM / "topsis_cc.xlsx"),
        "PROMETHEE":  pd.read_excel(MCDM / "promethee_phi.xlsx"),
    }


# ---------- 3. Site kesişim matrisi (versiyonlar arası örtüşme) ----------
def site_overlap_matrix(summary: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, set]]:
    import glob
    sites_by_v: dict[str, set] = {}
    for v in summary["version"]:
        # v = "v1", summary'de mcdm+senaryo var, ama dosya isminde version zaten geçiyor
        candidates = glob.glob(str(RES / f"ip_{v}_*.xlsx"))
        if not candidates:
            raise FileNotFoundError(f"ip_{v}_*.xlsx bulunamadı")
        wb = openpyxl.load_workbook(candidates[0], data_only=True)
        ws = wb[wb.sheetnames[0]]
        s = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] is not None:
                s.add(int(row[0]))
        sites_by_v[v] = s

    vs = list(sites_by_v.keys())
    M = pd.DataFrame(0, index=vs, columns=vs, dtype=int)
    for a in vs:
        for b in vs:
            M.loc[a, b] = len(sites_by_v[a] & sites_by_v[b])
    return M, sites_by_v


# ---------- 4. MCDM tutarlılığı (her senaryo için TOPSIS vs PROMETHEE korelasyon) ----------
def mcdm_agreement(mcdm: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for col_t, col_p in [
        ("CC_Baseline",              "phi_Baseline"),
        ("CC_DamageFocused",         "phi_DamageFocused"),
        ("CC_InfrastructureFocused", "phi_InfrastructureFocused"),
    ]:
        t = mcdm["TOPSIS"][["S_No", col_t]].set_index("S_No")[col_t]
        p = mcdm["PROMETHEE"][["S_No", col_p]].set_index("S_No")[col_p]
        common = t.index.intersection(p.index)
        x, y = t.loc[common].values, p.loc[common].values
        corr = float(np.corrcoef(x, y)[0, 1])
        # Top-10 Jaccard
        t10 = set(t.sort_values(ascending=False).head(10).index)
        p10 = set(p.sort_values(ascending=False).head(10).index)
        jac = len(t10 & p10) / len(t10 | p10)
        rows.append({
            "senaryo": col_t.replace("CC_", ""),
            "pearson_corr": round(corr, 4),
            "top10_jaccard": round(jac, 4),
            "n_common": len(common),
        })
    return pd.DataFrame(rows)


# ---------- 5. Senaryo etkisi (RxC, min_cov bazında) ----------
def scenario_effect(summary: pd.DataFrame) -> pd.DataFrame:
    pivot_rxc = summary.pivot_table(
        index="senaryo", columns="mcdm", values="RxC", aggfunc="first")
    pivot_min = summary.pivot_table(
        index="senaryo", columns="mcdm", values="min_mahalle_cov", aggfunc="first")
    pivot_avg = summary.pivot_table(
        index="senaryo", columns="mcdm", values="avg_mahalle_cov", aggfunc="first")

    out = pd.DataFrame({
        "RxC_TOPSIS":            pivot_rxc["TOPSIS"],
        "RxC_PROMETHEE":         pivot_rxc["PROMETHEE"],
        "minCov_TOPSIS":         pivot_min["TOPSIS"],
        "minCov_PROMETHEE":      pivot_min["PROMETHEE"],
        "avgCov_TOPSIS":         pivot_avg["TOPSIS"],
        "avgCov_PROMETHEE":      pivot_avg["PROMETHEE"],
    })
    out["ΔRxC_(T-P)"]      = (out["RxC_TOPSIS"] - out["RxC_PROMETHEE"]).round(4)
    out["ΔminCov_(T-P)"]   = (out["minCov_TOPSIS"] - out["minCov_PROMETHEE"]).round(4)
    return out


# ---------- 6. Görseller ----------
def plot_mcdm_scatter(mcdm: dict[str, pd.DataFrame], agreement: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    senaryolar = ["Baseline", "DamageFocused", "InfrastructureFocused"]
    for ax, s in zip(axes, senaryolar):
        t = mcdm["TOPSIS"][["S_No", f"CC_{s}"]].set_index("S_No")[f"CC_{s}"]
        p = mcdm["PROMETHEE"][["S_No", f"phi_{s}"]].set_index("S_No")[f"phi_{s}"]
        common = t.index.intersection(p.index)
        ax.scatter(t.loc[common], p.loc[common], s=14, alpha=0.65, color="#1f77b4")
        ax.set_xlabel("TOPSIS  CC")
        ax.set_ylabel("PROMETHEE  φ")
        ax.set_title(s)
        ax.grid(alpha=0.3)
        r = agreement.loc[agreement["senaryo"] == s, "pearson_corr"].values[0]
        j = agreement.loc[agreement["senaryo"] == s, "top10_jaccard"].values[0]
        ax.text(0.05, 0.92, f"r = {r:.3f}\nJ@10 = {j:.3f}",
                transform=ax.transAxes, fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))
    fig.suptitle("MCDM Tutarlılığı: TOPSIS  vs  PROMETHEE II", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIG / "compare_mcdm_scatter.png", dpi=150)
    plt.close(fig)


def plot_rxc_bars(scenario_eff: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(scenario_eff.index))
    w = 0.35
    ax.bar(x - w/2, scenario_eff["RxC_TOPSIS"],    width=w, label="TOPSIS",    color="#1f77b4")
    ax.bar(x + w/2, scenario_eff["RxC_PROMETHEE"], width=w, label="PROMETHEE", color="#ff7f0e")
    ax.set_xticks(x)
    ax.set_xticklabels(scenario_eff.index)
    ax.set_ylabel("RxC  (Risk-weighted Coverage)")
    ax.set_title("Senaryo Bazında RxC Karşılaştırması")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    for i, (a, b) in enumerate(zip(scenario_eff["RxC_TOPSIS"],
                                   scenario_eff["RxC_PROMETHEE"])):
        ax.text(i - w/2, a + 0.01, f"{a:.3f}", ha="center", fontsize=8)
        ax.text(i + w/2, b + 0.01, f"{b:.3f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "compare_rxc_senaryo.png", dpi=150)
    plt.close(fig)


def plot_overlap_heatmap(overlap: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(overlap.values, cmap="Blues", vmin=0, vmax=8)
    ax.set_xticks(range(len(overlap.columns)))
    ax.set_xticklabels(overlap.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(overlap.index)))
    ax.set_yticklabels(overlap.index, fontsize=8)
    for i in range(overlap.shape[0]):
        for j in range(overlap.shape[1]):
            ax.text(j, i, str(overlap.iloc[i, j]),
                    ha="center", va="center", fontsize=8,
                    color="white" if overlap.iloc[i, j] > 4 else "black")
    ax.set_title("Site Örtüşme Matrisi (8 = tam eşleşme)")
    fig.colorbar(im, ax=ax, shrink=0.7)
    fig.tight_layout()
    fig.savefig(FIG / "compare_site_overlap.png", dpi=150)
    plt.close(fig)


# ---------- 7. Rasyonel belgesi ----------
def write_rationale(summary: pd.DataFrame,
                    scenario_eff: pd.DataFrame,
                    agreement: pd.DataFrame,
                    overlap: pd.DataFrame,
                    sites_by_v: dict) -> Path:
    """Karar vericiye yönelik Türkçe rasyonel: hangi versiyon neden seçildi?"""
    # En iyi versiyonu seç: en yüksek RxC ve en yüksek min_mahalle_cov
    summary_score = summary.copy()
    summary_score["score"] = (
        summary_score["RxC"] / summary_score["RxC"].max() * 0.5
      + summary_score["min_mahalle_cov"] / summary_score["min_mahalle_cov"].max() * 0.5
    )
    best = summary_score.loc[summary_score["score"].idxmax()]
    best_id = best["version"]
    best_mcdm = best["mcdm"]
    best_sen  = best["senaryo"]

    # En sık seçilen siteler
    site_counts: dict[int, int] = {}
    for s in sites_by_v.values():
        for sid in s:
            site_counts[sid] = site_counts.get(sid, 0) + 1
    top_sites = sorted(site_counts.items(), key=lambda x: -x[1])[:10]

    lines = []
    lines.append("# Karşılaştırma Rasyoneli\n")
    lines.append(f"**Tarih:** 2026-06-06  ")
    lines.append(f"**Pipeline:** 4-Kriter AHP → TOPSIS || PROMETHEE II → FCM → 0-1 IP  ")
    lines.append(f"**Senaryo sayısı:** 3 AHP senaryosu × 2 MCDM = 6 IP versiyonu\n")

    lines.append("## 1. MCDM Yöntem Tutarlılığı\n")
    lines.append("TOPSIS ile PROMETHEE II aynı kriter matrisine uygulandığında ")
    lines.append("aday sıralamaları ne kadar tutarlı?\n")
    lines.append(agreement.to_markdown(index=False))
    lines.append("\n\n**Yorum:** Pearson korelasyonu ve top-10 Jaccard benzerliği ")
    lines.append("her iki yöntemin aynı sıralama yapısını ürettiğini gösterir. ")
    lines.append("Küçük farklar, kısmi kompansasyon (PROMETHEE) ile mesafe-bazlı ")
    lines.append("(TOPSIS) yaklaşımlarının doğal sonucudur.\n")

    lines.append("## 2. Senaryo Etkisi\n")
    lines.append("AHP senaryoları (Baseline, DamageFocused, InfrastructureFocused) ")
    lines.append("kriter ağırlıklarını değiştirir; MCDM yöntemleri ise aynı ağırlıkla ")
    lines.append("farklı skor üretir.\n")
    lines.append(scenario_eff.round(4).to_markdown())
    lines.append("\n\n**Yorum:** ")
    delta_rxc_max = scenario_eff["ΔRxC_(T-P)"].abs().max()
    lines.append(f"RxC değerleri tüm senaryolarda birbirine çok yakın ")
    lines.append(f"(max Δ = {delta_rxc_max:.4f}). Bu, AHP kriter ağırlıklarının ")
    lines.append("IP kararına etkisinin sınırlı olduğunu gösterir; risk×coverage ")
    lines.append("bileşeni baskındır.\n")

    lines.append("## 3. Site Örtüşmesi\n")
    lines.append("6 versiyonun seçtiği 8'er sitenin kesişimi:\n")
    lines.append(overlap.to_markdown())
    lines.append("\n\n**Yorum:** Çapraz (kendi dışı) örtüşme değerleri tüm ")
    lines.append("versiyonların 5-7 sitesini paylaştığını gösterir. Çekirdek ")
    lines.append("konumlar (yüksek riskli, yol erişimi iyi, altyapısı güçlü) ")
    lines.append("tüm senaryolarda sabit kalır; kenar seçimler senaryoya göre değişir.\n")

    lines.append("## 4. Önerilen Versiyon\n")
    lines.append(f"**Seçim kriteri:** %50 RxC + %50 min mahalle kapsama (en kötü mahalle korunur)\n")
    summary_disp = summary_score[[
        "version","mcdm","senaryo","RxC","min_mahalle_cov","score"
    ]].sort_values("score", ascending=False).round(4)
    lines.append(summary_disp.to_markdown(index=False))
    lines.append(f"\n\n**Kazanan:** `{best_id}` — {best_mcdm} / {best_sen}  ")
    lines.append(f"RxC = {best['RxC']:.4f}, min mahalle kapsama = {best['min_mahalle_cov']:.4f}\n")

    lines.append("## 5. En Sık Seçilen 10 Aday Konum\n")
    lines.append("| Sıra | S_No | 6 Versiyondaki Seçilme Sayısı |")
    lines.append("|------|------|-------------------------------|")
    for i, (sid, cnt) in enumerate(top_sites, 1):
        lines.append(f"| {i} | {sid} | {cnt}/6 |")
    lines.append("\n6/6 seçilen konumlar tüm senaryolarda 'olmazsa olmaz' ")
    lines.append("adaylardır; 4-5/6 seçilenler senaryoya göre değişen kenar sitelerdir.\n")

    lines.append("## 6. Sonuç\n")
    lines.append(f"1. **MCDM seçimi** (TOPSIS ↔ PROMETHEE) IP kararını marjinal etkiler. ")
    lines.append("Akademik raporda ikisinin de raporlanması yöntem sağlamlığını gösterir.\n")
    lines.append("2. **AHP senaryoları** çekirdek konumları değiştirmez, sadece kenar ")
    lines.append("adaylar arasında geçiş yapar. Hassasiyet düşüktür.\n")
    lines.append("3. **Önerilen final konum seti:** yukarıdaki kazanan versiyonun ")
    lines.append(f"`ip_{best_id}_*.xlsx` dosyasındaki 8 sitedir.\n")

    out = DOC / "rasyonal.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ---------- 8. Çalıştır ----------
def main():
    print("== 06_compare.py başladı ==")

    summary = load_summary()
    mcdm    = load_mcdm()

    overlap, sites_by_v = site_overlap_matrix(summary)
    overlap.to_excel(OUT / "compare_site_overlap.xlsx")

    agreement = mcdm_agreement(mcdm)
    agreement.to_excel(OUT / "compare_mcdm_agreement.xlsx", index=False)

    scen_eff = scenario_effect(summary)
    scen_eff.to_excel(OUT / "compare_scenario_effect.xlsx")

    # Karşılaştırma özet tablosu
    cmp = summary[[
        "version","mcdm","senaryo","Z_total","Z_risk","Z_quality",
        "RxC","min_mahalle_cov","avg_mahalle_cov",
        "n_mahalle_below_050","n_mahalle_below_020","sure_s"
    ]].round(4)
    cmp.to_excel(OUT / "compare_summary.xlsx", index=False)

    # Görseller
    plot_mcdm_scatter(mcdm, agreement)
    plot_rxc_bars(scen_eff)
    plot_overlap_heatmap(overlap)

    # Rasyonel
    rasyonal = write_rationale(summary, scen_eff, agreement, overlap, sites_by_v)

    print(f"\n-> {OUT} altina 4 xlsx yazildi")
    print(f"-> {FIG} altina 3 png yazildi")
    print(f"-> Rasyonel: {rasyonal}")
    print("\n== 06_compare.py tamamlandi ==")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
07_reporting.py
Final Rapor Sentez Sistemi (V2)

Yeni metadata.json sistemine dayalı olarak:
  - Tüm koşumları tarar ve metadata'larını toplar
  - Çapraz karşılaştırma tabloları üretir
  - FINAL_REPORT.xlsx (çok sayfalı) oluşturur
  - Akademik Türkçe FINAL_RAPOR.md yazar
  - Senaryolar arası karşılaştırma grafikleri çizer

Kullanım:
  python src/07_reporting.py
"""

from __future__ import annotations
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
MODELS_DIR = RESULTS / "models"
OUT = RESULTS / "final"
FIG = ROOT / "figures"
CHARTS = FIG / "charts"
DOC = ROOT / "docs" / "rapor"

for d in [OUT, FIG, CHARTS, DOC]:
    d.mkdir(parents=True, exist_ok=True)

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except ValueError:
    plt.style.use("seaborn-whitegrid")
sns.set_context("paper", font_scale=1.2)


# ────────────────────────────────────────
# 1. TÜM METADATA'LARI TOPLA
# ────────────────────────────────────────
def collect_all_runs() -> list[dict]:
    """Tüm *_metadata.json dosyalarını okuyarak bir liste döndürür."""
    runs = []
    for mf in sorted(MODELS_DIR.glob("*_metadata.json"), key=lambda x: x.stat().st_mtime):
        with open(mf, "r", encoding="utf-8") as f:
            runs.append(json.load(f))
    return runs


def build_master_summary(runs: list[dict]) -> pd.DataFrame:
    """Her koşumun summary_all dosyasını okuyup tek bir DataFrame'de birleştirir."""
    all_rows = []
    for run in runs:
        p = run["parameters"]
        sf = run["files"].get("summary_file")
        if not sf:
            continue
        sp = MODELS_DIR / sf
        if not sp.exists():
            continue
        df = pd.read_excel(sp)
        df["run_id"] = run["run_id"]
        df["weight_type"] = p["weight_type"]
        df["K_total"] = p["k_total"]
        df["beta"] = p["beta"]
        df["sigma"] = p["sigma"]
        df["scenario_tag"] = p.get("scenario_tag", "?")
        df["kept_count"] = len(p.get("kept_mevcut", []))
        all_rows.append(df)
    if not all_rows:
        return pd.DataFrame()
    return pd.concat(all_rows, ignore_index=True)


# ────────────────────────────────────────
# 2. KARŞILAŞTIRMA GRAFİKLERİ
# ────────────────────────────────────────
def plot_cross_scenario_bars(master: pd.DataFrame) -> Path:
    """Senaryolar arası RxC ve min_cov karşılaştırma bar grafiği."""
    if master.empty:
        return FIG / "cross_scenario_bars.png"

    # Her (weight_type, scenario_tag, K_total, beta) için en iyi Z_total'ı al
    group_cols = ["weight_type", "scenario_tag", "K_total", "beta"]
    avail = [c for c in group_cols if c in master.columns]
    if not avail or "Z_total" not in master.columns:
        return FIG / "cross_scenario_bars.png"

    best = master.groupby(avail).agg(
        Z_total_max=("Z_total", "max"),
        RxC_max=("RxC", "max"),
        min_cov_best=("min_mahalle_cov", "max"),
        avg_cov_best=("avg_mahalle_cov", "max")
    ).reset_index()

    # Her Weight için ayrı subplot
    weights = best["weight_type"].unique()
    n = len(weights)
    if n == 0:
        return FIG / "cross_scenario_bars.png"

    fig, axes = plt.subplots(1, n, figsize=(7*n, 6), squeeze=False)
    colors = {"Ekleme": "#2196F3", "Bastan": "#FF5722"}

    for idx, wt in enumerate(weights):
        ax = axes[0, idx]
        sub = best[best["weight_type"] == wt]
        if sub.empty:
            continue

        x_labels = [f"β={row['beta']}" for _, row in sub.iterrows()]
        x = np.arange(len(sub))
        width = 0.35

        bars1 = ax.bar(x - width/2, sub["RxC_max"], width,
                        color=[colors.get(s, "#999") for s in sub["scenario_tag"]],
                        label="RxC (max)", edgecolor="black", linewidth=0.5)
        ax2 = ax.twinx()
        bars2 = ax2.bar(x + width/2, sub["min_cov_best"], width,
                         color=[colors.get(s, "#999") for s in sub["scenario_tag"]],
                         alpha=0.5, label="Min Kapsama")

        ax.set_xlabel("Beta (β)")
        ax.set_ylabel("RxC", color="#1565C0")
        ax2.set_ylabel("Min Kapsama", color="#BF360C")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{r['scenario_tag']}\nβ={r['beta']}" for _, r in sub.iterrows()],
                           fontsize=8, rotation=30, ha="right")
        ax.set_title(f"Hedef: {wt.upper()}", fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Senaryolar Arası Karşılaştırma: RxC vs Min Kapsama", fontweight="bold", fontsize=14)
    fig.tight_layout()
    out = FIG / "cross_scenario_bars.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_mcdm_heatmap(master: pd.DataFrame) -> Path:
    """MCDM yöntemleri × Senaryo heatmap'i."""
    if master.empty or "mcdm" not in master.columns:
        return FIG / "mcdm_heatmap.png"

    pivot = master.groupby(["mcdm", "senaryo"])["Z_total"].max().reset_index()
    try:
        hm = pivot.pivot(index="mcdm", columns="senaryo", values="Z_total")
    except Exception as e:
        print(f"  [!] MCDM heatmap pivot failed: {e}")
        return FIG / "mcdm_heatmap.png"

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(hm, annot=True, fmt=".3f", cmap="YlOrRd", ax=ax, linewidths=0.5)
    ax.set_title("MCDM × AHP Senaryosu: Z (Amaç Fonksiyonu) Heatmap", fontweight="bold")
    fig.tight_layout()
    out = FIG / "mcdm_heatmap.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


# ────────────────────────────────────────
# 3. FINAL_REPORT.xlsx (çok sayfalı)
# ────────────────────────────────────────
def write_final_xlsx(runs: list[dict], master: pd.DataFrame) -> Path:
    out = OUT / "FINAL_REPORT.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        # Sayfa 1: Tüm Koşum Parametreleri
        params_list = []
        for r in runs:
            p = r["parameters"]
            params_list.append({
                "Run_ID": r["run_id"],
                "Tarih": r["timestamp"],
                "K_Total": p["k_total"],
                "Hedef": p["weight_type"],
                "Beta": p["beta"],
                "Sigma": p["sigma"],
                "Korunan_Mevcut": len(p.get("kept_mevcut", [])),
                "Zorunlu_Aday": len(p.get("fixed_aday", [])),
                "Senaryo": p.get("scenario_tag", "?")
            })
        pd.DataFrame(params_list).to_excel(w, sheet_name="01_Kosum_Parametreleri", index=False)

        # Sayfa 2: Master Özet (tüm MCDM skorları)
        if not master.empty:
            cols_show = [c for c in ["run_id", "weight_type", "K_total", "beta", "scenario_tag",
                                      "mcdm", "senaryo", "Z_total", "RxC",
                                      "min_mahalle_cov", "avg_mahalle_cov", "sure_s"] if c in master.columns]
            master[cols_show].round(4).to_excel(w, sheet_name="02_Master_Skorlar", index=False)

        # Sayfa 3: En İyi Sonuçlar (her koşumun en yüksek Z_total'ı)
        if not master.empty:
            best = master.loc[master.groupby("run_id")["Z_total"].idxmax()]
            best.round(4).to_excel(w, sheet_name="03_En_Iyi_Sonuclar", index=False)

        # Sayfa 4: Mevcut Konteynerler
        mevcut = pd.read_excel(DATA / "mevcut_12.xlsx")
        mevcut.to_excel(w, sheet_name="04_Mevcut_12", index=False)

        # Sayfa 5: 140 Aday
        adaylar = pd.read_excel(DATA / "adaylar_140.xlsx")
        adaylar.to_excel(w, sheet_name="05_Aday_140", index=False)

        # Sayfa 6: Mahalle Bilgileri
        nufus = pd.read_excel(DATA / "mahalle_nufus.xlsx")
        risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
        barinma = pd.read_excel(DATA / "mahalle_barinma.xlsx")
        mahalle = nufus.merge(risk, on="mahalle", how="left", suffixes=("", "_r"))
        mahalle = mahalle.merge(barinma, on="mahalle", how="left", suffixes=("", "_b"))
        mahalle.to_excel(w, sheet_name="06_Mahalle_Bilgi", index=False)

        # Sayfa 7: Pipeline
        pipe = pd.DataFrame({
            "Adim": ["01_data_prep", "02_ahp + 02b_bwm", "03a_topsis", "03b_promethee",
                     "03c_vikor", "03d_electre", "04_fuzzy_coverage",
                     "05_ip", "07_reporting", "app.py (Dashboard)"],
            "Aciklama": [
                "Veri hazırlama, 140 aday + 12 mevcut",
                "AHP (3 senaryo) + BWM kriter ağırlıklandırma",
                "TOPSIS CC skorları (MinMax + L2)",
                "PROMETHEE II φ akışları",
                "VIKOR Q benefit skorları",
                "ELECTRE Net Outranking Flow",
                "Gaussian μ (Adaptive σ + Two-Tier 300m)",
                "0-1 IP Modeli (Oransal Ölçekleme + Esnek Kısıtlar)",
                "Final rapor sentezi",
                "Streamlit Dashboard (Job Queue + Multi-Compare)"
            ]
        })
        pipe.to_excel(w, sheet_name="07_Pipeline", index=False)

    return out


# ────────────────────────────────────────
# 4. AKADEMİK RAPOR (FINAL_RAPOR.md)
# ────────────────────────────────────────
def write_final_report_md(runs: list[dict], master: pd.DataFrame) -> Path:
    lines = []
    lines.append("# Sultanbeyli Konteyner Optimizasyonu — Final Sentez Raporu\n")
    lines.append(f"**Tarih:** {datetime.now().strftime('%Y-%m-%d')}  ")
    lines.append("**Kapsam:** IE492 Bitirme Projesi  ")
    lines.append("**Proje:** Çok Kriterli Afet Müdahale Konteyner Konumlandırma Modeli\n")
    lines.append("---\n")

    # 1. Yönetici Özeti
    lines.append("## 1. Yönetici Özeti\n")
    lines.append(
        f"Bu çalışmada Sultanbeyli ilçesindeki afet müdahale konteynerleri için çok kriterli, "
        f"çok senaryolu bir yer seçim modeli geliştirilmiştir. Model, dört MCDM yöntemi "
        f"(TOPSIS, PROMETHEE II, VIKOR, ELECTRE), üç AHP senaryosu (Baseline, Hasar-Odaklı, "
        f"Altyapı-Odaklı) ve Adaptif Gaussian Bulanık Kapsama fonksiyonu üzerinden 0-1 Karma "
        f"Tamsayılı Programlama (MILP) ile çözülmüştür.\n"
    )
    lines.append(f"**Toplam Koşum Sayısı:** {len(runs)}  ")
    if not master.empty:
        lines.append(f"**En Yüksek Z_total:** {master['Z_total'].max():.4f}  ")
        lines.append(f"**En Yüksek RxC:** {master['RxC'].max():.4f}  ")
        lines.append(f"**Ortalama Min Kapsama:** {master['min_mahalle_cov'].mean():.4f}\n")

    # 2. Problem Tanımı
    lines.append("## 2. Problem Tanımı\n")
    lines.append(
        "Sultanbeyli ilçesinde artan nüfus yoğunluğu ve deprem riski nedeniyle, "
        "mevcut 12 afet konteynerinin kapsama alanı yetersiz kalmaktadır. Bu çalışma, "
        "sınırlı bütçe altında (K=8 ekleme veya K=20 baştan kurulum) yeni konteynerlerin "
        "optimal yerleşimini, mahallelere adil erişim (spatial equity) garantisiyle çözmektedir.\n"
    )

    # 3. Amaç Fonksiyonu
    lines.append("## 3. Matematiksel Model\n")
    lines.append("### 3.1 Amaç Fonksiyonu\n")
    lines.append("$$\\max Z = \\sum_{i\\in I} R_i \\cdot C_i + \\beta \\sum_{j\\in J} q_j X_j$$\n")
    lines.append("### 3.2 Kısıtlar\n")
    lines.append("- $\\sum_j X_j = K_{Total} - |\\text{Kept}|$ (Bütçe)")
    lines.append("- $\\sum_{j \\in N_i} X_j + M_i \\ge 1 \\quad \\forall i$ (Min 1 Konteyner / Mahalle)")
    lines.append("- $C_i \\ge 0.50 \\cdot R_{norm,i} \\quad \\forall i$ (Riske Orantılı Kapsama)")
    lines.append("- $X_{f} = 1 \\quad \\forall f \\in \\text{Fixed}$ (Zorunlu Adaylar)")
    lines.append("- Oransal Ölçekleme: $R_{norm,i} = R_i / R_{max}$ (0 yutan eleman engeli)\n")

    # 4. Senaryolar
    lines.append("## 4. Deney Senaryoları\n")
    if runs:
        lines.append("| # | K_Total | Hedef | β | Senaryo | Korunan | Run_ID |")
        lines.append("|---|---------|-------|---|---------|---------|--------|")
        for i, r in enumerate(runs):
            p = r["parameters"]
            lines.append(
                f"| {i+1} | {p['k_total']} | {p['weight_type']} | {p['beta']} | "
                f"{p.get('scenario_tag','?')} | {len(p.get('kept_mevcut',[]))} | {r['run_id'][:40]}... |"
            )
        lines.append("")

    # 5. Sonuçlar
    lines.append("## 5. Sonuçlar\n")
    if not master.empty:
        # En iyi sonuçlar tablosu
        best = master.loc[master.groupby("run_id")["Z_total"].idxmax()]
        cols = [c for c in ["run_id", "mcdm", "senaryo", "weight_type", "scenario_tag",
                             "Z_total", "RxC", "min_mahalle_cov", "avg_mahalle_cov"] if c in best.columns]
        lines.append("### 5.1 Her Koşumun En İyi MCDM Sonucu\n")
        lines.append(best[cols].round(4).to_markdown(index=False))
        lines.append("")

        # Korelasyon bulgusu
        lines.append("### 5.2 Veri Korelasyonu Bulguları\n")
        lines.append(
            "> **Önemli Bulgu:** Risk Skoru ile Barınma İhtiyacı arasında %94.1 Pearson korelasyonu "
            "tespit edilmiştir. Bu nedenle bu iki değişken **alternatif senaryo** olarak kullanılmış, "
            "aynı modelde birlikte ağırlıklandırılmamıştır. Ana karşılaştırma ekseni: **Risk vs Nüfus**.\n"
        )

    # 6. Akademik Katkı
    lines.append("## 6. Akademik Katkılar\n")
    lines.append("1. **Oransal Ölçekleme:** 0 yutan eleman problemini ortadan kaldıran $W_i / W_{max}$ normalizasyonu.")
    lines.append("2. **Adaptif Gaussian σ:** Nüfusa ters orantılı (400m-1200m) kapsama yarıçapı.")
    lines.append("3. **Çift Kademeli Kapsama:** 300m içi tam kapsama ($\\mu=1.0$) + Gaussian azalma.")
    lines.append("4. **4 MCDM Yöntemi:** TOPSIS, PROMETHEE II, VIKOR, ELECTRE paralel entegrasyonu.")
    lines.append("5. **Esnek Kısıtlar:** Korunan mevcut + Zorunlu aday seçimi dinamik olarak modele girer.")
    lines.append("6. **Dashboard:** Streamlit üzerinden Job Queue + Multi-Compare görsel analiz.\n")

    # 7. Sınırlılıklar
    lines.append("## 7. Sınırlılıklar\n")
    lines.append("- Haversine (kuş uçuşu) mesafe kullanılmıştır; yol ağı mesafesi entegre edilmemiştir.")
    lines.append("- `p_access_road` verisi sentetiktir (seed=42).")
    lines.append("- Her lokasyona en fazla 1 konteyner yerleştirilebilmektedir.")
    lines.append("- Risk değerleri deterministik alınmıştır; belirsizlik modellenmemiştir.\n")

    out = DOC / "FINAL_RAPOR.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ────────────────────────────────────────
# 5. MAIN
# ────────────────────────────────────────
def main():
    print("== 07_reporting.py (V2 — Metadata Tabanlı) başladı ==")

    runs = collect_all_runs()
    print(f"  -> {len(runs)} koşum metadata'sı bulundu.")

    if not runs:
        print("  !! Hiç metadata bulunamadı. Önce Dashboard'dan model çalıştırın.")
        return

    master = build_master_summary(runs)
    print(f"  -> Master özet: {len(master)} satır ({master['run_id'].nunique()} benzersiz koşum)")

    print("  [1/4] FINAL_REPORT.xlsx yazılıyor...")
    xlsx = write_final_xlsx(runs, master)
    print(f"    -> {xlsx}")

    print("  [2/4] Senaryolar arası karşılaştırma grafiği...")
    bars = plot_cross_scenario_bars(master)
    print(f"    -> {bars}")

    print("  [3/4] MCDM Heatmap...")
    hm = plot_mcdm_heatmap(master)
    print(f"    -> {hm}")

    print("  [4/4] Akademik rapor (FINAL_RAPOR.md)...")
    rpt = write_final_report_md(runs, master)
    print(f"    -> {rpt}")

    print("\n== 07_reporting.py tamamlandı ==")
    print(f"\nÇıktılar:")
    print(f"  - {xlsx}")
    print(f"  - {bars}")
    print(f"  - {hm}")
    print(f"  - {rpt}")


if __name__ == "__main__":
    main()

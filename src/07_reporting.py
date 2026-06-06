# -*- coding: utf-8 -*-
"""
07_reporting.py
Final paketleme: kazanan versiyon v1 (TOPSIS-Baseline) için
  - FINAL_REPORT.xlsx (çok sayfalı, tüm çıktıları derler)
  - Final harita (PNG): mevcut + yeni konteynerler, mahalle poligonları
  - docs/rapor/FINAL_RAPOR.md (akademik Türkçe özet)
  - figures/ harita + bar grafikleri

Girdi: 06_compare.py'nin ürettiği tüm dosyalar + 01-05 çıktıları
"""

from __future__ import annotations
import os
import sys
import glob
import json
import numpy as np
import pandas as pd
import openpyxl
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
RES  = ROOT / "results"
OUT  = ROOT / "results" / "final"
FIG  = ROOT / "figures"
DOC  = ROOT / "docs" / "rapor"
for d in [OUT, FIG, DOC]:
    d.mkdir(parents=True, exist_ok=True)

KAZANAN = "v1"  # 06_compare.py rasyoneli


# ---------- 1. Veri yükleme ----------
def load_all() -> dict[str, object]:
    return {
        "adaylar":      pd.read_excel(DATA / "adaylar_140.xlsx"),
        "mevcut":       pd.read_excel(DATA / "mevcut_12.xlsx"),
        "mahalle":      pd.read_excel(DATA / "mahalle_nufus.xlsx"),
        "mahalle_risk": pd.read_excel(DATA / "mahalle_risk.xlsx"),
        "criteria":     pd.read_excel(RES / "ahp" / "criteria_definitions.xlsx"),
        "ahp":          pd.read_excel(RES / "ahp" / "ahp_weights.xlsx"),
        "topsis":       pd.read_excel(RES / "mcdm" / "topsis_cc.xlsx"),
        "promethee":    pd.read_excel(RES / "mcdm" / "promethee_phi.xlsx"),
        "fcm":          pd.read_excel(RES / "fcm" / "mu_aday_140x17.xlsx"),
        "summary":      pd.read_excel(RES / "models" / "summary_all.xlsx").dropna(subset=["version"]),
        "ip_kazanan":   pd.read_excel(RES / "models" / f"ip_{KAZANAN}_TOPSIS_Baseline.xlsx"),
        "cov_kazanan":  pd.read_excel(RES / "models" / f"coverage_{KAZANAN}_TOPSIS_Baseline.xlsx"),
        "compare":      pd.read_excel(RES / "comparison" / "compare_summary.xlsx"),
    }


# ---------- 2. FINAL_REPORT.xlsx (çok sayfalı) ----------
def write_final_xlsx(data: dict) -> Path:
    out = OUT / "FINAL_REPORT.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        # Sayfa 1: Özet
        meta = pd.DataFrame({
            "Alan": [
                "Proje", "Tarih", "Kazanan versiyon", "Kazanan MCDM",
                "Kazanan senaryo", "Toplam RxC", "Min mahalle kapsama",
                "Seçilen yeni konteyner sayısı", "Mevcut konteyner sayısı",
                "Toplam konteyner sayısı", "Kriter sayısı",
                "AHP senaryo sayısı", "MCDM yöntem sayısı",
                "IP versiyon sayısı"
            ],
            "Deger": [
                "IE492 Sultanbeyli Konteyner Optimizasyonu",
                "2026-06-06", KAZANAN, "TOPSIS", "Baseline",
                f"{data['summary'].loc[data['summary']['version']==KAZANAN,'RxC'].values[0]:.4f}",
                f"{data['summary'].loc[data['summary']['version']==KAZANAN,'min_mahalle_cov'].values[0]:.4f}",
                "8", "12", "20", "4", "3", "2", "6"
            ]
        })
        meta.to_excel(w, sheet_name="00_Ozet", index=False)

        # Sayfa 2: Seçilen 8 yeni konteyner
        data["ip_kazanan"].to_excel(w, sheet_name="01_Secilen_Konteynerler", index=False)

        # Sayfa 3: Mahalle kapsama
        data["cov_kazanan"].to_excel(w, sheet_name="02_Mahalle_Kapsama", index=False)

        # Sayfa 4: 6 versiyon özeti
        data["summary"][[
            "version","mcdm","senaryo","Z_total","Z_risk","Z_quality",
            "RxC","min_mahalle_cov","avg_mahalle_cov",
            "n_mahalle_below_050","n_mahalle_below_020","sure_s"
        ]].round(4).to_excel(w, sheet_name="03_6_Versiyon_Ozet", index=False)

        # Sayfa 5: AHP ağırlıkları
        data["ahp"].to_excel(w, sheet_name="04_AHP_Agirliklari", index=False)

        # Sayfa 6: TOPSIS CC
        data["topsis"].to_excel(w, sheet_name="05_TOPSIS_CC", index=False)

        # Sayfa 7: PROMETHEE phi
        data["promethee"].to_excel(w, sheet_name="06_PROMETHEE_phi", index=False)

        # Sayfa 8: Mevcut 12 konteyner
        data["mevcut"].to_excel(w, sheet_name="07_Mevcut_12", index=False)

        # Sayfa 9: 140 aday
        data["adaylar"].to_excel(w, sheet_name="08_Aday_140", index=False)

        # Sayfa 10: Mahalle nüfus + risk
        mrg = data["mahalle"].merge(
            data["mahalle_risk"], on="mahalle", how="left", suffixes=("", "_risk"))
        mrg.to_excel(w, sheet_name="09_Mahalle_Bilgi", index=False)

        # Sayfa 11: Karşılaştırma
        data["compare"].to_excel(w, sheet_name="10_Karsilastirma", index=False)

        # Sayfa 12: Pipeline özeti
        pipe = pd.DataFrame({
            "Adim": ["01_data_prep","02_ahp","03a_topsis","03b_promethee",
                     "04_fcm","05_ip","06_compare","07_reporting"],
            "Girdi": ["5 orijinal xlsx","krit.docx + eski 3 AHP",
                      "criteria + ahp","criteria + ahp",
                      "adaylar+mevcut koord","MU+CC+phi+R+P",
                      "6 IP cikti","Kazanan versiyon"],
            "Cikti": ["8 processed xlsx","ahp_weights.xlsx",
                      "topsis_cc.xlsx","promethee_phi.xlsx",
                      "mu_matrices.xlsx","6 ip_v* + coverage_v*",
                      "compare_*.xlsx + rasyonal","FINAL_REPORT.xlsx"]
        })
        pipe.to_excel(w, sheet_name="11_Pipeline", index=False)

    return out


# ---------- 3. Final harita (mahalle bazlı statik) ----------
def plot_final_map(data: dict) -> Path:
    """Mevcut 12 + yeni 8 konteyneri koordinat düzleminde gösterir."""
    fig, ax = plt.subplots(figsize=(11, 9))

    mev = data["mevcut"]
    yeni = data["ip_kazanan"]

    # Mevcut konteynerler (küçük harf kolon)
    mev_lat, mev_lon = mev["enlem"], mev["boylam"]
    ax.scatter(mev_lon, mev_lat,
               s=180, c="#2ca02c", marker="s", edgecolors="black", linewidth=1.5,
               label="Mevcut 12 konteyner", zorder=4)

    # Yeni konteynerler
    ax.scatter(yeni["Boylam"], yeni["Enlem"],
               s=220, c="#d62728", marker="*", edgecolors="black", linewidth=1.5,
               label=f"YENİ 8 konteyner ({KAZANAN})", zorder=5)

    # Etiketler (mevcut)
    for _, r in mev.iterrows():
        ax.annotate(str(int(r["container_no"])), (r["boylam"], r["enlem"]),
                    xytext=(4, 4), textcoords="offset points", fontsize=7,
                    color="darkgreen", weight="bold")
    for _, r in yeni.iterrows():
        ax.annotate(str(int(r["S_No"])), (r["Boylam"], r["Enlem"]),
                    xytext=(4, 4), textcoords="offset points", fontsize=8,
                    color="darkred", weight="bold")

    # Tüm 140 aday (gri, arka plan)
    aday = data["adaylar"]
    ax.scatter(aday["Boylam"], aday["Enlem"],
               s=12, c="gray", alpha=0.35, label=f"Aday 140 parsel", zorder=2)

    ax.set_xlabel("Boylam")
    ax.set_ylabel("Enlem")
    ax.set_title("Sultanbeyli Konteyner Yerleşim Planı (Kazanan: TOPSIS-Baseline, v1)\n"
                 "Mevcut 12 (yeşil) + Önerilen 8 yeni (kırmızı yıldız)", fontsize=12)
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = FIG / "final_harita.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ---------- 4. Karşılaştırma bar grafiği (nihai) ----------
def plot_compare_bars(data: dict) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    s = data["summary"]

    # Sol: RxC
    pivot_rxc = s.pivot_table(index="senaryo", columns="mcdm", values="RxC", aggfunc="first")
    pivot_rxc.plot(kind="bar", ax=axes[0], color=["#1f77b4", "#ff7f0e"])
    axes[0].set_title("RxC (Risk-weighted Coverage) — 6 Versiyon")
    axes[0].set_ylabel("RxC")
    axes[0].legend(title="MCDM")
    axes[0].grid(axis="y", alpha=0.3)
    axes[0].tick_params(axis="x", rotation=20)

    # Sağ: min mahalle kapsama
    pivot_min = s.pivot_table(index="senaryo", columns="mcdm",
                              values="min_mahalle_cov", aggfunc="first")
    pivot_min.plot(kind="bar", ax=axes[1], color=["#1f77b4", "#ff7f0e"])
    axes[1].set_title("Minimum Mahalle Kapsama — 6 Versiyon")
    axes[1].set_ylabel("min C_i")
    axes[1].legend(title="MCDM")
    axes[1].grid(axis="y", alpha=0.3)
    axes[1].tick_params(axis="x", rotation=20)

    fig.tight_layout()
    out = FIG / "final_compare_bars.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ---------- 5. Kapsama radar grafiği (mahalle bazlı) ----------
def plot_coverage_radar(data: dict) -> Path:
    cov = data["cov_kazanan"].copy()
    # Sütun adlarını güvenli hale getir
    cov.columns = [str(c).strip() for c in cov.columns]
    if "mahalle" not in cov.columns:
        # ilk sütun mahalle olabilir
        cov = cov.rename(columns={cov.columns[0]: "mahalle"})
    cov["mahalle"] = cov["mahalle"].astype(str)

    # Eğer 'toplam' sütunu varsa onu kullan
    target = None
    for cand in ["toplam", "toplam_coverage", "C_i", "coverage", "toplam_kapsama"]:
        if cand in cov.columns:
            target = cand
            break
    if target is None:
        # sayısal sütunlardan birini seç
        for c in cov.columns:
            if c != "mahalle" and pd.api.types.is_numeric_dtype(cov[c]):
                target = c
                break

    if target is None or len(cov) < 3:
        print("  Radar grafigi icin uygun kolon bulunamadi, atlanıyor.")
        return FIG / "final_radar.png"

    m = cov.sort_values(target, ascending=False).head(12)

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    cats = m["mahalle"].tolist()
    vals = m[target].tolist()
    # normalize 0-1
    vmin, vmax = min(vals), max(vals)
    rng = vmax - vmin if vmax > vmin else 1.0
    nv = [(v - vmin) / rng for v in vals]

    angles = np.linspace(0, 2*np.pi, len(cats), endpoint=False).tolist()
    nv_plot = nv + [nv[0]]
    angles += angles[:1]
    ax.plot(angles, nv_plot, color="#d62728", linewidth=2)
    ax.fill(angles, nv_plot, color="#d62728", alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_title("Mahalle Kapsama Radarı (Kazanan v1)", pad=20)
    fig.tight_layout()
    out = FIG / "final_radar.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ---------- 6. Akademik Türkçe özet rapor ----------
def write_final_report(data: dict) -> Path:
    s = data["summary"]
    win = s[s["version"] == KAZANAN].iloc[0]
    sites = data["ip_kazanan"]

    mahalle_ort = data["mahalle"]
    risk = data["mahalle_risk"]

    # 6 versiyon tablosu
    cmp = s[["version","mcdm","senaryo","RxC","min_mahalle_cov",
             "avg_mahalle_cov","sure_s"]].round(4)

    lines: list[str] = []
    lines.append("# Sultanbeyli Konteyner Optimizasyonu — Final Rapor\n")
    lines.append("**Tarih:** 2026-06-06  ")
    lines.append("**Kapsam:** IE492 Bitirme Projesi  ")
    lines.append("**Yazar:** [öğrenci adı]  ")
    lines.append("**Danışman:** [danışman adı]\n")
    lines.append("---\n")

    lines.append("## 1. Yönetici Özeti\n")
    lines.append(
        f"Bu çalışmada Sultanbeyli ilçesindeki 12 mevcut afet konteynerinin "
        f"üzerine eklenecek **8 yeni konteyner** için çok kriterli, çok senaryolu "
        f"bir yer seçim modeli geliştirilmiştir. Model, dört kriterli bir AHP "
        f"ağırlıklandırmasını (Nüfus, Deprem Riski, Erişilebilirlik, Ulaşım) "
        f"iki farklı ÇKKV yöntemiyle (TOPSIS ve PROMETHEE II) üç senaryoda "
        f"(Baseline, Hasar-Odaklı, Altyapı-Odaklı) birleştirmiş, FCM tabanlı "
        f"uzaysal üyelik fonksiyonu üzerinden 0-1 Karma Tamsayılı Programlama "
        f"(MILP) ile toplam **6 versiyon** çözmüştür.\n"
    )
    lines.append(
        f"**Kazanan versiyon:** `{KAZANAN}` (TOPSIS / Baseline)  \n"
        f"- Risk-ağırlıklı kapsama (RxC): **{win['RxC']:.4f}**  \n"
        f"- Minimum mahalle kapsama: **{win['min_mahalle_cov']:.4f}**  \n"
        f"- Ortalama mahalle kapsama: **{win['avg_mahalle_cov']:.4f}**  \n"
        f"- Çözüm süresi: **{win['sure_s']*1000:.0f} ms**\n"
    )
    lines.append(
        "Modelin temel katkısı: AHP ağırlıklarının doğrudan MILP amaç "
        "fonksiyonuna kalite katsayısı (β=0.30) olarak eklenmesi, "
        "böylece senaryoların ve MCDM yöntemlerinin kararı **gerçekten** "
        "etkilemesinin sağlanmasıdır.\n"
    )

    lines.append("## 2. Problem Tanımı\n")
    lines.append(
        "Sultanbeyli ilçesinde artan nüfus yoğunluğu ve kentsel yapısal "
        "yoğunluk nedeniyle afet anında konteynerlere erişim eşit dağılmamaktadır. "
        "Mevcut 12 konteyner bazı mahallelerde yığılma, bazılarında ise uzun "
        "erişim mesafesi yaratmaktadır. Çalışmanın temel sorusu:\n\n"
        "> *\"Sınırlı sayıda (K=8) yeni konteyner, hangi aday parselere yerleştirilmelidir "
        "ki risk-ağırlıklı kapsama maksimize edilsin, ortalama erişim mesafesi "
        "azalsın ve tüm mahallelerde kritik eşik (μ ≥ 0.50) sağlansın?*\"\n"
    )

    lines.append("## 3. Veri ve Kriterler\n")
    lines.append("| Kriter | Açıklama | Veri Kaynağı |")
    lines.append("|--------|----------|--------------|")
    lines.append("| C1 Nüfus | Mahalle nüfusu | TÜİK 2024 |")
    lines.append("| C2 Deprem Riski | Hasar senaryosu skoru | İBB Hasar Senaryosu |")
    lines.append("| C3 Erişilebilirlik | En yakın mevcut konteynere mesafe | Hesaplanan (Haversine) |")
    lines.append("| C4 Ulaşım | Yol erişim olasılığı P_access | OSM/parseller |")
    lines.append("| C5 Barınma | Hane ihtiyacı (yardımcı değişken) | Mahalle anketi |")
    lines.append("| _FCM_ | _Uzaysal üyelik μ(i,j)_ | _Hesaplanan (σ=800m)_ |\n")

    lines.append("## 4. Yöntem\n")
    lines.append("### 4.1 Pipeline (6 Aşama)\n")
    lines.append("```")
    lines.append("01 Veri Hazırlama  → 02 AHP (3 senaryo)")
    lines.append("                   → 03a TOPSIS      (CC_j)")
    lines.append("                   → 03b PROMETHEE II (phi_j)")
    lines.append("                   → 04 FCM (μ_ij)")
    lines.append("                   → 05 0-1 IP (max Z, K=8)")
    lines.append("                   → 06 Karşılaştırma")
    lines.append("                   → 07 Raporlama")
    lines.append("```\n")
    lines.append("### 4.2 Amaç Fonksiyonu\n")
    lines.append("$$\\max Z = \\sum_{i\\in I} R_i \\cdot C_i + \\beta \\sum_{j\\in J} q_j X_j$$")
    lines.append("$$\\text{s.t.}\\quad C_i = \\mu^{mev}_i + \\sum_{j\\in J} \\mu_{ij}\\,P_j\\,X_j,$$")
    lines.append("$$\\quad\\sum_{j\\in J} X_j = K,\\quad X_j\\in\\{0,1\\},\\quad \\mu_{ij}=\\exp\\!\\left(-\\tfrac{d_{ij}^2}{2\\sigma^2}\\right)$$\n")
    lines.append(f"Burada $q_j$ TOPSIS durumunda $CC_j$, PROMETHEE durumunda $\\phi_j$'dir; $\\beta=0.30$ sabit.\n")

    lines.append("## 5. Sonuçlar\n")
    lines.append("### 5.1 Kazanan Versiyon — Seçilen 8 Yeni Konteyner\n")
    lines.append("| S_No | Alan Adı | Mahalle | Enlem | Boylam | q (TOPSIS) | p_road | Σμ |")
    lines.append("|------|----------|---------|-------|--------|-----------|--------|-----|")
    for _, r in sites.iterrows():
        lines.append(
            f"| {int(r['S_No'])} | {r['Alan_Adi']} | {r['Mahalle']} | "
            f"{r['Enlem']:.5f} | {r['Boylam']:.5f} | "
            f"{r['q_TOPSIS']:.4f} | {r['p_access_road']:.4f} | "
            f"{r['toplam_mu_saglanan']:.4f} |"
        )
    lines.append("")

    lines.append("### 5.2 6 Versiyon Karşılaştırması\n")
    lines.append(cmp.to_markdown(index=False))
    lines.append("\n")
    lines.append("**Gözlem:** RxC değerleri 21.18–21.20 bandında sıkışmıştır; "
                 "MCDM yöntemi (TOPSIS ↔ PROMETHEE) ve AHP senaryosu (Baseline ↔ "
                 "Hasar-Odaklı) marjinal etki yaratır. Altyapı-Odaklı senaryo biraz "
                 "düşük RxC üretir (21.1834) ama yine 0.82 minimum mahalle kapsama "
                 "sağlar.\n")

    lines.append("### 5.3 Mevcut 12 Konteyner\n")
    lines.append("| S_No | Mahalle | Enlem | Boylam |")
    lines.append("|------|---------|-------|--------|")
    for _, r in data["mevcut"].iterrows():
        lines.append(f"| {int(r['container_no'])} | {r['mahalle']} | "
                     f"{r['enlem']:.5f} | {r['boylam']:.5f} |")
    lines.append("")

    lines.append("## 6. Akademik Katkı\n")
    lines.append("1. **Kod düzeyinde kanıtlanmış etki:** q_j (TOPSIS CC veya PROMETHEE φ) "
                 "MILP amaç fonksiyonuna doğrudan parametre olarak girer; bu sayede AHP "
                 "senaryoları ve MCDM yöntemi kararı gerçekten etkiler (eski "
                 "uygulamalarda q_j raporlama süslemesiydi).\n")
    lines.append("2. **Karşılaştırmalı MCDM değerlendirme:** Aynı kriter matrisine iki "
                 "farklı ÇKKV yönteminin paralel uygulanması, Pearson korelasyonu "
                 "(≈ 0.98) ve top-10 Jaccard (0.54-1.00) ile yöntem sağlamlığını "
                 "gösterir.\n")
    lines.append("3. **Çok senaryolu hassasiyet:** 3 AHP senaryosu × 2 MCDM = 6 "
                 "versiyon, senaryolar arası çekirdek konum sabitliğini (7-8/8 örtüşme) "
                 "ve kenar seçim değişimini ortaya koyar.\n")
    lines.append("4. **Hesaplama verimliliği:** Her versiyon < 100 ms CBC çözücü ile "
                 "optimal çözülmüştür; operasyonel kullanıma uygundur.\n")

    lines.append("## 7. Sınırlılıklar ve Gelecek Çalışmalar\n")
    lines.append("- **FCM σ=800m** keyfidir; mobil veri ile kalibrasyon gerekir.")
    lines.append("- **Yol ağı mesafesi** yok (Haversine kullanıldı); OSM entegrasyonu ileriki adım.")
    lines.append("- **Dinamik/periyot** yok; afet öncesi/sonrası ayrımı modellenmedi.")
    lines.append("- **Belirsizlik** modellenmedi; risk deterministik alındı.")
    lines.append("- **Çok amaçlı** (RxC + ortalama mesafe) Pareto cephesi üretilmedi; "
                 "tek amaçlı skalerleştirme yapıldı (β ağırlığı).\n")

    lines.append("## 8. Dosya Yapısı\n")
    lines.append("```")
    lines.append("IE492/")
    lines.append("├── data/")
    lines.append("│   ├── raw/             # 5 orijinal girdi dosyası")
    lines.append("│   └── processed/       # 8 temiz xlsx")
    lines.append("├── src/                 # 01-07 Python kodları")
    lines.append("├── results/")
    lines.append("│   ├── ahp/             # AHP ağırlıkları")
    lines.append("│   ├── mcdm/            # TOPSIS CC, PROMETHEE phi")
    lines.append("│   ├── fcm/             # μ matrisleri")
    lines.append("│   ├── models/          # 6 IP versiyonu")
    lines.append("│   ├── comparison/      # Karşılaştırma tabloları")
    lines.append("│   └── final/           # FINAL_REPORT.xlsx")
    lines.append("├── figures/             # Tüm grafikler (final_harita.png dahil)")
    lines.append("└── docs/")
    lines.append("    ├── planlar/         # Planlar ve rasyonal.md")
    lines.append("    └── rapor/           # FINAL_RAPOR.md (bu dosya)")
    lines.append("```\n")

    out = DOC / "FINAL_RAPOR.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ---------- 7. Çalıştır ----------
def main():
    print("== 07_reporting.py basladi ==")
    data = load_all()

    print("  [1/4] FINAL_REPORT.xlsx yaziliyor...")
    fxlsx = write_final_xlsx(data)
    print(f"    -> {fxlsx}")

    print("  [2/4] Final harita ciziliyor...")
    fmap = plot_final_map(data)
    print(f"    -> {fmap}")

    print("  [3/4] Karsilastirma grafigi...")
    fbar = plot_compare_bars(data)
    print(f"    -> {fbar}")

    print("  [3b/4] Radar grafigi...")
    fradar = plot_coverage_radar(data)
    print(f"    -> {fradar}")

    print("  [4/4] Akademik rapor yaziliyor...")
    frpt = write_final_report(data)
    print(f"    -> {frpt}")

    print("\n== 07_reporting.py tamamlandi ==")
    print(f"\nTeslimatlar:")
    print(f"  - {fxlsx}")
    print(f"  - {fmap}")
    print(f"  - {fbar}")
    print(f"  - {fradar}")
    print(f"  - {frpt}")


if __name__ == "__main__":
    main()

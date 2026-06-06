# -*- coding: utf-8 -*-
"""
06_final_xlsx.py
==========================================================
Cozum Alternatifi 2: 18-sayfa birlestirilmis final xlsx
(Sultanbeyli_Final_Results_CA2.xlsx) olusturur.
==========================================================
"""
import unicodedata
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("D:/IE492")
CA2 = ROOT / "cozum_alternatifi_2_road_closure"
RES = CA2 / "results"
FIN = CA2 / "final"
FIN.mkdir(parents=True, exist_ok=True)
RES_O = ROOT / "output" / "results"

def norm(s):
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())

def read(path, sheet=None):
    if sheet is None:
        return pd.read_excel(path)
    return pd.read_excel(path, sheet_name=sheet)

def read_md(path):
    return Path(path).read_text(encoding="utf-8")

if __name__ == "__main__":
    print("=" * 60)
    print("STEP 6: CA2 Final xlsx (18 sayfa)")
    print("=" * 60)

    sheets = {}

    # 0. README
    readme = ("# Sultanbeyli - Cozum Alternatifi 2: Yol Kapanma Olasiligi\n"
              "Bu calisma, orijinal 4-asamali AHP + TOPSIS + FCM + 0-1 IP\n"
              "pipeline'ina IBB Tablo 1'den elde edilen P(yol acik) mahalle\n"
              "katsayisini carpan olarak entegre eder.\n\n"
              "**Yontem**: P(yol acik) = exp(-lambda * N_cok_agir) [lambda=0.005]\n"
              "**Entegrasyon**: IP Z = sum_i R_i * [mu_mev(i) + sum_j mu(i,j) * P_access(j) * X_j]\n"
              "**Kapsam**: 140 aday, 12 mevcut, 17 mahalle, 6 senaryo (3 AHP x 2 IP mod)\n"
              "**Cikti**: 8 yeni konteyner sahasi (S55, S59, S60, S62, S83, S88, S140, S141)\n")
    sheets["README"] = pd.DataFrame({"aciklama": [readme]})

    # 1. KPI_Summary
    sens = pd.read_excel(RES / "selection_sensitivity_CA2.xlsx")
    sheets["KPI_Summary"] = pd.DataFrame({
        "metrik": ["Secilen site sayisi", "Senaryo sayisi", "Sigma (m)",
                    "Coverage threshold", "Ortalama Z (CA2)",
                    "Ortalama Z (Orijinal)", "Delta Z (ortalama)",
                    "Kritik mahalle < threshold", "P(yol acik) ortalama"],
        "deger": [8, 6, 800, 0.50,
                   float(sens["objective"].mean()),
                   935.621365,
                   float(sens["objective"].mean()) - 935.621365,
                   int(sens["n_critical_below_threshold"].sum()),
                   0.9686]
    })

    # 2. Selected_8
    sel = pd.read_excel(RES / "selection_Baseline_hard_CA2.xlsx", sheet_name="Selected_8")
    sheets["Selected_8"] = sel

    # 3. AHP_Weights
    ahp = pd.read_excel(RES / "ahp_weights_CA2.xlsx")
    sheets["AHP_Weights"] = ahp

    # 4. TOPSIS_Top20
    top = pd.read_excel(RES / "topsis_sonuclar_CA2.xlsx").nlargest(20, "CC_Baseline")
    sheets["TOPSIS_Top20"] = top

    # 5. Sensitivity
    sheets["Sensitivity"] = sens

    # 6. Coverage_per_Mahalle
    cov = pd.read_excel(RES / "selection_Baseline_hard_CA2.xlsx", sheet_name="Coverage_per_Mahalle")
    sheets["Coverage_per_Mahalle"] = cov

    # 7. Coverage_KPI
    sheets["Coverage_KPI"] = pd.read_excel(RES_O / "coverage_score_kpi.xlsx")

    # 8. Inputs_Candidates
    sheets["Inputs_Candidates"] = pd.read_excel(ROOT / "output" / "data" / "adaylar.xlsx")

    # 9. Inputs_Existing
    sheets["Inputs_Existing"] = pd.read_excel(ROOT / "output" / "data" / "mevcut_12.xlsx")

    # 10. Inputs_Mahalle_Risk
    sheets["Inputs_Mahalle_Risk"] = pd.read_excel(ROOT / "output" / "data" / "mahalle_risk.xlsx")

    # 11. Inputs_Mahalle_Pop
    sheets["Inputs_Mahalle_Pop"] = pd.read_excel(ROOT / "output" / "data" / "mahalle_nufus.xlsx")

    # 12. Mu_Aday
    sheets["Mu_Aday"] = pd.read_excel(RES / "mu_aday_CA2.xlsx")

    # 13. Mu_Mevcut
    sheets["Mu_Mevcut"] = pd.read_excel(RES / "mu_mevcut_CA2.xlsx")

    # 14. Centroids
    sheets["Centroids"] = pd.read_excel(RES / "mahalle_centroids_CA2.xlsx")

    # 15. Criteria_Matrix
    sheets["Criteria_Matrix"] = pd.read_excel(RES / "criteria_matrix_CA2.xlsx")

    # 16. AHP_Robustness - from original
    sheets["AHP_Robustness"] = pd.read_excel(RES_O / "ahp_robustness.xlsx")

    # 17. Road_Closure (yeni)
    road = pd.read_excel(CA2 / "data" / "mahalle_data_road.xlsx")
    sheets["Road_Closure"] = road

    out_path = FIN / "Sultanbeyli_Final_Results_CA2.xlsx"
    with pd.ExcelWriter(out_path) as w:
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name, index=False)
    print(f"[OK] {out_path}")

    # Reporting.md
    md = []
    md.append("# Cozum Alternatifi 2 - Final Rapor")
    md.append("## Sultanbeyli Konteyner Optimizasyonu - Yol Kapanma Entegrasyonlu")
    md.append("")
    md.append("**Tarih:** 2026  \n**Pipeline:** AHP + TOPSIS + FCM (Gaussian) + 0-1 IP  \n"
              "**Orijinal:** `D:/IE492/output/` (korundu, degistirilmedi)  \n"
              "**CA2:** `D:/IE492/cozum_alternatifi_2_road_closure/`  \n")
    md.append("## 1. Problem")
    md.append("Orijinal 4 kriterli optimizasyon (hasar, lojistik, mesafe, nufus) konteyner"
              " yerlesimini sadece talep ve altyapi acidan degerlendirir. Ancak deprem sonrasi"
              " yol hasarlari konteynirlara erisimi kisitlayabilir. Bu cozum alternatifi,"
              " IBB Tablo 1'deki 'cok agir hasarli bina' sayisindan yol kapanma olasiligini"
              " hesaplar ve IP solver'ina carpan olarak entegre eder.")
    md.append("")
    md.append("## 2. Yontem")
    md.append("### 2.1 P(yol acik) hesabi")
    md.append("```")
    md.append("P(yol acik | mahalle) = exp(-lambda * N_cok_agir)")
    md.append("lambda = 0.005   (ampirik, literatur)")
    md.append("N_cok_agir = IBB Tablo 1, mahalle bazli cok agir hasarli bina sayisi")
    md.append("```")
    md.append("### 2.2 IP entegrasyonu")
    md.append("```")
    md.append("Max Z = Sum_i R_i * [ Sum_k mu(i,k) + Sum_j mu(i,j) * P_access(j) * X_j ]")
    md.append("P_access(j) = P(yol acik | dominant_mahalle(j))")
    md.append("```")
    md.append("")
    md.append("## 3. Sonuclar")
    md.append("| Metrik | Orijinal | CA2 | Delta |")
    md.append("|--------|----------|-----|-------|")
    z_orig = 935.621365
    z_ca2 = float(sens["objective"].mean())
    md.append(f"| Z (ortalama) | {z_orig:.2f} | {z_ca2:.2f} | {z_ca2-z_orig:+.2f} |")
    md.append("| Secilen 8 | S4, S59, S60, S61, S62, S83, S88, S141 | "
               "S55, S59, S60, S62, S83, S88, S140, S141 | 6/8 ortak |")
    md.append("| En dusuk P(yol acik) | 0.93 (ABDURRAHMANGAZI) | 0.93 (degismedi) | - |")
    md.append("| En buyuk site swap | - | S4->S55 (FATIH), S61->S140 (FATIH) | - |")
    md.append("")
    md.append("## 4. Mahalle Coverage Etkisi")
    md.append("En cok etkilenen mahalleler:")
    cov_sorted = cov.sort_values("total_coverage_20_weighted", ascending=False)
    for _, r in cov_sorted.head(5).iterrows():
        md.append(f"- **{r['mahalle']}**: coverage {r['total_coverage_20_weighted']:.3f}, "
                  f"P_road_open = {r.get('P_road_open', '-')}")
    md.append("")
    md.append("## 5. Sensitivity")
    md.append("6 senaryo (3 AHP x 2 IP mod) icin Z degerleri:")
    md.append("")
    md.append("| Senaryo | Mod | Status | Z |")
    md.append("|---------|-----|--------|---|")
    for _, r in sens.iterrows():
        md.append(f"| {r['scenario']} | {r['mode']} | {r['status']} | {r['objective']:.3f} |")
    md.append("")
    md.append("## 6. Sonuc ve Oneriler")
    md.append("- Yol kapanma entegrasyonu solver'in secimini %25 oraninda (2/8) degistirmistir.")
    md.append("- Solver, yuksek riskli ama dusuk erisilebilirligi olan ABDURRAHMANGAZI ve "
              "HAMIDIYE yerine daha erisebilir FATIH ve YAVUZ SELIM mahallelerine yonelmistir.")
    md.append("- Z degeri yaklasik 27 birim azalmistir (carpan etkisi 0.93-1.00 araliginda).")
    md.append("- Bu yaklasim, deprem sonrasi erisim kisitlarini hesaba katan daha gercekci "
              "bir optimizasyon saglar.")
    md.append("")
    md.append("## 7. Dosya Yapisi")
    md.append("```")
    md.append("D:/IE492/cozum_alternatifi_2_road_closure/")
    md.append("  scripts/01-08 + 99_run_all")
    md.append("  data/    (mahalle_data_road.xlsx)")
    md.append("  results/ (criteria_matrix, mu_*, p_access, selection_*, sensitivity)")
    md.append("  maps/    (CA2_selection_map.png)")
    md.append("  comparison/ (compare_summary, comparison_report)")
    md.append("  final/   (Sultanbeyli_Final_Results_CA2.xlsx, reporting.md)")
    md.append("```")

    (FIN / "reporting.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] {FIN / 'reporting.md'}")

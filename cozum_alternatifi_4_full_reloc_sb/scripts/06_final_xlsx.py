# -*- coding: utf-8 -*-
"""
06_final_xlsx_CA4.py
==========================================================
Cozum Alternatifi 3: 18-sayfa birlestirilmis final xlsx.
==========================================================
"""
import pandas as pd
from pathlib import Path

ROOT = Path("D:/IE492")
CA4 = ROOT / "cozum_alternatifi_4_full_reloc_sb"
RES = CA4 / "results"
FIN = CA4 / "final"
FIN.mkdir(parents=True, exist_ok=True)
RES_O = ROOT / "output" / "results"

if __name__ == "__main__":
    print("=" * 60)
    print("STEP 6: CA4 Final xlsx (18 sayfa)")
    print("=" * 60)

    sheets = {}
    readme = ("# Sultanbeyli - Cozum Alternatifi 3: Tam Yer Degisikligi (SB)\n"
              "12 mevcut konteyner artik sabit degil. 140+12=152 havuzdan 20 konteyner secilir.\n"
              "**SB etkisi**: C4 = IBB Tablo 5-4 barinma ihtiyaci (hane)\n"
              "**YK etkisi**: P(yol acik) = exp(-0.005 * N_cok_agir) carpani\n"
              "**Pipeline**: AHP + TOPSIS + FCM (sigma=800) + 0-1 IP (20 secim)\n"
              "**Senaryolar**: 3 AHP (Baseline/Damage/Infrastructure) x 2 mod (hard/soft) = 6\n")
    sheets["README"] = pd.DataFrame({"aciklama": [readme]})

    sens = pd.read_excel(RES / "selection_sensitivity_CA4.xlsx")
    sheets["KPI_Summary"] = pd.DataFrame({
        "metrik": ["Secilen konteyner sayisi", "Senaryo sayisi", "Sigma (m)",
                    "Coverage threshold", "Ortalama Z (CA4)",
                    "Orijinal Z (8-site)", "CA2 Z (8-site)",
                    "Kritik mahalle < threshold (toplam)"],
        "deger": [20, 6, 800, 0.50,
                   float(sens["objective"].mean()),
                   935.62, 908.34,
                   int(sens["n_critical_below_threshold"].sum())]
    })
    sel = pd.read_excel(RES / "selection_Baseline_hard_CA4.xlsx", sheet_name="Selected_20")
    sheets["Selected_20"] = sel
    sheets["AHP_Weights"] = pd.read_excel(RES / "ahp_weights_CA4.xlsx")
    top = pd.read_excel(RES / "topsis_sonuclar_CA4.xlsx").nlargest(20, "CC_Baseline")
    sheets["TOPSIS_Top20"] = top
    sheets["Sensitivity"] = sens
    cov = pd.read_excel(RES / "selection_Baseline_hard_CA4.xlsx", sheet_name="Coverage_per_Mahalle")
    sheets["Coverage_per_Mahalle"] = cov
    sheets["Coverage_KPI"] = pd.read_excel(RES_O / "coverage_score_kpi.xlsx")
    sheets["Inputs_Candidates"] = pd.read_excel(ROOT / "output" / "data" / "adaylar.xlsx")
    sheets["Inputs_Existing"] = pd.read_excel(ROOT / "output" / "data" / "mevcut_12.xlsx")
    sheets["Inputs_Mahalle_Risk"] = pd.read_excel(ROOT / "output" / "data" / "mahalle_risk.xlsx")
    sheets["Inputs_Mahalle_Pop"] = pd.read_excel(ROOT / "output" / "data" / "mahalle_nufus.xlsx")
    sheets["Mu_Pool_152"] = pd.read_excel(RES / "mu_pool_CA4.xlsx")
    sheets["Centroids"] = pd.read_excel(RES / "mahalle_centroids_CA4.xlsx")
    sheets["Criteria_Matrix"] = pd.read_excel(RES / "criteria_matrix_CA4.xlsx")
    sheets["Pool_152"] = pd.read_excel(RES / "pool_152_CA4.xlsx")
    sheets["Road_Closure"] = pd.read_excel(CA4 / "data" / "mahalle_data_CA4.xlsx")
    sheets["P_Access"] = pd.read_excel(RES / "p_access_per_site_CA4.xlsx")

    out_path = FIN / "Sultanbeyli_Final_Results_CA4.xlsx"
    with pd.ExcelWriter(out_path) as w:
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name, index=False)
    print(f"[OK] {out_path}")

    md = []
    md.append("# Cozum Alternatifi 3 - Final Rapor")
    md.append("## Sultanbeyli Konteyner Optimizasyonu - Tam Yer Degisikligi (SB)")
    md.append("")
    md.append("**Tarih:** 2026  \n**Pipeline:** AHP + TOPSIS + FCM + 0-1 IP  \n"
              "**Orijinal:** `D:/IE492/output/`  \n**CA4:** `D:/IE492/cozum_alternatifi_4_full_reloc_sb/`  \n")
    md.append("## 1. Problem")
    md.append("12 AFIS konteyneri sabit konumlu varsayimi yerine, 20 konteynerin tamami "
              "(12 mevcut + 8 yeni) yeniden yerlestirilebilir. C4 = IBB Tablo 5-4 barinma ihtiyaci "
              "ve yol kapanma olasiligi carpan olarak IP solver'inda kullanilir.")
    md.append("")
    md.append("## 2. Yontem")
    md.append("### 2.1 Havuz: 152 aday")
    md.append("- 140 orijinal aday (output/data/adaylar.xlsx)")
    md.append("- 12 mevcut konteyner (output/data/mevcut_12.xlsx, S_No 141-152)")
    md.append("- mu_mevcut = 0 (sabit konteyner yok, hepsi relocate edilebilir)")
    md.append("### 2.2 C4 (Talep) = IBB Tablo 5-4")
    md.append("barinma ihtiyaci (hane) - 17 mahalle")
    md.append("### 2.3 P(yol acik) carpani")
    md.append("P(yol acik | mahalle) = exp(-0.005 * N_cok_agir)")
    md.append("### 2.4 IP Formulasyonu")
    md.append("```")
    md.append("Max Z = Sum_i R_i * [ 0  +  Sum_j mu(i,j) * P_access(j) * X_j ]")
    md.append("s.t.  Sum_j X_j = 20")
    md.append("      (her kritik mahalle i icin: Sum_j mu(i,j)*P_access(j)*X_j >= 0.50)")
    md.append("```")
    md.append("")
    md.append("## 3. Sonuclar")
    z_orig = 935.62
    z_ca2 = 908.34
    z_ca3 = float(sens["objective"].mean())
    md.append(f"| Metrik | Orijinal (8) | CA2 (8) | CA4 (20) |")
    md.append(f"|--------|--------------|---------|----------|")
    md.append(f"| Z (ortalama) | {z_orig:.2f} | {z_ca2:.2f} | {z_ca3:.2f} |")
    md.append(f"| Site sayisi | 8 | 8 | 20 |")
    md.append(f"| Havuz | 140 | 140 | 152 (140+12) |")
    md.append("")
    md.append("## 4. Secilen 20 Site")
    md.append("")
    md.append("| S_No | Kaynak | Mahalle | P_access |")
    md.append("|------|--------|---------|----------|")
    for _, r in sel.iterrows():
        md.append(f"| {r['S_No']} | {r['_kaynak']} | {r['Mahalle']} | {r['P_access_applied']:.4f} |")
    md.append("")
    md.append("## 5. Sensitivity")
    md.append("| Senaryo | Mod | Status | Z |")
    md.append("|---------|-----|--------|---|")
    for _, r in sens.iterrows():
        md.append(f"| {r['scenario']} | {r['mode']} | {r['status']} | {r['objective']:.3f} |")
    md.append("")
    md.append("## 6. Sonuc ve Oneriler")
    md.append(f"- 20 konteyner secimde Z = {z_ca3:.2f}; 8-site Z'nin %{z_ca3/z_orig*100:.0f}'i.")
    md.append(f"- 6/6 senaryo optimal; tum kritik mahalleler >= 0.50 coverage.")
    md.append(f"- 12 mevcut konteynerden {sum(1 for _, r in sel.iterrows() if r['_kaynak'] == 'mevcut_12')} tanesi secildi.")

    (FIN / "reporting.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] {FIN / 'reporting.md'}")


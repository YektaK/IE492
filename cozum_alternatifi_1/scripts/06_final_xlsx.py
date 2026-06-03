# -*- coding: utf-8 -*-
"""
06_final_xlsx.py - Consolidated final xlsx (mirrors original Sultanbeyli_Final_Results)
ÇÖZÜM ALTERNATİFİ 1

Produces:
  final/Sultanbeyli_Final_Results_CA1.xlsx   (18 sheets)
"""
import math
import unicodedata
import pandas as pd
import numpy as np
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path("D:/IE492/cozum_alternatifi_1")
DATA = ROOT / "data"
RES = ROOT / "results"
FIN = ROOT / "final"
FIN.mkdir(parents=True, exist_ok=True)

CA1_NAME = "ÇÖZÜM ALTERNATİFİ 1 (C4 = İBB Barınma İhtiyacı)"


def norm(s):
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())


def style_header(cell, color="2F5496"):
    cell.font = Font(bold=True, color="FFFFFF", size=11)
    cell.fill = PatternFill("solid", fgColor=color)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def autosize(ws, max_w=40):
    for col_idx, col in enumerate(ws.columns, 1):
        max_len = 8
        col_letter = get_column_letter(col_idx)
        for cell in col:
            try:
                v = str(cell.value) if cell.value is not None else ""
                if len(v) > max_len:
                    max_len = len(v)
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 2, max_w)


if __name__ == "__main__":
    print("=" * 60)
    print(f"Final xlsx - {CA1_NAME}")
    print("=" * 60)

    ahp = pd.read_excel(RES / "ahp_weights.xlsx")
    crit = pd.read_excel(RES / "criteria_matrix.xlsx")
    topsis = pd.read_excel(RES / "topsis_sonuclar.xlsx")
    mu_a = pd.read_excel(RES / "mu_aday.xlsx")
    mu_m = pd.read_excel(RES / "mu_mevcut.xlsx")
    centroids = pd.read_excel(RES / "mahalle_centroids.xlsx")
    risk = pd.read_excel(DATA / "mahalle_risk.xlsx")
    sel = pd.read_excel(RES / "selection_Baseline_hard.xlsx")
    cov = pd.read_excel(RES / "selection_Baseline_hard.xlsx", sheet_name="Coverage_per_Mahalle")
    kpi = pd.read_excel(RES / "selection_Baseline_hard.xlsx", sheet_name="KPI")
    sens = pd.read_excel(RES / "selection_sensitivity.xlsx")
    shelter = pd.read_excel(RES.parent / "results" / "shelter_demand.xlsx") if (RES.parent / "results" / "shelter_demand.xlsx").exists() else None
    if shelter is None:
        shelter = pd.read_excel(ORIG_DATA := Path("D:/IE492/output/data/mahalle_barinma_ihtiyaci.xlsx"))

    OUT = FIN / "Sultanbeyli_Final_Results_CA1.xlsx"

    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        pd.DataFrame([{
            "Proje": "Sultanbeyli Konteyner Alanı Optimizasyonu",
            "Çözüm": "ALTERNATİF 1",
            "Talep proxy (C4)": "İBB Tablo 5-4 Barınma İhtiyacı (hane)",
            "Orijinal talep proxy": "TÜİK 2024 Gece Nüfusu",
            "Pipeline": "AHP + TOPSIS + FCM + 0-1 IP",
            "Aday sayısı": 140,
            "Mevcut konteyner": 12,
            "Yeni eklenecek": 8,
            "Kapsama yarıçapı (σ)": "800 m",
            "Eşik (kritik mahalle)": "0.50 toplam μ",
            "Kaynak veri": "İBB Sultanbeyli Deprem Raporu, TÜİK 2024, AYDES",
        }]).to_excel(writer, sheet_name="00_Ozet", index=False)

        ahp.to_excel(writer, sheet_name="01_AHP_Weights", index=False)
        crit.to_excel(writer, sheet_name="02_Criteria_Matrix", index=False)
        topsis.to_excel(writer, sheet_name="03_TOPSIS_Sonuclar", index=False)
        mu_a.to_excel(writer, sheet_name="04_mu_Aday_140", index=False)
        mu_m.to_excel(writer, sheet_name="05_mu_Mevcut_12", index=False)
        centroids.to_excel(writer, sheet_name="06_Mahalle_Centroids", index=False)
        risk.to_excel(writer, sheet_name="07_Mahalle_Risk", index=False)
        sel.to_excel(writer, sheet_name="08_Selected_8", index=False)
        cov.to_excel(writer, sheet_name="09_Coverage_Per_Mahalle", index=False)
        kpi.to_excel(writer, sheet_name="10_KPI", index=False)
        sens.to_excel(writer, sheet_name="11_Sensitivity_3x2", index=False)
        shelter.to_excel(writer, sheet_name="12_Shelter_Demand_IBB", index=False)

        cov_sens_rows = []
        for sc in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
            for mode in ["hard", "soft"]:
                p = RES / f"selection_{sc}_{mode}.xlsx"
                if p.exists():
                    c = pd.read_excel(p, sheet_name="Coverage_per_Mahalle")
                    c["scenario"] = sc
                    c["mode"] = mode
                    cov_sens_rows.append(c)
        if cov_sens_rows:
            pd.concat(cov_sens_rows, ignore_index=True).to_excel(
                writer, sheet_name="13_Coverage_Sensitivity", index=False)

        sel_sens_rows = []
        for sc in ["Baseline", "DamageFocused", "InfrastructureFocused"]:
            for mode in ["hard", "soft"]:
                p = RES / f"selection_{sc}_{mode}.xlsx"
                if p.exists():
                    s = pd.read_excel(p, sheet_name="Selected_8")
                    s["scenario"] = sc
                    s["mode"] = mode
                    sel_sens_rows.append(s)
        if sel_sens_rows:
            pd.concat(sel_sens_rows, ignore_index=True).to_excel(
                writer, sheet_name="14_Selection_Sensitivity", index=False)

        compare = pd.read_excel(ROOT / "comparison" / "compare_summary.xlsx", sheet_name="Summary")
        compare.to_excel(writer, sheet_name="15_vs_Orijinal", index=False)

        pd.DataFrame([{
            "Not": "Bu çözüm alternatifi orijinal pipeline'ın C4 kriterini (talep proxy) değiştirir.",
            "Orijinal C4": "Gece nüfusu (TÜİK 2024)",
            "Alternatif C4": "İBB Tablo 5-4 barınma ihtiyacı (hane)",
            "Gerekçe": "Barınma ihtiyacı doğrudan afete yönelik, nüfus daha genel bir göstergedir.",
            "Sonuç": "Solver aynı 8 site'ı seçti; talep proxy'sine karşı sağlam (robust).",
        }]).to_excel(writer, sheet_name="16_Notlar", index=False)

        reporting = pd.DataFrame([
            {"Bölüm": "1. Yöntem",
             "İçerik": "AHP ağırlıkları (3 senaryo) + TOPSIS sıralaması + FCM Gaussian üyeliği (σ=800m) + 0-1 IP (hard & soft)."},
            {"Bölüm": "2. Veri",
             "İçerik": "140 İBB aday yer, 12 mevcut konteyner, 17 mahalle. Talep: İBB Tablo 5-4 barınma ihtiyacı (hane)."},
            {"Bölüm": "3. Sonuç",
             "İçerik": "8 yeni konteyner: S4, S59, S60, S61, S62, S83, S88, S141. Tüm 5 kritik mahalle eşik üstü."},
            {"Bölüm": "4. Karşılaştırma",
             "İçerik": "Orijinal C4 (nüfus) ile aynı seçim. Z değerleri özdeş. Kapsama dağılımı özdeş."},
            {"Bölüm": "5. Çıkarım",
             "İçerik": "Sonuç C4 proxy seçimine duyarsız. Coğrafi kapsama ve kriter ağırlıkları belirleyici."},
        ])
        reporting.to_excel(writer, sheet_name="17_Raporlama", index=False)

    wb = openpyxl.load_workbook(OUT)
    for ws in wb.worksheets:
        for cell in ws[1]:
            style_header(cell, color="2F5496")
        ws.row_dimensions[1].height = 22
        autosize(ws, max_w=35)
        ws.freeze_panes = "A2"
    wb.save(OUT)
    print(f"[OK] {OUT}")
    print(f"     {len(wb.sheetnames)} sheet: {wb.sheetnames}")

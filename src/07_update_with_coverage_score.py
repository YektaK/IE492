"""
07_update_with_coverage_score.py
Append 'Toplam Kapsama Skoru' section to reporting.md and add a new sheet
to the Solver-ready Excel workbook.
"""
from __future__ import annotations
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT   = Path(r"D:\IE492\output")
RES   = OUT / "results"
FINAL = OUT / "final"

# ---- Load data ----
detailed = pd.read_excel(RES / "coverage_score_detailed.xlsx")
kpi      = pd.read_excel(RES / "coverage_score_kpi.xlsx")

n_total   = 17
n_urban   = 15
pct_b_all = 76.5
pct_p_all = 82.4
uplift_pp = 5.9
pct_b_urb = 86.7
pct_p_urb = 93.3

# ---- 1. Update reporting.md ----
REPORT = FINAL / "reporting.md"
text   = REPORT.read_text(encoding="utf-8")

new_section = f"""
## 6B. Toplam Kapsama Skoru (Mahalle Düzeyi, Eşik μ ≥ 0.50)

Bu metrik, bir mahallenin FCM üyelik fonksiyonu (σ=800m) ile **herhangi bir konteynerden** en az 0.50 kapsama alması koşulunu sayar. Mahalle sayısı / toplam mahalle sayısı yüzde olarak ifade edilir.

| Kapsam | Mevcut 12 Konteyner | Önerilen 20 Konteyner (12 + 8 yeni) | İyileşme |
|---|---:|---:|---:|
| **İlçe geneli (17 mahalle)** | **{pct_b_all:.1f}%** (13/17) | **{pct_p_all:.1f}%** (14/17) | **+{uplift_pp:.1f} yüzde puan** |
| **Kentsel mahalleler (15, orman alanları hariç)** | **{pct_b_urb:.1f}%** (13/15) | **{pct_p_urb:.1f}%** (14/15) | **+{pct_p_urb - pct_b_urb:.1f} yüzde puan** |
| **Ortalama FCM μ (17 mahalle, sürekli)** | 0.658 | 0.716 | +5.8 % |

### Eşik altında kalan mahalleler (μ < 0.50)
| Mahalle | Risk (R) | μ Mevcut 12 | μ Önerilen 20 | Açıklama |
|---|---:|---:|---:|---|
| TEFERRUC TEPE ORMANI | 0.0 | 0.000 | 0.000 | Yapısal orman alanı, aday yok |
| SALGAMLI DEVLET ORMANI | 0.0 | 0.000 | 0.000 | Yapısal orman alanı, aday yok |
| ADIL | 3.4 | 0.321 | 0.321 | Düşük riskli; 800m içinde mevcut konteyner yok, aday konteyner de eşik altı |
| HAMIDIYE | 32.7 | 0.473 ❌ | 0.992 ✓ | **2. en riskli mahalle → model 4 yeni konteynerle (S59/60/61/62) eşiğin üzerine taşıdı** |

### Yorumlama
- **Mevcut 12 konteyner** 17 mahallenin 13'ünü (%76.5) yeterli düzeyde kapsamaktadır; ancak en kritik ikinci mahalle olan **Hamidiye** eşiğin hemen altında (μ=0.473) kalmaktadır.
- **Önerilen 20 konteyner (12 mevcut + 8 yeni)** ile Hamidiye μ=0.992'ye çıkarılmış, ilçe kapsama oranı **%82.4**'e yükseltilmiştir.
- Orman alanları (Salgamlı, Teferruç) yapısal olarak kapsanamaz; bunlar hariç tutulduğunda kentsel kapsama **%86.7 → %93.3** olur.
- Model yalnızca "en iyi boş alanları" seçmekle kalmamış, **mevcut kaynakları sisteme dahil ederek 20 konteynerlik ağı bir bütün olarak optimize etmiştir**.
"""

# Insert after "## 6. KPI Summary" block, before "## 7. Coverage per Mahalle"
anchor_old = "## 7. Coverage per Mahalle"
assert anchor_old in text, "anchor not found in reporting.md"
text = text.replace(anchor_old, new_section.strip() + "\n\n## " + anchor_old.split("## ", 1)[1])

# Update the "Key Findings" section with the new metric
old_findings = "- Total FCM coverage uplift: **96.6%** vs baseline 12"
new_findings = (f"- Toplam Kapsama Skoru: **{pct_b_all:.1f}% → {pct_p_all:.1f}%** (17 mahalle, eşik μ≥0.50); "
                f"kentsel 15 mahallede **{pct_b_urb:.1f}% → {pct_p_urb:.1f}%**.\n"
                f"- Toplam FCM coverage uplift (sürekli): **+96.6%** vs baseline 12")
text = text.replace(old_findings, new_findings)

# Update deliverables list to mention the new figure
old_deliv = "- `coverage_comparison.png` - Per-mahalle coverage baseline vs proposed"
new_deliv = (f"- `coverage_comparison.png` - Per-mahalle coverage baseline vs proposed\n"
             f"- `toplam_kapsama_skoru.png` - **Toplam Kapsama Skoru karşılaştırması (% kapsanan mahalle, eşik μ≥0.50)**")
text = text.replace(old_deliv, new_deliv)

# Re-number 6B and update the next section number from 7 to 8 etc
# Actually keep 6B as inserted and let subsequent sections be 7/8/9 (already correct)
REPORT.write_text(text, encoding="utf-8")
print(f"[OK] Updated {REPORT}")

# ---- 2. Add new sheet to Excel workbook ----
XLSX = FINAL / "Sultanbeyli_Konteyner_Optimizasyon.xlsx"
wb = openpyxl.load_workbook(XLSX)

# Remove existing sheet if any
if "Toplam_Kapsama_Skoru" in wb.sheetnames:
    del wb["Toplam_Kapsama_Skoru"]

ws = wb.create_sheet("Toplam_Kapsama_Skoru", index=1)

# Styles
hdr_font   = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
hdr_fill   = PatternFill("solid", fgColor="2E5C8A")
sub_fill   = PatternFill("solid", fgColor="D6E4F0")
crit_fill  = PatternFill("solid", fgColor="F8D7DA")
good_fill  = PatternFill("solid", fgColor="D4EDDA")
thin = Side(border_style="thin", color="B0B0B0")
box  = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left   = Alignment(horizontal="left",   vertical="center", wrap_text=True)
bold   = Font(bold=True)
big_title = Font(name="Calibri", size=14, bold=True, color="2E5C8A")

# ---- Title ----
ws["A1"] = "Toplam Kapsama Skoru — Mevcut 12 vs Önerilen 20 Konteyner"
ws["A1"].font = big_title
ws.merge_cells("A1:F1")
ws.row_dimensions[1].height = 24

ws["A2"] = "Tanım: Bir mahalle, içindeki herhangi bir konteynerin FCM üyelik değeri (σ=800m) ≥ 0.50 ise 'yeterli kapsamda' sayılır. Yüzde = (kapsanan mahalle sayısı) / (toplam mahalle sayısı)."
ws["A2"].font = Font(italic=True, size=10, color="555555")
ws.merge_cells("A2:F2")
ws.row_dimensions[2].height = 30

# ---- KPI summary block ----
ws["A4"] = "Kapsam Düzeyi"
ws["B4"] = "Mevcut 12 Konteyner"
ws["C4"] = "Önerilen 20 Konteyner"
ws["D4"] = "İyileşme"
ws["E4"] = "Kapsanan Mahalle (Mevcut)"
ws["F4"] = "Kapsanan Mahalle (Önerilen)"
for c in ["A4","B4","C4","D4","E4","F4"]:
    ws[c].font = hdr_font
    ws[c].fill = hdr_fill
    ws[c].alignment = center
    ws[c].border = box

rows = [
    ("İlçe geneli (17 mahalle)", f"{pct_b_all:.1f}%", f"{pct_p_all:.1f}%", f"+{uplift_pp:.1f} yp", "13/17", "14/17"),
    ("Kentsel mahalleler (15, orman hariç)", f"{pct_b_urb:.1f}%", f"{pct_p_urb:.1f}%", f"+{pct_p_urb - pct_b_urb:.1f} yp", "13/15", "14/15"),
    ("Ortalama FCM μ (sürekli, 17 mahalle)", "0.658", "0.716", "+5.8 %", "—", "—"),
]
for i, row in enumerate(rows, start=5):
    for j, v in enumerate(row, start=1):
        c = ws.cell(row=i, column=j, value=v)
        c.alignment = center
        c.border = box
        c.fill = sub_fill if i % 2 == 0 else PatternFill("solid", fgColor="FFFFFF")
    # bold the percentage cells
    ws.cell(row=i, column=2).font = bold
    ws.cell(row=i, column=3).font = bold
    ws.cell(row=i, column=3).fill = good_fill

ws.row_dimensions[4].height = 32

# ---- Per-mahalle detail ----
hdr_row = 9
headers = ["Mahalle", "Risk R (%)", "μ Mevcut 12", "μ Önerilen 20", "Mevcut Kapsamda mı?", "Önerilen Kapsamda mı?", "İyileşme"]
for j, h in enumerate(headers, start=1):
    c = ws.cell(row=hdr_row, column=j, value=h)
    c.font = hdr_font
    c.fill = hdr_fill
    c.alignment = center
    c.border = box

# Sort: uncovered first (most informative), then by proposed coverage desc
det_sorted = detailed.sort_values(
    by=["Covered_Proposed", "Covered_Baseline", "Mu_Proposed_20"],
    ascending=[True, True, False]
).reset_index(drop=True)

for i, r in det_sorted.iterrows():
    rr = hdr_row + 1 + i
    ws.cell(row=rr, column=1, value=r["Mahalle"]).border = box
    ws.cell(row=rr, column=2, value=float(r["Risk_R_pct"])).border = box
    ws.cell(row=rr, column=3, value=float(r["Mu_Baseline_12"])).border = box
    ws.cell(row=rr, column=4, value=float(r["Mu_Proposed_20"])).border = box

    cb = ws.cell(row=rr, column=5, value="EVET" if r["Covered_Baseline"] else "HAYIR")
    cp = ws.cell(row=rr, column=6, value="EVET" if r["Covered_Proposed"] else "HAYIR")
    ws.cell(row=rr, column=7, value=float(r["Improvement"])).border = box

    for cc in (cb, cp):
        cc.alignment = center
        cc.border = box
    if r["Covered_Baseline"]:
        cb.fill = good_fill
    else:
        cb.fill = crit_fill
        cb.font = bold
    if r["Covered_Proposed"]:
        cp.fill = good_fill
    else:
        cp.fill = crit_fill
        cp.font = bold
    # risk color
    rc = ws.cell(row=rr, column=2)
    if rc.value >= 25:
        rc.font = Font(bold=True, color="C0392B")

# Column widths
widths = {"A": 28, "B": 12, "C": 14, "D": 14, "E": 20, "F": 20, "G": 12}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

# Add a comment / note
note_row = hdr_row + 2 + len(det_sorted)
ws.cell(row=note_row, column=1, value="Açıklama").font = bold
ws.cell(row=note_row+1, column=1, value=(
    "• Eşik: μ ≥ 0.50 (FCM Gaussian üyelik fonksiyonu, σ=800m).\n"
    "• 'Mevcut 12' = sadece mevcut 12 AFIS konteynerinden max μ; 'Önerilen 20' = 12 mevcut + 8 yeni seçilen konteynerden max μ.\n"
    "• Orman alanları (Salgamlı, Teferruç) yapısal olarak aday konteyner içermediğinden kapsama dışıdır.\n"
    "• Modelin asıl başarısı: en riskli 2. mahalle olan Hamidiye'yi (R=32.7) eşiğin üzerine taşımak (μ: 0.473 → 0.992)."
))
ws.merge_cells(start_row=note_row+1, end_row=note_row+5, start_column=1, end_column=7)
ws.cell(row=note_row+1, column=1).alignment = Alignment(wrap_text=True, vertical="top")
ws.cell(row=note_row+1, column=1).fill = PatternFill("solid", fgColor="FFF9E6")

wb.save(XLSX)
print(f"[OK] Added sheet 'Toplam_Kapsama_Skoru' to {XLSX}")

# ---- 3. Re-order sheets to put Toplam_Kapsama_Skoru right after KPI/Introduction ----
wb = openpyxl.load_workbook(XLSX)
desired = ["Aciklama", "Toplam_Kapsama_Skoru", "Mahalle_Datasi", "Optimizasyon", "Karar_Degiskenleri", "Cozum_Ozeti"]
existing = [s for s in desired if s in wb.sheetnames]
# Move them in order
for i, sname in enumerate(existing):
    ws = wb[sname]
    current_idx = wb.sheetnames.index(sname)
    if current_idx != i:
        wb.move_sheet(sname, offset=i - current_idx)
wb.save(XLSX)
print(f"[OK] Sheet order normalized: {wb.sheetnames}")

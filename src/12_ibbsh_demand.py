# -*- coding: utf-8 -*-
"""
12_ibbsh_demand.py
Extracts IBB Report Table 5-4 (Temporary Shelter Need by Mahalle)
and adds it as a new demand signal to the project.

Output:
  output/data/mahalle_barinma_ihtiyaci.xlsx     raw IBB values
  output/results/shelter_demand.xlsx           normalized + ranking
  output/results/shelter_vs_nightpop.xlsx      comparison vs current C4
  output/figures/shelter_demand_map.png        bar chart by mahalle
"""
from pathlib import Path
import docx
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path("D:/IE492")
DOC = ROOT / "docs" / "Sultanbeyli Deprem raporu iBB.docx"
DATA = ROOT / "output" / "data"
RES = ROOT / "output" / "results"
FIG = ROOT / "output" / "figures"

# ---------------------------------------------------------------------------
# 1. Extract Table 5-4 (Temporary Shelter Need) from the IBB docx
# ---------------------------------------------------------------------------
d = docx.Document(str(DOC))
t = d.tables[4]  # 5th table = 5-4
rows = []
for r in t.rows[1:-1]:  # skip header and TOPLAM
    mah = r.cells[0].text.strip()
    hane = r.cells[1].text.strip()
    if mah and hane:
        # 1.763 -> 1763 (dotted thousands)
        hane_val = int(hane.replace(".", "").replace(",", "")) if hane.replace(".", "").replace(",", "").isdigit() else 0
        rows.append({"mahalle_ibb": mah, "hane_ihtiyaci": hane_val})

ibbsh_raw = pd.DataFrame(rows)
print(f"Extracted {len(ibbsh_raw)} mahalle from IBB Table 5-4")
print(ibbsh_raw.to_string(index=False))

# Normalize names to match our mahalle_nufus keys (uppercase, no diacritics)
def norm(s):
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return s.translate(tr).upper().strip()

ibbsh_raw["mahalle"] = ibbsh_raw["mahalle_ibb"].apply(norm)
ibbsh_raw["mahalle"] = ibbsh_raw["mahalle"].str.replace(" SALGAMLI DEVLET ORMANI", "SALGAMLI DEVLET ORMANI")
ibbsh_raw["mahalle"] = ibbsh_raw["mahalle"].str.replace(" TEFERRUC TEPE ORMANI", "TEFERRUC TEPE ORMANI")

ibbsh = ibbsh_raw[["mahalle", "hane_ihtiyaci"]].copy()
ibbsh.to_excel(DATA / "mahalle_barinma_ihtiyaci.xlsx", index=False)
print(f"[OK] {DATA / 'mahalle_barinma_ihtiyaci.xlsx'}")

# ---------------------------------------------------------------------------
# 2. Compare with current C4 (night pop) and risk score
# ---------------------------------------------------------------------------
nufus = pd.read_excel(DATA / "mahalle_nufus.xlsx")
risk = pd.read_excel(DATA / "mahalle_risk.xlsx")

comp = ibbsh.merge(nufus, on="mahalle").merge(
    risk[["mahalle", "can_kaybi", "risk_score"]], on="mahalle")

# Add normalized scores (0-1)
def norm01(s):
    return (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0

comp["C4_NightPop_norm"] = norm01(comp["nufus_2024"])
comp["Shelter_norm"] = norm01(comp["hane_ihtiyaci"])
comp["Demand_proxy_delta"] = comp["Shelter_norm"] - comp["C4_NightPop_norm"]
comp = comp.sort_values("hane_ihtiyaci", ascending=False).reset_index(drop=True)

comp.to_excel(RES / "shelter_vs_nightpop.xlsx", index=False)
print(f"[OK] {RES / 'shelter_vs_nightpop.xlsx'}")

# ---------------------------------------------------------------------------
# 3. Shelter demand only (for IP/excel use)
# ---------------------------------------------------------------------------
shelter_demand = comp[["mahalle", "hane_ihtiyaci"]].copy()
shelter_demand["shelter_norm"] = comp["Shelter_norm"]
shelter_demand.to_excel(RES / "shelter_demand.xlsx", index=False)
print(f"[OK] {RES / 'shelter_demand.xlsx'}")

# ---------------------------------------------------------------------------
# 4. Bar chart: shelter need vs night pop, side by side
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 7))
mhs = comp["mahalle"].str.replace(" DEVLET ORMANI", "").str.replace(" TEPE ORMANI", "")
x = range(len(mhs))
w = 0.38
ax.bar([i - w/2 for i in x], comp["hane_ihtiyaci"], w, label="İBB Tablo 5-4 - Barınma ihtiyacı (hane)", color="crimson", alpha=0.85)
ax.bar([i + w/2 for i in x], comp["nufus_2024"], w, label="Gece nüfusu (TÜİK 2024)", color="steelblue", alpha=0.7)
ax.set_xticks(list(x))
ax.set_xticklabels(mhs, rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Hane / Kişi", fontsize=11)
ax.set_title("Sultanbeyli - Barınma İhtiyacı (İBB Tablo 5-4) vs Gece Nüfusu (TÜİK 2024)\n17 mahalle, Mw=7.5 senaryo depremi", fontsize=12, fontweight="bold")
ax.legend(loc="upper right")
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(FIG / "shelter_demand_map.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"[OK] {FIG / 'shelter_demand_map.png'}")

print()
print("=" * 60)
print("Quick stats:")
print(f"  Total shelter need: {ibbsh['hane_ihtiyaci'].sum():,} hane")
print(f"  Largest: {ibbsh.loc[ibbsh['hane_ihtiyaci'].idxmax(), 'mahalle']} ({ibbsh['hane_ihtiyaci'].max():,})")
print(f"  Smallest (excl. forests): {ibbsh[ibbsh['hane_ihtiyaci'] > 0].sort_values('hane_ihtiyaci').iloc[0]['mahalle']}")
print()
print("Demand proxy delta (Shelter - NightPop, both 0-1 normalized):")
print(comp[["mahalle", "hane_ihtiyaci", "nufus_2024", "Demand_proxy_delta"]].to_string(index=False))

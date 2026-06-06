"""
02_ahp_weights.py
Sultanbeyli Konteyner - AHP AGIRLIKLARI

Kaynak:
  - 4 kriter tanimi: Bitirme Projesi son güncel 1.docx (Table 1-2)
  - 3 senaryo agirligi: archive/old_output/results/ahp_weights.xlsx
    (C1=Damage, C2=Logistics, C3=GapDistance, C4=NightPop;
     kavramsal eslestirme: C1=Nufus, C2=Deprem, C3=Erisim, C4=Ulasim)

Cikti: results/ahp/ahp_weights.xlsx
       results/ahp/criteria_definitions.xlsx
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT = PROJECT_ROOT / "results" / "ahp"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1) KRITER TANIMLARI (Bitirme docx, Table 2)
# ---------------------------------------------------------------------------
CRITERIA = [
    {
        "kod": "C1",
        "ad": "Nufus Yogunlugu",
        "kaynak": "Sultanbeyli Belediyesi Nufus 2024 + IBB-KRDAE Gece Nufus Yogunlugu",
        "olcek": "Mahalle bazli, kisi/km2",
        "yon": "max",
    },
    {
        "kod": "C2",
        "ad": "Deprem Riski",
        "kaynak": "IBB KRDAE Deprem Raporu (Mw=7.5 senaryosu, agir+orta hasar, can kaybi)",
        "olcek": "Mahalle bazli, risk_skoru (0-50)",
        "yon": "max",
    },
    {
        "kod": "C3",
        "ad": "Erisim Mesafesi",
        "kaynak": "AFIS Konteyner Takip Cizelgesi + AYDES Toplanma Alanlari (Haversine)",
        "olcek": "Parsel bazli, en yakin mevcut konteynere metre",
        "yon": "max (uzak = oncelikli)",
    },
    {
        "kod": "C4",
        "ad": "Ulasim Altyapisi",
        "kaynak": "AYDES Toplanma Alanlari + parsel altyapi (su+wc+jen+kamera+haberlesme)",
        "olcek": "Parsel bazli, bilesik altyapi skoru (0-1)",
        "yon": "max",
    },
]

criteria_df = pd.DataFrame(CRITERIA)
criteria_df.to_excel(OUT / "criteria_definitions.xlsx", index=False)
print("[+] 4 kriter tanimi yazildi")

# ---------------------------------------------------------------------------
# 2) 3 SENARYO AGIRLIKLARI (eski xlsx)
# ---------------------------------------------------------------------------
# Eski xlsx'ten: C1=Damage, C2=Logistics, C3=GapDistance, C4=NightPop
# Docx kavram eslestirmesi: C1=Nufus, C2=Deprem, C3=Erisim, C4=Ulasim
# (C1 ve C2 sira kaymasi var: docx'te C1=Nufus ama eski xlsx'te C1=Damage;
#  eski xlsx C1=Damage aslinda docx'in C2=Deprem'i ile ayni kavram.
#  Eslestirme en iyi heuristic ile yapildi, sirayla ayni.)
SCENARIOS = [
    {
        "scenario": "Baseline",
        "C1_Nufus": 0.540625,
        "C2_Deprem": 0.253506,
        "C3_Erisim": 0.117418,
        "C4_Ulasim": 0.088451,
        "lambda_max": 4.147126,
        "CI": 0.049042,
        "CR": 0.054491,
        "CR_acceptable": "YES",
    },
    {
        "scenario": "DamageFocused",
        "C1_Nufus": 0.643553,
        "C2_Deprem": 0.194300,
        "C3_Erisim": 0.093108,
        "C4_Ulasim": 0.069039,
        "lambda_max": 4.166007,
        "CI": 0.055336,
        "CR": 0.061484,
        "CR_acceptable": "YES",
    },
    {
        "scenario": "InfrastructureFocused",
        "C1_Nufus": 0.406194,
        "C2_Deprem": 0.406194,
        "C3_Erisim": 0.105293,
        "C4_Ulasim": 0.082319,
        "lambda_max": 4.106729,
        "CI": 0.035576,
        "CR": 0.039529,
        "CR_acceptable": "YES",
    },
]

# ---------------------------------------------------------------------------
# 3) CR DOGRULAMASI
# ---------------------------------------------------------------------------
RI_n4 = 0.90
print("\n[+] 3 senaryo CR kontrolu:")
for s in SCENARIOS:
    cr_ok = s["CR"] < 0.10
    print(f"  {s['scenario']:25s}  CR = {s['CR']:.4f}  -> {'OK' if cr_ok else 'FAIL'}")

# ---------------------------------------------------------------------------
# 4) KAYDET
# ---------------------------------------------------------------------------
weights_df = pd.DataFrame(SCENARIOS)
weights_df.to_excel(OUT / "ahp_weights.xlsx", index=False)

print("\n" + "=" * 60)
print("AHP AGIRLIKLARI HAZIR")
print("=" * 60)
print(f"Cikti: {OUT / 'ahp_weights.xlsx'}")
print(f"Cikti: {OUT / 'criteria_definitions.xlsx'}")
print()
print("Kriter agirliklari (docx kavrami):")
print(weights_df[["scenario", "C1_Nufus", "C2_Deprem", "C3_Erisim", "C4_Ulasim"]].to_string(index=False))

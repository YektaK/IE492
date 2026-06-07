"""
02_ahp_weights.py
Sultanbeyli Konteyner - AHP AGIRLIKLARI

Kaynak:
  - 4 kriter tanimi: Bitirme Projesi son güncel 1.docx (Table 1-2)
  - 3 senaryo agirligi: archive/old_output/results/ahp_weights.xlsx
    (C1=Damage, C2=Logistics, C3=GapDistance, C4=NightPop;
     kavramsal eslestirme: C1=Nufus, C2=Deprem, C3=Erisim, C4=Ulasim)

Degisiklik (Faz 1, Gorev 1.5):
  Eski: Sadece sonuc agirliklar hardcoded (trace yok).
  Yeni: Ikili karsilastirma matrisleri acikca tanimlanmis;
        eigenvalue yontemi ile agirliklar hesaplaniyor;
        CR dogrulama matristen turetiliyor.
  Bu yaklasim: akademik seffaflik + juri denetlenebilirligi saglar.

Cikti: results/ahp/ahp_weights.xlsx
       results/ahp/criteria_definitions.xlsx
       results/ahp/ahp_pairwise_matrices.json
"""

from __future__ import annotations
import json
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
# 2) AHP YARDIMCI FONKSIYONLARI
# ---------------------------------------------------------------------------
# Saaty (1980) rassal tutarlilik indeksleri (n=4 icin RI=0.90)
RI_TABLE = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
             6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}


def ahp_from_matrix(A: np.ndarray, scenario_name: str) -> dict:
    """
    Ikili karsilastirma matrisinden AHP agirliklari uret.

    Yontem: Dominant eigenvector (Saaty 1980)
      1) Her sutunu kendi toplamina bol (normalize)
      2) Satir ortalamasi al -> agirlik vektoru w
      3) lambda_max = ortalama( (A @ w)_i / w_i )
      4) CI = (lambda_max - n) / (n - 1)
      5) CR = CI / RI[n]

    Parametre
    ---------
    A : np.ndarray (n, n)  --- ikili karsilastirma matrisi
    scenario_name : str    --- senaryo adi (raporlama icin)

    Donus
    -----
    dict: agirliklar, lambda_max, CI, CR, CR_acceptable, pairwise_matrix
    """
    n = A.shape[0]
    assert A.shape == (n, n), "Matris kare olmali"

    # Karsitlik tutarliligi: A[i,j] * A[j,i] yaklasik 1 olmali
    for i in range(n):
        for j in range(i + 1, n):
            product = A[i, j] * A[j, i]
            if abs(product - 1.0) > 1e-4:
                print(f"  [UYARI] {scenario_name}: A[{i},{j}]*A[{j},{i}] = {product:.4f} != 1")

    # Adim 1: Sutun normalize
    col_sums = A.sum(axis=0)
    A_norm = A / col_sums

    # Adim 2: Satir ortalamalari -> agirlik vektoru
    w = A_norm.mean(axis=1)
    w = w / w.sum()   # sayisal kayan nokta hatalarina karsi normalize

    # Adim 3: lambda_max
    Aw = A @ w
    lambda_max = float((Aw / w).mean())

    # Adim 4-5: CI, CR
    CI = (lambda_max - n) / (n - 1)
    RI = RI_TABLE.get(n, 1.0)
    CR = CI / RI if RI > 0 else 0.0

    return {
        "scenario":        scenario_name,
        "C1_Nufus":        round(float(w[0]), 6),
        "C2_Deprem":       round(float(w[1]), 6),
        "C3_Erisim":       round(float(w[2]), 6),
        "C4_Ulasim":       round(float(w[3]), 6),
        "lambda_max":      round(lambda_max, 6),
        "CI":              round(CI, 6),
        "CR":              round(CR, 6),
        "CR_acceptable":   "YES" if CR < 0.10 else "NO",
        "pairwise_matrix": A.tolist(),
    }


# ---------------------------------------------------------------------------
# 3) IKILI KARSILASTIRMA MATRISLERI — 3 SENARYO
# ---------------------------------------------------------------------------
# Satir/Sutun sirasi: [C1_Nufus, C2_Deprem, C3_Erisim, C4_Ulasim]
# A[i,j] = i. kriterin j. kritere gore goreli onemi (Saaty 1-9 olcegi)
# A[j,i] = 1 / A[i,j]  (otomatik saglanmali)
#
# Saaty olcegi hatirlatma:
#   1 = esit onem   3 = orta   5 = guclu   7 = cok guclu   9 = mutlak

print("\n[+] Ikili karsilastirma matrisleri tanimlaniyor...")

# ---- Senaryo 1: Baseline ----
# Nufus yogunlugu baskın; deprem riski ikincil; erisim ve altyapi tali
# Gerekce: Sultanbeyli'de nufus yogunlugu hasarin boyutunu belirler;
#          kalabalik mahallelere ulasim her seyden once gelir.
A_baseline = np.array([
    [1,     3,     5,     7   ],
    [1/3,   1,     3,     5   ],
    [1/5,   1/3,   1,     3   ],
    [1/7,   1/5,   1/3,   1   ],
], dtype=float)

# ---- Senaryo 2: DamageFocused ----
# Deprem hasarı ve nüfus birlikte maksimum oneme sahip;
# can kaybi riski yuksek mahallelere neredeyse tum agirlik verilir.
A_damage = np.array([
    [1,     4,     7,     9   ],
    [1/4,   1,     3,     5   ],
    [1/7,   1/3,   1,     3   ],
    [1/9,   1/5,   1/3,   1   ],
], dtype=float)

# ---- Senaryo 3: InfrastructureFocused ----
# Nüfus ve deprem riski esit agirlikta; her ikisi de cok kritik.
# Altyapi duzgun olan konum, mudahaleyi hizlandirir.
A_infra = np.array([
    [1,     1,     5,     7   ],
    [1,     1,     5,     7   ],
    [1/5,   1/5,   1,     3   ],
    [1/7,   1/7,   1/3,   1   ],
], dtype=float)

# ---------------------------------------------------------------------------
# 4) AGIRLIKLARI HESAPLA & CR DOGRULA
# ---------------------------------------------------------------------------
print("\n[+] AHP agirliklari hesaplaniyor (eigenvalue yontemi)...")

results_raw = [
    ahp_from_matrix(A_baseline, "Baseline"),
    ahp_from_matrix(A_damage,   "DamageFocused"),
    ahp_from_matrix(A_infra,    "InfrastructureFocused"),
]

# CR dogrulama
print("\n[+] 3 senaryo CR kontrolu:")
for r in results_raw:
    cr_ok = r["CR"] < 0.10
    status = "OK" if cr_ok else "FAIL — CR>=0.10, matris tutarsiz!"
    print(f"  {r['scenario']:25s}  CR = {r['CR']:.4f}  -> {status}")
    if not cr_ok:
        raise ValueError(
            f"Senaryo '{r['scenario']}' CR={r['CR']:.4f} >= 0.10! "
            "Ikili karsilastirma matrisini gozden gecirin."
        )

# ---------------------------------------------------------------------------
# 5) KAYDET
# ---------------------------------------------------------------------------
SCENARIOS = []
for r in results_raw:
    row = {k: v for k, v in r.items() if k != "pairwise_matrix"}
    SCENARIOS.append(row)

weights_df = pd.DataFrame(SCENARIOS)
weights_df.to_excel(OUT / "ahp_weights.xlsx", index=False)

# Pairwise matrisler JSON (akademik dokumantasyon)
pairwise_export = {}
for r in results_raw:
    pairwise_export[r["scenario"]] = {
        "matrix":          r["pairwise_matrix"],
        "criteria_order":  ["C1_Nufus", "C2_Deprem", "C3_Erisim", "C4_Ulasim"],
        "weights": {
            "C1_Nufus":  r["C1_Nufus"],
            "C2_Deprem": r["C2_Deprem"],
            "C3_Erisim": r["C3_Erisim"],
            "C4_Ulasim": r["C4_Ulasim"],
        },
        "lambda_max":     r["lambda_max"],
        "CI":             r["CI"],
        "CR":             r["CR"],
        "CR_acceptable":  r["CR_acceptable"],
        "RI_n4":          RI_TABLE[4],
    }
pairwise_path = OUT / "ahp_pairwise_matrices.json"
with open(pairwise_path, "w", encoding="utf-8") as f:
    json.dump(pairwise_export, f, ensure_ascii=False, indent=2)
print(f"\n  Pairwise matrisler kaydedildi: {pairwise_path}")

print("\n" + "=" * 60)
print("AHP AGIRLIKLARI HAZIR")
print("=" * 60)
print(f"Cikti: {OUT / 'ahp_weights.xlsx'}")
print(f"Cikti: {OUT / 'criteria_definitions.xlsx'}")
print(f"Cikti: {pairwise_path}")
print()
print("Kriter agirliklari (docx kavrami):")
print(weights_df[["scenario", "C1_Nufus", "C2_Deprem", "C3_Erisim", "C4_Ulasim", "CR", "CR_acceptable"]].to_string(index=False))

# ---------------------------------------------------------------------------
# 6) ESKI HARDCODED DEGERLERLE KARSILASTIRMA (referans)
# ---------------------------------------------------------------------------
HARDCODED_REF = {
    "Baseline":              [0.540625, 0.253506, 0.117418, 0.088451],
    "DamageFocused":         [0.643553, 0.194300, 0.093108, 0.069039],
    "InfrastructureFocused": [0.406194, 0.406194, 0.105293, 0.082319],
}
keys = ["C1_Nufus", "C2_Deprem", "C3_Erisim", "C4_Ulasim"]
print("\n[+] Eski hardcoded degerlerle karsilastirma:")
for r in results_raw:
    ref = HARDCODED_REF.get(r["scenario"], [None] * 4)
    new = [r[k] for k in keys]
    diffs = [abs(n - o) for n, o in zip(new, ref) if o is not None]
    max_diff = max(diffs) if diffs else 0.0
    flag = "(tutarli)" if max_diff < 0.05 else "(FARK VAR — matris gozden gecirin)"
    print(f"  {r['scenario']:25s}  max_diff={max_diff:.4f}  {flag}")

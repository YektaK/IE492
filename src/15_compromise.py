# -*- coding: utf-8 -*-
"""
15_compromise.py
Compromise programming: Pareto cephesi (eps_constraint) uzerinde
her cozumun ideal noktaya (max RxC, max min_cov) uzakligini hesapla.
En kisa uzaklikli cozum onerilir.

L_p normu ile: d = [sum_k (|f*_k - f_k|/range_k)^p]^(1/p)
p=1: aritmetik ortalama
p=2: oklid
p=inf: maksimum (kok noktasi)
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
RES  = ROOT / "results"
OUT  = ROOT / "results" / "compromise"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="A", choices=["A", "B"])
    args = parser.parse_args()
    SCENARIO = args.scenario
    print(f"== 15_compromise.py basladi (senaryo={SCENARIO}) ==")
    df = pd.read_excel(RES / "eps_constraint" / f"eps_pareto_S{SCENARIO}.xlsx")
    df = df.dropna(subset=["RxC", "min_cov"]).reset_index(drop=True)
    if len(df) < 2:
        print("  Yeterli Pareto noktasi yok, eps_constraint calistirilmamis olabilir.")
        return

    # Ideal nokta: her iki amac da maksimize ediliyor
    f_star = {
        "RxC": float(df["RxC"].max()),
        "min_cov": float(df["min_cov"].max())
    }
    f_anti = {
        "RxC": float(df["RxC"].min()),
        "min_cov": float(df["min_cov"].min())
    }
    ranges = {
        "RxC": f_star["RxC"] - f_anti["RxC"] if f_star["RxC"] != f_anti["RxC"] else 1.0,
        "min_cov": f_star["min_cov"] - f_anti["min_cov"] if f_star["min_cov"] != f_anti["min_cov"] else 1.0
    }

    print(f"  Ideal nokta: RxC*={f_star['RxC']:.4f}, min_cov*={f_star['min_cov']:.4f}")
    print(f"  Anti-ideal : RxC-={f_anti['RxC']:.4f}, min_cov-={f_anti['min_cov']:.4f}")

    # p=1, 2, inf normlari
    for p, label in [(1, "L1"), (2, "L2"), (np.inf, "Linf")]:
        df[f"d_{label}"] = 0.0
        for i, row in df.iterrows():
            d_terms = []
            for k in ["RxC", "min_cov"]:
                if p == np.inf:
                    d_terms.append(abs(f_star[k] - row[k]) / ranges[k])
                else:
                    d_terms.append((abs(f_star[k] - row[k]) / ranges[k]) ** p)
            if p == np.inf:
                df.at[i, f"d_{label}"] = max(d_terms)
            else:
                df.at[i, f"d_{label}"] = (sum(d_terms)) ** (1/p)

    # En iyi compromise her norm icin
    rows = []
    for label in ["L1", "L2", "Linf"]:
        best_idx = df[f"d_{label}"].idxmin()
        b = df.loc[best_idx]
        rows.append({
            "norm": label,
            "best_eps": float(b["eps"]),
            "RxC": float(b["RxC"]),
            "min_cov": float(b["min_cov"]),
            "distance": round(float(b[f"d_{label}"]), 4),
            "secilen": b["secilen"]
        })
        print(f"  {label}: eps={b['eps']}, RxC={b['RxC']:.4f}, min_cov={b['min_cov']:.4f}, d={b[f'd_{label}']:.4f}")

    out_df = pd.DataFrame(rows)
    out_path = OUT / f"compromise_solution_S{SCENARIO}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        out_df.to_excel(w, sheet_name="Onerilen", index=False)
        df.to_excel(w, sheet_name="Tum_Pareto_Noktalari", index=False)

    print(f"\n  -> {out_path}")

    # Markdown
    md = ["# Compromise Programming Sonucu\n",
          "**Ideal nokta:** max RxC + max min mahalle kapsama\n\n",
          f"| Norm | En iyi eps | RxC | min_C | Mesafe |\n",
          f"|------|------------|------|-------|--------|\n"]
    for r in rows:
        md.append(f"| L={r['norm']} | {r['best_eps']} | {r['RxC']:.4f} | "
                  f"{r['min_cov']:.4f} | {r['distance']:.4f} |\n")
    md_path = OUT / f"compromise_solution_S{SCENARIO}.md"
    md_path.write_text("".join(md), encoding="utf-8")
    print(f"  -> {md_path}")
    print("== 15_compromise.py tamamlandi ==")


if __name__ == "__main__":
    main()

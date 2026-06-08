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


def pareto_suffix(SCENARIO="A", SIGMA="800", K_TOTAL=20, BETA=0.30, WEIGHT_TYPE="risk", NO_MEVCUT=False):
    sg_str = "" if SIGMA == "800" else f"_sg{SIGMA}"
    b_str = f"_b{int(BETA * 100)}"
    k_str = f"_K{K_TOTAL}"
    nm_str = "_nomez" if NO_MEVCUT else ""
    wt_str = f"_{WEIGHT_TYPE}"
    return f"S{SCENARIO}{sg_str}{b_str}{k_str}{nm_str}{wt_str}"


def main(K_TOTAL=20, WEIGHT_TYPE="risk", argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--K", type=int, default=K_TOTAL)
    parser.add_argument("--weight", type=str, default=WEIGHT_TYPE)
    parser.add_argument("--scenario", default="A", choices=["A", "B"])
    parser.add_argument("--sigma", type=str, default="800")
    parser.add_argument("--beta", type=float, default=0.30)
    parser.add_argument("--no-mevcut", action="store_true")
    args = parser.parse_args(argv)
    
    K = args.K
    WT = args.weight
    suffix = pareto_suffix(args.scenario, args.sigma, K, args.beta, WT, args.no_mevcut)
    
    print(f"== 15_compromise.py basladi (K_Total={K}, Weight={WT}, scenario={args.scenario}, sigma={args.sigma}, beta={args.beta}) ==")
    file_path = RES / "eps_constraint" / f"pareto_results_{suffix}.xlsx"
    legacy_path = RES / "eps_constraint" / f"pareto_results_K{K}_{WT}.xlsx"
    if not file_path.exists() and legacy_path.exists():
        print(f"  Uyari: senaryo-ozel Pareto dosyasi bulunamadi, legacy dosya kullaniliyor: {legacy_path}")
        file_path = legacy_path
    if not file_path.exists():
        print(f"  Pareto dosyesi bulunamadi: {file_path}")
        return 1
        
    df = pd.read_excel(file_path)
    df = df.rename(columns={"eps_target": "eps", "actual_min_cov": "min_cov"})
    df = df.dropna(subset=["RxC", "min_cov"]).reset_index(drop=True)
    if len(df) < 2:
        print("  Yeterli Pareto noktasi yok, eps_constraint calistirilmamis olabilir.")
        return 1

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
            "secilen": b["selected_sites"]
        })
        print(f"  {label}: eps={b['eps']:.3f}, RxC={b['RxC']:.4f}, min_cov={b['min_cov']:.4f}, d={b[f'd_{label}']:.4f}")

    out_df = pd.DataFrame(rows)
    out_path = OUT / f"compromise_solution_{suffix}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        out_df.to_excel(w, sheet_name="Onerilen", index=False)
        df.to_excel(w, sheet_name="Tum_Pareto_Noktalari", index=False)

    print(f"\n  -> {out_path}")

    # Markdown
    md = f"# Compromise Programlama Onerisi ({suffix})\n\n"
    md += "Pareto cephesindeki noktalar ideal noktaya gore siralandi.\n\n"
    md += out_df.to_markdown(index=False)
    with open(OUT / f"compromise_{suffix}.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("== 15_compromise.py tamamlandi ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())

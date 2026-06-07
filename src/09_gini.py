# -*- coding: utf-8 -*-
"""
09_gini.py
Mahalle kapsama esitsizligi Gini katsayisi ile degerlendirme.

Gini = (sum_i sum_j |C_i - C_j|) / (2 * n * sum(C))

C_i: i. mahallenin toplam mu kapsamasi
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
RES  = ROOT / "results"
OUT  = ROOT / "results" / "gini"
OUT.mkdir(parents=True, exist_ok=True)


def gini(values: np.ndarray) -> float:
    """Dizinin Gini katsayisi (0=tam esitlik, 1=tam esitsizlik)."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if v.size == 0 or v.sum() == 0:
        return 0.0
    v = np.sort(v)
    n = v.size
    cum = np.cumsum(v)
    # G = (2 * sum_i i * x_i) / (n * sum) - (n+1)/n  (Lorenz tabanli)
    idx = np.arange(1, n + 1)
    return float((2.0 * np.sum(idx * v)) / (n * v.sum()) - (n + 1) / n)


def main():
    print("== 09_gini.py basladi ==")
    # coverage dosyalarini dinamik olarak oku
    models_dir = RES / "models"
    coverage_files = list(models_dir.glob("coverage_*.xlsx"))
    
    if not coverage_files:
        print("  Hic coverage dosyasi bulunamadi. Lutfen once 05_ip.py'yi calistirin.")
        return

    rows = []
    for path in coverage_files:
        v = path.stem.replace("coverage_", "")
        df = pd.read_excel(path)
        # 'mahalle' ve coverage sutununu bul
        cols = list(df.columns)
        # Olasilikli coverage kolonu isimleri
        target_col = None
        for cand in ["toplam_coverage", "C_i", "toplam_kapsama",
                     "toplam", "coverage", "mu_toplam"]:
            if cand in cols:
                target_col = cand
                break
        if target_col is None:
            # ilk sayisal kolonu sec (mahalle disinda)
            for c in cols:
                if c.lower() not in ["mahalle", "mahalle_norm", "s_no"] and pd.api.types.is_numeric_dtype(df[c]):
                    target_col = c
                    break
        c_values = df[target_col].values
        g = gini(c_values)
        rows.append({
            "versiyon": v,
            "mahalle_sayisi": len(c_values),
            "min_C": float(np.min(c_values)),
            "max_C": float(np.max(c_values)),
            "mean_C": float(np.mean(c_values)),
            "std_C": float(np.std(c_values)),
            "gini": round(g, 4),
        })
        print(f"  {v}: Gini={g:.4f}  min={np.min(c_values):.4f}  max={np.max(c_values):.4f}")

    out_df = pd.DataFrame(rows)
    out_path = OUT / "gini_results.xlsx"
    out_df.to_excel(out_path, index=False)
    print(f"\n  -> {out_path}")

    # Markdown ozet
    md = ["# Gini Esitsizligi Raporu\n",
          "Mahalle kapsama degerlerinin Gini katsayisi ", "**(0 = tam esitlik, 1 = tam esitsizlik)**.\n\n",
          "| Versiyon | min C_i | max C_i | ort C_i | std C_i | Gini |",
          "|----------|---------|---------|---------|---------|------|"]
    for r in rows:
        md.append(f"| {r['versiyon']} | {r['min_C']:.3f} | {r['max_C']:.3f} | "
                  f"{r['mean_C']:.3f} | {r['std_C']:.3f} | **{r['gini']:.3f}** |")
    md_text = "\n".join(md)
    md_path = OUT / "gini_results.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"  -> {md_path}")
    print("== 09_gini.py tamamlandi ==")


if __name__ == "__main__":
    main()

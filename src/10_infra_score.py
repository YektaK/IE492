# -*- coding: utf-8 -*-
"""
10_infra_score.py
V5 altyapi composite skoru: Su_bin + WC_bin + Jen_bin + Kamera_bin
ortalamasi. Mevcut C2 (Deprem Riski) yerine V5'te bu kullanilir.

Cikti: data/processed/criteria_matrix_V5.xlsx
"""

from __future__ import annotations
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
DATA = ROOT / "data" / "processed"
OUT  = DATA


def main():
    print("== 10_infra_score.py basladi (V5 altyapi composite) ==")

    aday = pd.read_excel(DATA / "adaylar_140.xlsx")
    crit_v4 = pd.read_excel(DATA / "criteria_matrix.xlsx")

    # Altyapi bilesen sutunlari
    bilesenler = ["Su_bin", "WC_bin", "Jen_bin", "Kamera_bin"]
    for b in bilesenler:
        if b not in aday.columns:
            print(f"  HATA: {b} bulunamadi, adaylar dosyasini kontrol edin")
            return
    # Composite: ortalama (0-1 arasi)
    aday["C2_infra_composite"] = aday[bilesenler].mean(axis=1)

    # criteria_matrix'i guncelle: S_No uzerinden join
    # V4 kriterleri + C2 yerine V5 composite
    merged = crit_v4.merge(
        aday[["S_No"] + bilesenler + ["C2_infra_composite"]],
        on="S_No", how="left"
    )

    # V4'te C2 hangi kolon? criteria_def'ten
    crit_def = pd.read_excel(ROOT / "results" / "ahp" / "criteria_definitions.xlsx")
    c2_adi = None
    for c in crit_def.columns:
        if c.lower().startswith("c2") or "deprem" in str(c).lower():
            c2_adi = c
            break
    if c2_adi is None:
        # V4'te risk_score olarak geciyor
        for cand in ["C2_Deprem", "C2_risk", "C2", "risk_score", "lojistik"]:
            if cand in merged.columns:
                c2_adi = cand
                break
    if c2_adi is None:
        c2_adi = "C2_lojistik"

    print(f"  C2 sutunu: {c2_adi}")
    merged["C2_V4_original"] = merged[c2_adi]
    merged["C2_V5_infra"] = merged["C2_infra_composite"]

    # Yeniden olcekle (0-1 normalize) - V4 ile karsilastirilabilir olmasi icin
    # V4'un C2'si muhtemelen farkli olcekte, biz V5'i V4'un min-max araligina normalize edelim
    v4 = merged["C2_V4_original"]
    v5_raw = merged["C2_V5_infra"]
    if v4.max() > v4.min():
        vmin, vmax = v4.min(), v4.max()
        merged["C2_V5_normalized"] = vmin + (v5_raw - v5_raw.min()) / (v5_raw.max() - v5_raw.min()) * (vmax - vmin)
    else:
        merged["C2_V5_normalized"] = v5_raw

    # Son hali: V4'un C2'si yerine V5 normalized
    merged_final = merged.drop(columns=[c2_adi]).rename(columns={"C2_V5_normalized": c2_adi})
    merged_final = merged_final[["S_No"] + [c for c in merged_final.columns if c != "S_No"]]

    out_path = OUT / "criteria_matrix_V5.xlsx"
    merged_final.to_excel(out_path, index=False)
    print(f"  V4 C2 ({c2_adi}) korundu, V5 composite eklendi: {out_path}")
    print(f"  V5 composite (C2_infra_composite) istatistik:")
    print(f"    min={v5_raw.min():.4f}  max={v5_raw.max():.4f}  ort={v5_raw.mean():.4f}")

    print("== 10_infra_score.py tamamlandi ==")


if __name__ == "__main__":
    main()

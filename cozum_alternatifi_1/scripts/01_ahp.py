# -*- coding: utf-8 -*-
"""
01_ahp.py - AHP weights computation (identical to original)
ÇÖZÜM ALTERNATİFİ 1 - Demand proxy = İBB Tablo 5-4 barınma ihtiyacı
"""
import math
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("D:/IE492/cozum_alternatifi_1")
RES = ROOT / "results"
RES.mkdir(parents=True, exist_ok=True)


def ahp_weights(pairwise):
    A = np.array(pairwise, dtype=float)
    n = A.shape[0]
    eigvals, eigvecs = np.linalg.eig(A)
    real_eigs = np.real(eigvals)
    idx = np.argmax(real_eigs)
    lambda_max = real_eigs[idx]
    v = np.real(eigvecs[:, idx])
    v = np.abs(v)
    w = v / v.sum()
    CI = (lambda_max - n) / (n - 1)
    RI_table = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
                6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    RI = RI_table.get(n, 1.49)
    CR = CI / RI if RI > 0 else 0.0
    return w, float(lambda_max), float(CI), float(CR)


AHPS = {
    "Baseline": [
        [1, 3, 5, 4],
        [1/3, 1, 3, 3],
        [1/5, 1/3, 1, 2],
        [1/4, 1/3, 1/2, 1],
    ],
    "DamageFocused": [
        [1, 5, 7, 6],
        [1/5, 1, 3, 3],
        [1/7, 1/3, 1, 2],
        [1/6, 1/3, 1/2, 1],
    ],
    "InfrastructureFocused": [
        [1, 1, 5, 4],
        [1, 1, 5, 4],
        [1/5, 1/5, 1, 2],
        [1/4, 1/4, 1/2, 1],
    ],
}


if __name__ == "__main__":
    print("=" * 60)
    print("AHP - Çözüm Alternatifi 1 (C4 = İBB barınma ihtiyacı)")
    print("=" * 60)

    rows = []
    for name, M in AHPS.items():
        w, lm, ci, cr = ahp_weights(M)
        rows.append({
            "scenario": name,
            "w_C1_Damage": float(w[0]),
            "w_C2_Logistics": float(w[1]),
            "w_C3_GapDistance": float(w[2]),
            "w_C4_Demand": float(w[3]),
            "lambda_max": lm,
            "CI": ci,
            "CR": cr,
            "CR_acceptable": "YES" if cr < 0.10 else "NO",
        })
        print(f"  {name:24s}  w=[{w[0]:.3f}, {w[1]:.3f}, {w[2]:.3f}, {w[3]:.3f}]  CR={cr:.4f} ({'OK' if cr<0.10 else 'REVIEW'})")

    df = pd.DataFrame(rows)
    df.to_excel(RES / "ahp_weights.xlsx", index=False)
    print(f"[OK] {RES / 'ahp_weights.xlsx'}")

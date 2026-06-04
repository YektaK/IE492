"""
CA8a - FCM Truncation
Mevcut mu matrisinden mu < 0.20 olan hucreleri sifirla.
Sadece "anlamli" iliskiler (~1.4 km icinde) IP'ye girer.

Cikti:
  - data/mu_aday_truncated.xlsx
  - data/mu_mevcut_truncated.xlsx
"""
import os
import pandas as pd
import numpy as np

ROOT = "D:/IE492"
CA = "cozum_alternatifi_8a_fcm_truncation"
DATA = os.path.join(ROOT, CA, "data")

THRESHOLD = 0.20
MAHALLE_KEYS = ("Mahalle", "mahalle")


def truncate(df, cols_to_check):
    n_cells = 0
    n_zeroed = 0
    for col in cols_to_check:
        if col in df.columns:
            n_cells += len(df[col])
            mask = df[col].astype(float) < THRESHOLD
            n_zeroed += int(mask.sum())
            df.loc[mask, col] = 0.0
    return df, n_cells, n_zeroed


def main():
    mu_aday = pd.read_excel(os.path.join(DATA, "mu_aday_orig.xlsx"))
    mu_mev = pd.read_excel(os.path.join(DATA, "mu_mevcut_orig.xlsx"))

    skip = {"_id", "S_No", "container_no", "Mahalle", "mahalle", "_TOTAL_mu", "_mh_norm"}
    cols_aday = [c for c in mu_aday.columns if c not in skip]
    cols_mev = [c for c in mu_mev.columns if c not in skip]

    mu_aday_t, n_a, z_a = truncate(mu_aday, cols_aday)
    mu_mev_t, n_m, z_m = truncate(mu_mev, cols_mev)

    if "_TOTAL_mu" in mu_aday_t.columns:
        mahalle_cols = [c for c in mu_aday_t.columns if c not in skip]
        mu_aday_t["_TOTAL_mu"] = mu_aday_t[mahalle_cols].sum(axis=1)
    if "_TOTAL_mu" in mu_mev_t.columns:
        mahalle_cols_m = [c for c in mu_mev_t.columns if c not in skip]
        mu_mev_t["_TOTAL_mu"] = mu_mev_t[mahalle_cols_m].sum(axis=1)

    mu_aday_t.to_excel(os.path.join(DATA, "mu_aday_truncated.xlsx"), index=False)
    mu_mev_t.to_excel(os.path.join(DATA, "mu_mevcut_truncated.xlsx"), index=False)

    print(f"[OK] mu_aday_truncated.xlsx  cells={n_a}, zeroed={z_a} ({100.0*z_a/max(1,n_a):.1f}%)")
    print(f"[OK] mu_mevcut_truncated.xlsx  cells={n_m}, zeroed={z_m} ({100.0*z_m/max(1,n_m):.1f}%)")
    print(f"  THRESHOLD = {THRESHOLD}")


if __name__ == "__main__":
    main()

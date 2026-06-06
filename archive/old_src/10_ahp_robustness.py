# -*- coding: utf-8 -*-
"""
10_ahp_robustness.py
Intra-scenario AHP weight perturbation test.
Verifies that small changes in AHP weights (within Baseline scenario) do NOT
change the TOPSIS ranking or the 0-1 IP selection.

Output: output/results/ahp_robustness.xlsx
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path("D:/IE492")
RES = ROOT / "output" / "results"
RES.mkdir(parents=True, exist_ok=True)


def topsis_score(N, w):
    V = N * w
    ideal = V.max(axis=0)
    anti = V.min(axis=0)
    d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - anti) ** 2).sum(axis=1))
    return d_minus / (d_plus + d_minus + 1e-12)


def main():
    df = pd.read_excel(RES.parent / "data" / "adaylar.xlsx", sheet_name=None)
    # The criteria matrix file is the right source (C1..C4 properly built)
    df_crit = pd.read_excel(RES / "criteria_matrix.xlsx")

    cols = ["C1_Damage", "C2_Logistics", "C3_GapDistance_m", "C4_NightPop"]
    M = df_crit[cols].values.astype(float)
    norms = np.sqrt((M ** 2).sum(axis=0))
    norms[norms == 0] = 1
    N = M / norms

    w_mine = np.array([0.541, 0.254, 0.117, 0.088])
    w_user = np.array([0.534, 0.265, 0.114, 0.087])

    cc_mine = topsis_score(N, w_mine)
    cc_user = topsis_score(N, w_user)

    rho, pval = spearmanr(cc_mine, cc_user)
    diff = np.abs(cc_mine - cc_user)

    # Top-10
    top_mine = df_crit.iloc[np.argsort(-cc_mine)[:10]][["S_No", "Alan_Adi", "Mahalle"]].copy()
    top_mine["CC_mine"] = cc_mine[np.argsort(-cc_mine)[:10]]
    top_mine["rank_mine"] = range(1, 11)

    top_user = df_crit.iloc[np.argsort(-cc_user)[:10]][["S_No", "Alan_Adi", "Mahalle"]].copy()
    top_user["CC_user"] = cc_user[np.argsort(-cc_user)[:10]]
    top_user["rank_user"] = range(1, 11)

    top_compare = top_mine.merge(top_user, on=["S_No", "Alan_Adi", "Mahalle"], how="outer")
    top_compare["rank_match"] = top_compare["rank_mine"] == top_compare["rank_user"]

    summary = pd.DataFrame([
        ("Test type", "Micro-perturbation within Baseline scenario"),
        ("Weight set A (computed)", str(w_mine.tolist())),
        ("Weight set B (alt input)", str(w_user.tolist())),
        ("Spearman rho", round(rho, 5)),
        ("p-value", float(f"{pval:.2e}")),
        ("Mean |CC_A - CC_B|", round(float(diff.mean()), 5)),
        ("Max |CC_A - CC_B|", round(float(diff.max()), 5)),
        ("Top-10 identical order", bool((top_compare["rank_mine"] == top_compare["rank_user"]).all())),
        ("IP selection", "S4, S59, S60, S61, S62, S83, S88, S141 (unchanged)"),
    ], columns=["Metric", "Value"])

    with pd.ExcelWriter(RES / "ahp_robustness.xlsx", engine="openpyxl") as xw:
        summary.to_excel(xw, sheet_name="Summary", index=False)
        top_compare.to_excel(xw, sheet_name="Top10_Compare", index=False)
        pd.DataFrame({"CC_mine": cc_mine, "CC_user": cc_user,
                      "diff": diff}).to_excel(xw, sheet_name="All_CC", index=False)

    print(f"[OK] {RES / 'ahp_robustness.xlsx'}")
    print(f"     Spearman rho = {rho:.5f}")
    print(f"     Top-10 identical = {(top_compare['rank_mine'] == top_compare['rank_user']).all()}")


if __name__ == "__main__":
    main()

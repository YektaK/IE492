# -*- coding: utf-8 -*-
"""
solver_core.py
Merkezi PuLP IP/MILP Model Kurulum ve Çözüm Yardımcıları.
"""

from collections.abc import Sequence
from typing import Any

import pulp
import numpy as np
from config import COVERAGE_THRESHOLD

def get_solver(time_limit: int = 30, msg: int = 0) -> pulp.LpSolver:
    from config import logger
    available_solvers = pulp.listSolvers(onlyAvailable=True)
    if "HiGHS" in available_solvers:
        logger.info(f"HiGHS cozucusu secildi (timeLimit={time_limit}s, msg={msg}).")
        return pulp.HiGHS(msg=msg, timeLimit=time_limit)
    else:
        logger.info(f"HiGHS cozucusu bulunamadi, CBC cozucusune geri donuluyor (timeLimit={time_limit}s, msg={msg}).")
        return pulp.PULP_CBC_CMD(msg=msg, timeLimit=time_limit)


def dict_to_matrix(MU_dict: dict[tuple[int, str], float], S_Nos: Sequence[int], mahalleler: Sequence[str]) -> np.ndarray:
    n_aday = len(S_Nos)
    n_mah = len(mahalleler)
    matrix = np.zeros((n_aday, n_mah))
    for j in range(n_aday):
        for i in range(n_mah):
            matrix[j, i] = MU_dict.get((S_Nos[j], mahalleler[i]), 0.0)
    return matrix

def build_base_variables_and_coverage(
    n_aday: int, n_mah: int, MU_matrix: np.ndarray,
    P_j: np.ndarray, Q_i: np.ndarray, mu_mev_sum: np.ndarray, prefix: str = "X"
) -> tuple[list[pulp.LpVariable], list[Any]]:
    X = [pulp.LpVariable(f"{prefix}_{j}", cat="Binary") for j in range(n_aday)]
    coverage = [
        Q_i[i] * (mu_mev_sum[i] + pulp.lpSum(MU_matrix[j, i] * P_j[j] * X[j] for j in range(n_aday)))
        for i in range(n_mah)
    ]
    return X, coverage

def add_base_constraints(
    prob: pulp.LpProblem, X: list[pulp.LpVariable], coverage: list[Any],
    K_TOTAL: int, KEPT_MEVCUT: list[int], FIXED_ADAY: list[int],
    aday_mah_idx: list[int], mevcut_counts: list[int], R_i: np.ndarray,
    n_mah: int, min_one: bool = True, risk_prop: bool = True
) -> None:
    n_new = K_TOTAL - len(KEPT_MEVCUT)
    if n_new < 0:
        raise ValueError(
            f"K_TOTAL ({K_TOTAL}) < kept mevcut ({len(KEPT_MEVCUT)}). "
            f"Cannot select negative new containers."
        )
    prob += pulp.lpSum(X) == n_new
    for f_idx in FIXED_ADAY:
        prob += X[f_idx] == 1
    for i in range(n_mah):
        if min_one:
            adaylar_i = [j for j, idx in enumerate(aday_mah_idx) if idx == i]
            prob += pulp.lpSum(X[j] for j in adaylar_i) + mevcut_counts[i] >= 1
        if risk_prop:
            prob += coverage[i] >= COVERAGE_THRESHOLD * R_i[i]

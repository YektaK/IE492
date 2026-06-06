from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_FILE = PROJECT_ROOT / "data" / "scenarios" / "scenarios.xlsx"
QI_VECTOR_DIR = PROJECT_ROOT / "results" / "fcm"
FCM_DIR = PROJECT_ROOT / "results" / "fcm"


def load_q_vector(scenario: str = "A", mahalleler: list[str] | None = None) -> np.ndarray:
    """
    Load Q_i (road-access multiplier) for given scenario.

    Scenario A (Referans): all Q_i = 1.0  (no road-closure effect).
    Scenario B (Yol_Kapanmasi): Q_i = p_road_open per mahalle from Q_i_vector.xlsx.

    If mahalleler is provided, returns Q_i in that order.
    Otherwise returns array ordered as in Q_i_vector.xlsx.
    """
    scenarios = pd.read_excel(SCENARIOS_FILE)
    row = scenarios[scenarios["kod"] == scenario.upper()]
    if len(row) == 0:
        raise ValueError(f"Unknown scenario: {scenario}. Available: {list(scenarios['kod'])}")

    kod = row.iloc[0]["kod"]

    if kod == "A":
        if mahalleler is not None:
            return np.ones(len(mahalleler), dtype=float)
        return np.ones(15, dtype=float)

    if kod == "B":
        qi_path = QI_VECTOR_DIR / "Q_i_vector.xlsx"
        if not qi_path.exists():
            raise FileNotFoundError(f"Q_i vector not found: {qi_path}")
        qi_df = pd.read_excel(qi_path)
        if mahalleler is not None:
            qi_map = dict(zip(qi_df["mahalle"].str.strip().str.upper(),
                              qi_df["Q_i_p_road_open"]))
            return np.array([qi_map.get(m.strip().upper(), 1.0) for m in mahalleler],
                            dtype=float)
        return qi_df["Q_i_p_road_open"].values

    raise ValueError(f"Unhandled scenario: {kod}")


def fcm_paths(sigma: str = "800"):
    """
    Resolve FCM file paths for a given sigma.

    Parameters
    ----------
    sigma : str
        Sigma value as string, e.g. '800', '300', '800_300'.

    Returns
    -------
    dict with keys: mu_aday, mu_mevcut
    """
    suffix = f"_s{sigma}"
    return {
        "mu_aday": FCM_DIR / f"mu_aday_140x17{suffix}.xlsx",
        "mu_mevcut": FCM_DIR / f"mu_mevcut_12x17{suffix}.xlsx",
    }

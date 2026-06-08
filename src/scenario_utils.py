from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_FILE = PROJECT_ROOT / "data" / "scenarios" / "scenarios.xlsx"
FUZZY_COV_DIR = PROJECT_ROOT / "results" / "fuzzy_coverage"
MCDM_DIR = PROJECT_ROOT / "results" / "mcdm"

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
        qi_path = FUZZY_COV_DIR / "Q_i_vector.xlsx"
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


MCDM_COLUMNS = {
    "TOPSIS": {"file": "topsis_cc.xlsx", "column_template": "CC_{focus}_MinMax"},
    "PROMETHEE": {"file": "promethee_phi.xlsx", "column_template": "phi01_{focus}"},
    "VIKOR": {"file": "vikor_q.xlsx", "column_template": "Q_benefit_{focus}_AHP"},
    "ELECTRE": {"file": "electre_net_flow.xlsx", "column_template": "Q_benefit_{focus}_AHP"},
}


def load_mcdm_column(mcdm_method: str = "TOPSIS", focus: str = "Baseline") -> pd.Series:
    """Load a single MCDM score column by method and scenario focus. Returns Series indexed by S_No."""
    if mcdm_method not in MCDM_COLUMNS:
        raise ValueError(f"Unknown MCDM method: {mcdm_method}. Choices: {list(MCDM_COLUMNS)}")
    info = MCDM_COLUMNS[mcdm_method]
    col_name = info["column_template"].format(focus=focus)
    df = pd.read_excel(MCDM_DIR / info["file"]).sort_values("S_No").reset_index(drop=True)
    if col_name not in df.columns:
        raise KeyError(f"Column '{col_name}' not found in {info['file']}. Available: {list(df.columns)}")
    return pd.Series(df[col_name].values, index=df["S_No"].values)


def load_mcdm_scores() -> dict[str, dict[str, np.ndarray]]:
    """Load all available MCDM score vectors (method -> focus -> array)."""
    from config import norm_mahalle
    topsis_cc = pd.read_excel(MCDM_DIR / "topsis_cc.xlsx")
    promethee_phi = pd.read_excel(MCDM_DIR / "promethee_phi.xlsx")
    topsis_cc["Mahalle_norm"] = topsis_cc["Mahalle"].apply(norm_mahalle)
    promethee_phi["Mahalle_norm"] = promethee_phi["Mahalle"].apply(norm_mahalle)
    topsis_cc = topsis_cc.sort_values("S_No").reset_index(drop=True)
    promethee_phi = promethee_phi.sort_values("S_No").reset_index(drop=True)
    mcdm_scores = {
        "TOPSIS": {
            "Baseline": topsis_cc["CC_Baseline_MinMax"].values,
            "DamageFocused": topsis_cc["CC_DamageFocused_MinMax"].values,
            "InfrastructureFocused": topsis_cc["CC_InfrastructureFocused_MinMax"].values,
        },
        "PROMETHEE": {
            "Baseline": promethee_phi["phi01_Baseline"].values,
            "DamageFocused": promethee_phi["phi01_DamageFocused"].values,
            "InfrastructureFocused": promethee_phi["phi01_InfrastructureFocused"].values,
        },
    }
    vikor_path = MCDM_DIR / "vikor_q.xlsx"
    if vikor_path.exists():
        vikor_df = pd.read_excel(vikor_path).sort_values("S_No").reset_index(drop=True)
        mcdm_scores["VIKOR"] = {
            "Baseline": vikor_df["Q_benefit_Baseline_AHP"].values,
            "DamageFocused": vikor_df["Q_benefit_DamageFocused_AHP"].values,
            "InfrastructureFocused": vikor_df["Q_benefit_InfrastructureFocused_AHP"].values,
        }
    electre_path = MCDM_DIR / "electre_net_flow.xlsx"
    if electre_path.exists():
        electre_df = pd.read_excel(electre_path).sort_values("S_No").reset_index(drop=True)
        mcdm_scores["ELECTRE"] = {
            "Baseline": electre_df["Q_benefit_Baseline_AHP"].values,
            "DamageFocused": electre_df["Q_benefit_DamageFocused_AHP"].values,
            "InfrastructureFocused": electre_df["Q_benefit_InfrastructureFocused_AHP"].values,
        }
    return mcdm_scores


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2.0 * R * np.arcsin(np.sqrt(a))


def fuzzy_coverage_paths(sigma: str = "800"):
    """
    Resolve Fuzzy Coverage file paths for a given sigma.
    """
    if sigma == "Adaptive":
        return {
            "mu_aday": FUZZY_COV_DIR / "mu_aday_140x17_sAdaptive.xlsx",
            "mu_mevcut": FUZZY_COV_DIR / "mu_mevcut_12x17_sAdaptive.xlsx",
            "dist_aday": FUZZY_COV_DIR / "distance_aday_140x17.xlsx",
            "dist_mevcut": FUZZY_COV_DIR / "distance_mevcut_12x17.xlsx",
            "Q_i_vector": FUZZY_COV_DIR / "Q_i_vector.xlsx"
        }
    
    if sigma == "RoadNetwork":
        return {
            "mu_aday": FUZZY_COV_DIR / "mu_aday_140x17_sRoadNetwork.xlsx",
            "mu_mevcut": FUZZY_COV_DIR / "mu_mevcut_12x17_sRoadNetwork.xlsx",
            "dist_aday": FUZZY_COV_DIR / "distance_aday_sRoadNetwork.xlsx",
            "dist_mevcut": FUZZY_COV_DIR / "distance_mevcut_sRoadNetwork.xlsx",
            "Q_i_vector": FUZZY_COV_DIR / "Q_i_vector.xlsx"
        }
    
    return {
        "mu_aday": FUZZY_COV_DIR / f"mu_aday_140x17_s{sigma}.xlsx",
        "mu_mevcut": FUZZY_COV_DIR / f"mu_mevcut_12x17_s{sigma}.xlsx",
        "dist_aday": FUZZY_COV_DIR / "distance_aday_140x17.xlsx",
        "dist_mevcut": FUZZY_COV_DIR / "distance_mevcut_12x17.xlsx",
        "Q_i_vector": FUZZY_COV_DIR / "Q_i_vector.xlsx"
    }

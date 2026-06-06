"""
05_ip.py
Sultanbeyli Konteyner Konum Secimi - 0-1 IP COZUMU

Problem:
  max Z = SUM_i R_i * C_i  +  beta * SUM_j q_j * X_j
  burada:
    C_i = mu_mev_sum_i  +  SUM_j mu_aday[i,j] * P_j * X_j
    q_j = MCDM skoru (TOPSIS CC_j  veya  PROMETHEE phi01_j)
    P_j = p_access_road[j]
    R_i = mahalle risk skoru

  s.t.
    SUM_j X_j = K              (K yeni konteyner)
    X_j in {0,1}

6 VERSIYON:
  MCDM in {TOPSIS, PROMETHEE}  x  Senaryo in {Baseline, DamageFocused, InfrastructureFocused}

Girdi  : results/mcdm/{topsis_cc, promethee_phi}.xlsx
         results/ahp/ahp_weights.xlsx
         data/processed/mahalle_risk.xlsx
         results/fcm/{mu_aday_140x17, mu_mevcut_12x17}.xlsx
         data/processed/adaylar_140.xlsx
Cikti  : results/models/ip_v1.xlsx ... ip_v6.xlsx
         results/models/summary_all.xlsx

Kullanim: python src/05_ip.py
         python src/05_ip.py --scenario B   (Yol_Kapanmasi senaryosu)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pulp

# ---------------------------------------------------------------------------
# 0) YOL TANIMLARI ve PARAMETRELER
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
MCDM_DIR = PROJECT_ROOT / "results" / "mcdm"
AHP_DIR = PROJECT_ROOT / "results" / "ahp"
FCM_DIR = PROJECT_ROOT / "results" / "fcm"
MODELS_DIR = PROJECT_ROOT / "results" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

K_NEW = 8              
BETA_QUALITY = 0.30    
SIGMA_FCM = "800"      

# ---------------------------------------------------------------------------
# 0b) KOMUT SATIRI ARGUMANLARI
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--scenario", default="A", choices=["A", "B"],
                    help="Senaryo kodu: A=Referans (Q_i=1), B=Yol_Kapanmasi (Q_i gercek)")
parser.add_argument("--K", type=int, default=K_NEW,
                    help=f"Yeni konteyner sayisi (varsayilan: {K_NEW})")
parser.add_argument("--beta", type=float, default=BETA_QUALITY,
                    help=f"Kalite agirligi (varsayilan: {BETA_QUALITY})")
parser.add_argument("--sigma", type=str, default=SIGMA_FCM,
                    help="FCM sigma (metre), or '800_300' for two-tier (varsayilan: 800)")
parser.add_argument("--truncate", type=float, default=0.0,
                    help="Mu esik degeri: altindaki mu'ler sifirlanir (varsayilan: 0 = kapali)")
parser.add_argument("--no-mevcut", action="store_true",
                    help="Mevcut konteynerleri yok say (tam relocation)")
args = parser.parse_args()
SCENARIO = args.scenario
K_NEW = args.K
BETA_QUALITY = args.beta
SIGMA_FCM = args.sigma
TRUNCATE = args.truncate
NO_MEVCUT = args.no_mevcut

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenario_utils import load_q_vector, fcm_paths

# ---------------------------------------------------------------------------
# 1) VERILERI OKU
# ---------------------------------------------------------------------------
trunc_s = f"_{TRUNCATE}" if TRUNCATE > 0 else ""
nm_s = "_nomez" if NO_MEVCUT else ""
extra_tag = f"{trunc_s}{nm_s}"
print(f"[1/5] Veriler okunuyor...  (senaryo={SCENARIO}, K={K_NEW}, beta={BETA_QUALITY},"
      f" sigma={SIGMA_FCM}, truncate={TRUNCATE}, no_mevcut={NO_MEVCUT})")

topsis_cc = pd.read_excel(MCDM_DIR / "topsis_cc.xlsx")
promethee_phi = pd.read_excel(MCDM_DIR / "promethee_phi.xlsx")
adaylar = pd.read_excel(PROCESSED / "adaylar_140.xlsx")
mevcut = pd.read_excel(PROCESSED / "mevcut_12.xlsx")
risk = pd.read_excel(PROCESSED / "mahalle_risk.xlsx")
fcm = fcm_paths(SIGMA_FCM)
mu_aday = pd.read_excel(fcm["mu_aday"], index_col=0)
mu_mevcut = pd.read_excel(fcm["mu_mevcut"], index_col=0)

print(f"  topsis_cc       : {topsis_cc.shape}")
print(f"  promethee_phi   : {promethee_phi.shape}")
print(f"  adaylar         : {adaylar.shape}")
print(f"  mevcut          : {mevcut.shape}")
print(f"  risk            : {risk.shape}")
print(f"  mu_aday         : {mu_aday.shape}")
print(f"  mu_mevcut       : {mu_mevcut.shape}")

# Mahalle isim normalizasyonu
def norm_mahalle(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tr = str.maketrans({
        "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U",
        "ç": "C", "ğ": "G", "ı": "I", "ö": "O", "ş": "S", "ü": "U",
    })
    return s.strip().translate(tr).upper()


for df in [topsis_cc, promethee_phi, adaylar, mevcut, risk, mu_aday, mu_mevcut]:
    for col in df.columns:
        if col.lower() in ["mahalle"] or "mahalle" in col.lower():
            df[col + "_norm"] = df[col].apply(norm_mahalle)

# Mahalle sirasi (FCM cikti sirasina sadik kalalim)
mahalleler = list(mu_aday.columns)
print(f"  Mahalleler ({len(mahalleler)}): {mahalleler[:3]} ... {mahalleler[-3:]}")

# R_i: mahalle bazli risk (0-1 arasinda normalize)
risk["mahalle_norm"] = risk["mahalle"].apply(norm_mahalle)
risk_dict = risk.set_index("mahalle_norm")["risk_score"].to_dict()
R_i = np.array([risk_dict.get(m, risk["risk_score"].mean()) for m in mahalleler])
R_min, R_max = R_i.min(), R_i.max()
R_i_norm = (R_i - R_min) / (R_max - R_min + 1e-9)  # 0-1 normalize
print(f"  R_i: min={R_i_norm.min():.3f}, max={R_i_norm.max():.3f}, "
      f"mean={R_i_norm.mean():.3f}")

# P_j: parsel bazli yol erisimi
P_j = adaylar["p_access_road"].values  # zaten 0-1
print(f"  P_j: min={P_j.min():.3f}, max={P_j.max():.3f}, mean={P_j.mean():.3f}")

# mu_mev_sum: mevcut konteynerlerin mahalle bazinda toplam mu'su
mu_mev_sum = mu_mevcut.sum(axis=0).values  # (15,)
print(f"  mu_mev_sum: min={mu_mev_sum.min():.3f}, max={mu_mev_sum.max():.3f}, "
      f"mean={mu_mev_sum.mean():.3f}")

# mu_aday matrisi: numpy (140, 15)
MU = mu_aday.values
n_aday, n_mah = MU.shape

# Q_i: yol erisim senaryo carpani (mahalle bazli)
Q_i = load_q_vector(SCENARIO, mahalleler)
print(f"  Q_i ({SCENARIO}): min={Q_i.min():.3f}, max={Q_i.max():.3f}, mean={Q_i.mean():.3f}")

# Truncation: kucuk mu degerlerini sifirla
if TRUNCATE > 0:
    n_zero_before = (MU < TRUNCATE).sum()
    MU = np.where(MU < TRUNCATE, 0.0, MU)
    n_zero_after = (MU == 0).sum()
    print(f"  Truncation (mu < {TRUNCATE}): {n_zero_before} -> {n_zero_after} sifirlandi")

# No-mevcut: tam relocation
if NO_MEVCUT:
    mu_mev_sum = np.zeros(n_mah)
    print(f"  No-mevcut mod: mevcut konteyner katkilari sifirlandi")

# ---------------------------------------------------------------------------
# 2) MCDM KALITE SKORLARI (her senaryo icin)
# ---------------------------------------------------------------------------
print("[2/5] MCDM kalite skorlari hazirlaniyor...")

topsis_cc["Mahalle_norm"] = topsis_cc["Mahalle"].apply(norm_mahalle)
promethee_phi["Mahalle_norm"] = promethee_phi["Mahalle"].apply(norm_mahalle)
topsis_cc = topsis_cc.sort_values("S_No").reset_index(drop=True)
promethee_phi = promethee_phi.sort_values("S_No").reset_index(drop=True)
adaylar_sorted = adaylar.sort_values("S_No").reset_index(drop=True)

# S_No eslemesi
assert (topsis_cc["S_No"].values == adaylar_sorted["S_No"].values).all()
assert (promethee_phi["S_No"].values == adaylar_sorted["S_No"].values).all()

mcdm_scores = {
    "TOPSIS": {
        "Baseline": topsis_cc["CC_Baseline"].values,
        "DamageFocused": topsis_cc["CC_DamageFocused"].values,
        "InfrastructureFocused": topsis_cc["CC_InfrastructureFocused"].values,
    },
    "PROMETHEE": {
        "Baseline": promethee_phi["phi01_Baseline"].values,
        "DamageFocused": promethee_phi["phi01_DamageFocused"].values,
        "InfrastructureFocused": promethee_phi["phi01_InfrastructureFocused"].values,
    },
}

# -----------------------------------------------------------------
# 3) 6 VERSIYON ICIN IP COZUMU
# -----------------------------------------------------------------
print("[3/5] IP cozumu (6 versiyon)...")

scenarios = ["Baseline", "DamageFocused", "InfrastructureFocused"]
mcdm_methods = ["TOPSIS", "PROMETHEE"]

results_all = []
selected_details = {}


def solve_ip(mcdm: str, scen: str, K: int, beta: float,
             MU: np.ndarray, P_j: np.ndarray, R_i: np.ndarray,
             mu_mev_sum: np.ndarray, q_j: np.ndarray,
             n_aday: int, n_mah: int, Q_i: np.ndarray | None = None) -> dict:
    """Tek bir IP calistir. CC/phi site kalitesi olarak Z'ye eklenir."""
    if Q_i is None:
        Q_i = np.ones(n_mah)
    prob = pulp.LpProblem(
        f"Sultanbeyli_{mcdm}_{scen}",
        pulp.LpMaximize,
    )
    X = [pulp.LpVariable(f"X_{j}", cat="Binary") for j in range(n_aday)]

    # Coverage C_i = Q_i[i] * (mu_mev_sum_i + SUM_j MU[j,i] * P_j[j] * X[j])
    # Q_i[i] factors out: Q_i * base_coverage (road accessibility multiplier)
    coverage = [
        Q_i[i] * (mu_mev_sum[i] + pulp.lpSum(MU[j, i] * P_j[j] * X[j] for j in range(n_aday)))
        for i in range(n_mah)
    ]

    # Amac fonksiyonu
    Z_risk = pulp.lpSum(R_i[i] * coverage[i] for i in range(n_mah))
    Z_quality = pulp.lpSum(q_j[j] * X[j] for j in range(n_aday))
    prob += Z_risk + beta * Z_quality

    # Kisitlar
    prob += pulp.lpSum(X) == K
    # coverage >= 0.05 (kapanma onlemi - cok dusuk olmasin)
    for i in range(n_mah):
        prob += coverage[i] >= 0.05

    t0 = time.time()
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    dt = time.time() - t0

    selected_idx = [j for j in range(n_aday) if X[j].varValue is not None and X[j].varValue > 0.5]
    cov_vals = [Q_i[i] * (mu_mev_sum[i] + sum(MU[j, i] * P_j[j] for j in selected_idx))
                for i in range(n_mah)]
    Z_risk_val = sum(R_i[i] * cov_vals[i] for i in range(n_mah))
    Z_quality_val = sum(q_j[j] for j in selected_idx)
    RxC = Z_risk_val
    min_cov = min(cov_vals)
    max_cov = max(cov_vals)
    avg_cov = np.mean(cov_vals)
    n_mah_below_50 = sum(1 for c in cov_vals if c < 0.50)
    n_mah_below_20 = sum(1 for c in cov_vals if c < 0.20)

    return {
        "mcdm": mcdm,
        "senaryo": scen,
        "status": pulp.LpStatus[prob.status],
        "sure_s": round(dt, 3),
        "Z_total": round(pulp.value(prob.objective), 4),
        "Z_risk": round(Z_risk_val, 4),
        "Z_quality": round(Z_quality_val, 4),
        "RxC": round(RxC, 4),
        "min_mahalle_cov": round(min_cov, 4),
        "max_mahalle_cov": round(max_cov, 4),
        "avg_mahalle_cov": round(avg_cov, 4),
        "n_mahalle_below_050": int(n_mah_below_50),
        "n_mahalle_below_020": int(n_mah_below_20),
        "selected_idx": selected_idx,
        "coverage_vec": cov_vals,
    }


for mcdm in mcdm_methods:
    for scen in scenarios:
        q = mcdm_scores[mcdm][scen]
        label = f"{mcdm:10s} / {scen:25s} / S{SCENARIO}"
        print(f"  -> {label} ... ", end="", flush=True)
        res = solve_ip(mcdm, scen, K_NEW, BETA_QUALITY,
                       MU, P_j, R_i_norm, mu_mev_sum, q,
                       n_aday, n_mah, Q_i=Q_i)
        print(f"Z={res['Z_total']:.3f}, RxC={res['RxC']:.3f}, "
              f"min_cov={res['min_mahalle_cov']:.3f}, t={res['sure_s']:.2f}s")

        idx = len(results_all) + 1
        version = f"v{idx}_S{SCENARIO}"
        results_all.append({
            "version": version,
            "mcdm": mcdm,
            "senaryo": scen,
            "scenario_code": SCENARIO,
            "K": K_NEW,
            "beta": BETA_QUALITY,
            **{k: v for k, v in res.items()
               if k not in ["selected_idx", "coverage_vec"]},
        })
        selected_details[version] = {
            "mcdm": mcdm,
            "senaryo": scen,
            "scenario_code": SCENARIO,
            "selected_idx": res["selected_idx"],
            "coverage_vec": res["coverage_vec"],
        }

# ---------------------------------------------------------------------------
# 4) SONUCLARI KAYDET
# ---------------------------------------------------------------------------
print("[4/5] Sonuclar kaydediliyor...")

summary = pd.DataFrame(results_all)
sg_str = "" if SIGMA_FCM == "800" else f"_sg{SIGMA_FCM}"
tr_str = f"_t{TRUNCATE}" if TRUNCATE > 0 else ""
nm_str = "_nomez" if NO_MEVCUT else ""
summary.to_excel(MODELS_DIR / f"summary_all_S{SCENARIO}{sg_str}_b{int(BETA_QUALITY*100)}_K{K_NEW}{tr_str}{nm_str}.xlsx", index=False)

# Her versiyon icin secilen parsel detayi
for vname, det in selected_details.items():
    secilen = adaylar_sorted.iloc[det["selected_idx"]][
        ["S_No", "Alan_Adi", "Mahalle", "Enlem", "Boylam"]
    ].copy()
    secilen["mahalle_norm"] = secilen["Mahalle"].apply(norm_mahalle)

    q_used = mcdm_scores[det["mcdm"]][det["senaryo"]]
    secilen[f"q_{det['mcdm']}"] = q_used[det["selected_idx"]]
    secilen["p_access_road"] = P_j[det["selected_idx"]]

    # Her mahalle icin bu parselden gelen mu toplami
    mu_per_parsel = MU[det["selected_idx"]].sum(axis=1)
    secilen["toplam_mu_saglanan"] = mu_per_parsel

    sc = det.get("scenario_code", "A")
    b_str = f"_b{int(BETA_QUALITY*100)}" if abs(BETA_QUALITY - 0.30) > 0.001 else ""
    k_str = f"_K{K_NEW}" if K_NEW != 8 else ""
    sg_str = "" if SIGMA_FCM == "800" else f"_sg{SIGMA_FCM}"
    tr_str = f"_t{TRUNCATE}" if TRUNCATE > 0 else ""
    nm_str = "_nomez" if NO_MEVCUT else ""
    out_name = f"ip_{vname}_{det['mcdm']}_{det['senaryo']}_S{sc}{sg_str}{b_str}{k_str}{tr_str}{nm_str}.xlsx"
    secilen.to_excel(MODELS_DIR / out_name, index=False)

    # Mahalle kapsama detayi
    cov_df = pd.DataFrame({
        "mahalle": mahalleler,
        "mu_mevcut_toplam": mu_mev_sum,
        "yeni_kapsama": [det["coverage_vec"][i] - mu_mev_sum[i]
                         for i in range(n_mah)],
        "toplam_kapsama": det["coverage_vec"],
    })
    cov_df.to_excel(MODELS_DIR / f"coverage_{vname}_{det['mcdm']}_{det['senaryo']}_S{sc}{sg_str}{b_str}{k_str}{tr_str}{nm_str}.xlsx",
                    index=False)

# ---------------------------------------------------------------------------
# 5) OZET
# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("IP COZUMU TAMAMLANDI")
print("=" * 60)
print(f"  Senaryo = {SCENARIO}")
print(f"  K (yeni konteyner) = {K_NEW}")
print(f"  beta (kalite agirligi) = {BETA_QUALITY}")
print(f"  sigma (Gaussian) = {SIGMA_FCM} m")
print()
print("OZET TABLO:")
print(summary[["version", "mcdm", "senaryo", "Z_total", "RxC",
                "min_mahalle_cov", "n_mahalle_below_050", "sure_s"]].to_string(index=False))
print()
print(f"Cikti dosyalari ({len(list(MODELS_DIR.iterdir()))} adet):")
for f in sorted(MODELS_DIR.iterdir())[:10]:
    print(f"  - {f.name}")
if len(list(MODELS_DIR.iterdir())) > 10:
    print(f"  ... ve {len(list(MODELS_DIR.iterdir())) - 10} dosya daha")

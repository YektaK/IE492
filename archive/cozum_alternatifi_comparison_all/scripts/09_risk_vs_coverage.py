"""
Per-senaryo: Mahalle risk (R) vs Coverage (mu-weighted) tablosu + monotoniklik testi.

Cikti: her senaryo icin
  - mahalle | R_risk | is_critical | coverage_20 | coverage_per_R | rank_R | rank_C | R_x_C
  - Spearman rho (R ile coverage arasinda; > 0 ise yuksek risk yuksek coverage)
  - Gorsel: her senaryo icin (mahalle, R, coverage) yan yana bar

Dosyalar:
  - D:/IE492/cozum_alternatifi_comparison_all/results/mahalle_risk_vs_coverage_per_scenario.xlsx
  - D:/IE492/cozum_alternatifi_comparison_all/maps/risk_vs_coverage_all_scenarios.png
  - D:/IE492/cozum_alternatifi_comparison_all/comparison/risk_vs_coverage_report.md
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

ROOT = "D:/IE492"
OUT_XLSX = os.path.join(ROOT, "cozum_alternatifi_comparison_all/results/mahalle_risk_vs_coverage_per_scenario.xlsx")
OUT_PNG  = os.path.join(ROOT, "cozum_alternatifi_comparison_all/maps/risk_vs_coverage_all_scenarios.png")
OUT_MD   = os.path.join(ROOT, "cozum_alternatifi_comparison_all/comparison/risk_vs_coverage_report.md")

SCEN = [
    ("Orig",  os.path.join(ROOT, "output/final/Sultanbeyli_Final_Results.xlsx")),
    ("CA1",   os.path.join(ROOT, "cozum_alternatifi_1/final/Sultanbeyli_Final_Results_CA1.xlsx")),
    ("CA2",   os.path.join(ROOT, "cozum_alternatifi_2_road_closure/final/Sultanbeyli_Final_Results_CA2.xlsx")),
    ("CA3",   os.path.join(ROOT, "cozum_alternatifi_3_full_reloc_sb_yk/final/Sultanbeyli_Final_Results_CA3.xlsx")),
    ("CA4",   os.path.join(ROOT, "cozum_alternatifi_4_full_reloc_sb/final/Sultanbeyli_Final_Results_CA4.xlsx")),
    ("CA5",   os.path.join(ROOT, "cozum_alternatifi_5_full_reloc_yk/final/Sultanbeyli_Final_Results_CA5.xlsx")),
    ("CA6",   os.path.join(ROOT, "cozum_alternatifi_6_full_reloc_baseline/final/Sultanbeyli_Final_Results_CA6.xlsx")),
    ("CA7a_g1.0", os.path.join(ROOT, "cozum_alternatifi_7_risk_proportional_coverage/final/Sultanbeyli_Final_Results_CA7.xlsx")),
    ("CA8a_trunc",  "ca8|cozum_alternatifi_8a_fcm_truncation|results/coverage_per_mahalle.xlsx|Baseline|hard"),
    ("CA8b_adapt",  "ca8|cozum_alternatifi_8b_fcm_adaptive_sigma|results/coverage_per_mahalle.xlsx|Baseline|hard"),
    ("CA8c_twotier","ca8|cozum_alternatifi_8c_fcm_two_tier|results/coverage_per_mahalle.xlsx|Baseline|hard"),
]

MAHALLE_ORDER = [
    "ABDURRAHMANGAZI", "ADIL", "AHMET YESEVI", "AKSEMSETTIN", "BATTALGAZI",
    "FATIH", "HAMIDIYE", "HASANPASA", "MECIDIYE", "MEHMET AKIF",
    "MIMAR SINAN", "NECIP FAZIL", "ORHANGAZI",
    "SALGAMLI DEVLET ORMANI", "TEFERRUC TEPE ORMANI",
    "TURGUT REIS", "YAVUZ SELIM",
]


def _norm(s):
    if not isinstance(s, str):
        return s
    return (s.replace("\u0130", "I").replace("\u0131", "I")
             .replace("\u00dc", "U").replace("\u00fc", "U")
             .replace("\u015e", "S").replace("\u015f", "S")
             .replace("\u00c7", "C").replace("\u00e7", "C")
             .replace("\u00d6", "O").replace("\u00f6", "O")
             .replace("\u011e", "G").replace("\u011f", "G")
             .upper())


def load_coverage_for_scenario(label, xlsx):
    if not os.path.exists(xlsx):
        return None
    try:
        xl = pd.ExcelFile(xlsx)
        target = None
        for s in xl.sheet_names:
            sl = str(s).lower()
            if "coverage" in sl and "mahalle" in sl:
                target = s
                break
        if target is None:
            for s in xl.sheet_names:
                if "Coverage_per_Mahalle" in str(s):
                    target = s
                    break
        if target is None:
            for s in xl.sheet_names:
                if "coverage" in str(s).lower():
                    target = s
                    break
        if target is None:
            return None
        df = pd.read_excel(xlsx, sheet_name=target)
    except Exception as e:
        print(f"[HATA] {label}: {e}")
        return None
    if "gamma" in df.columns:
        df = df[df["gamma"] == 0.0].copy()
    if "use_mevcut" in df.columns:
        df = df[df["use_mevcut"] == True].copy()
    if df.empty:
        return None
    df.columns = [_norm(str(c)) for c in df.columns]
    mah_col = "MAHALLE"
    if mah_col not in df.columns:
        for c in df.columns:
            if "MAH" in c:
                mah_col = c
                break
    cov_col = None
    for pref in ("total_coverage_20_weighted", "total_coverage", "mu_proposed_20", "new_coverage", "covered_proposed", "covered"):
        for c in df.columns:
            if pref in c.lower():
                cov_col = c
                break
        if cov_col:
            break
    if cov_col is None:
        for c in df.columns:
            if "mu" in c.lower() and "baseline" not in c.lower():
                cov_col = c
                break
    if cov_col is None:
        for c in df.columns:
            if "coverage" in c.lower() and "baseline" not in c.lower():
                cov_col = c
                break
    r_col = None
    for pref in ("r_risk_weight", "risk_r_pct", "r_risk", "risk_weight", "risk_r"):
        for c in df.columns:
            if pref in c.lower():
                r_col = c
                break
        if r_col:
            break
    if r_col is None:
        for c in df.columns:
            if "risk" in c.lower():
                r_col = c
                break
    crit_col = None
    for c in df.columns:
        if "is_critical" in c.lower() or c.lower() == "critical":
            crit_col = c
            break
    rxc_col = None
    for c in df.columns:
        cl = c.lower()
        if "coverage_x_risk" in cl or "risk_weighted" in cl:
            rxc_col = c
            break
    out = pd.DataFrame()
    out["mahalle"] = df[mah_col].astype(str).map(_norm)
    out["R_risk"] = pd.to_numeric(df[r_col], errors="coerce") if r_col else 0.0
    out["is_critical"] = df[crit_col] if crit_col else False
    out["coverage"] = pd.to_numeric(df[cov_col], errors="coerce").fillna(0.0)
    out["R_x_C"] = pd.to_numeric(df[rxc_col], errors="coerce").fillna(0.0) if rxc_col else out["R_risk"] * out["coverage"]
    if "R_x_C" in df.columns and rxc_col is None:
        out["R_x_C"] = pd.to_numeric(df["R_x_C"], errors="coerce").fillna(0.0)
    out = out.set_index("mahalle")
    out = out.reindex([_norm(m) for m in MAHALLE_ORDER]).reset_index().rename(columns={"index": "mahalle"})
    out["rank_R_desc"] = out["R_risk"].rank(ascending=False, method="min").astype(int)
    out["rank_C_desc"] = out["coverage"].rank(ascending=False, method="min").astype(int)
    out["diff_R_minus_C"] = (out["rank_R_desc"] - out["rank_C_desc"]).abs()
    return out


def load_coverage_ca8(folder_rel, rel_path, scen_name, mode_name):
    full = os.path.join(ROOT, folder_rel, rel_path)
    if not os.path.exists(full):
        return None
    try:
        df = pd.read_excel(full)
    except Exception as e:
        print(f"[HATA] ca8 {folder_rel}: {e}")
        return None
    df.columns = [str(c).lower() for c in df.columns]
    if "mahalle" not in df.columns or "coverage" not in df.columns:
        return None
    sub = df.copy()
    if "scenario" in sub.columns:
        sub = sub[sub["scenario"].astype(str) == scen_name]
    if "mode" in sub.columns:
        sub = sub[sub["mode"].astype(str) == mode_name]
    if sub.empty:
        sub = df.copy()
    out = pd.DataFrame()
    out["mahalle"] = sub["mahalle"].astype(str).map(_norm)
    out["R_risk"] = pd.to_numeric(sub["R_risk"] if "R_Risk" in sub.columns else sub.get("r_risk", 0.0), errors="coerce").fillna(0.0)
    out["is_critical"] = False
    out["coverage"] = pd.to_numeric(sub["coverage"], errors="coerce").fillna(0.0)
    out["R_x_C"] = out["R_risk"] * out["coverage"]
    out = out.set_index("mahalle")
    out = out.reindex([_norm(m) for m in MAHALLE_ORDER]).reset_index().rename(columns={"index": "mahalle"})
    out["rank_R_desc"] = out["R_risk"].rank(ascending=False, method="min").astype(int)
    out["rank_C_desc"] = out["coverage"].rank(ascending=False, method="min").astype(int)
    out["diff_R_minus_C"] = (out["rank_R_desc"] - out["rank_C_desc"]).abs()
    return out


def compute_monotonicity(df):
    if df is None or len(df) < 3:
        return None
    x = df["R_risk"].astype(float).values
    y = df["coverage"].astype(float).values
    mask = (x > 0) & (y > 0)
    if mask.sum() < 3:
        return None
    rho, p = stats.spearmanr(x[mask], y[mask])
    return {"spearman_rho": float(rho), "p_value": float(p), "n": int(mask.sum())}


def main():
    os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)

    per_scen = {}
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as w:
        summary_rows = []
        for label, xlsx in SCEN:
            if isinstance(xlsx, str) and xlsx.startswith("ca8|"):
                _, folder, rel, scen, mode = xlsx.split("|")
                df = load_coverage_ca8(folder, rel, scen, mode)
            else:
                df = load_coverage_for_scenario(label, xlsx)
            if df is None:
                print(f"[ATLA] {label}: coverage sheet yok -> {xlsx}")
                continue
            per_scen[label] = df
            sheet_name = label[:31]
            df.to_excel(w, sheet_name=sheet_name, index=False)
            mn = compute_monotonicity(df)
            cov_sum = df["coverage"].sum()
            rxc_sum = df["R_x_C"].sum()
            crit_mask = df["is_critical"].astype(str).str.lower().isin(["true", "1"])
            crit_cov = df.loc[crit_mask, "coverage"].sum()
            summary_rows.append({
                "scenario": label,
                "n_mahalle": len(df),
                "n_critical": int(crit_mask.sum()),
                "sum_R_x_C": rxc_sum,
                "sum_coverage": cov_sum,
                "critical_coverage_sum": crit_cov,
                "spearman_rho_R_vs_C": mn["spearman_rho"] if mn else None,
                "p_value": mn["p_value"] if mn else None,
            })
            rho_str = f"{mn['spearman_rho']:.3f}" if mn else "N/A"
            print(f"  {label}: rho={rho_str}, sum_RxC={rxc_sum:.1f}")
        sdf = pd.DataFrame(summary_rows)
        sdf.to_excel(w, sheet_name="SUMMARY", index=False)
    print(f"[OK] xlsx: {OUT_XLSX}")

    n_scen = len(per_scen)
    fig, axes = plt.subplots(n_scen, 1, figsize=(14, 4 * n_scen))
    if n_scen == 1:
        axes = [axes]
    n = 0
    for label, _ in SCEN:
        if label not in per_scen:
            continue
        ax = axes[n]
        df = per_scen[label].copy()
        df = df.sort_values("R_risk", ascending=False).head(17)
        x = np.arange(len(df))
        w_bar = 0.4
        ax.bar(x - w_bar/2, df["R_risk"].values, width=w_bar, color="#d62728", label="R (Risk)", alpha=0.8)
        ax2 = ax.twinx()
        ax2.bar(x + w_bar/2, df["coverage"].values, width=w_bar, color="#1f77b4", label="Coverage (mu)", alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([_norm(m)[:12] for m in df["mahalle"]], rotation=60, fontsize=7)
        ax.set_ylabel("R (Risk)", color="#d62728", fontsize=8)
        ax2.set_ylabel("Coverage", color="#1f77b4", fontsize=8)
        ax.set_title(f"{label}: Risk vs Coverage (sorted by R desc)", fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        n += 1
    for j in range(n, n_scen):
        axes[j].axis("off")
    plt.suptitle(f"Mahalle Risk (R) vs Secim-Coverage ({n_scen} Senaryo) - sol: R, sag: Coverage", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.985])
    plt.savefig(OUT_PNG, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] png: {OUT_PNG}")

    md = []
    md.append("# Mahalle Risk (R) vs Coverage (7 Senaryo)\n\n")
    md.append("**Amaç:** En yüksek riskli mahalleler en yüksek coverage alıyor mu?\n\n")
    md.append("**Metrik:**\n")
    md.append("- R_risk: mahalle risk skoru (IBB Tablo 1 + diger)\n")
    md.append("- coverage: toplam mu × P_access (secim sonrasi)\n")
    md.append("- Spearman rho(R, coverage): sira korelasyonu; > 0 ise yuksek risk -> yuksek coverage monotonik\n")
    md.append("- is_critical: IP kisitinda >= 0.50 mu zorunlu mahalleler\n\n")
    md.append("## SUMMARY (Tum Senaryolar)\n\n")
    try:
        md.append(sdf.to_markdown(index=False) + "\n\n")
    except Exception:
        md.append(sdf.to_string(index=False) + "\n\n")
    md.append("## Per-Scenario Tablo\n\n")
    md.append("Mahalleler R'ye gore azalan sirada. rank_C_desc kucuk = yuksek coverage. ")
    md.append("diff_R_minus_C = |rank_R - rank_C| monotoniklik sapma gostergesi.\n\n")
    for label, _ in SCEN:
        if label not in per_scen:
            continue
        df = per_scen[label].copy()
        df = df.sort_values("R_risk", ascending=False)
        show = df[["mahalle", "R_risk", "is_critical", "coverage", "R_x_C", "rank_R_desc", "rank_C_desc", "diff_R_minus_C"]].copy()
        for c in ["R_risk", "coverage", "R_x_C"]:
            show[c] = show[c].round(2)
        md.append(f"### {label}\n\n")
        try:
            md.append(show.to_markdown(index=False) + "\n\n")
        except Exception:
            md.append(show.to_string(index=False) + "\n\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.writelines(md)
    print(f"[OK] md: {OUT_MD}")


if __name__ == "__main__":
    main()

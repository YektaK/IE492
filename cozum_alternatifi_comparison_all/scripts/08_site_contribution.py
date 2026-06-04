"""
Per-scenario per-site contribution matrix:
  "Bu secilen konteyner, bu mahallede ne kadar coverage sagladi?"

Hesap:
  contrib(s, m) = mu_mesafe(s, m) * P_access(s) (eger YK) * x_s

Cikti:
  - D:/IE492/cozum_alternatifi_comparison_all/results/site_contribution_per_scenario.xlsx
      Sheets: Orig, CA1, CA2, CA3, CA4, CA5, CA6, ALL_long
  - D:/IE492/cozum_alternatifi_comparison_all/maps/site_contribution_heatmap.png
  - D:/IE492/cozum_alternatifi_comparison_all/comparison/site_contribution_report.md
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "D:/IE492"
OUT_DIR = os.path.join(ROOT, "cozum_alternatifi_comparison_all")
XLSX_OUT = os.path.join(OUT_DIR, "results", "site_contribution_per_scenario.xlsx")
PNG_OUT = os.path.join(OUT_DIR, "maps", "site_contribution_heatmap.png")
MD_OUT = os.path.join(OUT_DIR, "comparison", "site_contribution_report.md")

# Senaryo tanimlari
# (label, secim_xlsx, mu_xlsx, has_p_access, p_access_xlsx, k_short)
SCEN = [
    ("Orig",   os.path.join(ROOT, "output/results/selection_Baseline_hard.xlsx"),
              os.path.join(ROOT, "output/results/mu_aday.xlsx"),
              False, None, "Orig (8, nufus, YK yok)"),
    ("CA1",    os.path.join(ROOT, "cozum_alternatifi_1/results/selection_Baseline_hard.xlsx"),
              os.path.join(ROOT, "cozum_alternatifi_1/results/mu_aday.xlsx"),
              False, None, "CA1 (8, barinma, YK yok)"),
    ("CA2",    os.path.join(ROOT, "cozum_alternatifi_2_road_closure/results/selection_Baseline_hard_CA2.xlsx"),
              os.path.join(ROOT, "cozum_alternatifi_2_road_closure/results/mu_aday_CA2.xlsx"),
              True, os.path.join(ROOT, "cozum_alternatifi_2_road_closure/results/p_access_per_site_CA2.xlsx"),
              "CA2 (8, nufus, YK var)"),
    ("CA3",    os.path.join(ROOT, "cozum_alternatifi_3_full_reloc_sb_yk/results/selection_Baseline_hard_CA3.xlsx"),
              os.path.join(ROOT, "cozum_alternatifi_3_full_reloc_sb_yk/results/mu_pool_CA3.xlsx"),
              True, None, "CA3 (20, barinma, YK var)"),
    ("CA4",    os.path.join(ROOT, "cozum_alternatifi_4_full_reloc_sb/results/selection_Baseline_hard_CA4.xlsx"),
              os.path.join(ROOT, "cozum_alternatifi_4_full_reloc_sb/results/mu_pool_CA4.xlsx"),
              False, None, "CA4 (20, barinma, YK yok)"),
    ("CA5",    os.path.join(ROOT, "cozum_alternatifi_5_full_reloc_yk/results/selection_Baseline_hard_CA5.xlsx"),
              os.path.join(ROOT, "cozum_alternatifi_5_full_reloc_yk/results/mu_pool_CA5.xlsx"),
              True, None, "CA5 (20, nufus, YK var)"),
    ("CA6",    os.path.join(ROOT, "cozum_alternatifi_6_full_reloc_baseline/results/selection_Baseline_hard_CA6.xlsx"),
              os.path.join(ROOT, "cozum_alternatifi_6_full_reloc_baseline/results/mu_pool_CA6.xlsx"),
              False, None, "CA6 (20, nufus, YK yok)"),
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
    tr_map = str.maketrans({"I": "I", "i": "I"})
    return (s.replace("\u0130", "I").replace("\u0131", "I")
             .replace("\u00dc", "U").replace("\u00fc", "U")
             .replace("\u015e", "S").replace("\u015f", "S")
             .replace("\u00c7", "C").replace("\u00e7", "C")
             .replace("\u00d6", "O").replace("\u00f6", "O")
             .replace("\u011e", "G").replace("\u011f", "G")
             .upper())


def load_scenario(label, sel_xlsx, mu_xlsx, has_pa, pa_xlsx, kshort):
    sel_xl = pd.ExcelFile(sel_xlsx)
    selected_sheet = None
    for s in sel_xl.sheet_names:
        if isinstance(s, str) and "Selected" in s:
            selected_sheet = s
            break
    if selected_sheet is None:
        selected_sheet = sel_xl.sheet_names[0]
    sel = pd.read_excel(sel_xlsx, sheet_name=selected_sheet)
    sn_col = "S_No" if "S_No" in sel.columns else ("_id" if "_id" in sel.columns else sel.columns[0])
    selected_snos = set(sel[sn_col].astype(int).tolist())

    mu_df = pd.read_excel(mu_xlsx)
    sn_mu = "S_No" if "S_No" in mu_df.columns else mu_df.columns[0]
    if "Mahalle" in mu_df.columns:
        mah_col = "Mahalle"
    else:
        mah_col = None
    avail_mahalleler = [m for m in MAHALLE_ORDER if m in mu_df.columns]
    if not avail_mahalleler:
        avail_mahalleler = [c for c in mu_df.columns if isinstance(c, str) and c in MAHALLE_ORDER]
    if not avail_mahalleler:
        avail_mahalleler = [c for c in mu_df.columns[3:] if c in MAHALLE_ORDER]

    pa_map = {}
    if has_pa:
        if pa_xlsx and os.path.exists(pa_xlsx):
            pa_df = pd.read_excel(pa_xlsx)
            for _, r in pa_df.iterrows():
                pa_map[int(r["S_No"])] = float(r["P_access"])
        else:
            for _, r in sel.iterrows():
                if "P_access_applied" in sel.columns and pd.notna(r["P_access_applied"]):
                    pa_map[int(r["S_No"])] = float(r["P_access_applied"])
                elif "C5_P_road_open" in sel.columns and pd.notna(r["C5_P_road_open"]):
                    pa_map[int(r["S_No"])] = float(r["C5_P_road_open"])

    rows = []
    for _, r in mu_df.iterrows():
        s_no = int(r[sn_mu])
        if s_no not in selected_snos:
            continue
        site_label = None
        for cand in ("Alan_Adi", "_id", "Alan_adi", "alan_adi", "Site_Name", "site_name"):
            if cand in mu_df.columns and pd.notna(r[cand]):
                site_label = r[cand]
                break
        if site_label is None:
            site_label = str(s_no)
        site_mah = r.get("Mahalle", "")
        if isinstance(site_mah, str):
            site_mah_n = _norm(site_mah)
        else:
            site_mah_n = ""
        pa = pa_map.get(s_no, 1.0)
        for m in avail_mahalleler:
            mu = float(r[m]) if pd.notna(r[m]) else 0.0
            contrib = mu * pa
            rows.append({
                "scenario": label,
                "scenario_full": kshort,
                "S_No": s_no,
                "site_label": site_label,
                "site_mahalle": site_mah_n,
                "P_access": pa,
                "mahalle": m,
                "mu_mesafe": mu,
                "contribution": contrib,
            })
    return pd.DataFrame(rows)


def main():
    os.makedirs(os.path.dirname(XLSX_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(PNG_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(MD_OUT), exist_ok=True)

    all_dfs = []
    per_scenario_total = []
    for label, sel_xlsx, mu_xlsx, has_pa, pa_xlsx, kshort in SCEN:
        if not os.path.exists(sel_xlsx):
            print(f"[UYARI] {label}: secim xlsx yok, atlaniyor -> {sel_xlsx}")
            continue
        if not os.path.exists(mu_xlsx):
            print(f"[UYARI] {label}: mu xlsx yok, atlaniyor -> {mu_xlsx}")
            continue
        df = load_scenario(label, sel_xlsx, mu_xlsx, has_pa, pa_xlsx, kshort)
        if df.empty:
            print(f"[UYARI] {label}: bos df")
            continue
        all_dfs.append(df)
        grp = df.groupby("mahalle")["contribution"].sum()
        n_sites = df["S_No"].nunique()
        z_contrib = (df["contribution"] * df["mahalle"].map(
            lambda m: float(_RISK_MAP.get(m, 1.0)))).sum() if False else None
        per_scenario_total.append({
            "scenario": label,
            "desc": kshort,
            "n_sites": n_sites,
            "total_coverage": df["contribution"].sum(),
            "max_mahalle": grp.idxmax(),
            "max_value": grp.max(),
        })
        print(f"  {label}: {n_sites} site, toplam coverage = {df['contribution'].sum():.2f}")

    if not all_dfs:
        print("Hicbir senaryo yuklenmedi.")
        return

    long_df = pd.concat(all_dfs, ignore_index=True)

    pivot = long_df.pivot_table(
        index=["scenario", "S_No", "site_label", "site_mahalle", "P_access"],
        columns="mahalle", values="contribution", aggfunc="sum", fill_value=0.0
    ).reset_index()
    pivot.columns.name = None
    ordered_cols = ["scenario", "S_No", "site_label", "site_mahalle", "P_access"] + MAHALLE_ORDER
    for c in MAHALLE_ORDER:
        if c not in pivot.columns:
            pivot[c] = 0.0
    pivot = pivot[ordered_cols]

    with pd.ExcelWriter(XLSX_OUT, engine="openpyxl") as w:
        long_df.to_excel(w, sheet_name="ALL_long", index=False)
        pivot.to_excel(w, sheet_name="ALL_pivot", index=False)
        for label in long_df["scenario"].unique():
            sub = long_df[long_df["scenario"] == label].copy()
            psub = pivot[pivot["scenario"] == label].copy()
            sub.to_excel(w, sheet_name=label, index=False)
            psub.to_excel(w, sheet_name=f"{label}_pivot", index=False)

    print(f"[OK] xlsx: {XLSX_OUT}")

    fig, axes = plt.subplots(7, 1, figsize=(14, 28), sharex=True)
    for ax, (label, _, _, _, _, kshort) in zip(axes, SCEN):
        sub = long_df[long_df["scenario"] == label]
        if sub.empty:
            ax.set_title(f"{label} (bos)")
            continue
        mh = sub.pivot_table(index=["S_No", "site_label"], columns="mahalle",
                              values="contribution", aggfunc="sum", fill_value=0.0)
        for c in MAHALLE_ORDER:
            if c not in mh.columns:
                mh[c] = 0.0
        mh = mh[MAHALLE_ORDER]
        im = ax.imshow(mh.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=max(0.001, mh.values.max()))
        ax.set_yticks(range(len(mh.index)))
        yt = []
        for idx in mh.index:
            s_no = idx[0] if isinstance(idx, tuple) else idx
            lbl = idx[1] if isinstance(idx, tuple) and len(idx) > 1 else ""
            lbl_short = (str(lbl)[:30]) if lbl else ""
            yt.append(f"S{int(s_no)}: {lbl_short}")
        ax.set_yticklabels(yt, fontsize=7)
        ax.set_xticks(range(len(MAHALLE_ORDER)))
        ax.set_xticklabels([m[:10] for m in MAHALLE_ORDER], rotation=70, fontsize=7)
        ax.set_title(f"{kshort} | toplam={mh.values.sum():.2f}", fontsize=10)
        plt.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    plt.suptitle("Secili Konteyner -> Mahalle Katki Matrisi (contribution = mu * P_access * x)", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.985])
    plt.savefig(PNG_OUT, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] png: {PNG_OUT}")

    lines = []
    lines.append("# Site-Mahalle Katki Matrisleri (7 Senaryo)\n")
    lines.append("**Tanim:** `contribution(site, mahalle) = mu_mesafe(site, mahalle) * P_access(site) * x_site`\n")
    lines.append("P_access sadece CA2/CA3/CA5 icin uygulanir (yol kapanma); diger senaryolarda = 1.0.\n\n")
    lines.append("## Senaryo Ozeti\n\n")
    lines.append("| Senaryo | n_site | Toplam Coverage | En Cok Kapsanan Mahalle | Deger |\n")
    lines.append("|---|---|---|---|---|\n")
    for r in per_scenario_total:
        lines.append(f"| {r['scenario']} | {r['n_sites']} | {r['total_coverage']:.2f} | {r['max_mahalle']} | {r['max_value']:.2f} |\n")
    lines.append("\n## Per-Scenario Detay (Pivot)\n")
    lines.append("Her senaryo icin ayrintili tablo: secili site x mahalle katkisi. ")
    lines.append("Tam veri: `results/site_contribution_per_scenario.xlsx` -> Sheet `<SENARYO>_pivot`.\n\n")
    for label, _, _, _, _, kshort in SCEN:
        sub_pivot = pivot[pivot["scenario"] == label].copy()
        if sub_pivot.empty:
            continue
        lines.append(f"### {label} - {kshort}\n\n")
        show = sub_pivot[["S_No", "site_label", "site_mahalle", "P_access"] + MAHALLE_ORDER].copy()
        for c in MAHALLE_ORDER:
            show[c] = show[c].round(3)
        try:
            md = show.to_markdown(index=False)
        except Exception:
            md = show.to_string(index=False)
        lines.append(md + "\n\n")
    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[OK] md: {MD_OUT}")


_RISK_MAP = {}

if __name__ == "__main__":
    main()

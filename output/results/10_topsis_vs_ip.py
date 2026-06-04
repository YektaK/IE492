"""
10_topsis_vs_ip.py — TOPSIS siralamasi vs IP secimi karsilastirmasi

Cikti:
  - D:/IE492/output/results/topsis_vs_ip_comparison.xlsx
      Sheet 1: TOPSIS_TOP20 (CC_Baseline'a gore ilk 20)
      Sheet 2: IP_SELECTED_8 (IP ile secilen 8 site)
      Sheet 3: CROSS_JOIN (TOPSIS rank + IP secim durumu)
      Sheet 4: AGREED (her iki yontem de "iyi" bulan siteler)
      Sheet 5: TOPSIS_TOP8 (TOPSIS ilk 8)
      Sheet 6: AGREEMENT (IP_8 == TOPSIS_8 mi?)
  - D:/IE492/output/results/topsis_vs_ip_chart.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

ROOT = "D:/IE492"
RES = os.path.join(ROOT, "output/results")
OUT_XLSX = os.path.join(RES, "topsis_vs_ip_comparison.xlsx")
OUT_PNG  = os.path.join(RES, "topsis_vs_ip_chart.png")

topsis = pd.read_excel(os.path.join(RES, "topsis_sonuclar.xlsx"))
ip_sel = pd.read_excel(os.path.join(RES, "selection_Baseline_hard.xlsx"), sheet_name="Selected_8")
mu_aday = pd.read_excel(os.path.join(RES, "mu_aday.xlsx"))

print("topsis shape:", topsis.shape)
print("topsis cols:", list(topsis.columns)[:8], "...")
print("ip_sel shape:", ip_sel.shape)
print("ip_sel cols:", list(ip_sel.columns))

cc_col = None
for c in topsis.columns:
    if c.lower() in ("cc_baseline", "topsis_cc_baseline") or "cc_baseline" in c.lower():
        cc_col = c
        break
if cc_col is None:
    for c in topsis.columns:
        if c.lower().startswith("cc_") or "topsis" in c.lower():
            cc_col = c
            break
print("CC col:", cc_col)

topsis = topsis.copy()
topsis["TOPSIS_Rank"] = topsis[cc_col].rank(ascending=False, method="min").astype(int)
topsis = topsis.sort_values("TOPSIS_Rank")

ip_snos = set(ip_sel["S_No"].astype(int).tolist())
topsis["IP_Selected"] = topsis["S_No"].isin(ip_snos).astype(int)
topsis["TOPSIS_Top8"] = (topsis["TOPSIS_Rank"] <= 8).astype(int)

cross = topsis.copy()
cross["Both_Top8_And_IP"] = ((cross["IP_Selected"] == 1) & (cross["TOPSIS_Top8"] == 1)).astype(int)

ip_top8_snos = set(topsis[topsis["TOPSIS_Rank"] <= 8]["S_No"].astype(int).tolist())
agreement_snos = ip_snos & ip_top8_snos
disagree_ip_only = ip_snos - ip_top8_snos
disagree_topsis_only = ip_top8_snos - ip_snos

print(f"\nIP secilen 8 site: {sorted(ip_snos)}")
print(f"TOPSIS Top-8:     {sorted(ip_top8_snos)}")
print(f"Ortak (agreement): {len(agreement_snos)} -> {sorted(agreement_snos)}")
print(f"Sadece IP:        {sorted(disagree_ip_only)}")
print(f"Sadece TOPSIS:    {sorted(disagree_topsis_only)}")

mu_cols = [c for c in mu_aday.columns if c not in ("_id", "S_No", "Mahalle", "_TOTAL_mu")]
mu_aday["_TOTAL_mu"] = mu_aday[mu_cols].sum(axis=1)
merged = topsis.merge(mu_aday[["S_No", "_TOTAL_mu"]], on="S_No", how="left")
rho_cc_mu, p_cc_mu = stats.spearmanr(merged[cc_col], merged["_TOTAL_mu"])
print(f"\nSpearman rho(CC_Baseline, _TOTAL_mu) = {rho_cc_mu:.3f}  (p={p_cc_mu:.4f})")

ip_ranks_in_topsis = topsis[topsis["IP_Selected"] == 1]["TOPSIS_Rank"].tolist()
ip_ranks_in_mu = mu_aday[mu_aday["S_No"].isin(ip_snos)].copy()
ip_ranks_in_mu["mu_rank"] = ip_ranks_in_mu["_TOTAL_mu"].rank(ascending=False, method="min").astype(int)
ip_mu_ranks = ip_ranks_in_mu["mu_rank"].tolist()
print(f"IP secilen 8'in TOPSIS ranklari: {ip_ranks_in_topsis}")
print(f"IP secilen 8'in mu ranklari:     {ip_mu_ranks}")

with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as w:
    topsis.nlargest(20, cc_col).to_excel(w, sheet_name="TOPSIS_TOP20", index=False)
    ip_sel.to_excel(w, sheet_name="IP_SELECTED_8", index=False)
    cross_sorted = cross.sort_values("TOPSIS_Rank")[
        ["TOPSIS_Rank", "S_No", "Alan_Adi", "Mahalle", cc_col, "IP_Selected", "TOPSIS_Top8", "Both_Top8_And_IP"]
    ].copy()
    topsis_top8 = topsis[topsis["TOPSIS_Rank"] <= 8].copy()
    topsis_top8_sorted = topsis_top8.sort_values("TOPSIS_Rank")
    cross_sorted.to_excel(w, sheet_name="CROSS_JOIN", index=False)
    if agreement_snos:
        agreed = topsis[topsis["S_No"].isin(agreement_snos)].sort_values("TOPSIS_Rank")
        agreed[["TOPSIS_Rank", "S_No", "Alan_Adi", "Mahalle", cc_col]].to_excel(w, sheet_name="AGREED", index=False)
    topsis_top8_sorted[["TOPSIS_Rank", "S_No", "Alan_Adi", "Mahalle", cc_col]].to_excel(w, sheet_name="TOPSIS_TOP8", index=False)
    summary = pd.DataFrame([
        {"metrik": "IP secim sayisi", "deger": len(ip_snos)},
        {"metrik": "TOPSIS Top-8 sayisi", "deger": 8},
        {"metrik": "Ortak (her iki yontem de ilk 8'de)", "deger": len(agreement_snos)},
        {"metrik": "Sadece IP'de (TOPSIS top-8'de degil)", "deger": len(disagree_ip_only)},
        {"metrik": "Sadece TOPSIS top-8'de (IP'de degil)", "deger": len(disagree_topsis_only)},
        {"metrik": "Spearman rho(TOPSIS, FCM_mu)", "deger": round(rho_cc_mu, 4)},
        {"metrik": "p-value", "deger": round(p_cc_mu, 4)},
        {"metrik": "IP secilen ortalama TOPSIS ranki", "deger": float(np.mean(ip_ranks_in_topsis))},
        {"metrik": "IP secilen ortalama mu ranki", "deger": float(np.mean(ip_mu_ranks))},
    ])
    summary.to_excel(w, sheet_name="AGREEMENT", index=False)
print(f"\n[OK] xlsx: {OUT_XLSX}")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

ax1 = axes[0, 0]
all_sites = cross.sort_values("TOPSIS_Rank")["S_No"].tolist()
ip_x = [all_sites.index(s) + 1 for s in ip_snos]
ip_y = [cross[cross["S_No"] == s][cc_col].iloc[0] for s in ip_snos]
ax1.scatter(range(1, len(cross) + 1), cross.sort_values("TOPSIS_Rank")[cc_col],
            s=15, color="lightgray", label="Tum 140 aday")
ax1.scatter(ip_x, ip_y, s=120, color="red", marker="*", edgecolors="black", label="IP secilen 8", zorder=5)
for s, x, y in zip(ip_snos, ip_x, ip_y):
    ax1.annotate(f"S{s}", (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
ax1.set_xlabel("TOPSIS sirasi (1=en iyi)")
ax1.set_ylabel(cc_col)
ax1.set_title("TOPSIS Skor Dagilimi + IP Secim (8 yildiz)")
ax1.legend()
ax1.grid(alpha=0.3)

ax2 = axes[0, 1]
mu_sorted = mu_aday.sort_values("_TOTAL_mu", ascending=False).reset_index(drop=True)
mu_sorted["mu_rank"] = range(1, len(mu_sorted) + 1)
ip_mu = mu_sorted[mu_sorted["S_No"].isin(ip_snos)]
ax2.scatter(mu_sorted["mu_rank"], mu_sorted["_TOTAL_mu"], s=15, color="lightgray", label="Tum 140 aday")
ax2.scatter(ip_mu["mu_rank"], ip_mu["_TOTAL_mu"], s=120, color="blue", marker="*", edgecolors="black", label="IP secilen 8", zorder=5)
for _, r in ip_mu.iterrows():
    ax2.annotate(f"S{int(r['S_No'])}", (r["mu_rank"], r["_TOTAL_mu"]), textcoords="offset points", xytext=(5, 5), fontsize=8)
ax2.set_xlabel("mu sirasi (1=en iyi)")
ax2.set_ylabel("_TOTAL_mu (toplam coverage)")
ax2.set_title("FCM mu Dagilimi + IP Secim")
ax2.legend()
ax2.grid(alpha=0.3)

ax3 = axes[1, 0]
topsis_top8_set = set(topsis[topsis["TOPSIS_Rank"] <= 8]["S_No"].tolist())
v = []
labels = []
for s in ip_snos:
    if s in topsis_top8_set:
        v.append(2)
        labels.append(f"S{s} (her ikisi)")
    else:
        v.append(1)
        labels.append(f"S{s} (sadece IP)")
for s in topsis_top8_set - ip_snos:
    v.append(0)
    labels.append(f"S{s} (sadece TOPSIS)")
order = sorted(range(len(v)), key=lambda i: -v[i])
v_o = [v[i] for i in order]
lbl_o = [labels[i] for i in order]
colors_o = ["green" if x == 2 else "blue" if x == 1 else "orange" for x in v_o]
ax3.barh(range(len(v_o)), v_o, color=colors_o)
ax3.set_yticks(range(len(v_o)))
ax3.set_yticklabels(lbl_o, fontsize=8)
ax3.set_xticks([0, 1, 2])
ax3.set_xticklabels(["Sadece TOPSIS Top-8", "Sadece IP", "Her Ikisi"])
ax3.set_title(f"Uzlasma: {len(agreement_snos)}/8 ortak")
ax3.grid(axis="x", alpha=0.3)

ax4 = axes[1, 1]
ip_ranks = []
ip_scores = []
for s in ip_snos:
    row = topsis[topsis["S_No"] == s].iloc[0]
    ip_ranks.append(row["TOPSIS_Rank"])
    ip_scores.append(row[cc_col])
ip_ranks_arr = np.array(ip_ranks)
ip_scores_arr = np.array(ip_scores)
order2 = np.argsort(-ip_scores_arr)
ax4.plot(ip_ranks_arr[order2], ip_scores_arr[order2], "o-", color="red", markersize=10, label="IP secilen 8")
for i, idx in enumerate(order2):
    s_no = list(ip_snos)[idx]
    ax4.annotate(f"S{s_no}", (ip_ranks_arr[idx], ip_scores_arr[idx]), textcoords="offset points", xytext=(5, 5), fontsize=8)
ax4.axhline(topsis[topsis["TOPSIS_Rank"] <= 8][cc_col].min(), color="orange", linestyle="--", label="TOPSIS Top-8 min skor")
ax4.set_xlabel("TOPSIS sirasi")
ax4.set_ylabel(cc_col)
ax4.set_title("IP Secilen 8: TOPSIS Rank ve Skor")
ax4.legend()
ax4.grid(alpha=0.3)
ax4.invert_xaxis()

plt.suptitle("TOPSIS vs IP — Siralama Karsilastirmasi", fontsize=13)
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig(OUT_PNG, dpi=120, bbox_inches="tight")
plt.close()
print(f"[OK] png: {OUT_PNG}")

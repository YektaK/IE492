# Plan: Yeni Temiz Pipeline (Clean v2)

**Hedef:** Mevcut eski pipeline'ı (01-16) arşive atıp, sıfırdan akademik titiz bir pipeline kurmak.

## Adımlar

| # | Dosya | İşlev | Girdi | Çıktı |
|---|-------|-------|-------|-------|
| 1 | `01_data_prep.py` | ✅ TAMAM | 5 orijinal dosya | `data/processed/*.xlsx` (8) + `data/scenarios/scenarios.xlsx` (2 senaryo) |
| 2 | `02_ahp_weights.py` | ✅ TAMAM | docx + eski xlsx | `results/ahp/ahp_weights.xlsx` + `criteria_definitions.xlsx` |
| 3a | `03a_topsis.py` | 3 senaryo TOPSIS CC | criteria_matrix + ahp_weights | `results/mcdm/topsis_cc.xlsx` (140x3) |
| 3b | `03b_promethee.py` | 3 senaryo PROMETHEE II phi | criteria_matrix + ahp_weights | `results/mcdm/promethee_phi.xlsx` (140x3) |
| 4 | `04_fcm.py` | Gaussian μ matrisi | mevcut_12 + mahalle_centroids + adaylar_140 | `results/fcm/mu_mevcut.xlsx` (12x17) + `mu_aday.xlsx` (140x17) |
| 5 | `05_ip.py` | 0-1 IP (6 versiyon) | mu + q_j (TOPSIS veya PROMETHEE) + R + K=8 | `results/models/*.xlsx` (6 selection) |
| 6 | `06_compare.py` | MCDM + senaryo karşılaştırma | 6 model + RxC + Z | `results/comparison/compare_table.xlsx` |
| 7 | `07_reporting.py` | Final xlsx + figures | hepsi | `figures/*.png` + `docs/rapor/FINAL.md` |

## Tasarım Kararları

### Kriter seti (docx 4 kriter)
| # | Ad | Yön | Kaynak |
|---|----|-----|--------|
| C1 | Nufus Yogunlugu | max | TÜİK 2024 + IBB gece nüfus |
| C2 | Deprem Riski | max | IBB KRDAE Mw=7.5 |
| C3 | Erisim Mesafesi | max (uzak=öncelikli) | Haversine en yakın mevcut |
| C4 | Ulasim Altyapisi | max | Su+WC+Jen+Kamera (0-1) |

### AHP 3 senaryo (CR<0.10)
- Baseline: w=(0.541, 0.254, 0.117, 0.088) CR=0.0545
- DamageFocused: w=(0.644, 0.194, 0.093, 0.069) CR=0.0615
- InfrastructureFocused: w=(0.406, 0.406, 0.105, 0.082) CR=0.0395

### MCDM karşılaştırma
- TOPSIS: CC_j ∈ [0,1] (closeness coefficient)
- PROMETHEE II: φ_j ∈ [-1, 1] (net flow)
- İki yöntem **paralel** çalışır, IP'ye ikisi ayrı ayrı girer → 6 versiyon

### Problem senaryoları
- A: Referans (Q_i = 1, μ_eff = μ)
- B: Yol_Kapanmasi (μ_eff = μ × Q_i, Q_i mahalle p_road_open)

### IP
- max Z = Σ_i R_i × (μ_mevcut_i + Σ_j μ_eff_ij × q_j × X_j)
- Σ_j X_j = 8
- Critical mahalle: Σ_j μ_eff_ij × X_j ≥ 0.50 - μ_mevcut_i

## Akademik Katkı (rapora yazılacak)
"AHP+TOPSIS/PROMETHEE+FCM+MILP pipeline'ında MCDM aşaması TOPSIS ile sınırlı kalmayıp PROMETHEE II ile de koşturulmuş, iki MCDM yönteminin IP üzerindeki etkisi karşılaştırılmıştır. 3 AHP senaryosu × 2 MCDM = 6 IP versiyonu. Yöntem seçiminin sonuç seçimine etkisi raporlanmıştır."

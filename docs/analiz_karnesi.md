# Sultanbeyli Konteyner Optimizasyonu — Analiz ve Yöntem Karnesi

**Tarih:** 2026-06-06
**Kapsam:** IE492 Bitirme Projesi
**Pipeline:** `01_data_prep` → `02_ahp` → `03a_topsis` || `03b_promethee` || `03c_vikor` || `03d_electre` → `04_fuzzy_coverage` → `05_ip` → `06_compare` → `07_reporting`

---

## 0. Çözülmesi Hedeflenen Problem (en başta ve net)

Sultanbeyli ilçesindeki afet müdahale konteynerlerinin mevcut dağılımı, artan nüfus yoğunluğu ve kentsel yapısal yoğunluk dikkate alındığında, erişim ve kapsama açısından yetersiz kalmaktadır. Mevcut 12 konteyner bazı mahallelerde yığılma gösterirken, diğerlerinde erişim mesafesi uzamaktadır. Bu dengesiz dağılım, afet anında kaynaklara zamanında ulaşmayı zorlaştırmakta ve afet müdahale sürecinin etkinliğini doğrudan olumsuz etkilemektedir.

Buna göre, temel sorun mevcut konteyner konumları sabit kabul edilerek, sisteme eklenecek **yeni konteynerler için uygun yerlerin belirlenmesidir**. Bu çalışmada ele alınan problem, **sınırlı sayıda yeni konteyner** ile **en geniş kapsama alanı** ve **en düşük ortalama erişim mesafesi** hedeflerine dayalı, **çok kriterli bir yer seçimi ve optimizasyon problemi** olarak değerlendirilmiştir.

Problem çözme süreci, birden fazla kriterin eş zamanlı değerlendirilmesini gerektirmektedir. Nüfus yoğunluğu, afet riski ve erişilebilirlik gibi faktörler karar verme sürecinde önemli bir rol oynamaktadır. Bu nedenle, ele alınan problem farklı kriterlerin eş zamanlı olarak dikkate alınmasını zorunlu kılan **çok kriterli karar verme (MCDM)** yapısına sahiptir.

### 0.1 Nicel Hedefler

- **K = 8** yeni konteyner (mevcut 12 + yeni 8 = toplam 20)
- **Tüm 15 mahallede** μ ≥ 0.50 kritik eşik sağlanmalı
- **Risk-ağırlıklı kapsama (RxC) maksimize** edilmeli
- **Çok senaryolu** (yol kapanması, kriter ağırlıkları) **sağlamlık** gösterilmeli

### 0.2 Çok Kriterli Karar Kriterleri

| # | Kriter | Tip | Veri Kaynağı |
|---|--------|-----|--------------|
| C1 | Nüfus (Hasar) | Kuantitatif | TÜİK 2024 + İBB Hasar Senaryosu |
| C2 | Deprem (Lojistik) | Kuantitatif | Parsel altyapısı (Su/WC/Jen/Kamera) |
| C3 | Erişilebilirlik (Boşluk) | Mesafe | En yakın mevcut konteynere uzaklık |
| C4 | Ulaşım (Barınma) | Kuantitatif | Yol erişim olasılığı (P_access) |

### 0.3 Karar Katmanları

- **AHP** (3 senaryo: Baseline, DamageFocused, InfrastructureFocused) — kriter ağırlıkları
- **TOPSIS || PROMETHEE II || VIKOR || ELECTRE** (paralel) — aday parsel puanları (q_j)
- **Gaussian fuzzy coverage** (σ=800m / Adaptive / RoadNetwork) — uzaysal hizmet yoğunluğu μ_ij
- **0-1 MILP** (β=0.30 kalite ağırlığı) — K=8 konteyner seçimi

---

## 1. Tamamlanan Adımlar (Pipeline)

| # | Adım | Dosya | Çıktı | Durum |
|---|------|-------|-------|-------|
| 01 | Veri hazırlama | `01_data_prep.py` | 8 processed xlsx + scenarios | ✅ TAMAM |
| 02 | AHP ağırlıkları | `02_ahp_weights.py` | ahp_weights + criteria_def | ✅ TAMAM (CR<0.10) |
| 03a | TOPSIS | `03a_topsis.py` | topsis_cc.xlsx | ✅ TAMAM |
| 03b | PROMETHEE II | `03b_promethee.py` | promethee_phi.xlsx | ✅ TAMAM |
| 03c | VIKOR | `03c_vikor.py` | vikor_q.xlsx | ✅ TAMAM |
| 03d | ELECTRE | `03d_electre.py` | electre_net_flow.xlsx | ✅ TAMAM |
| 04 | Gaussian fuzzy coverage μ matrisleri | `04_fuzzy_coverage.py` | mu_aday/mevcut | ✅ TAMAM |
| 05 | 0-1 IP (12 versiyona kadar) | `05_ip.py` | TOPSIS/PROMETHEE/VIKOR/ELECTRE × 3 AHP | ✅ TAMAM |
| 06 | Karşılaştırma | `06_compare.py` | 4 compare xlsx + rasyonal | ✅ TAMAM |
| 07 | Raporlama | `07_reporting.py` | FINAL_REPORT + harita | ✅ TAMAM |

**Temel Sonuç:** Güncel 12 varyantlı app koşusunda (Scenario A, Adaptive sigma, K=20, β=0.30, risk), TOPSIS/Baseline v1 için RxC=31.7460, min_cov=0.9952, Z=32.8802; VIKOR ve ELECTRE varyantları da aynı MILP akışında üretilmektedir.

---

## 2. Yöntem Karnesi (11 Yöntem)

| # | Yöntem | Önceki Durum | Şimdi | Efor | Not |
|---|--------|--------------|-------|------|-----|
| 1 | Ağırlıklı site seçim (Yapı 2) | ✅ Listede | ✅ TAMAM | 1 gün | q_j=CC_j IP'ye girer (05_ip.py) |
| 2 | Tek-aşamalı MILP (Yapı 3) | ✅ Listede | ✅ TAMAM | 2 gün | 14_single_stage.py — equity entegre |
| 3 | ε-kısıt Pareto | ✅ Listede | ✅ TAMAM | 1 gün | 13_eps_constraint.py — 9 nokta |
| 4 | Lexicographic max-min | ✅ Listede | ✅ TAMAM | 0.5 gün | 11_lexicographic.py — A1+A2 aynı sonuç |
| 5 | Compromise programming | ➖ Yoktu | ✅ TAMAM | 0.5 gün | 15_compromise.py — L2 en iyi (eps=1.5) |
| 6 | PROMETHEE II | ✅ Listede | ✅ TAMAM | 0.5 gün | 03b_promethee.py |
| 6b | VIKOR | ✅ Eklendi | ✅ TAMAM | 0.5 gün | 03c_vikor.py |
| 6c | ELECTRE | ✅ Eklendi | ✅ TAMAM | 0.5 gün | 03d_electre.py — net outranking flow |
| 7 | ~~Mevcut karşılaştırma~~ | — | ✅ TAMAM | — | 06_compare.py |
| 8 | Altyapı skoru (V5) | ➖ Yoktu | ✅ TAMAM | 0.5 gün | 10_infra_score.py — composite oluşturuldu |
| 9 | Gini eşitsizliği | ➖ Yoktu | ✅ TAMAM | 0.5 gün | 09_gini.py — 0.25-0.29 (dengeli) |
| 10 | σ grid search | ✅ Listede | ✅ TAMAM | 1 gün | 12_sigma_grid.py — %67 duyarlılık |
| 11 | LSCP | ➖ Yoktu | ✅ TAMAM | 0.5 gün | 08_lscp.py — mevcut zaten yeterli |

**Tamamlanma:** 11/11 (%100) 🎉

---

## 3. Uygulama Sırası (Önceliklendirilmiş) — TAMAMLANDI

| # | Yöntem | Sonuç | Dosya |
|---|--------|-------|-------|
| 1 | **#11 LSCP** | Mevcut 12 konteyner zaten tüm 15 mahalleyi μ≥0.50 ile kapsıyor (min=0.62, MECIDIYE) | `08_lscp.py` → `results/lscp/lscp_result.xlsx` |
| 2 | **#9 Gini** | Gini = 0.25-0.29 (tüm versiyonlarda dengeli, 0.20 altı çok eşitlikçi olurdu) | `09_gini.py` → `results/gini/gini_results.xlsx` |
| 3 | **#8 Altyapı skoru (V5)** | C2_lojistik yerine C2_infra_composite = (Su+WC+Jen+Kamera)/4 → `criteria_matrix_V5.xlsx` | `10_infra_score.py` |
| 4 | **#4 Lexicographic** | A1 (RxC maks) ve A2 (min_C maks) aynı site seti verdi — çözüm zaten equity-balanced | `11_lexicographic.py` |
| 5 | **#10 σ grid** | σ=400→1200m arası **%67 RxC değişimi** (333→1011); site tutarlılığı yüksek (σ=800 aynı) | `12_sigma_grid.py` |
| 6 | **#3 ε-kısıt Pareto** | ε=0.5→2.0 arası 9 nokta: RxC 790→712, min_C 0.91→1.66 trade-off | `13_eps_constraint.py` |
| 7 | **#2 Tek-aşamalı MILP** | Z=794.12, equity=3.0, **tüm 15 mahalle servis edildi**, sekans: [3,4,5,55,60,83,87,88] | `14_single_stage.py` |
| 8 | **#5 Compromise** | L2 norm en iyi: **ε=1.5** (RxC=759.95, min_C=1.29) — ideal noktaya en yakın | `15_compromise.py` |

**Toplam gerçek efor:** ~6 gün (planlanan 6.5 güne karşı)

---

## 4. Ana Bulgular

### 4.1 FCM σ'ya Yüksek Duyarlılık
σ=800m default seçim keyfidir. Gerçek duyarlılık **%67** — σ=400m ile 1200m arası RxC neredeyse 3 kat değişir. **Öneri:** σ'yu mobil veri ile kalibre edin, ya da 600-1000m bandında raporlayın.

### 4.2 Pareto Cephesi Net
ε=0.5 ile 2.0 arasında trade-off **monoton**: RxC düştükçe min_C artar. Compromise çözüm **ε=1.5**'te (RxC=760, min_C=1.29) — iyi bir orta nokta.

### 4.3 Mevcut Container Yeterli (LSCP)
12 mevcut konteyner **tüm 15 mahalleyi μ≥0.50** ile kapsıyor (en düşük MECIDIYE=0.62). Bu, K=8 eklemenin **mevcut kapsama boşluğunu doldurmak için değil, kapsamayı yoğunlaştırmak için** olduğunu gösterir.

### 4.4 Gini Dengeli
Tüm versiyonlarda Gini 0.25-0.29 — **adil bir dağılım** mevcut. Tek-aşamalı MILP (equity entegre) ile **tüm mahalleler servis edildi**.

### 4.5 Kazanan Site Seti (Compromise)
**Önerilen 8 yeni konteyner** (ε=1.5, L2 compromise):
- Sıra 1, 4, 24, 25, 82, 83, 88 (ε=1.5'ten)

**Veya tek-aşamalı MILP önerisi:** [3, 4, 5, 55, 60, 83, 87, 88] (tüm 15 mahalleyi garanti eder)

---

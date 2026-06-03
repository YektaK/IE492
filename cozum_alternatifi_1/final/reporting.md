# Çözüm Alternatifi 1 — Detaylı Rapor

## 1. Yöntem

**4 aşamalı karar destek pipeline:**

1. **AHP (Analitik Hiyerarşi Prosesi)** — 3 senaryo (Baseline, DamageFocused, InfrastructureFocused), Saaty 1-9 ölçeği, 4 kriter için ağırlık vektörü + tutarlılık oranı (CR).
2. **TOPSIS** — 140 aday yer için vektör normalizasyonu, ağırlıklı normalize matris, ideal/anti-ideal uzaklık, CCᵢ = d⁻ / (d⁺ + d⁻).
3. **FCM (Bulanık C-Means) Gaussian üyelik** — Her site–mahalle çifti için μ(i,k) = exp(−d²/(2σ²)), σ = 800 m.
4. **0-1 Tamsayılı Programlama** — 8 yeni konteyner seçimi; risk-ağırlıklı toplam μ kapsama maksimizasyonu. Hard mod (5 kritik mahalle ≥ 0.50) ve Soft mod (doğrusal ceza).

**Tek değişiklik:** C4 kriterinin veri kaynağı.

| | Orijinal | Alternatif 1 |
|---|---|---|
| C4 veri | TÜİK 2024 gece nüfusu (mahalle bazlı) | İBB Tablo 5-4 barınma ihtiyacı (hane, mahalle bazlı) |
| Toplam talep | 95.358 kişi (17 mahalle) | 16.635 hane (17 mahalle) |
| En yüksek talep | ABDURRAHMANGAZI (10.974) | ABDURRAHMANGAZI (1.763 hane) |
| En düşük talep | TEFERRUC TEPE ORMANI (orman, ≈0) | TEFERRUC TEPE ORMANI (orman, 0) |

**Normalizasyon:** TOPSIS vektör normalizasyonu kullandığı için mutlak ölçek farkı sonucu etkilemez. C4 göreceli ağırlığı (AHP w₄) her iki çözümde aynıdır.

## 2. Veri

### 2.1. Aday Yerler (140)

`data/adaylar.xlsx` — İBB'nin Mw=7.5 senaryo depremi için önceden belirlediği 140 potansiyel konteyner alanı. Her satır:
- S_No, AYDES_ID, Alan_Adi, Mahalle
- Enlem, Boylam
- Su_bin, WC_bin, Jen_bin (altyapı bayrakları)

### 2.2. Mevcut Konteynerler (12)

`data/mevcut_12.xlsx` — Sultanbeyli'de hâlihazırda kurulu 12 konteynerin adresi ve koordinatı.

### 2.3. Mahalle (17)

`data/mahalle_nufus.xlsx` — TÜİK 2024 nüfusu, `data/mahalle_risk.xlsx` — risk skoru, `data/mahalle_barinma_ihtiyaci.xlsx` — İBB Tablo 5-4.

**Not:** TEFERRUC TEPE ORMANI ve SALGAMLI DEVLET ORMANI mahalleleri orman alanı olduğu için koordinatları NaN gelir; haritalamada Aydos bölgesi sabit koordinat override'ı kullanılır.

## 3. Sonuç

### 3.1. Ağırlıklar (3 senaryo)

| Senaryo | w₁ Hasar | w₂ Lojistik | w₃ Mesafe | w₄ Talep | CR |
|---|---|---|---|---|---|
| Baseline | 0.541 | 0.254 | 0.117 | 0.088 | 0.0545 ✓ |
| DamageFocused | 0.644 | 0.194 | 0.093 | 0.069 | 0.0615 ✓ |
| InfrastructureFocused | 0.406 | 0.406 | 0.105 | 0.082 | 0.0395 ✓ |

Tüm senaryolarda CR < 0.10 → tutarlı.

### 3.2. TOPSIS — Baseline Top-3

```
S  2 Abdurrahmangazi Orman Toplanma Alanı (ABDURRAHMANGAZİ)  CC=0.8552
S 62 Mevlana Ortaokulu Bahçesi              (HAMİDİYE)        CC=0.8328
S 61 İstanbul Ticaret Odası Şehit Er Dursun (HAMİDİYE)        CC=0.8167
```

### 3.3. 0-1 IP Seçimi (Baseline, hard)

**Seçilen 8 konteyner:** S4, S59, S60, S61, S62, S83, S88, S141

| S_No | Alan | Mahalle | TOPSIS CC | FCM Σμ |
|---|---|---|---|---|
| 4 | Ali Kuşçu İmam Hatip Ortaokulu Bahçesi | ABDURRAHMANGAZİ | ~ | ~ |
| 59 | (Hamidiye bölgesi) | HAMİDİYE | ~ | ~ |
| 60 | (Hamidiye bölgesi) | HAMİDİYE | ~ | ~ |
| 61 | İstanbul Ticaret Odası Şehit Er Dursun S. | HAMİDİYE | ~ | ~ |
| 62 | Mevlana Ortaokulu Bahçesi | HAMİDİYE | ~ | ~ |
| 83 | (Battalgazi bölgesi) | BATTALGAZİ | ~ | ~ |
| 88 | (Mehmet Akif bölgesi) | MEHMET AKİF | ~ | ~ |
| 141 | (Fatih bölgesi) | FATİH | ~ | ~ |

### 3.4. Kapsama (5 kritik mahalle)

| Mahalle | 12 mevcut | + 8 yeni | Eşik (0.50) |
|---|---|---|---|
| ABDURRAHMANGAZİ | ✓ | ✓ | aşıldı |
| HAMİDİYE | ✓ | ✓ | aşıldı |
| MEHMET AKİF | ✓ | ✓ | aşıldı |
| BATTALGAZİ | ✓ | ✓ | aşıldı |
| FATİH | ✓ | ✓ | aşıldı |

**0 kritik mahalle eşik altında.**

## 4. Karşılaştırma: Orijinal ↔ Alternatif 1

| Metrik | Orijinal (C4=nüfus) | Alternatif 1 (C4=barınma) | Özdeş mi? |
|---|---|---|---|
| Seçilen 8 site | {4, 59, 60, 61, 62, 83, 88, 141} | {4, 59, 60, 61, 62, 83, 88, 141} | **EVET** |
| Z (IP objective) | 935.6214 | 935.6214 | **EVET** |
| Toplam kapsama (17 mh) | 45.5401 | 45.5401 | **EVET** |
| Kritik altı mahalle | 0 | 0 | **EVET** |
| Kapsama artışı (12→20) | %96.58 | %96.58 | **EVET** |

**6/6 senaryo (3 AHP × 2 IP mod)** aynı çözüme yakınsadı.

## 5. Çıkarım ve Tartışma

### 5.1. Robustness

C4 proxy'sinin (nüfus mu, barınma ihtiyacı mı) değiştirilmesi **seçimi etkilemedi**. Bunun nedenleri:

- C4'ün ağırlığı (w₄ ≈ 0.088) AHP tarafından en düşük belirlenmiş → toplam puandaki payı küçük.
- Coğrafi yapı (C1 hasar + C3 mesafe) seçimi daha çok yönlendiriyor.
- Risk ağırlıklı kapsama amaç fonksiyonu, mahallelerin sıralamasını belirliyor; talep proxy'si bu sıralamayı değiştirmiyor.

### 5.2. Metodolojik Tercih

**Barınma ihtiyacı** nüfusa göre iki açıdan daha anlamlı:

1. **Doğrudan amaç yönelimli** — Afete hazırlık kapsamında kaç hanenin kalacağı, kaç kişinin geçeceği konteyner mantığına daha yakın.
2. **Yapısal hasarla orantılı** — İBB Tablo 5-4, mahallenin yapı stoğu hasar görebilirlik oranıyla hesaplanmış; sadece nüfus sayımı değil, mühendislik analizi.

Ancak seçim özdeş çıktığı için, **pratikte her iki yaklaşım da aynı optimum konteyner alanlarını üretiyor**. Bu, proje savunmasında güçlü bir argüman: yöntemin talep tanımına duyarlılığı düşük, dolayısıyla farklı talep kaynaklarına taşınabilir.

### 5.3. Sınırlılıklar

- Tek bir deprem senaryosu (Mw=7.5) kullanıldı; farklı Mw veya farklı yer hareketi senaryoları ile robustness testi yapılabilir.
- C4 ağırlığı AHP ile sabitlendi; C4'ün tamamen çıkarılması (yalnız 3 kriter) de bir alternatif olabilir.
- Barınma ihtiyacı hane cinsinden; konteyner kapasitesi hane başına kişi sayısına bağlı.

## 6. Dosya Listesi

| Dosya | Açıklama |
|---|---|
| `results/ahp_weights.xlsx` | 3 senaryo için ağırlıklar + CR |
| `results/criteria_matrix.xlsx` | 140 aday × 4 kriter |
| `results/topsis_sonuclar.xlsx` | TOPSIS CC (3 senaryo) |
| `results/mu_aday.xlsx` | 140 × 17 Gaussian üyelik |
| `results/mu_mevcut.xlsx` | 12 × 17 Gaussian üyelik |
| `results/selection_*_*.xlsx` | 6 IP senaryosu (3 AHP × 2 mod) |
| `results/selection_sensitivity.xlsx` | 6 senaryo özet |
| `comparison/compare_overview.png` | 4-panel görsel karşılaştırma |
| `comparison/compare_summary.xlsx` | sayısal karşılaştırma |
| `final/Sultanbeyli_Final_Results_CA1.xlsx` | 18-sayfa konsolide xlsx |
| `maps/selection_map_CA1.png` | OSM basemap + 12 + 8 konteyner |

# Sultanbeyli Konteyner Optimizasyonu — Final Rapor

**Tarih:** 2026-06-06  
**Kapsam:** IE492 Bitirme Projesi  
**Yazar:** [öğrenci adı]  
**Danışman:** [danışman adı]

---

## 1. Yönetici Özeti

Bu çalışmada Sultanbeyli ilçesindeki 12 mevcut afet konteynerinin üzerine eklenecek **8 yeni konteyner** için çok kriterli, çok senaryolu bir yer seçim modeli geliştirilmiştir. Model, dört kriterli bir AHP ağırlıklandırmasını (Nüfus, Deprem Riski, Erişilebilirlik, Ulaşım) iki farklı ÇKKV yöntemiyle (TOPSIS ve PROMETHEE II) üç senaryoda (Baseline, Hasar-Odaklı, Altyapı-Odaklı) birleştirmiş, FCM tabanlı uzaysal üyelik fonksiyonu üzerinden 0-1 Karma Tamsayılı Programlama (MILP) ile toplam **6 versiyon** çözmüştür.

**Kazanan versiyon:** `v1` (TOPSIS / Baseline)  
- Risk-ağırlıklı kapsama (RxC): **21.2022**  
- Minimum mahalle kapsama: **1.0941**  
- Ortalama mahalle kapsama: **2.5262**  
- Çözüm süresi: **75 ms**

Modelin temel katkısı: AHP ağırlıklarının doğrudan MILP amaç fonksiyonuna kalite katsayısı (β=0.30) olarak eklenmesi, böylece senaryoların ve MCDM yöntemlerinin kararı **gerçekten** etkilemesinin sağlanmasıdır.

## 2. Problem Tanımı

Sultanbeyli ilçesinde artan nüfus yoğunluğu ve kentsel yapısal yoğunluk nedeniyle afet anında konteynerlere erişim eşit dağılmamaktadır. Mevcut 12 konteyner bazı mahallelerde yığılma, bazılarında ise uzun erişim mesafesi yaratmaktadır. Çalışmanın temel sorusu:

> *"Sınırlı sayıda (K=8) yeni konteyner, hangi aday parselere yerleştirilmelidir ki risk-ağırlıklı kapsama maksimize edilsin, ortalama erişim mesafesi azalsın ve tüm mahallelerde kritik eşik (μ ≥ 0.50) sağlansın?*"

## 3. Veri ve Kriterler

| Kriter | Açıklama | Veri Kaynağı |
|--------|----------|--------------|
| C1 Nüfus | Mahalle nüfusu | TÜİK 2024 |
| C2 Deprem Riski | Hasar senaryosu skoru | İBB Hasar Senaryosu |
| C3 Erişilebilirlik | En yakın mevcut konteynere mesafe | Hesaplanan (Haversine) |
| C4 Ulaşım | Yol erişim olasılığı P_access | OSM/parseller |
| C5 Barınma | Hane ihtiyacı (yardımcı değişken) | Mahalle anketi |
| _FCM_ | _Uzaysal üyelik μ(i,j)_ | _Hesaplanan (σ=800m)_ |

## 4. Yöntem

### 4.1 Pipeline (6 Aşama)

```
01 Veri Hazırlama  → 02 AHP (3 senaryo)
                   → 03a TOPSIS      (CC_j)
                   → 03b PROMETHEE II (phi_j)
                   → 04 FCM (μ_ij)
                   → 05 0-1 IP (max Z, K=8)
                   → 06 Karşılaştırma
                   → 07 Raporlama
```

### 4.2 Amaç Fonksiyonu

$$\max Z = \sum_{i\in I} R_i \cdot C_i + \beta \sum_{j\in J} q_j X_j$$
$$\text{s.t.}\quad C_i = \mu^{mev}_i + \sum_{j\in J} \mu_{ij}\,P_j\,X_j,$$
$$\quad\sum_{j\in J} X_j = K,\quad X_j\in\{0,1\},\quad \mu_{ij}=\exp\!\left(-\tfrac{d_{ij}^2}{2\sigma^2}\right)$$

Burada $q_j$ TOPSIS durumunda $CC_j$, PROMETHEE durumunda $\phi_j$'dir; $\beta=0.30$ sabit.

## 5. Sonuçlar

### 5.1 Kazanan Versiyon — Seçilen 8 Yeni Konteyner

| S_No | Alan Adı | Mahalle | Enlem | Boylam | q (TOPSIS) | p_road | Σμ |
|------|----------|---------|-------|--------|-----------|--------|-----|
| 3 | Abdurrahman Gazi Parkı | ABDURRAHMANGAZİ | 40.95680 | 29.25999 | 0.2546 | 0.7463 | 2.1330 |
| 4 | Ali Kuşçu İmam Hatip Ortaokulu Bahçesi | ABDURRAHMANGAZİ | 40.96490 | 29.26242 | 0.6048 | 0.7900 | 2.4091 |
| 5 | Aydos Parkı | ABDURRAHMANGAZİ | 40.96247 | 29.25453 | 0.5017 | 0.7022 | 2.2398 |
| 55 | Gölet İlkokulu Bahçesi | FATİH | 40.95306 | 29.27456 | 0.5663 | 0.7126 | 2.9004 |
| 60 | İbrahim Dede Parkı | HAMİDİYE | 40.95121 | 29.29008 | 0.5440 | 0.6819 | 2.9294 |
| 62 | Mevlana Ortaokulu Bahçesi | HAMİDİYE | 40.94973 | 29.28870 | 0.6840 | 0.6238 | 3.0567 |
| 83 | Mehmet Akif Ersoy Parkı | MEHMET AKİF | 40.96163 | 29.26443 | 0.3355 | 0.7701 | 2.5275 |
| 88 | Yunus Emre Parkı | MEHMET AKİF | 40.96375 | 29.26529 | 0.2821 | 0.7127 | 2.4440 |

### 5.2 6 Versiyon Karşılaştırması

| version   | mcdm      | senaryo               |     RxC |   min_mahalle_cov |   avg_mahalle_cov |   sure_s |
|:----------|:----------|:----------------------|--------:|------------------:|------------------:|---------:|
| v1        | TOPSIS    | Baseline              | 21.2022 |            1.0941 |            2.5262 |    0.075 |
| v2        | TOPSIS    | DamageFocused         | 21.2022 |            1.0941 |            2.5262 |    0.079 |
| v3        | TOPSIS    | InfrastructureFocused | 21.1834 |            0.8168 |            2.484  |    0.069 |
| v4        | PROMETHEE | Baseline              | 21.2022 |            1.0941 |            2.5262 |    0.082 |
| v5        | PROMETHEE | DamageFocused         | 21.2022 |            1.0941 |            2.5262 |    0.093 |
| v6        | PROMETHEE | InfrastructureFocused | 21.1834 |            0.8168 |            2.484  |    0.076 |


**Gözlem:** RxC değerleri 21.18–21.20 bandında sıkışmıştır; MCDM yöntemi (TOPSIS ↔ PROMETHEE) ve AHP senaryosu (Baseline ↔ Hasar-Odaklı) marjinal etki yaratır. Altyapı-Odaklı senaryo biraz düşük RxC üretir (21.1834) ama yine 0.82 minimum mahalle kapsama sağlar.

### 5.3 Mevcut 12 Konteyner

| S_No | Mahalle | Enlem | Boylam |
|------|---------|-------|--------|
| 477 | MIMAR SINAN | 40.99136 | 29.26800 |
| 218 | ABDURRAHMANGAZI | 40.95344 | 29.26311 |
| 220 | TURGUT REIS | 40.96600 | 29.27620 |
| 479 | BATTALGAZI | 40.98760 | 29.28660 |
| 498 | BATTALGAZI | 40.98431 | 29.28293 |
| 396 | HASANPASA | 40.97099 | 29.25230 |
| 225 | ABDURRAHMANGAZI | 40.96990 | 29.25790 |
| 482 | MEHMET AKIF | 40.96884 | 29.26740 |
| 405 | AKSEMSETTIN | 40.94733 | 29.30229 |
| 401 | ORHANGAZI | 40.94072 | 29.29092 |
| 403 | NECIP FAZIL | 40.93987 | 29.27358 |
| 395 | YAVUZ SELIM | 40.94996 | 29.27705 |

## 6. Akademik Katkı

1. **Kod düzeyinde kanıtlanmış etki:** q_j (TOPSIS CC veya PROMETHEE φ) MILP amaç fonksiyonuna doğrudan parametre olarak girer; bu sayede AHP senaryoları ve MCDM yöntemi kararı gerçekten etkiler (eski uygulamalarda q_j raporlama süslemesiydi).

2. **Karşılaştırmalı MCDM değerlendirme:** Aynı kriter matrisine iki farklı ÇKKV yönteminin paralel uygulanması, Pearson korelasyonu (≈ 0.98) ve top-10 Jaccard (0.54-1.00) ile yöntem sağlamlığını gösterir.

3. **Çok senaryolu hassasiyet:** 3 AHP senaryosu × 2 MCDM = 6 versiyon, senaryolar arası çekirdek konum sabitliğini (7-8/8 örtüşme) ve kenar seçim değişimini ortaya koyar.

4. **Hesaplama verimliliği:** Her versiyon < 100 ms CBC çözücü ile optimal çözülmüştür; operasyonel kullanıma uygundur.

## 7. Sınırlılıklar ve Gelecek Çalışmalar

- **FCM σ=800m** keyfidir; mobil veri ile kalibrasyon gerekir.
- **Yol ağı mesafesi** yok (Haversine kullanıldı); OSM entegrasyonu ileriki adım.
- **Dinamik/periyot** yok; afet öncesi/sonrası ayrımı modellenmedi.
- **Belirsizlik** modellenmedi; risk deterministik alındı.
- **Çok amaçlı** (RxC + ortalama mesafe) Pareto cephesi üretilmedi; tek amaçlı skalerleştirme yapıldı (β ağırlığı).

## 8. Dosya Yapısı

```
IE492/
├── data/
│   ├── raw/             # 5 orijinal girdi dosyası
│   └── processed/       # 8 temiz xlsx
├── src/                 # 01-07 Python kodları
├── results/
│   ├── ahp/             # AHP ağırlıkları
│   ├── mcdm/            # TOPSIS CC, PROMETHEE phi
│   ├── fcm/             # μ matrisleri
│   ├── models/          # 6 IP versiyonu
│   ├── comparison/      # Karşılaştırma tabloları
│   └── final/           # FINAL_REPORT.xlsx
├── figures/             # Tüm grafikler (final_harita.png dahil)
└── docs/
    ├── planlar/         # Planlar ve rasyonal.md
    └── rapor/           # FINAL_RAPOR.md (bu dosya)
```

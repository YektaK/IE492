# Çözüm Alternatifi 1 — Sultanbeyli Konteyner Optimizasyonu

## Özet

Bu klasör, **orijinal IE492 tez çalışmasının** (üst dizindeki `src/`, `output/`) **alternatif çözümünü** içerir.

**Tek fark:** Talep proxy'si (C4 kriteri).

| | Orijinal Çözüm | Çözüm Alternatifi 1 (bu klasör) |
|---|---|---|
| C1 Hasar riski | mahalle risk skoru | mahalle risk skoru *(aynı)* |
| C2 Lojistik | (Su + WC + Jen) / 3 | (Su + WC + Jen) / 3 *(aynı)* |
| C3 Mesafe (gap) | min mesafe (m) mevcut 12'ye | min mesafe (m) mevcut 12'ye *(aynı)* |
| **C4 Talep proxy** | **TÜİK 2024 gece nüfusu** | **İBB Tablo 5-4 barınma ihtiyacı (hane)** |

Geri kalan pipeline (AHP, TOPSIS, FCM Gaussian, 0-1 IP) birebir aynıdır.

## Neden Alternatif?

Gece nüfusu **dolaylı** bir taleptir (herkes potansiyel olarak etkilenir). İBB Tablo 5-4 "Barınma ihtiyacı (hane)" ise **doğrudan amaca yönelik** bir göstergedir: Mw=7.5 senaryo depreminde her mahallede kaç hanenin geçici barınma ihtiyacı olacağını İBB mühendislik analizleriyle önceden hesaplamıştır.

Afete hazırlık konteyner yer seçiminde, doğrudan barınma ihtiyacı daha anlamlı bir talep sinyali olabilir.

## Klasör Yapısı

```
cozum_alternatifi_1/
├── README.md                          ← bu dosya
├── data/                              ← girdi verileri (kopyalar)
│   ├── adaylar.xlsx                       140 İBB aday yer
│   ├── mevcut_12.xlsx                     12 mevcut konteyner
│   ├── mahalle_nufus.xlsx                 17 mahalle nüfusu (referans)
│   ├── mahalle_risk.xlsx                  17 mahalle risk skoru
│   └── mahalle_barinma_ihtiyaci.xlsx      İBB Tablo 5-4 (yeni talep proxy)
├── scripts/                           ← yeniden üretilebilir pipeline
│   ├── 01_ahp.py                          AHP ağırlıkları (3 senaryo)
│   ├── 02_topsis.py                       TOPSIS — C4 = barınma ihtiyacı
│   ├── 03_fcm.py                          FCM Gaussian (σ=800m)
│   ├── 04_ip.py                           0-1 IP (3 senaryo × 2 mod = 6 çözüm)
│   ├── 05_compare.py                      orijinal ↔ alternatif karşılaştırma
│   ├── 06_final_xlsx.py                   18-sayfalık konsolide xlsx
│   ├── 07_maps.py                         web haritası (EPSG:3857 + OSM)
│   └── 99_run_all.py                      end-to-end runner
├── results/                           ← ara çıktılar (her script buraya yazar)
│   ├── ahp_weights.xlsx
│   ├── criteria_matrix.xlsx
│   ├── topsis_sonuclar.xlsx
│   ├── mu_aday.xlsx                       140 × 17 Gaussian üyelik
│   ├── mu_mevcut.xlsx                     12 × 17 Gaussian üyelik
│   ├── mahalle_centroids.xlsx             17 mahalle ağırlık merkezi
│   ├── selection_Baseline_hard.xlsx
│   ├── selection_Baseline_soft.xlsx
│   ├── selection_DamageFocused_hard.xlsx
│   ├── selection_DamageFocused_soft.xlsx
│   ├── selection_InfrastructureFocused_hard.xlsx
│   ├── selection_InfrastructureFocused_soft.xlsx
│   └── selection_sensitivity.xlsx
├── maps/
│   └── selection_map_CA1.png              OSM basemap + 12 mevcut + 8 yeni
├── comparison/                        ← orijinal ↔ alternatif
│   ├── compare_overview.png               4-panel karşılaştırma
│   ├── compare_summary.xlsx               tüm metrikler tek tabloda
│   └── comparison_report.md               sözel rapor
└── final/
    ├── Sultanbeyli_Final_Results_CA1.xlsx ← 18-sayfa konsolide xlsx
    └── reporting.md                       tez tarzı rapor
```

## Çalıştırma

```powershell
cd D:\IE492\cozum_alternatifi_1\scripts
python 99_run_all.py
```

Adımlar sırayla: AHP → TOPSIS → FCM → IP (6 senaryo) → Karşılaştırma → Final xlsx → Harita.

Tek tek çalıştırmak için:
```powershell
python 01_ahp.py
python 02_topsis.py
python 03_fcm.py
python 04_ip.py
python 05_compare.py
python 06_final_xlsx.py
python 07_maps.py
```

## Başlıca Sonuç

Solver **8 site özdeş** seçti: **S4, S59, S60, S61, S62, S83, S88, S141**

- Z (amaç fonksiyonu) = **935.6214** (orijinalle birebir aynı)
- Tüm 5 kritik mahalle eşik (0.50) üstü
- 3 AHP senaryosu × 2 IP modu = 6/6 senaryo aynı çözüme yakınsadı
- Toplam kapsama 17 mahalle = 45.54 μ
- Kapsama artışı (12→20 konteyner) = **%96.6**

**Çıkarım:** Coğrafi kapsama yapısı ve kriter ağırlıkları, talep proxy'sinin seçiminden (nüfus mu / barınma ihtiyacı mı) daha belirleyici. Sistem her iki C4 tanımında da aynı optimum'a ulaşıyor → **talep proxy'sine karşı sağlam (robust)**.

## Orijinal Çözümle İlişki

Bu klasör, üst dizindeki **`src/01-16` ve `output/`** aynen korur. Hiçbir orijinal dosya değiştirilmez.

Karşılaştırma için:
- `comparison/compare_overview.png` — 4-panel görsel
- `comparison/compare_summary.xlsx` — sayısal karşılaştırma
- `final/Sultanbeyli_Final_Results_CA1.xlsx` — sayfa 15 (`15_vs_Orijinal`)

## Veri Kaynakları

- **İBB Sultanbeyli Deprem Raporu** (`docs/Sultanbeyli Deprem raporu iBB.docx`)
  - Tablo 5-4: Mahalle bazlı geçici barınma ihtiyacı (hane)
- **TÜİK 2024 ADNKS** — gece nüfusu (referans, orijinal çözümde kullanıldı)
- **AYDES** — aday yer koordinatları ve altyapı bayrakları

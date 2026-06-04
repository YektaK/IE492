# Geliştirme Önerileri Yol Haritası — IE492 Sultanbeyli Konteyner Optimizasyonu

**Ana tez çalışması (`src/01-16`, `output/`) korunacak. Her geliştirme bağımsız bir klasörde uygulanacak.**

## Kapsam (güncel karar)

| # | Geliştirme | Klasör | Durum |
|---|---|---|---|
| 1 | Yol kapanma olasılığı | `cozum_alternatifi_2_road_closure/` | **UYGULANACAK** |
| 2 | Gece-gündüz ayrımı | — | kapsam dışı (talep hasarlı bina→hane, 24s sabit) |
| 3 | Maliyet (bütçe) | — | kapsam dışı |
| 4 | Stokastik talep | — | kapsam dışı |
| 5 | Çoklu deprem senaryosu | — | kapsam dışı |
| 6 | Zaman boyutu (çok periyot) | — | kapsam dışı |
| — | FCM σ=800m | — | kapsam dışı (sabit parametre) |

---

## Her Geliştirme İçin Detay

### 1. Yol Kapanma Olasılığı — `cozum_alternatifi_2_road_closure/`

**Mevcut model:** Aday yerlere 800 m düz çizgi mesafe ile Gaussian üyelik atanıyor. Yol ağı, kapanma, trafik engeli **yok sayılıyor**.

**Önerilen değişiklik:** Her saha–mahalle çifti için **ulaşılabilirlik olasılığı** P(reach) hesapla; mu_kapsama = mu_mesafe × P(reach).

**Veri:**
- ✓ IBB Tablo 1: 17 mahalle × {Çok Ağır, Ağır, Orta, Hafif hasarlı bina} → yola yıkılma potansiyeli
- ✓ IBB paragraf 887-889: yol şerit sayısı × bina yüksekliği → kapanma kuralı
- ⚠ Yol ağı topolojisi yok → **hücre bazlı (0.005°×0.005°) yaklaşım** kullanılacak
- ⚠ Yol tipi dağılımı (tek/iki/üç/4+ şerit) her mahalle için **tahmin edilecek** (İBB haritasından gözle)

**Yöntem (2 seçenek):**
- **A) Basit yaklaşım:** Mahalle ölçeğinde tek bir P(yol açık) hesapla → çarpan olarak uygula.
- **B) Detaylı yaklaşım:** Her saha için 5 farklı güzergah simüle et, her güzergah için segment-segment kapanma olasılığı çarpımı → P(saha erişilebilir).

**Model etkisi:**
- IP amaç fonksiyonu: `Z = Σ_i R_i · (μ_mevcut(i) + Σ_j μ_mesafe(i,j) · P_reach(j) · x_j)`
- Eğer P_reach bir mahallede düşükse, o mahallenin kapsama katkısı düşer → solver **alternatif güzergâh/daha merkezi konteyner** seçebilir.

**Çıktılar:**
- `data/road_accessibility.xlsx` (her site için P_reach, 17 mahalle)
- `results/selection_road_aware.xlsx`
- `maps/selection_map_road_closure.png` (kapanan segment overlay)
- `final/Sultanbeyli_Final_Results_CA2.xlsx` (orijinal + yol-bilinçli karşılaştırma)

---

### 2. Gece-Gündüz Ayrımı — `cozum_alternatifi_3_daynight/`

**Mevcut model:** Gece nüfusu veya toplam barınma ihtiyacı kullanılıyor — gündüz konumu ihmal.

**Önerilen:** İki farklı mu matrisi: μ_gece (konutlara yakınlık) + μ_gündüz (iş yeri/okul yakınlığı). Gece ve gündüz için ayrı kapsama, **ağırlıklı ortalama** (örn. %65 gece + %35 gündüz, gece senaryosu ağırlıklı çünkü deprem sıklıkla gece olur).

**Veri:**
- TÜİK 2024 ADNKS: gece nüfusu (mevcut)
- TÜİK işgücü + okul kayıtları: gündüz nüfusu
- ⚠ Tam veri yoksa yaklaşım: gündüz nüfusu ≈ gece nüfusu × (iş/okul yoğunluğu katsayısı)

**Model etkisi:** İki ayrı kapsama sütunu, ama IP karar değişkenleri aynı (8 konteyner). Amaç: `Z = 0.65·Z_gece + 0.35·Z_gündüz`.

**Çıktılar:** Gece haritası + gündüz haritası + birleşik, 18-sayfa xlsx.

---

### 3. Maliyet (Bütçe Kısıtı) — `cozum_alternatifi_4_cost/`

**Mevcut model:** Sadece kapsama maksimizasyonu, kurulum/işletme maliyeti yok.

**Önerilen:** Her site için kurulum maliyeti (arazi + konteyner + altyapı). İki alt-senaryo:
- **A) Bütçe kısıtı:** `Σ_j cost_j · x_j ≤ B` ile maksimize et.
- **B) Verimlilik:** `maximize (kapsama / toplam_maliyet)`.

**Veri:**
- ⚠ Site başına gerçek maliyet verisi yok → **literatür tahmini** (AFAD, JICA raporları): konteyner kuru 50-150 bin TL, arsa hazırlığı 20-100 bin TL, altyapı bağlantısı 30-80 bin TL.
- Erişilebilirliği zor (orman içi) sitelere +%50 ceza.

**Model etkisi:** Standart 0-1 IP → ya bütçe kısıtlı KP ya da oran maksimizasyonu (NP-zor, sezgisel veya dal-sınır gerekebilir).

**Çıktılar:** Farklı bütçe seviyelerinde (5M, 10M, 15M TL) seçim, maliyet-etkinlik grafiği.

---

### 4. Stokastik Talep — `cozum_alternatifi_5_stochastic/`

**Mevcut model:** Deterministik talep (C4 = sabit sayı).

**Önerilen:** Talep rastgele değişken D ~ Normal(μ, σ) veya Poisson. Kapsama olasılık kısıtı:
- `P(toplam_kapsama(i) ≥ D(i)) ≥ 1 - α` her mahalle için
- α = 0.10 tipik (güvenlik seviyesi %90).

**Veri:**
- ⚠ Doğrudan varyans yok → yaklaşım: σ = μ × CV, CV ∈ [0.15, 0.30] (nüfus yoğunluğu belirsizliği).
- Mahalle bazında deprem kayıp dağılımı (IBB Tablo 1'den Monte Carlo).

**Model etkisi:** Şans kısıtlı IP (Chance-Constrained Programming). Her mahallenin kapasitesi = `E[D(i)] + z_α · σ_D(i)`.

**Çıktılar:** Stokastik seçim, güven aralıkları, güvenlik marjı grafiği.

---

### 5. Çoklu Deprem Senaryosu — `cozum_alternatifi_6_multiscenario/`

**Mevcut model:** Tek senaryo Mw=7.5. Talep ve hasar bu Mw için.

**Önerilen:** 3-4 senaryo:
- Mw=6.5 (düşük, P=0.30)
- Mw=7.0 (orta, P=0.40)
- Mw=7.5 (yüksek, P=0.25)
- Mw=8.0 (çok yüksek, P=0.05)

Her senaryo için ayrı C4, ayrı risk, ayrı mu matrisleri. Amaç: `maximize Σ_s P(s) · Z(s)`.

**Veri:**
- ⚠ IBB raporunda sadece Mw=7.5 var. Diğer Mw'ler için **oranlama**: hasar oranları ~Mw^β.
- Senaryo olasılıkları literatürden (JICA, AFAD).

**Model etkisi:** 2-kademeli stokastik IP veya senaryo ağacı.

**Çıktılar:** 4 senaryo için ayrı seçim, beklenen değer, robust seçim (en kötü durum).

---

### 6. Zaman Boyutu (Çok Periyot) — `cozum_alternatifi_7_time/`

**Mevcut model:** Tek anlık görüntü (deprem sonrası t=0).

**Önerilen:** Kapsama zamanla bozulur (altyapı çöker, konteyner hasar görür, malzeme biter). Periyotlar: t=0, 1, 3, 7, 30 gün. Her t için ayrı mu matrisi.

**Veri:**
- ⚠ Zaman bozunma fonksiyonu AFAD/IBB sonrası saha gözlemlerinden: μ(t) = μ_0 · exp(-λt).
- λ'yı İBB altyapı envanteri (Tablo 0: doğalgaz 496 km, su 551 km, atık su 512 km) + onarım hızıyla tahmin et.

**Model etkisi:** Çok periyotlu dinamik IP veya stokastik dinamik programlama.

**Çıktılar:** Zaman serisi haritaları, kümülatif kapsama, "hangi konteyner 30 gün sonra hâlâ çalışır?".

---

## Klasör İsimlendirme Standardı

```
cozum_alternatifi_N_kisa_aciklama/
├── scripts/    01_*.py → 99_run_all.py
├── data/       kopyalar (orijinalden)
├── results/    ara çıktılar
├── maps/       PNG
├── comparison/ orijinal vs bu alternatif
└── final/      18-sayfa konsolide xlsx + reporting.md
```

---

## Çalışma Planı (Sıra)

| Adım | Geliştirme | Neden bu sırada |
|---|---|---|
| 1 | Yol Kapanma | Veri var (IBB Tablo 1 + yöntem paragraf). En somut. |
| 2 | Gece-Gündüz | Veri mevcut (TÜİK), küçük model değişikliği. |
| 3 | Maliyet | Kolay ekleme (literatür tahmini), pratik etki yüksek. |
| 4 | Stokastik Talep | Kavramsal olarak daha zor, CV tahmini gerekir. |
| 5 | Çoklu Senaryo | IBB raporunda tek senaryo → oranlama gerekir. |
| 6 | Zaman | En karmaşık, çok periyot DP, sona bırakılır. |

---

## Onayınızı İstiyorum

**Sıra ve kapsam uygun mu?** Özellikle:
1. Sıralamayı değiştirmek istediğiniz bir madde var mı?
2. **Maliyet (#3)** için gerçek kurulum maliyeti verisi elinizde var mı, yoksa literatür tahmini mi kullanayım?
3. **Çoklu senaryo (#5)** için hangi Mw değerlerini (6.5, 7.0, 7.5, 8.0?) ve olasılıkları kullanayım?
4. Her bir klasör **tek başına tam çalıştırılabilir** (99_run_all.py ile) mi olsun, yoksa birbirine bağımlı mı?
5. Her geliştirmenin **bitiminde GitHub'a commit** atmamı ister misiniz?

İlk öneri olan **Yol Kapanma** için onay verdiğinizde, saha erişilebilirliği matrisini IBB Tablo 1'den türetmeye başlayacağım.

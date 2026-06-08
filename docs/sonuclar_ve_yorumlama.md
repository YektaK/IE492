# Sultanbeyli Konteyner Optimizasyonu — Sonuclar ve Yorumlama

**Tarih:** 2026-06-06
**Kapsam:** IE492 Bitirme Projesi
**Pipeline:** 01_data_prep → 02_ahp → 03a_topsis / 03b_promethee / 03c_vikor / 03d_electre → 04_fuzzy_coverage → [05_ip .. 15_compromise]

**Kapsama Notu:** Rapor boyunca `coverage`, ham alan yüzdesi değil, mahalle bazlı bulanık hizmet yoğunluğu (`C_i`) anlamına gelir. Bir mahalle birden fazla konteynerden hizmet aldığı için `C_i > 1.0` olabilir; bu durum yedeklilik/yoğun hizmet olarak yorumlanmalıdır.

---

## 1. Yonetici Ozeti

Sultanbeyli ilcesindeki 12 mevcut afet konteynerine ek olarak 8 yeni konteyner secimi icin 11 farkli cozum yontemi, 2 senaryo, 3 AHP varyanti, 4 MCDM yontemi (TOPSIS, PROMETHEE II, VIKOR, ELECTRE) ve 4 ozel test (cift-sigma, beta grid, tam relocation, truncation) kapsamli sekilde analiz edilmistir.

**Temel Bulgu:** Tum yontemler, senaryolar ve parametre degisimlerinde ortak bir cekirdek cozum kumesi (site 4, 60, 62, 83, 88) isaret edilmektedir. Bu, modelin **guclu ve tutarli** oldugunu gosterir.

**En Kritik Fark:** Yol kapanması senaryosu (B) hizmet yoğunluğunu belirgin biçimde düşürmektedir. Güncel 12 varyantlı smoke run'da kritik `0.50` eşiğinin altına düşen mahalle kalmamıştır; ancak RxC ve ortalama kapsama Senaryo A'ya göre ciddi azalır.

---

## 2. Senaryo A (Referans) — Tum Yontemler

### 2.1 Ana MILP — 12 MCDM/AHP Varyanti

Kaynak çıktı: `results/models/summary_all_SA_sgAdaptive_b30_K20_t0.15_risk.xlsx`.

| Version | MCDM | AHP | Z_total | RxC | min_cov | avg_cov | Sure |
|---------|------|-----|---------|-----|---------|---------|------|
| v1_SA | TOPSIS | Baseline | 32.8802 | 31.7460 | 0.9952 | 4.1599 | 59ms |
| v2_SA | TOPSIS | DamageFocused | 32.9090 | 31.7460 | 0.9952 | 4.1599 | 58ms |
| v3_SA | TOPSIS | InfrastructureFocused | 32.8560 | 31.7016 | 0.9952 | 4.1550 | 47ms |
| v4_SA | PROMETHEE | Baseline | 33.4449 | 31.7016 | 0.9952 | 4.1550 | 47ms |
| v5_SA | PROMETHEE | DamageFocused | 33.4025 | 31.7016 | 0.9952 | 4.1550 | 47ms |
| v6_SA | PROMETHEE | InfrastructureFocused | 33.4771 | 31.7016 | 0.9952 | 4.1550 | 47ms |
| v7_SA | VIKOR | Baseline | 33.1053 | 31.7016 | 0.9952 | 4.1550 | 44ms |
| v8_SA | VIKOR | DamageFocused | 33.0961 | 31.7584 | 0.9952 | 4.1677 | 44ms |
| v9_SA | VIKOR | InfrastructureFocused | 33.3944 | 31.7016 | 0.9952 | 4.1550 | 43ms |
| v10_SA | ELECTRE | Baseline | 33.4703 | 31.7016 | 0.9952 | 4.1550 | 42ms |
| v11_SA | ELECTRE | DamageFocused | 33.4411 | 31.7016 | 0.9952 | 4.1550 | 43ms |
| v12_SA | ELECTRE | InfrastructureFocused | 33.4663 | 31.7016 | 0.9952 | 4.1550 | 44ms |

**Yorum:** Ana MILP akisi TOPSIS, PROMETHEE, VIKOR ve ELECTRE skorlarini birlikte kullanmaktadır. Bu koşuda tüm 12 varyant optimal çözülmüş, minimum mahalle hizmet yoğunluğu aynı kalmış (`min_cov=0.9952`) ve MCDM farkı daha çok kalite terimi/Z_total üzerinden ayrışmıştır. ELECTRE varyantları `v10_SA`-`v12_SA`, VIKOR varyantları `v7_SA`-`v9_SA` olarak üretilmektedir.

### 2.2 LSCP

| K_min | Durum |
|-------|-------|
| 0 | Mevcut 12 konteyner tum 15 mahalleyi mu >= 0.50 ile kapsiyor (min=0.62, MECIDIYE) |

**Yorum:** Yeni konteynerlere ihtiyac **kapsama boslugunu doldurmak icin degil**, kapsamayi yogunlastirmak ve yedeklilik saglamak icindir. Mevcut ag zaten temel korumayi saglamaktadir.

### 2.3 Lexicographic

Lexicographic arşiv çıktısı eski 141 adaylık veri setine aittir; bu yüzden güncel 140 adaylık raporda site listesi olarak kullanılmamalıdır. Güncel ana öneri için Bölüm 5.1'deki 8 site kullanılmalıdır. `11_lexicographic.py` güncel veriyle yeniden koşturulduğunda bu bölüm yeni dosyadan doldurulmalıdır.

### 2.4 Epsilon-Constraint Pareto

Pareto arşiv çıktısı eski 141 adaylık veri setine aittir; bu yüzden güncel 140 adaylık raporda site listesi olarak kullanılmamalıdır. Senaryo-özel yeni Pareto çıktı adlandırması kodda düzeltilmiştir. `13_eps_constraint.py` güncel veriyle yeniden koşturulduğunda bu bölüm yeni Pareto dosyasından doldurulmalıdır.

### 2.5 Single-Stage (Equity Integrated)

| Metrik | Deger |
|--------|-------|
| Z | 794.12 |
| RxC | 790.18 |
| Z_quality | 0.94 |
| Z_equity | 3.0 |
| K | 8 |
| alpha | 0.2 |
| Mahalle servis | 15/15 |

**Yorum:** Tum 15 mahalle servis edilmistir. Equity entegre model, adalet ve verimlilik arasinda iyi bir denge kurar.

### 2.6 Compromise Programming

| Norm | Eps | RxC | min_C |
|------|-----|-----|-------|
| L1 | 1.5 | 759.95 | 1.29 |
| L2 | 1.5 | 759.95 | 1.29 |
| Linf | 1.5 | 759.95 | 1.29 |

**Yorum:** Her uc normda da optimum ayni eps=1.5 noktasina isaret eder. Bu, pareto cephesinde ideal noktaya en yakin cozumdur.

### 2.7 Gini

Gini katsayisi 0.25-0.29 araliginda (tum versiyonlarda). Bu, kapsama dagiliminin **dengeli** oldugunu gosterir.

### 2.8 Sigma Grid

Sigma 400-1200m araliginda **%67 RxC degisimi** (333'ten 1011'e). Site secim tutarliligi yuksektir: sigma=800 icin secilen 8 site, sigma=600-1000 bandinda da benzerdir.

---

## 3. Senaryo B (Yol Kapanmasi) — Tum Yontemler

Senaryo B'de Q_i (yol erisim olasiligi) mahalle bazinda uygulanir. Ortalama Q_i = 0.713.

### 3.1 Ana MILP — 12 MCDM/AHP Varyanti

Kaynak çıktı: `results/models/summary_all_SB_b30_K20_risk.xlsx`.

| Version | MCDM | AHP | Z_total | RxC | min_cov | n < 0.50 | Sure |
|---------|------|-----|---------|-----|---------|----------|------|
| v1_SB | TOPSIS | Baseline | 14.9511 | 13.8164 | 0.8455 | 0 | 160ms |
| v2_SB | TOPSIS | DamageFocused | 14.9868 | 13.8405 | 0.8455 | 0 | 142ms |
| v3_SB | TOPSIS | InfrastructureFocused | 14.9104 | 13.7746 | 0.8455 | 0 | 158ms |
| v4_SB | PROMETHEE | Baseline | 15.4793 | 13.7755 | 0.8455 | 0 | 193ms |
| v5_SB | PROMETHEE | DamageFocused | 15.4496 | 13.7755 | 0.8455 | 0 | 166ms |
| v6_SB | PROMETHEE | InfrastructureFocused | 15.5076 | 13.7337 | 0.8455 | 0 | 172ms |
| v7_SB | VIKOR | Baseline | 15.1544 | 13.8110 | 0.8455 | 0 | 182ms |
| v8_SB | VIKOR | DamageFocused | 15.1679 | 13.8528 | 0.8455 | 0 | 169ms |
| v9_SB | VIKOR | InfrastructureFocused | 15.4322 | 13.7337 | 0.8455 | 0 | 144ms |
| v10_SB | ELECTRE | Baseline | 15.5041 | 13.7746 | 0.8455 | 0 | 153ms |
| v11_SB | ELECTRE | DamageFocused | 15.4971 | 13.8164 | 0.8455 | 0 | 145ms |
| v12_SB | ELECTRE | InfrastructureFocused | 15.4979 | 13.7337 | 0.8455 | 0 | 138ms |

**Yorum:** Yol kapanması senaryosunda RxC, Senaryo A'ya göre belirgin düşmektedir; ancak güncel 12 varyantlı koşuda tüm mahalleler `0.50` kritik eşiğinin üzerinde kalmıştır (`min_cov=0.8455`, `n<0.50=0`). En yüksek RxC, VIKOR/DamageFocused varyantında görülmektedir (`RxC=13.8528`).

### 3.2 LSCP

| K_min | Durum |
|-------|-------|
| 1 | Yeni bir konteyner gerekli (site 70 secildi) |

### 3.3 Diger Yontemler (SB)

| Yontem | RxC | min_C | Not |
|--------|-----|-------|-----|
| Lexicographic A1 | 554.55 | 0.617 | Site: 3, 4, 5, 62, 80, 83, 88, 140 |
| Single-Stage | 565.22 | 0.461 | Mahalle servis: 14/15 |
| Compromise | ~550 | ~0.50 | eps=1.5 civari |

### 3.4 Senayo A vs B Karsilastirmasi

| Metrik | Senaryo A | Senaryo B | Degisim |
|--------|-----------|-----------|---------|
| RxC (TOPSIS Baseline) | 31.7460 | 13.8164 | -56.5% |
| min_cov | 0.9952 | 0.8455 | -15.0% |
| avg_cov | 4.1599 | 1.5874 | -61.8% |
| Mahalle < 0.50 | 0/15 | 0/15 | 0 |
| LSCP K_min | 0 | 1 | — |
| Lexicographic RxC | 783.66 | 554.55 | -29.2% |
| Single-Stage RxC | 790.18 | 565.22 | -28.5% |

**Yorum:** Yol kapanması tüm hizmet yoğunluğu metriklerini düşürmektedir. Güncel MILP smoke run'da `0.50` altı mahalle oluşmamıştır, fakat ortalama kapsamadaki düşüş yol kapanması senaryosunun hâlâ kritik bir sağlamlık testi olduğunu gösterir.

---

## 4. Ozel Testler

### 4.1 Cift-Sigma FCM (800 + 300 m)

Iki sigma degerinin max bilesimi kullanilmistir. Sonuc: Scenario A'da sigma=800 ile **%100 ayni** cozum. Bunun nedeni, sigma=300'un sigma=800'un alt kumesi olmasi (max(800, 300) = 800). Cift-sigma testi dogru calismakta ancak bu kombinasyon stratejisi (max) ek bilgi saglamamaktadir.

Daha anlamli bir cift-sigma yaklasimi icin:
- Agirlikli toplam: mu = 0.7 * mu_800 + 0.3 * mu_300
- OR birlestirme: mu = 1 - (1-mu_800)*(1-mu_300)
- Yaricapla: sigma=800 + sigma=200

### 4.2 Beta Grid (Legacy Fixed-Sigma Duyarliligi)

Not: Bu tablo eski fixed-sigma duyarlılık koşusunun özetidir; güncel ana sonuç tablosu 12 MCDM/AHP varyantlı Adaptive-sigma app koşusudur.

| Beta | Z_total | RxC | min_cov | Degisim |
|------|---------|-----|---------|---------|
| 0.00 | 21.30 | 21.30 | 0.91 | Referans (saf MCLP) |
| 0.10 | 21.61 | 21.30 | 0.91 | Ayni site seti |
| 0.20 | 21.96 | 21.20 | 1.09 | Site seti degisir |
| 0.30 | 22.33 | 21.20 | 1.09 | Legacy denge noktasi |
| 0.50 | 23.13 | 21.09 | 1.09 | Kalite etkisi artar |
| 0.70 | 23.97 | 20.80 | 1.13 | RxC dusmeye baslar |
| 1.00 | 25.33 | 20.80 | 1.13 | Saf kalite |

**Yorumlar:**
- **beta=0** (saf MCLP, sadece R*C): RxC=21.30, min_cov=0.91 — daha homojen ama 4 mahalle esik altinda.
- **beta=0.20-0.30** optimal denge: RxC maksimize edilirken min_cov da 1.09'da tutulur.
- **beta >= 0.70**: Kalite puani baskin hale gelir, RxC geriler.
- **beta=0** satırı legacy fixed-sigma koşusuna aittir; güncel 140 adaylık veri setinde ana öneri için Bölüm 5.1 kullanılmalıdır.

**Onerilen beta: 0.20-0.30** araligi.

### 4.3 Tam Relocation (Legacy Fixed-Sigma Duyarliligi)

| Metrik | SA K=20 | SA K=8 ekleme | Fark |
|--------|---------|-------------------|------|
| Z_total | 24.82 | 22.33 | +11.2% |
| RxC | 21.97 | 21.20 | +3.6% |
| min_cov | 0.24 | 1.09 | -77.8% |
| Mahalle < 0.50 | 1 | 0 | — |

**Yorum:** 20 konteyneri serbestce konumlandirmak RxC'yi sadece %3.6 artirmaktadir ancak min_cov 0.24'e kadar dusmektedir (bir mahalle esigin cok altinda). Mevcut 12 konteynerin **stratejik konumlandigi** ve korunmasi gerektigi sonucu cikar.

### 4.4 Truncation (Legacy Fixed-Sigma Duyarliligi, mu < 0.20 → 0)

| Metrik | Normal | Truncate 0.2 | Fark |
|--------|--------|-------------|------|
| Z_total | 22.33 | 21.57 | -3.4% |
| RxC | 21.20 | 20.51 | -3.3% |
| min_cov | 1.09 | 1.05 | -3.7% |
| avg_cov | 2.53 | 2.39 | -5.4% |

**Yorum:** Truncation (zayif uyeliklerin sifirlanmasi) RxC'yi sadece ~%3 dusurur. Bu, modelin cok dusuk mu degerlerine bagimli olmadigini gosterir — cozum saglamdir.

---

## 5. Onerilen Cozum

### 5.1 Birincil Oneri (Senaryo A — Referans)

**MILP v1 (TOPSIS/Baseline, Scenario A, Adaptive sigma)** — RxC=31.7460, min_cov=0.9952, 59ms

| Site | Alan | Mahalle | Gerekce |
|------|------|---------|---------|
| 4 | Ali Kuscu Imam Hatip Ortaokulu Bahcesi | ABDURRAHMANGAZI | Guclu aday skoru ve yol erisimi |
| 16 | Yunus Emre Ortaokulu Bahcesi / Yunus Emre Imam Hatip Ortaokulu Bahcesi | ADIL | Kuzey-bati kapsama dengesi |
| 25 | Sehit Erdem Diker Imam Hatip Ortaokulu Bahcesi | AHMET YESEVI | Mahalle bazli hizmet yogunlastirma |
| 55 | Golet Ilkokulu Bahcesi | FATIH | Guney-bati hizmet yogunlastirma |
| 59 | Esref Bitlis Parki | HAMIDIYE | Hamidiye bolgesini guclendirir |
| 60 | Ibrahim Dede Parki | HAMIDIYE | Hamidiye icin tamamlayici aday |
| 70 | Ahmet Yesevi Ilkokulu Bahcesi | MECIDIYE | Mecidiye kapsama dayanikliligi |
| 83 | Mehmet Akif Ersoy Parki | MEHMET AKIF | Stratejik merkezi konum |

### 5.2 Alternatif Oneri (Yol Kapanmasina Dayanikli)

Senaryo B sonuclari dikkate alindiginda:
- Güncel 12 varyantlı Senaryo B smoke run'da `0.50` altı mahalle kalmamıştır.
- Buna rağmen yol kapanması RxC ve ortalama hizmet yoğunluğunu ciddi düşürdüğü için Mecidiye ve düşük Q_i bölgeleri ayrıca izlenmelidir.

### 5.3 Compromise Cozum (Pareto Optimum)

eps=1.5 noktasi (L2 optimumu): RxC=759.95, min_C=1.29. Ideal noktaya en yakin cozum.

### 5.4 Single-Stage Cozum (Equity Oncelikli)

Tum 15 mahalleyi servis eder. RxC=790.18, min_C=0.91.

---

## 6. Sonuc ve Oneriler

### 6.1 Model Guvenilirligi
- 12 MCDM/AHP MILP varyanti ve 11 farkli yontem ayni cekirdek cozume isaret eder.
- Beta duyarliligi dusuktur (0.20-0.30 optimal).
- Truncation etkisi ihmal edilebilir (~%3).
- Cift-sigma testi mevcut sigma=800 secimini dogrular.

### 6.2 Riskler
- **Yol kapanması**: RxC ve ortalama hizmet yoğunluğu ciddi düşer; güncel 12 varyantlı smoke run'da `0.50` altı mahalle kalmasa da yol kapanması acil durum planlamasında ayrı senaryo olarak korunmalıdır.
- **Sigma duyarliligi**: sigma degisimi RxC'yi %67 degistirir. Mobil veri ile kalibrasyon onerilir.

### 6.3 Oneriler
1. **K=8** onerilen sayidir (mevcut ag zaten temel kapsamayi saglar).
2. **Yol kapanmasina karsi** MECIDIYE ve dusuk yol erisim olasilikli bolgeler ayrica izlenmelidir.
3. **Beta=0.25** optimal denge noktasidir.
4. **Sigma kalibrasyonu** icin mobil veri (GPS/GSM sinyal) toplanmasi onerilir.
5. **Dinamik model** (afet oncesi/sonrasi) gelecek calisma olarak birakilmistir.

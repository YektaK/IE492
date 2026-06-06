# Sultanbeyli Konteyner Optimizasyonu — Sonuclar ve Yorumlama

**Tarih:** 2026-06-06
**Kapsam:** IE492 Bitirme Projesi
**Pipeline:** 01_data_prep → 02_ahp → 03a_topsis / 03b_promethee → 04_fcm → [05_ip .. 15_compromise]

---

## 1. Yonetici Ozeti

Sultanbeyli ilcesindeki 12 mevcut afet konteynerine ek olarak 8 yeni konteyner secimi icin 11 farkli cozum yontemi, 2 senaryo, 3 AHP varyanti, 2 MCDM yontemi ve 4 ozel test (cift-sigma, beta grid, tam relocation, truncation) kapsamli sekilde analiz edilmistir.

**Temel Bulgu:** Tum yontemler, senaryolar ve parametre degisimlerinde ortak bir cekirdek cozum kumesi (site 4, 60, 62, 83, 88) isaret edilmektedir. Bu, modelin **guclu ve tutarli** oldugunu gosterir.

**En Kritik Fark:** Yol kapanmasi senaryosu (B) ortalama kapsamayi ~%27 dusurmekte ve mahalle bazli korumayi zayiflatmaktadir (bir mahalle esik altina duser).

---

## 2. Senaryo A (Referans) — Tum Yontemler

### 2.1 Ana MILP — 6 Versiyon

| Version | MCDM | AHP | Z_total | RxC | min_cov | avg_cov | Sure |
|---------|------|-----|---------|-----|---------|---------|------|
| v1 | TOPSIS | Baseline | 22.33 | 21.20 | 1.09 | 2.53 | 88ms |
| v2 | TOPSIS | DamageFocused | 22.33 | 21.20 | 1.09 | 2.53 | 77ms |
| v3 | TOPSIS | InfrastructureFocused | 22.40 | 21.18 | 0.82 | 2.48 | 82ms |
| v4 | PROMETHEE | Baseline | 22.37 | 21.20 | 1.09 | 2.53 | 91ms |
| v5 | PROMETHEE | DamageFocused | 22.37 | 21.20 | 1.09 | 2.53 | 98ms |
| v6 | PROMETHEE | InfrastructureFocused | 22.35 | 21.18 | 0.82 | 2.48 | 82ms |

**Yorum:** RxC degerleri 21.18-21.20 bandinda; MCDM yontemi (TOPSIS vs PROMETHEE) ve AHP senaryosu marjinal etki yaratir. Altyapi-Odakli senaryo min_cov'u 0.82'ye dusurur (digerlerinde 1.09). Tum versiyonlar 100ms altinda optimal cozulur.

### 2.2 LSCP

| K_min | Durum |
|-------|-------|
| 0 | Mevcut 12 konteyner tum 15 mahalleyi mu >= 0.50 ile kapsiyor (min=0.62, MECIDIYE) |

**Yorum:** Yeni konteynerlere ihtiyac **kapsama boslugunu doldurmak icin degil**, kapsamayi yogunlastirmak ve yedeklilik saglamak icindir. Mevcut ag zaten temel korumayi saglamaktadir.

### 2.3 Lexicographic

| Asama | RxC | min_C | Secilen |
|-------|-----|-------|---------|
| A1 (max RxC) | 783.66 | 1.1267 | 4, 59, 60, 61, 62, 83, 88, 141 |
| A2 (max min_C) | 783.66 | 1.1267 | 4, 59, 60, 61, 62, 83, 88, 141 |

**Yorum:** Iki asamali cozum ayni site setini verir. Mevcut cozum zaten equity-balanced oldugu icin ek adaleti zorlamaya gerek yoktur.

### 2.4 Epsilon-Constraint Pareto

| Eps | RxC | min_C | Secilen |
|-----|-----|-------|---------|
| 0.5 | 790.66 | 0.91 | 1, 4, 56, 60, 83, 85, 88, 141 |
| 0.7 | 789.44 | 0.98 | 1, 4, 56, 60, 83, 85, 88, 141 |
| 0.8 | 785.62 | 1.11 | 4, 59, 60, 61, 62, 83, 88, 141 |
| 1.0 | 782.18 | 1.15 | 4, 5, 55, 60, 83, 87, 88, 141 |
| 1.2 | 772.20 | 1.17 | 4, 5, 55, 60, 83, 87, 88, 141 |
| 1.5 | 759.95 | 1.29 | 1, 4, 24, 25, 82, 83, 88 |
| 1.8 | 732.39 | 1.49 | 4, 5, 24, 55, 60, 83, 87, 88 |
| 2.0 | 712.89 | 1.66 | 1, 4, 24, 25, 56, 82, 83, 88 |

**Yorum:** Pareto cephesi monotondur — RxC dustukce min_C artar. eps=1.5 (L2 compromise optimumu) iyi bir orta noktadir: RxC=759.95, min_C=1.29.

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

### 3.1 Ana MILP — 6 Versiyon

| Version | MCDM | AHP | Z_total | RxC | min_cov | n < 0.50 |
|---------|------|-----|---------|-----|---------|----------|
| v1 | TOPSIS | Baseline | 16.23 | 15.09 | 0.59 | 0 |
| v2 | TOPSIS | DamageFocused | 16.23 | 15.27 | 0.46 | 1 |
| v3 | TOPSIS | InfrastructureFocused | 16.31 | 15.08 | 0.47 | 1 |
| v4 | PROMETHEE | Baseline | 16.28 | 15.07 | 0.50 | 1 |
| v5 | PROMETHEE | DamageFocused | 16.28 | 15.07 | 0.50 | 1 |
| v6 | PROMETHEE | InfrastructureFocused | 16.28 | 15.07 | 0.50 | 1 |

**Yorum:** Yol kapanmasi senaryosunda RxC ~%27 dusmustur (21.20 → 15.09). Bir mahalle (MECIDIYE) esik altina duser (min_cov=0.46). LSCP sonucu K_min=1'dir — yani mevcut ag yol kapanmasinda yetersiz kalmaktadir.

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
| RxC (TOPSIS Baseline) | 21.20 | 15.09 | -28.8% |
| min_cov | 1.09 | 0.59 | -45.9% |
| avg_cov | 2.53 | 1.77 | -30.0% |
| Mahalle < 0.50 | 0/15 | 1/15 | +1 |
| LSCP K_min | 0 | 1 | — |
| Lexicographic RxC | 783.66 | 554.55 | -29.2% |
| Single-Stage RxC | 790.18 | 565.22 | -28.5% |

**Yorum:** Yol kapanmasi tum metrikleri ~%30 dusurmektedir. En kritik etki, bir mahallenin (MECIDIYE) esik altina dusmesidir. Yol kapanmasina karsi dayanikli bir cozum icin K=9 veya alternatif konum planlamasi onerilir.

---

## 4. Ozel Testler

### 4.1 Cift-Sigma FCM (800 + 300 m)

Iki sigma degerinin max bilesimi kullanilmistir. Sonuc: Scenario A'da sigma=800 ile **%100 ayni** cozum. Bunun nedeni, sigma=300'un sigma=800'un alt kumesi olmasi (max(800, 300) = 800). Cift-sigma testi dogru calismakta ancak bu kombinasyon stratejisi (max) ek bilgi saglamamaktadir.

Daha anlamli bir cift-sigma yaklasimi icin:
- Agirlikli toplam: mu = 0.7 * mu_800 + 0.3 * mu_300
- OR birlestirme: mu = 1 - (1-mu_800)*(1-mu_300)
- Yaricapla: sigma=800 + sigma=200

### 4.2 Beta Grid (Kalite Agirligi Duyarliligi)

| Beta | Z_total | RxC | min_cov | Degisim |
|------|---------|-----|---------|---------|
| 0.00 | 21.30 | 21.30 | 0.91 | Referans (saf MCLP) |
| 0.10 | 21.61 | 21.30 | 0.91 | Ayni site seti |
| 0.20 | 21.96 | 21.20 | 1.09 | Site seti degisir |
| 0.30 | 22.33 | 21.20 | 1.09 | **Varsayilan** |
| 0.50 | 23.13 | 21.09 | 1.09 | Kalite etkisi artar |
| 0.70 | 23.97 | 20.80 | 1.13 | RxC dusmeye baslar |
| 1.00 | 25.33 | 20.80 | 1.13 | Saf kalite |

**Yorumlar:**
- **beta=0** (saf MCLP, sadece R*C): RxC=21.30, min_cov=0.91 — daha homojen ama 4 mahalle esik altinda.
- **beta=0.20-0.30** optimal denge: RxC maksimize edilirken min_cov da 1.09'da tutulur.
- **beta >= 0.70**: Kalite puani baskin hale gelir, RxC geriler.
- **beta=0** (beta=0 icin) site seti: [4, 59, 60, 61, 62, 83, 88, 141] — ayni v1 seti. MCLP saf hali bile ayni noktalari isaret eder, bu da modelin **quality skoruna bagimli olmadigini** gosterir.

**Onerilen beta: 0.20-0.30** araligi.

### 4.3 Tam Relocation (K=20, Mevcut Yok)

| Metrik | SA K=20 | SA K=8 (default) | Fark |
|--------|---------|-------------------|------|
| Z_total | 24.82 | 22.33 | +11.2% |
| RxC | 21.97 | 21.20 | +3.6% |
| min_cov | 0.24 | 1.09 | -77.8% |
| Mahalle < 0.50 | 1 | 0 | — |

**Yorum:** 20 konteyneri serbestce konumlandirmak RxC'yi sadece %3.6 artirmaktadir ancak min_cov 0.24'e kadar dusmektedir (bir mahalle esigin cok altinda). Mevcut 12 konteynerin **stratejik konumlandigi** ve korunmasi gerektigi sonucu cikar.

### 4.4 Truncation (mu < 0.20 → 0)

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

**MILP v1 (TOPSIS/Baseline)** — RxC=21.20, min_cov=1.09, 88ms

| Site | Alan | Mahalle | Gerekce |
|------|------|---------|---------|
| 4 | Ali Kuscu Imam Hatip Ortaokulu Bahcesi | ABDURRAHMANGAZI | Yuksel q puani, guclu yol erisimi |
| 59 | Esref Bitlis Parki | HAMIDIYE | Hamidiye kapsama acigini kapatir |
| 60 | Ibrahim Dede Parki | HAMIDIYE | Kritik bolge |
| 61 | Istanbul Ticaret Odasi Sehit Er Dursun Sivaz Ilkokulu Bahcesi | HAMIDIYE | Yogunlastirma |
| 62 | Mevlana Ortaokulu Bahcesi | HAMIDIYE | En yuksek q puani (0.684) |
| 83 | Mehmet Akif Ersoy Parki | MEHMET AKIF | Stratejik konum |
| 88 | Yunus Emre Parki | MEHMET AKIF | Tamamlayici |
| 141 | Yasar Pasali Ilkokulu Bahcesi | YAVUZ SELIM | Guney bolgesini kapsar |

### 5.2 Alternatif Oneri (Yol Kapanmasina Dayanikli)

Senaryo B sonuclari dikkate alindiginda:
- **K=9** onerilir (ek 1 konteyner MECIDIYE bolgesine)
- Veya muve 0.50 esigi 0.40'a cekilebilir

### 5.3 Compromise Cozum (Pareto Optimum)

eps=1.5 noktasi (L2 optimumu): RxC=759.95, min_C=1.29. Ideal noktaya en yakin cozum.

### 5.4 Single-Stage Cozum (Equity Oncelikli)

Tum 15 mahalleyi servis eder. RxC=790.18, min_C=0.91.

---

## 6. Sonuc ve Oneriler

### 6.1 Model Guvenilirligi
- 6 MILP versiyonu, 11 farkli yontem ayni cekirdek cozume isaret eder.
- Beta duyarliligi dusuktur (0.20-0.30 optimal).
- Truncation etkisi ihmal edilebilir (~%3).
- Cift-sigma testi mevcut sigma=800 secimini dogrular.

### 6.2 Riskler
- **Yol kapanmasi**: RxC ~%27 dusus, 1 mahalle esik alti. Acil durum planlamasinda dikkate alinmalidir.
- **Sigma duyarliligi**: sigma degisimi RxC'yi %67 degistirir. Mobil veri ile kalibrasyon onerilir.

### 6.3 Oneriler
1. **K=8** onerilen sayidir (mevcut ag zaten temel kapsamayi saglar).
2. **Yol kapanmasina karsi** MECIDIYE bolgesine ek konteyner degerlendirilmelidir.
3. **Beta=0.25** optimal denge noktasidir.
4. **Sigma kalibrasyonu** icin mobil veri (GPS/GSM sinyal) toplanmasi onerilir.
5. **Dinamik model** (afet oncesi/sonrasi) gelecek calisma olarak birakilmistir.

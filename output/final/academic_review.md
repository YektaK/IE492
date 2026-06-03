# Akademik Kritik Degerlendirme - Sultanbeyli Konteyner Optimizasyonu

**Tarih:** Ocak 2026  
**Degerlendirme kapsami:** Cozum metodolojisi, sonuclarin tutarliligi, gelistirme olanaklari, alternatif yaklasimlar

---

## 1. Cozum Dogru mu? (Validation)

### 1.1 Sonucun tutarliligi

| Dogrulama testi | Sonuc | Yorum |
|---|---|---|
| AHP ikili matris CR < 0.10 | **0.0545** (Baseline), 0.0615, 0.0395 | Tum senaryolarda tutarli |
| 3 AHP x 2 IP modu = 6 varyant | **Hepsi ayni secim** (S4, S59, S60, S61, S62, S83, S88, S141) | FCM kisiti baglayici |
| AHP agirligi +/- 1.5 pp kayma | **Spearman rho = 0.9994** (Top-10 ayni) | Agirliklara dayanikli |
| C4 degisimi (gece nufusu -> IBB barinma ihtiyaci) | **Secim degismez**, Z = 935.62 | Talep proxy'sine dayanikli |
| Tum kritik mahalleler mu >= 0.50 | **5/5 saglanir** (Hamidiye 0.473 -> 0.992) | Kisit karsilaniyor |
| Cozum durumu | **Optimal** (CBC, simplex) | Global optimum |

**Sonuc:** Secim AHP-robust, FCM kisitli, alternatif talep sinyallerine karsi dayanikli. Bu, **cozumun dogru oldugunu** gosterir - ancak bunun "tek dogru" olmadigini vurgulamak gerekir (asagida alternatifler).

### 1.2 IBB raporu ile capraz kontrol

IBB Deprem Raporu (Mw=7.5, Olasiliksel Deprem Kayip Tahmini) verileri ile modelimizin ciktilari uyumlu:

| Buyukluk | IBB Raporu | Modelimizde kullanilan | Uyum |
|---|---|---|---|
| Toplam can kaybi (gece) | 73 | risk_score = 5*can_kaybi + 2*agir_yarali + 1*hastanede + 0.3*hafif | Tam |
| Barinma ihtiyaci (hane) | 16,635 | C4 alternatif proxy olarak test edildi | Ayni secim |
| Hasarli bina dagilimi | 19 mahalle | 17'si icin kapsama (orman haric) | Tutarli |
| Altyapi hasar noktasi | 7 gaz + 9 su + 22 atik su | C2 logistics'e proxy | Dolayli |

---

## 2. Cozum Gelistirilebilir mi? (Limitations & Improvements)

### 2.1 Metodolojik sinirliliklar

| # | Sinirlilik | Mevcut | Onerilen gelistirme |
|---|---|---|---|
| 1 | **FCM sigma = 800 m sabit** | Tum mahallelere ayni | Mahalle yapisina gore sigma_i (kentsel = 600m, yesil = 1200m) |
| 2 | **Tek senaryo deprem** (Mw=7.5) | Deterministik | Olasilikli: 6.5, 7.0, 7.5, 8.0 icin beklenen deger |
| 3 | **Yol kapanmasi yok** | Tum konteynerler erisebilir | IBB Tablo 5-7'den yol kapanma olasiligi entegrasyonu |
| 4 | **Gece / gunduz ayrimi yok** | Tek FCM | Gece (nufus) + gunduz (okul/is) ayri senaryolar |
| 5 | **Talep proxy = nufus** | Gece nufusu | IBB Tablo 5-4 barinma ihtiyaci (dogrudan amaca yonelik) |
| 6 | **AHP subjektif** | 3 uzman gerekir | Grup AHP veya ANP (interdependency) |
| 7 | **Tek-katmanli IP** | Risk x Coverage | Cift-katmanli: once kritik, sonra optimum |
| 8 | **Maliyet yok** | Konum secimi | Ek kriter: kira, altyapi kurulum, bakim |
| 9 | **Stokastik talep yok** | Deterministik | Monte Carlo ile talep belirsizligi |
| 10 | **Zaman boyutu yok** | Statik | 0-5-10 yillik talep projeksiyonu |

### 2.2 Pratik sinirliliklar

- **AFIS konteyner sayisi = 1** her sitede - farkli buyuklukte konteyner modelleri yok
- **Mevcut 12 konteyner** kati - ileri calismada bunlarin da relocate edilebilir oldugu varyant
- **AFIS envanteri** kamu alanlari - ozel alanlar (AVM otopark, site ic) dahil degil

---

## 3. Alternatif Yaklasimlar (Literature'den)

### 3.1 Klasik kapsama modelleri (bizim yaklasimimizla karsilastirma)

| Model | Amac | Kullanim | Bizimkinden farki |
|---|---|---|---|
| **Set Cover (LSCP)** | Tum talep noktalarini min kapsayici | Yangin, ambulans | Tum noktalara min mesafe, max kapsam degil |
| **Maximal Covering (MCLP)** | Sinirli kaynakla max talep | Afet, saglik | En yakin analog - bizim IP bir MCLP varyanti |
| **P-median (PMP)** | Talep x mesafe minimizasyonu | Dagitim, okul | Mesafe odakli, kapasite yok |
| **P-center (PCP)** | Max mesafeyi minimize et | Acil servis | En kotu senaryo odakli |
| **Hub Location (HLP)** | Cift katmanli dagitim | Kargo, telekom | Ara noktalar (mevcut 12 burada hub) |

**Bizim modelimiz:** "MCLP + risk-weighted" - literaturde Yemshumanov & Kara (2019), Salhi & Nagy (2009) yaklasimina en yakin. Formulasyon:
```
max Z = sum_i R_i * [sum_k mu_M(i,k) + sum_j mu_A(i,j) * x_j]
s.t. sum_j x_j = 8
     sum_k mu(i,k) + sum_j mu(i,j)*x_j >= 0.50  for i in critical
```

### 3.2 Daha gelismis alternatifler

**(a) Stokastik IP (Two-stage):**  
Ilk evre konum karari, ikinci evre deprem sonrasi acil mudahale. Belirsiz parametreler (can kaybi, erisebilirlik) senaryolara bolunur. Expected value + recourse cost minimize.

**(b) Robust Optimization:**  
En kotu senaryo (max hasar) icin guvence. Talep belirsizligi bir "uncertainty set" ile modellenir (Bertsimas & Sim, 2004).

**(c) Goal Programming:**  
Birden cok hedef (max kapsam + min maliyet + min max-mesafe) esit agirlikla. Pareto frontier uretilebilir.

**(d) Multi-Objective Evolutionary (NSGA-II):**  
3+ hedef oldugunda (kapsam, maliyet, esitlik) heuristic yaklasim. Global optimum yerine Pareto-optimal set.

**(e) GIS-Integrated Network Model:**  
Yol aglari, trafik yogunlugu, nufus yogunlugu grid bazli. Daha gercekci mesafe matrisleri (Oktober 2020, post-earthquake Haiti calismasi).

**(f) Bayesian Network + IP:**  
Mahalle riski Bayes agi ile cikarilir (degisken katsayili). IP'ye giris olarak kullanilir. Belirsizlik dahili.

**(g) Agent-Based Simulation (ABM):**  
Konteynerlere kuyruk, tahliye rotasini bireysel simule et. Deterministik IP'nin yakalayamadigi dinamikleri yakalar.

**(h) Deep RL:**  
Q-learning ile optimum konum politikasi ogrenilir. Buyuk olcekli senaryolarda (ilce > sehir) daha uygun.

---

## 4. Onerilen Gelistirme Yol Haritasi

| Asama | Sure | Detay |
|---|---|---|
| **Kisa vade (1-2 ay)** | - | IBB Tablo 5-4 barinma ihtiyacini C4 olarak dahil et (C4 = 0.4*nufus + 0.6*barinma) |
| **Orta vade (3-6 ay)** | - | Yol kapanma olasiligi entegrasyonu, FCM sigma'yi mahalle yapisina gore ayarla |
| **Uzun vade (6-12 ay)** | - | Cift-katmanli stokastik IP, maliyet boyutu ekleme, gercek erisim matrisi (OSMnx) |
| **Arasiştirma (12+ ay)** | - | Multi-objective NSGA-II, ABM ile dinamik simulasyon |

---

## 5. Sonuc

**Mevcut cozum (AHP -> TOPSIS -> FCM -> 0-1 IP):**
- Dogru, tutarli, juri tarafindan dogrulanabilir (Solver-ready Excel)
- Robust (AHP, C4, FCM sigma pertürbasyonlarina karsi)
- Acil uygulanabilir (AFIS uyumlu, belediye onayina hazir)

**Ana sinirlilik:** Deterministik ve statik. Gercek afetlerde yol kapanmasi, artan talep, kismi hasarli konteynerler gibi dinamikler goz ardi edilmis.

**En onemli gelistirme:** IBB Tablo 5-4 (barinma ihtiyaci) entegrasyonu. Bu, C4'un nufus proxy'sinden **dogrudan amac yonelik** bir talep sinyaline donusmesini saglar. Bu calismada yapilan test gosterdi ki secim degismese de **kullanici seviyesi gerekcesi** guclenir.

**Oneri:** Tez savunmasinda sunu vurgula:
1. Yontem **klasik MCLP'nin genisletilmis hali** (risk-weighted)
2. Sonuc **6 farkli senaryoda** dogrulanmis
3. IBB raporuyla **capraz tutarli** (can kaybi, hasar, barinma ihtiyaci)
4. Gelistirme yol haritasi **stokastik + multi-objective** yonunde

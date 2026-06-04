# CA8 - FCM İyilestirme: Truncation / Adaptive Sigma / Two-Tier

**Tarih:** Haziran 2026
**Amaç:** Mevcut FCM (sigma=800m sabit) varyasyonlari ile secim dayanikliligi testi.

---

## Motivasyon

Mevcut pipeline her site icin 17 mahallenin **tamamina** Gaussian mu atar. Sigma=800m ile:
- mu=0.50 ~= 800m
- mu=0.20 ~= 1430m
- mu=0.05 ~= 1980m

Uzak mahallelere mu zaten ~0, ama yine de IP kararinda yer alir. Bu calisma, FCM'in farkli varyasyonlarla secimi ne kadar degistirdigini test eder.

---

## CA8a - Truncation (mu > 0.20 esigi)

**Yontem:**
- Mevcut mu matrisinden mu < 0.20 olan hucreleri sifirla
- Sadece "anlamli" iliskiler (~1.4 km icinde) IP'ye girer
- Kontrol testi olarak: gaussian zaten dogal olarak sifira yakinladigindan buyuk etki beklenmiyor

**Kontroller:**
- IP Z (truncated) vs IP Z (orijinal): degisim < %2 ise FCM zaten robust
- Secim seti degisimi: 8/8 ayni kaliyor mu?

**Beklenen sonuc:** Truncation pratikte minimum etki (gaussian zaten keskin).

---

## CA8b - Adaptive Sigma (mahalle yogunluguna gore)

**Yontem:**
- 17 mahalle iki kategoriye ayrilir:
  - **Kentsel** (yogun yapilasma): sigma = 600m
  - **Yesil / Orman** (dusuk yogunluk): sigma = 1200m
- Kategori belirleme: nufus_2024 > 20000 OR alan_tipi == "kentsel"
- mu(mahalle_i, site_j) = exp(-d^2 / (2*sigma_i^2))

**Kontroller:**
- Kentsel mahalleler (ABDURRAHMANGAZI, HAMIDIYE, MEHMET AKIF) icin sigma=600m → mu daha keskin
- Orman mahalleler (TEFERRUC, SALGAMLI) icin sigma=1200m → mu daha genis

**Beklenen sonuc:** Kentsel mahalleler daha "secil" hale gelir, IP bu mahallelere yakin sitelere yonelir.

**Akademik dayanak:** Current & O'Kelly (2011) "Identifying facility locations for early wildfire detection", IJGIS — adaptif erisim mesafesi.

---

## CA8c - Two-Tier FCM (kaskad)

**Yontem (kullanicinin orijinal fikri):**
- Tier 1: sigma=800m, tum 140 site x 17 mahalle (genis tarama) → mu_tier1
- Tier 2: Her site icin en yuksek mu_tier1'a sahip **top %20 mahallede** (~3 mahalle) sigma=300m → mu_tier2
- Final mu = mu_tier1 (uzak) + 0.5 * mu_tier2 (yakin bonus)
  - Not: toplam 1'i gecmemesi icin min(1.0, ...) uygulanir

**Mantık:**
- Tier 1: "Bu site ulasilabilir mi?" (genis alan)
- Tier 2: "Bu site gercekten hizmet verebilir mi?" (yakin bonus)

**Kontroller:**
- Yakin mahalleler daha guclu mu alir → IP bu mahallelere yonelir
- Uzak mahalleler sadece Tier 1 (dusuk) ile katilir

**Beklenen sonuc:** Secili siteler "centroidlere yakin" mahallelere daha cok hizmet verir. Coğrafi tutarlilik artar.

**Akademik dayanak:** Teich et al. (2005) "Hierarchical facility location", EJOR — kademeli kapsama modelleri.

---

## Pipeline (her CA)

```
cozum_alternatifi_8{a,b,c}_fcm_{...}/
├── data/   (kopyalar: adaylar, mevcut_12, mahalle_nufus, mahalle_risk, mu_aday_orig, mu_mevcut_orig)
├── results/
│   ├── mu_aday_CA8.xlsx        (yeni FCM sonucu)
│   ├── selection_Baseline_hard.xlsx
│   ├── selection_Baseline_soft.xlsx
│   ├── selection_DamageFocused_hard.xlsx
│   ├── selection_DamageFocused_soft.xlsx
│   ├── selection_InfrastructureFocused_hard.xlsx
│   ├── selection_InfrastructureFocused_soft.xlsx
│   ├── selection_sensitivity.xlsx
│   ├── coverage_per_mahalle.xlsx
│   └── kpi_summary.xlsx
├── maps/   (selection_map_CA8{...}.png, fcm_profile.png)
├── comparison/
│   ├── CA8_vs_baseline.xlsx
│   └── comparison_report.md
├── final/
│   ├── Sultanbeyli_Final_Results_CA8{...}.xlsx
│   └── reporting.md
└── scripts/
    ├── 01_fcm.py
    ├── 02_ip.py
    ├── 03_sensitivity.py
    ├── 04_compare.py
    ├── 05_final_xlsx.py
    ├── 06_map.py
    └── 99_run_all.py
```

---

## Sonuclarin Karsilastirilmasi (Toplu)

`cozum_alternatifi_8_comparison/` klasoru:
- 3 CA + orijinal = 4 senaryo
- Her bir icin: 8 secili site, Z, mu_toplam, R*C toplami, rho(R, coverage)
- Site overlap matrisi
- Karar: FCM varyasyonlari secimi ne kadar etkiliyor?

---

## Onay

- 3 varyant (CA8a/b/c) → 3 ayri klasorde uygulanacak
- Her CA kendi 99_run_all ile tam calistirilabilir
- Her CA icin ayri GitHub commit
- Toplu karsilastirma + son commit

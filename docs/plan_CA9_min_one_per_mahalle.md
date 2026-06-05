# CA9 - Her Mahallede En Az 1 Konteyner (SPATIAL Constraint)

## Kullanici istegi (m0787, m0789)
"her mahallede en az 1 konteyner olacak şekilde bir kısıt ile 9. senaryoyu çalışalım. düz olarak, yol kapanması ile, 8a gibi..."

**Yorum:** "En az 1 konteyner" SPATIAL — secili konteyner o mahallenin sinirlari icinde olmali. `adaylar.xlsx` ve `mevcut_12.xlsx`'teki `Mahalle` kolonu kullanilir.

## Spec
- **3 varyant:**
  - CA9a: duz IP + spatial constraint
  - CA9b: + yol kapanma (P_access)
  - CA9c: + CA8a truncation (mu<0.20 → 0)
- **2 mod:** 12+8 (MEV) ve 20 full (NMEV)
- **n_sites = 20** her mod
- **Constraint:** 15 konutlu mahalle (orman haric) icin >= 1 site o mahallede olmali
- **Aktif kritik kisit:** kritik 5 mahalle icin mu >= 0.50 korunur

## IP Formulasyonu
```
max Z = sum_i R_i * [mu_mev(i) + sum_j mu(i,j) * x_j]
s.t.
  for each m in 15 mahalle: sum_{j: mahalle(j)=m} x_j >= 1   (SPATIAL)
  sum_j x_j = 20
  for each i in critical: sum_j mu(i,j) * x_j + mu_mev(i) >= 0.50
  x_j in {0, 1}
```

## Feasibility
- 15 mahalle × min 1 site = min 15 site gerekli
- n_sites = 20 → 5 ek serbestlik Z maksimizasyonu icin
- 12 mevcut mahallesinden kac tanesi 15'i kapsar? → muhtemelen ~10, geri kalan 5-6 yeni ile doldurulur

## Sensitivity
- 3 AHP × 2 mod × hard/soft = 12 senaryo her CA icin
- 3 CA × 12 = 36 toplam IP

## Akademik referanslar
- Marsh & Schilling 1994: equity measurements in facility location
- Erkut 1993: equity in service delivery
- Current et al. 1997: equity obj.

## Klasor yapisi
```
cozum_alternatifi_9a_min_one_per_mahalle/
cozum_alternatifi_9b_min_one_yk/
cozum_alternatifi_9c_min_one_truncation/
cozum_alternatifi_9_comparison/  (toplu)
docs/plan_CA9_min_one_per_mahalle.md (bu dosya)
```

Her CA:
```
data/    (orijinal kopyalar + spatial assignment)
results/ (ip 12 senaryo + coverage_per_mahalle + sensitivity)
maps/    (secim haritasi + spatial dagilim)
comparison/  (CA9 vs baseline)
final/   (18-sayfa xlsx + reporting.md)
scripts/ (01-04 + 99_run_all)
```

## Commit sirasi (5 commit)
1. docs/plan_CA9
2. CA9a
3. CA9b
4. CA9c
5. toplu karsilastirma (cozum_alternatifi_9_comparison)

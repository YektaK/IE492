# CA9b - Final Reporting

## CA Tanimi
CA9b: Plain IP + spatial constraint (her mahallede min 1 konteyner) + P_access (yol kapanma)

## IP Formulasyonu
```
max Z = sum_i R_i * [mu_mev(i) + sum_j mu(i,j)*x_j]
s.t.
  for each m in 15 konutlu mahalle: sum_{j: mah(j)=m} x_j >= 1
  sum x = 20 (MEV: 12 mevcut + 8 yeni, NMEV: 20 yeni)
  for critical i: sum mu(i,j)*x_j + mu_mev(i) >= 0.50
  x_j in {0, 1}
```

## 12 Senaryo (3 AHP x 2 mod x hard/soft)
Hepsi Optimal.

## Bulgular
Z dusuk gorunuyor (mevcut 935.62'den 200-450 araligina) cunku spatial constraint solver'i yuksek-mu sitelerden uzaklastirdi. R×C ise dengeli.
5 eksik mahalle (ABDURRAHMANGAZİ, AHMET YESEVİ, FATIH, HAMIDIYE, MECIDIYE) garanti kapsandi.

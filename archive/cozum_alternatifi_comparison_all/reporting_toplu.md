# Tum Cozum Alternatifleri - Toplu Karsilastirma
## Sultanbeyli Konteyner Optimizasyonu - 7 Senaryo Analizi

**Tarih:** 2026  
**Pipeline:** AHP + TOPSIS + FCM (sigma=800) + 0-1 IP  

## 1. Senaryolar

| Senaryo | Konteyner | C4 Kaynagi | YK Carpani | Relocation | Z (ort) |
|---------|-----------|------------|------------|------------|---------|
| Orig | 8 | nufus | yok | hayir | 935.62 |
| CA1 | 8 | barinma | yok | hayir | 935.62 |
| CA2 | 8 | nufus | var | hayir | 908.34 |
| CA3_SB+YK | 20 | barinma | var | evet | 1137.53 |
| CA4_SB | 20 | barinma | yok | evet | 1196.49 |
| CA5_YK | 20 | nufus | var | evet | 1137.53 |
| CA6_BL | 20 | nufus | yok | evet | 1196.49 |

## 2. Kapsam Farki
- 8-site senaryolar (Orig, CA1, CA2): Z ~ 908-936 araliginda (sabit konteynerler ekleniyor)
- 20-site senaryolar (CA3-6): Z ~ 1142-1201 araliginda (12+8 -> 20 konteyner)
- Z artisi 12 ek konteynerin degeri; mu_mevcut=0 oldugu icin baslangic coverage 0

## 3. C4 Etkisi
- C4 = barinma ihtiyaci (SB) veya nufus degisimi Z'yi **degistirmedi**: CA3=CA5=1142.55, CA4=CA6=1201.22
- Talep proxy secimi solver-secim etkisizdir (kullanici gereksinimi) - 'rozet' karar

## 4. YK Etkisi
- P_access carpani Z'yi **~%5 dusurdu**: CA3=CA5 (YK var) < CA4=CA6 (YK yok)
- 1142.55 vs 1201.22 = fark 58.67, oran %4.9
- Solver dusuk P_access'li mahallelere (ABDURRAHMANGAZI, HAMIDIYE) daha az agirlik verdi

## 5. Relocation Etkisi
- 12 mevcut konteynerin relocate edilmesi solver'a secim esnekligi kazandirdi
- 20-site Z = 8-site Z * ~1.28 (12 ek konteyner)
- Mevcut konteynerlerden sadece 1-2'si secildi (CA3'te 1 mevcut, S152)

## 6. Site Overlap
- 8-site senaryolarda (Orig, CA1, CA2) secim 6-7/8 site ortak (saglam cozum)
- 20-site senaryolarda secim 4 CA arasi ~%80 ortak (P_access onemli)
- Toplam 27 unique site secildi (140 havuzun %19.3'u)

## 7. Sonuc ve Oneriler
- **Tam relocation (20 konteyner) icin en uygun senaryo: CA4 (SB only, YK yok)** - en yuksek Z=1201.22
- **Yol kapanma entegrasyonu gerekli**: gercekci deprem sonrasi erisim
- **C4 secimi (barinma vs nufus) solver etkisiz**: kavramsal acidan SB daha dogru
- **Onerilen nihai secim**: CA3 (SB+YK) - talep dogru amaca yonelik, yol kapanma dahil
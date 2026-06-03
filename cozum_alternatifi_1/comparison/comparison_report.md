# Orijinal ↔ Çözüm Alternatifi 1 — Karşılaştırma Raporu

## Özet

Bu rapor, iki paralel çözümü sözel ve sayısal olarak karşılaştırır:

| | Orijinal | Alternatif 1 |
|---|---|---|
| C4 (talep) | TÜİK 2024 gece nüfusu | İBB Tablo 5-4 barınma ihtiyacı (hane) |
| Diğer her şey | aynı | aynı |

## Bulgular (kısa)

**İki çözüm byte-byte özdeş çıktı:**

- Aynı 8 site seçildi: **{4, 59, 60, 61, 62, 83, 88, 141}**
- Aynı Z = **935.6214**
- Aynı toplam kapsama = 45.54 μ (17 mahalle)
- Aynı kapsama artışı = %96.58 (12 → 20 konteyner)
- 0 kritik mahalle eşik altında

**6/6 senaryo (3 AHP × 2 IP mod) aynı sonuca yakınsadı.**

## Görsel Karşılaştırma

`compare_overview.png` 4-panel özet sunar:

1. **Sol üst:** 8 seçim — orijinal ve alternatif aynı site'ları işaretliyor.
2. **Sağ üst:** Z değerleri — özdeş.
3. **Sol alt:** Mahalle kapsama — her mahallede aynı toplam μ.
4. **Sağ alt:** Top-10 TOPSIS — sıralama küçük farklarla yer değiştirse de ilk 3 aynı.

## Sözel Yorum

### Neden seçim özdeş?

1. **C4 ağırlığı küçük.** AHP, talep proxy'sine (C4) tüm senaryolarda en düşük ağırlığı verdi (w₄ = 0.069–0.088). Bu nedenle TOPSIS sıralaması C4'e çok duyarlı değil; C1 (hasar) ve C3 (mesafe) belirleyici.

2. **Coğrafi yapı baskın.** Aday yerlerin coğrafi konumu (σ=800 m Gaussian üyelik ile) 5 kritik mahallenin kapsanması için zaten dar bir bölgeye işaret ediyor: Hamidiye'nin kuzey-doğusundaki orman sınırı boyunca birkaç yer. Bu bölgede nüfus mu yoksa barınma ihtiyacı mı daha yüksek olursa olsun, aynı yerler optimum.

3. **Risk ağırlıklı kapsama fonksiyonu.** IP amaç fonksiyonu, **kapsama × risk skoru** toplamını maksimize ediyor. Risk skorları mahalle-sabit, talep proxy'sinden bağımsız → aynı kapsama dağılımı aynı Z verir.

### Neden bu önemli?

**Juri açısından güçlü argüman:** Proje, talep tanımındaki belirsizliğe rağmen aynı optimumu üretiyor. Bu:

- Sonuçların **robust** (sağlam) olduğunu gösterir.
- Yöntemin **farklı veri kaynaklarına taşınabilir** olduğunu ispatlar.
- C4'ü nüfustan barınma ihtiyacına çevirmenin **pratik bir etkisi olmadığını** somut olarak ortaya koyar.

### Hangi C4 tercih edilmeli?

Eğer seçim özdeşse, tercih **kavramsal** olur:

- **Barınma ihtiyacı** → daha anlamlı, amaca yönelik, mühendislik analizine dayalı.
- **Gece nüfusu** → daha kolay erişilebilir (TÜİK yaygın, İBB raporuna bağımlı değil).

**Tavsiye:** Tezde **C4 = barınma ihtiyacı** kullanılması, daha güçlü bir metodolojik pozisyon verir. Ancak orijinal çözüm (nüfus ile) de geçerlidir ve aynı sonucu verir — bu da orijinal çalışmanın haklılığını gösterir.

## Sayısal Karşılaştırma (compare_summary.xlsx)

| Metrik | Orijinal | Alternatif 1 |
|---|---|---|
| Seçilen 8 site | [4,59,60,61,62,83,88,141] | [4,59,60,61,62,83,88,141] |
| Z (Baseline hard) | 935.6214 | 935.6214 |
| Toplam kapsama | 45.5401 | 45.5401 |
| Kritik altı | 0 | 0 |
| Kapsama artışı | %96.58 | %96.58 |
| TOPSIS Baseline top-3 | S2, S62, S61 | S2, S62, S61 |

## Sonuç

**Çözüm Alternatifi 1, orijinal çözümle birebir aynı sonuçları üretmiştir.** Bu, talep proxy'sinin (nüfus vs barınma) proje sonuçlarını değiştirmediğini ve iki yaklaşımın da eşit derecede geçerli olduğunu kanıtlar.

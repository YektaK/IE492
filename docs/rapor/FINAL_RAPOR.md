# Sultanbeyli Konteyner Optimizasyonu — Final Sentez Raporu

**Tarih:** 2026-06-07  
**Kapsam:** IE492 Bitirme Projesi  
**Proje:** Çok Kriterli Afet Müdahale Konteyner Konumlandırma Modeli

---

## 1. Yönetici Özeti

Bu çalışmada Sultanbeyli ilçesindeki afet müdahale konteynerleri için çok kriterli, çok senaryolu bir yer seçim modeli geliştirilmiştir. Model, dört MCDM yöntemi (TOPSIS, PROMETHEE II, VIKOR, ELECTRE), üç AHP senaryosu (Baseline, Hasar-Odaklı, Altyapı-Odaklı) ve Adaptif Gaussian Bulanık Kapsama fonksiyonu üzerinden 0-1 Karma Tamsayılı Programlama (MILP) ile çözülmüştür.

**Toplam Koşum Sayısı:** 1  
**En Yüksek Z_total:** 33.4771  
**En Yüksek RxC:** 31.7584  
**Ortalama Min Kapsama:** 0.9952

## 2. Problem Tanımı

Sultanbeyli ilçesinde artan nüfus yoğunluğu ve deprem riski nedeniyle, mevcut 12 afet konteynerinin kapsama alanı yetersiz kalmaktadır. Bu çalışma, sınırlı bütçe altında (K=8 ekleme veya K=20 baştan kurulum) yeni konteynerlerin optimal yerleşimini, mahallelere adil erişim (spatial equity) garantisiyle çözmektedir.

## 3. Matematiksel Model

### 3.1 Amaç Fonksiyonu

$$\max Z = \sum_{i\in I} R_i \cdot C_i + \beta \sum_{j\in J} q_j X_j$$

### 3.2 Kısıtlar

- $\sum_j X_j = K_{Total} - |\text{Kept}|$ (Bütçe)
- $\sum_{j \in N_i} X_j + M_i \ge 1 \quad \forall i$ (Min 1 Konteyner / Mahalle)
- $C_i \ge 0.50 \cdot R_{norm,i} \quad \forall i$ (Riske Orantılı Kapsama)
- $X_{f} = 1 \quad \forall f \in \text{Fixed}$ (Zorunlu Adaylar)
- Oransal Ölçekleme: $R_{norm,i} = R_i / R_{max}$ (0 yutan eleman engeli)

## 4. Deney Senaryoları

| # | K_Total | Hedef | β | Senaryo | Korunan | Run_ID |
|---|---------|-------|---|---------|---------|--------|
| 1 | 20 | risk | 0.3 | Ekleme | 12 | Run_20260607_174132_K20_Ekleme_risk_b30... |

## 5. Sonuçlar

### 5.1 Her Koşumun En İyi MCDM Sonucu

| run_id                                  | mcdm      | senaryo               | weight_type   | scenario_tag   |   Z_total |     RxC |   min_mahalle_cov |   avg_mahalle_cov |
|:----------------------------------------|:----------|:----------------------|:--------------|:---------------|----------:|--------:|------------------:|------------------:|
| Run_20260607_174132_K20_Ekleme_risk_b30 | PROMETHEE | InfrastructureFocused | risk          | Ekleme         |   33.4771 | 31.7016 |            0.9952 |             4.155 |

### 5.2 Veri Korelasyonu Bulguları

> **Önemli Bulgu:** Risk Skoru ile Barınma İhtiyacı arasında %94.1 Pearson korelasyonu tespit edilmiştir. Bu nedenle bu iki değişken **alternatif senaryo** olarak kullanılmış, aynı modelde birlikte ağırlıklandırılmamıştır. Ana karşılaştırma ekseni: **Risk vs Nüfus**.

## 6. Akademik Katkılar

1. **Oransal Ölçekleme:** 0 yutan eleman problemini ortadan kaldıran $W_i / W_{max}$ normalizasyonu.
2. **Adaptif Gaussian σ:** Nüfusa ters orantılı (400m-1200m) kapsama yarıçapı.
3. **Çift Kademeli Kapsama:** 300m içi tam kapsama ($\mu=1.0$) + Gaussian azalma.
4. **4 MCDM Yöntemi:** TOPSIS, PROMETHEE II, VIKOR, ELECTRE paralel entegrasyonu.
5. **Esnek Kısıtlar:** Korunan mevcut + Zorunlu aday seçimi dinamik olarak modele girer.
6. **Dashboard:** Streamlit üzerinden Job Queue + Multi-Compare görsel analiz.

## 7. Sınırlılıklar

- Haversine (kuş uçuşu) mesafe kullanılmıştır; yol ağı mesafesi entegre edilmemiştir.
- `p_access_road` verisi sentetiktir (seed=42).
- Her lokasyona en fazla 1 konteyner yerleştirilebilmektedir.
- Risk değerleri deterministik alınmıştır; belirsizlik modellenmemiştir.

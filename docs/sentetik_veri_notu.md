# Sentetik Veri Belgelendirmesi

**Tarih:** 7 Haziran 2026
**Bağlam:** IE492 - Sultanbeyli Afet Müdahale Konteyner Optimizasyonu

Proje kapsamında kullanılan verilerin büyük çoğunluğu açık kaynaklardan (AFİS, AYDES, İBB KRDAE Raporları, TÜİK) derlenmiş gerçek verilere dayanmaktadır. Ancak erişim analizi ve yol durumu gibi dinamik değişkenler için yeterli granülerlikte veri bulunamadığından, modelleme amacıyla **sentetik veriler** üretilmiştir.

Akademik dürüstlük ve tekrarlanabilirlik gereği sentetik verilerin detayları aşağıda listelenmiştir.

## Sentetik Değişkenler

### 1. `p_access_road` (Parsel Bazlı Yol Erişimi)
- **Kapsam:** Her bir aday parselin (n=140) ana yollara ve acil durum arterlerine erişilebilirlik düzeyi.
- **Üretim Yöntemi:** Mahalle bazlı temel altyapı puanlarına (0.70 civarı) `numpy.random.normal(0, 0.05)` kullanılarak Gaussian gürültü eklenmiş ve `[0.30, 0.99]` aralığına kırpılmıştır (`np.clip`).
- **Rastgelelik Tohumu (Seed):** `np.random.seed(42)` (Kod: `src/01_data_prep.py`)
- **Nedeni:** Parsel bazlı yol ağının fiziksel özelliklerine (sokak genişliği, eğim, zemin türü vb.) dair CBS verisi eksikliği.

### 2. `p_road_open` (Mahalle Bazlı Yol Açıklığı / Kapanma Olasılığı)
- **Kapsam:** Deprem anında bir mahalledeki yolların enkaz veya altyapı çökmesi nedeniyle kapanmama (açık kalma) olasılığı.
- **Üretim Yöntemi:** Bina hasar oranlarıyla ters orantılı olarak üretilmiş yarı-sentetik (semi-synthetic) bir değişkendir.
- **Kullanım:** Q_i vektörü olarak kapsama fonksiyonunda (Fuzzy Coverage) etkili mesafeyi daraltmak amacıyla kullanılmaktadır (`mu_ij_eff = mu_ij * Q_i`).

## Modeller Üzerindeki Etkisi ve Duyarlılık Testi İhtiyacı

Bu değişkenler, özellikle yol kapanması senaryosunda (Senaryo B) ve NMEV tam relokasyon optimizasyonunda sonuçları doğrudan etkileyebilir.

Akademik değerlendirme standartlarını karşılamak için, Faz 5 (İleri Analiz) kapsamında `src/19_sensitivity_synthetic.py` scripti ile bu sentetik değişkenlerin **±%20 oranında değiştirildiği bir duyarlılık testi (sensitivity analysis)** yapılacaktır. Bu testin amacı, seçilen konum setinin sentetik gürültüye ne kadar dirençli (robust) olduğunu kanıtlamaktır.

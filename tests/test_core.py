import sys
from pathlib import Path
import pytest
import pandas as pd

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from config import norm_mahalle, DATA_DIR, RESULTS_DIR

def test_norm_mahalle():
    """Türkçe karakter normalizasyonu testleri."""
    assert norm_mahalle("Aydos") == "AYDOS"
    assert norm_mahalle("Akşemsettin") == "AKSEMSETTIN"
    assert norm_mahalle("çöpçüöğüş") == "COPCUOGUS"
    assert norm_mahalle("  Mimar Sinan  ") == "MIMAR SINAN"
    assert norm_mahalle(None) == ""
    assert norm_mahalle(123) == ""

def test_paths_exist():
    """Veri ve sonuç klasörlerinin varlığı."""
    assert DATA_DIR.exists()
    assert RESULTS_DIR.exists()

def test_input_files():
    """Girdi veri dosyalarının doğrulanması."""
    adaylar_file = DATA_DIR / "adaylar_140.xlsx"
    mevcut_file = DATA_DIR / "mevcut_12.xlsx"
    
    assert adaylar_file.exists()
    assert mevcut_file.exists()
    
    df_aday = pd.read_excel(adaylar_file)
    df_mev = pd.read_excel(mevcut_file)
    
    assert "S_No" in df_aday.columns
    assert "Enlem" in df_aday.columns
    assert "Boylam" in df_aday.columns
    
    assert "mahalle" in df_mev.columns or "Mahalle" in df_mev.columns

def test_truncation_no_nameerror():
    """11_lexicographic ve 14_single_stage modellerinde TRUNCATE > 0 hatasız çalışmalı."""
    import importlib
    
    lexicographic = importlib.import_module("11_lexicographic")
    single_stage = importlib.import_module("14_single_stage")
    
    try:
        lexicographic.main(K_TOTAL=13, TRUNCATE=0.15)
    except Exception as e:
        pytest.fail(f"11_lexicographic TRUNCATE > 0 iken hata verdi: {e}")
        
    try:
        single_stage.main(K_TOTAL=13, TRUNCATE=0.15)
    except Exception as e:
        pytest.fail(f"14_single_stage TRUNCATE > 0 iken hata verdi: {e}")

def test_lorenz_and_gini():
    """Lorenz eğrisi çizimi ve Gini katsayısı hesabı doğruluğu."""
    from visualization import plot_lorenz_curve
    import numpy as np
    import tempfile
    
    # 1. Tam eşit dağılım: [1, 1, 1, 1] -> Gini = 0.0
    equal_vals = np.array([1.0, 1.0, 1.0, 1.0])
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        gini_equal = plot_lorenz_curve(equal_vals, tmp_path)
        assert abs(gini_equal) < 1e-6, f"Eşit dağılım Gini sıfır olmalı, alınan: {gini_equal}"
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    # 2. Eşitsiz dağılım: [0, 0, 0, 10] -> Gini = (n-1)/n = 3/4 = 0.75
    unequal_vals = np.array([0.0, 0.0, 0.0, 10.0])
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        gini_unequal = plot_lorenz_curve(unequal_vals, tmp_path)
        assert abs(gini_unequal - 0.75) < 1e-2, f"Eşitsiz dağılım Gini 0.75 olmalı, alınan: {gini_unequal}"
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_haversine():
    """Haversine mesafe fonksiyonunun dogruluk kontrolu."""
    from road_network import haversine_m
    # 40.97, 29.25 ile 40.98, 29.26 arasi mesafe ~1393.26 metre olmali
    val = haversine_m(40.97, 29.25, 40.98, 29.26)
    assert abs(val - 1393.26) < 1.0
    
    # Kendi kendine olan mesafe sifir olmali
    val_self = haversine_m(41.0082, 28.9784, 41.0082, 28.9784)
    assert abs(val_self) < 1e-6


def test_fuzzy_coverage_symmetry():
    """Bulanik kapsama matrislerinin (mu) boyut ve deger sinirlarinin kontrolu."""
    mu_aday_file = RESULTS_DIR / "fuzzy_coverage" / "mu_aday_140x17_sAdaptive.xlsx"
    mu_mevcut_file = RESULTS_DIR / "fuzzy_coverage" / "mu_mevcut_12x17_sAdaptive.xlsx"
    
    assert mu_aday_file.exists(), f"{mu_aday_file} dosyasi bulunamadi!"
    assert mu_mevcut_file.exists(), f"{mu_mevcut_file} dosyasi bulunamadi!"
    
    df_mu_aday = pd.read_excel(mu_aday_file, index_col=0)
    df_mu_mevcut = pd.read_excel(mu_mevcut_file, index_col=0)
    
    assert df_mu_aday.shape == (140, 15), f"Aday kapsama matrisi boyutu (140, 15) olmali, alinan: {df_mu_aday.shape}"
    assert df_mu_mevcut.shape == (12, 15), f"Mevcut kapsama matrisi boyutu (12, 15) olmali, alinan: {df_mu_mevcut.shape}"
    
    # Degerlerin [0.0, 1.0] araliginda olmasi
    assert df_mu_aday.min().min() >= 0.0
    assert df_mu_aday.max().max() <= 1.0
    assert df_mu_mevcut.min().min() >= 0.0
    assert df_mu_mevcut.max().max() <= 1.0


def test_mcdm_scores_range():
    """TOPSIS Closeness Coefficient (CC) degerlerinin [0, 1] araligi kontrolu."""
    topsis_file = RESULTS_DIR / "mcdm" / "topsis_cc.xlsx"
    assert topsis_file.exists(), f"{topsis_file} bulunamadi!"
    
    df_topsis = pd.read_excel(topsis_file)
    cc_cols = [c for c in df_topsis.columns if c.startswith("CC_")]
    assert len(cc_cols) > 0, "TOPSIS dosyasinda CC_ ile baslayan kolon bulunamadi!"
    
    for col in cc_cols:
        vals = df_topsis[col]
        assert vals.min() >= -1e-9, f"{col} kolonunda negatif deger var: {vals.min()}"
        assert vals.max() <= 1.0 + 1e-9, f"{col} kolonunda 1.0'den buyuk deger var: {vals.max()}"


def test_ip_small_instance():
    """Kucuk bir IP probleminin solver_core yardimiyla dogru sekilde kurulup cozulmesi."""
    import solver_core
    import pulp
    import numpy as np
    
    n_aday = 5
    n_mah = 3
    S_Nos = [101, 102, 103, 104, 105]
    mahalleler = ["MAH1", "MAH2", "MAH3"]
    
    MU_matrix = np.array([
        [0.8, 0.1, 0.0],
        [0.0, 0.9, 0.1],
        [0.1, 0.0, 0.85],
        [0.7, 0.6, 0.0],
        [0.0, 0.2, 0.9]
    ])
    
    P_j = np.array([1.0, 0.9, 1.0, 0.85, 0.95])
    Q_i = np.array([0.95, 0.90, 0.85])
    mu_mev_sum = np.array([0.1, 0.05, 0.0])
    
    prob = pulp.LpProblem("Test_Small_IP", pulp.LpMaximize)
    
    X, coverage = solver_core.build_base_variables_and_coverage(
        n_aday, n_mah, MU_matrix, P_j, Q_i, mu_mev_sum
    )
    
    # K_TOTAL = 3, FIXED_ADAY = [0], aday_mah_idx = [0, 1, 2, 0, 1]
    solver_core.add_base_constraints(
        prob, X, coverage,
        K_TOTAL=3,
        KEPT_MEVCUT=[],
        FIXED_ADAY=[0],
        aday_mah_idx=[0, 1, 2, 0, 1],
        mevcut_counts=[0, 0, 0],
        R_i=[0.1, 0.1, 0.1],
        n_mah=n_mah,
        min_one=True,
        risk_prop=True
    )
    
    prob += pulp.lpSum(coverage)
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    assert prob.status == pulp.LpStatusOptimal, f"Problem optimal cozulemedi: {pulp.LpStatus[prob.status]}"
    x_vals = [x.varValue for x in X]
    assert sum(x_vals) == 3, f"Secilen aday sayisi 3 olmali, alinan: {sum(x_vals)}"
    assert X[0].varValue == 1.0, "Zorunlu aday secilmemis!"


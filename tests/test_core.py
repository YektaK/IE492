import sys
import json
from pathlib import Path
import subprocess
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


def test_ip_loads_four_mcdm_methods_when_outputs_exist():
    """05_ip.py TOPSIS/PROMETHEE yaninda VIKOR ve ELECTRE skorlarini da yuklemeli."""
    import importlib

    ip = importlib.import_module("05_ip")
    mcdm_scores = ip.load_mcdm_scores()

    assert set(mcdm_scores) >= {"TOPSIS", "PROMETHEE", "VIKOR", "ELECTRE"}
    for method in ["TOPSIS", "PROMETHEE", "VIKOR", "ELECTRE"]:
        assert set(mcdm_scores[method]) == {"Baseline", "DamageFocused", "InfrastructureFocused"}
        for values in mcdm_scores[method].values():
            assert len(values) == 140
            assert values.min() >= -1e-9
            assert values.max() <= 1.0 + 1e-9


def test_app_runner_builds_variant_paths_for_all_mcdm_methods():
    """UI/Excel rapor yolu uretimi VIKOR ve ELECTRE dahil tum summary varyantlarini desteklemeli."""
    from app_runner import ip_file_suffix, variant_output_paths

    root = Path(__file__).resolve().parent.parent
    job = {
        "k_total": 20,
        "weight_type": "risk",
        "beta": 0.30,
        "sigma": "Adaptive",
        "kept_mevcut": list(range(12)),
        "fixed_aday": [],
    }

    suffix = ip_file_suffix(job)
    summary_rows = [
        ("v7_SA", "VIKOR", "Baseline"),
        ("v10_SA", "ELECTRE", "Baseline"),
    ]

    for vname, mcdm, scen in summary_rows:
        paths = variant_output_paths(job, root / "results" / "models", vname, mcdm, scen)
        assert paths["ip"].name == f"ip_{vname}_{mcdm}_{scen}_{suffix}.xlsx"
        assert paths["coverage"].name == f"coverage_{vname}_{mcdm}_{scen}_{suffix}.xlsx"


def test_lscp_imports_current_fuzzy_coverage_paths():
    """LSCP modulu legacy fcm_paths yerine guncel fuzzy_coverage_paths kullanmali."""
    import importlib

    lscp = importlib.import_module("08_lscp")
    mev_mu, aday_mu = lscp.load_mu("Adaptive")

    assert aday_mu.shape[0] == 140
    assert len(aday_mu.columns[1:]) == 15
    assert mev_mu.shape[0] == 12
    assert len(mev_mu.columns[1:]) == 15


def test_run_all_uses_current_fuzzy_coverage_generator():
    """Deney kosucusu src/04_fuzzy_coverage.py ve results/fuzzy_coverage uzerinden calismali."""
    import run_all_scenarios

    assert run_all_scenarios.coverage_files_exist("Adaptive")
    cmd = run_all_scenarios.coverage_generation_command("Adaptive")

    assert Path(cmd[1]).name == "04_fuzzy_coverage.py"
    assert cmd[-2:] == ["--sigma", "Adaptive"]


def test_configured_sigmas_use_current_coverage_paths():
    """experiments_config sigma degerleri current fuzzy_coverage path/generator ile uyumlu olmali."""
    import run_all_scenarios
    from scenario_utils import fuzzy_coverage_paths

    root = Path(__file__).resolve().parent.parent
    config = json.loads((root / "experiments_config.json").read_text(encoding="utf-8"))
    sigmas = {exp.get("sigma", "800") for exp in config["experiments"]}

    assert sigmas
    for sigma in sigmas:
        paths = fuzzy_coverage_paths(sigma)
        assert paths["mu_aday"].parent.name == "fuzzy_coverage"
        assert paths["mu_mevcut"].parent.name == "fuzzy_coverage"
        cmd = run_all_scenarios.coverage_generation_command(sigma)
        assert Path(cmd[1]).name == "04_fuzzy_coverage.py"
        assert cmd[-1] == sigma


def test_run_all_compromise_command_uses_experiment_specific_args():
    """15_compromise.py dogru Pareto dosyasini bulmak icin deney kimligini almali."""
    import run_all_scenarios

    cfg = {
        "name": "Baseline_SA",
        "scenario": "A",
        "sigma": "800",
        "beta": 0.30,
        "K": 8,
        "truncate": 0,
        "no_mevcut": False,
    }

    cmd = run_all_scenarios.build_args(cfg, "15_compromise")

    assert Path(cmd[1]).name == "15_compromise.py"
    assert cmd[cmd.index("--scenario") + 1] == "A"
    assert cmd[cmd.index("--sigma") + 1] == "800"
    assert cmd[cmd.index("--beta") + 1] == "0.3"
    assert "--K" in cmd
    assert cmd[cmd.index("--K") + 1] == "20"


def test_run_all_normalizes_k_semantics_by_script_contract():
    """Config K=8 yeni konteyner anlamina gelir; scriptlere kendi kontratlarina gore aktarilmali."""
    import run_all_scenarios

    cfg = {
        "name": "Baseline_SA",
        "scenario": "A",
        "sigma": "800",
        "beta": 0.30,
        "K": 8,
        "truncate": 0,
        "no_mevcut": False,
    }

    ip_cmd = run_all_scenarios.build_args(cfg, "05_ip")
    lscp_cmd = run_all_scenarios.build_args(cfg, "08_lscp")
    lex_cmd = run_all_scenarios.build_args(cfg, "11_lexicographic")
    eps_cmd = run_all_scenarios.build_args(cfg, "13_eps_constraint")
    single_cmd = run_all_scenarios.build_args(cfg, "14_single_stage")
    compromise_cmd = run_all_scenarios.build_args(cfg, "15_compromise")

    assert ip_cmd[ip_cmd.index("--K") + 1] == "20"
    assert ip_cmd[ip_cmd.index("--truncate") + 1] == "0"
    assert "--K" not in lscp_cmd
    assert lex_cmd[lex_cmd.index("--K") + 1] == "8"
    assert lex_cmd[lex_cmd.index("--truncate") + 1] == "0"
    assert eps_cmd[eps_cmd.index("--K") + 1] == "8"
    assert single_cmd[single_cmd.index("--K") + 1] == "8"
    assert single_cmd[single_cmd.index("--truncate") + 1] == "0"
    assert compromise_cmd[compromise_cmd.index("--K") + 1] == "20"


def test_run_all_does_not_pass_unsupported_truncate_to_eps_constraint():
    """13_eps_constraint.py --truncate desteklemez; runner bunu gecirmemeli."""
    import run_all_scenarios

    cfg = {
        "name": "Future_Eps_Truncation",
        "scenario": "A",
        "sigma": "800",
        "beta": 0.30,
        "K": 8,
        "truncate": 0.20,
        "no_mevcut": False,
    }

    cmd = run_all_scenarios.build_args(cfg, "13_eps_constraint")

    assert "--truncate" not in cmd


def test_run_all_dry_run_lists_commands_without_execution():
    """--dry-run komutlari listeler ve cozum betiklerini calistirmaz."""
    script = Path(__file__).resolve().parent.parent / "src" / "run_all_scenarios.py"

    result = subprocess.run(
        [sys.executable, str(script), "--name", "Baseline_SA", "--dry-run"],
        cwd=Path(__file__).resolve().parent.parent,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "[DRY-RUN]" in result.stdout
    assert "05_ip.py" in result.stdout
    assert "--truncate 0" in result.stdout
    assert "15_compromise.py" in result.stdout
    assert "05_ip.py basladi" not in result.stdout


def test_run_all_no_matching_name_returns_error():
    """Yanlis --name filtresi sessiz 0/0 basari olarak gecmemeli."""
    script = Path(__file__).resolve().parent.parent / "src" / "run_all_scenarios.py"

    result = subprocess.run(
        [sys.executable, str(script), "--name", "__NO_SUCH_EXPERIMENT__"],
        cwd=Path(__file__).resolve().parent.parent,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "No experiments matched" in (result.stdout + result.stderr)


def test_compromise_missing_pareto_file_fails():
    """15_compromise eksik Pareto girdisini batch runner'a basari gibi gostermemeli."""
    script = Path(__file__).resolve().parent.parent / "src" / "15_compromise.py"

    result = subprocess.run(
        [sys.executable, str(script), "--K", "999999", "--weight", "risk"],
        cwd=Path(__file__).resolve().parent.parent,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Pareto" in (result.stdout + result.stderr)


def test_app_runner_builds_commands_by_solver_contract():
    """Streamlit runner komutlari her solver'in K ve arguman kontratina uymali."""
    from app_runner import build_solver_command

    root = Path(__file__).resolve().parent.parent
    job = {
        "k_total": 20,
        "weight_type": "risk",
        "beta": 0.30,
        "sigma": "Adaptive",
        "kept_mevcut": list(range(12)),
        "fixed_aday": [3, 4],
    }

    ip_info = {"script": "05_ip.py", "has_kept": True, "has_fixed": True, "has_beta": True, "has_sigma": True, "k_is_total": True, "weights": ["risk", "population", "shelter"]}
    lex_info = {"script": "11_lexicographic.py", "has_kept": False, "has_fixed": False, "has_beta": True, "has_sigma": True, "k_is_total": False, "weights": ["risk", "population"]}
    mclp_info = {"script": "16_mclp.py", "has_kept": False, "has_fixed": False, "has_beta": False, "has_sigma": False, "k_is_total": False, "weights": ["risk", "population", "shelter"]}

    ip_cmd = build_solver_command(job, ip_info, root, python_executable="python")
    lex_cmd = build_solver_command(job, lex_info, root, python_executable="python")
    mclp_cmd = build_solver_command(job, mclp_info, root, python_executable="python")

    assert ip_cmd[ip_cmd.index("--K") + 1] == "20"
    assert ip_cmd[ip_cmd.index("--kept") + 1] == ",".join(map(str, range(12)))
    assert ip_cmd[ip_cmd.index("--fixed") + 1] == "3,4"
    assert lex_cmd[lex_cmd.index("--K") + 1] == "8"
    assert "--kept" not in lex_cmd
    assert "--fixed" not in lex_cmd
    assert mclp_cmd[mclp_cmd.index("--K") + 1] == "8"
    assert "--beta" not in mclp_cmd
    assert "--sigma" not in mclp_cmd

    invalid_job = dict(job)
    invalid_job["weight_type"] = "shelter"
    with pytest.raises(ValueError, match="supports weight types"):
        build_solver_command(invalid_job, lex_info, root, python_executable="python")


def test_app_runner_finds_ip_and_method_outputs(tmp_path):
    """App metadata dosya bulma mantigi 05_ip ve alt klasor ciktilarini ayirt etmeli."""
    from app_runner import find_solver_outputs, ip_file_suffix, equity_file_suffix, pareto_file_suffix

    models_dir = tmp_path / "results" / "models"
    results_dir = tmp_path / "results"
    (results_dir / "lexicographic").mkdir(parents=True)
    (results_dir / "eps_constraint").mkdir(parents=True)
    models_dir.mkdir(parents=True)

    job = {
        "k_total": 20,
        "weight_type": "population",
        "beta": 0.30,
        "sigma": "Adaptive",
        "kept_mevcut": list(range(12)),
        "fixed_aday": [],
    }

    ip_suffix = ip_file_suffix(job)
    summary = models_dir / f"summary_all_{ip_suffix}.xlsx"
    ip_file = models_dir / f"ip_v1_TOPSIS_Baseline_AHP_{ip_suffix}.xlsx"
    summary.touch()
    ip_file.touch()

    ip_outputs = find_solver_outputs(job, "05_ip", models_dir, results_dir)

    assert ip_outputs["summary"] == summary
    assert ip_outputs["ip"] == ip_file
    assert ip_outputs["result"] == summary

    lex_file = results_dir / "lexicographic" / f"lexicographic_result_{equity_file_suffix(job)}.xlsx"
    lex_file.touch()

    lex_outputs = find_solver_outputs(job, "11_lex", models_dir, results_dir)

    assert lex_outputs["result"] == lex_file
    assert lex_outputs["summary"] is None
    assert lex_outputs["ip"] is None

    pareto_file = results_dir / "eps_constraint" / f"pareto_results_{pareto_file_suffix(job)}.xlsx"
    pareto_file.touch()

    eps_outputs = find_solver_outputs(job, "13_eps", models_dir, results_dir)

    assert eps_outputs["result"] == pareto_file


def test_epsilon_and_compromise_use_same_specific_suffix():
    """13_eps_constraint ve 15_compromise ayni senaryo-ozel Pareto anahtarini kullanmali."""
    import importlib

    eps = importlib.import_module("13_eps_constraint")
    comp = importlib.import_module("15_compromise")

    eps_suffix = eps.pareto_suffix("B", "800_300", 20, 0.30, "population", list(range(12)))
    comp_suffix = comp.pareto_suffix("B", "800_300", 20, 0.30, "population", False)

    assert eps_suffix == comp_suffix
    assert eps_suffix == "SB_sg800_300_b30_K20_population"


def test_fuzzy_coverage_cli_accepts_sigma_modes():
    """Kapsama ureticisi dokumante edilen sigma arayuzunu sunmali."""
    script = Path(__file__).resolve().parent.parent / "src" / "04_fuzzy_coverage.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=Path(__file__).resolve().parent.parent,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--sigma" in result.stdout
    assert "Adaptive" in result.stdout
    assert "[1/5]" not in result.stdout


def test_fuzzy_coverage_import_has_no_data_loading_side_effects():
    """Modul importu Excel okuma/progress logu calistirmamali."""
    script = "import sys; sys.path.insert(0, 'src'); import importlib; importlib.import_module('04_fuzzy_coverage')"

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parent.parent,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""


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


def test_excel_report_generation():
    """Excel raporunun olusturulmasi ve sayfa yapisinin dogrulanmasi."""
    from excel_report_generator import generate_excel_report
    import tempfile
    import os
    from config import MODELS_DIR
    
    # 1. Mevcut bir metadata dosyası bulalım
    meta_files = sorted(MODELS_DIR.glob("*_metadata.json"))
    if not meta_files:
        pytest.skip("Test icin kayitli metadata dosyasi bulunamadi.")
        
    meta_path = meta_files[0]
    
    # Gecici bir excel dosyasi tanimla
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        
    try:
        # Ornek bir varyant ile raporu uret
        generate_excel_report(
            meta_path,
            tmp_path,
            vname="v1",
            mcdm_sel="SA_TOPSIS",
            scen_sel="Baseline"
        )
        
        # Dosyanin olusturuldugunu ve bos olmadigini dogrula
        assert tmp_path.exists()
        assert tmp_path.stat().st_size > 0
        
        # Sayfalari oku ve kontrol et
        with pd.ExcelFile(tmp_path) as xls:
            sheets = xls.sheet_names
        
        # Sayfalarin varligini dogrula
        assert "Özet ve Parametreler" in sheets
        assert "Seçilen Parseller" in sheets
        assert "Mahalle Kapsama Analizi" in sheets
        assert "Tüm Varyant Karşılaştırması" in sheets
        
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)

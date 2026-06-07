import streamlit as st
import pandas as pd
import numpy as np
import folium
from pathlib import Path
import sys
import subprocess
import time
import json

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

st.set_page_config(page_title="Sultanbeyli Konteyner Optimizasyonu", layout="wide")

# Custom Premium CSS for styling and glassmorphism
st.markdown("""
<style>
/* Modern styling for streamlit metrics */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    backdrop-filter: blur(10px);
    padding: 16px;
    transition: all 0.3s ease;
}
div[data-testid="stMetric"]:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 107, 53, 0.4);
    transform: translateY(-2px);
}
/* Glassmorphism containers */
.glass-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}
/* Customize tabs header */
button[data-baseweb="tab"] {
    font-size: 16px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# Veri Yolları ve Konfigürasyon
from config import DATA_DIR, RESULTS_DIR, MODELS_DIR, MAPS_DIR, CHARTS_DIR, JOBS_FILE, norm_mahalle

# ==========================================
# VERİ YÜKLEMELERİ
# ==========================================
@st.cache_data
def load_data():
    adaylar = pd.read_excel(DATA_DIR / "adaylar_140.xlsx")
    mevcut = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
    return adaylar, mevcut

@st.cache_data
def load_profile_data():
    df_nuf = pd.read_excel(DATA_DIR / "mahalle_nufus.xlsx")
    df_risk = pd.read_excel(DATA_DIR / "mahalle_risk.xlsx")
    df_bar = pd.read_excel(DATA_DIR / "mahalle_barinma.xlsx")
    df_mevcut = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
    return df_nuf, df_risk, df_bar, df_mevcut

def load_jobs():
    if JOBS_FILE.exists():
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4, ensure_ascii=False)

def weight_label(w):
    return {"risk": "Deprem Riski (İBB)", "population": "Gece Nüfusu", "shelter": "Barınma İhtiyacı"}.get(w, w)

MODEL_OPTIONS = {
    "05_ip": {"label": "Ana IP Modeli (12 MCDM Varyantı)", "script": "05_ip.py", "has_kept": True, "has_fixed": True, "has_beta": True, "has_sigma": True, "k_is_total": True},
    "11_lex": {"label": "Lexicographic Max-Min (Adalet Odaklı)", "script": "11_lexicographic.py", "has_kept": False, "has_fixed": False, "has_beta": True, "has_sigma": True, "k_is_total": False},
    "13_eps": {"label": "ε-Constraint (Pareto Cephesi)", "script": "13_eps_constraint.py", "has_kept": False, "has_fixed": False, "has_beta": True, "has_sigma": True, "k_is_total": False},
    "14_single": {"label": "Single-Stage MILP (Entegre Equity)", "script": "14_single_stage.py", "has_kept": False, "has_fixed": False, "has_beta": True, "has_sigma": True, "k_is_total": False},
    "16_mclp": {"label": "MCLP Benchmark (Klasik Kapsama)", "script": "16_mclp.py", "has_kept": False, "has_fixed": False, "has_beta": False, "has_sigma": False, "k_is_total": False}
}

def run_single_job(job, progress_callback=None):
    """Tek bir işi çalıştır, metadata JSON üret, harita ve grafik üret."""
    model_key = job.get('model', '05_ip')
    model_info = MODEL_OPTIONS.get(model_key, MODEL_OPTIONS['05_ip'])
    script_path = str(PROJECT_ROOT / "src" / model_info['script'])
    
    cmd = [sys.executable, script_path]
    
    # K parametresi: eski modeller K'yı "yeni eklenecek sayı" olarak yorumlar
    if model_info['k_is_total']:
        cmd.extend(["--K", str(job['k_total'])])
    else:
        k_new = job['k_total'] - len(job['kept_mevcut']) if job['kept_mevcut'] else job['k_total']
        cmd.extend(["--K", str(k_new)])
    
    cmd.extend(["--weight", job['weight_type']])
    
    if model_info['has_beta']:
        cmd.extend(["--beta", str(job['beta'])])
    if model_info['has_sigma']:
        cmd.extend(["--sigma", job['sigma']])
    
    if not job['kept_mevcut']:
        cmd.append("--no-mevcut")
    elif model_info['has_kept']:
        cmd.extend(["--kept", ",".join(map(str, job['kept_mevcut']))])
        
    if job.get('fixed_aday') and model_info['has_fixed']:
        cmd.extend(["--fixed", ",".join(map(str, job['fixed_aday']))])
    
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    
    if res.returncode != 0:
        return {"success": False, "error": res.stderr, "stdout": res.stdout}
    
    # Dosya ismi şablonu (05_ip.py ile tutarlı)
    sg_str = "" if job['sigma'] == "800" else f"_sg{job['sigma']}"
    nm_str = "_nomez" if not job['kept_mevcut'] else ""
    wt_str = f"_{job['weight_type']}"
    file_suffix = f"SA{sg_str}_b{int(float(job['beta'])*100)}_K{job['k_total']}_t0.15{nm_str}{wt_str}"
    
    # En yeni summary dosyasını bul
    sum_pattern = f"summary_all_*{file_suffix}*"
    sum_files = sorted(MODELS_DIR.glob(sum_pattern), key=lambda x: x.stat().st_mtime)
    latest_summary = sum_files[-1] if sum_files else None
    
    # En yeni IP dosyasını bul (ilk MCDM varyantı yeterli, harita için)
    ip_pattern = f"ip_v1_*{file_suffix}*"
    ip_files = sorted(MODELS_DIR.glob(ip_pattern), key=lambda x: x.stat().st_mtime)
    latest_ip = ip_files[-1] if ip_files else None
    
    # Harita ve Grafik Üretimi
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    scenario_tag = "Ekleme" if job['kept_mevcut'] else "Bastan"
    model_tag = model_key.replace('_', '')
    prefix = f"Run_{timestamp}_{model_tag}_K{job['k_total']}_{scenario_tag}_{job['weight_type']}_b{int(float(job['beta'])*100)}"
    
    map_file = None
    chart_file = None
    
    if latest_ip:
        cov_name = latest_ip.name.replace("ip_v1_", "coverage_v1_")
        cov_path = MODELS_DIR / cov_name
        
        try:
            from visualization import plot_solution_map, plot_coverage_bar
            
            mevcut_full = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
            yeni_df = pd.read_excel(latest_ip)
            
            # Kept / Removed mantığı
            if job['kept_mevcut']:
                kept_df = mevcut_full.iloc[job['kept_mevcut']].copy()
                all_idx = set(range(len(mevcut_full)))
                removed_idx = all_idx - set(job['kept_mevcut'])
                removed_df = mevcut_full.iloc[list(removed_idx)].copy() if removed_idx else pd.DataFrame()
            else:
                kept_df = pd.DataFrame()
                removed_df = mevcut_full.copy()
            
            fixed_df = pd.DataFrame()  # Gelecekte genişletilebilir
            
            cov_df_run = None
            if cov_path.exists():
                cov_df_run = pd.read_excel(cov_path)
                
            map_out = MAPS_DIR / f"{prefix}_map.html"
            plot_solution_map(yeni_df, kept_df, removed_df, fixed_df, map_out,
                              title=f"K={job['k_total']} | {weight_label(job['weight_type'])} | {scenario_tag}",
                              cov_df=cov_df_run,
                              sigma=int(job['sigma']))
            map_file = f"{prefix}_map.html"
            
            # Grafik
            if cov_path.exists():
                cov_df = pd.read_excel(cov_path)
                
                if job['weight_type'] == "population":
                    w_df = pd.read_excel(DATA_DIR / "mahalle_nufus.xlsx")
                    val_col = "nufus_2024"
                elif job['weight_type'] == "shelter":
                    w_df = pd.read_excel(DATA_DIR / "mahalle_barinma.xlsx")
                    val_col = "hane_ihtiyaci"
                else:
                    w_df = pd.read_excel(DATA_DIR / "mahalle_risk.xlsx")
                    val_col = "risk_score"
                
                w_df["mahalle_norm"] = w_df["mahalle"].apply(norm_mahalle)
                cov_df["mahalle_norm"] = cov_df["mahalle"].apply(norm_mahalle)
                merged = pd.merge(cov_df, w_df, on="mahalle_norm", how="left", suffixes=("", "_w"))
                
                max_val = merged[val_col].max()
                target_vals = merged[val_col] / (max_val + 1e-9)
                
                chart_out = CHARTS_DIR / f"{prefix}_coverage.png"
                plot_coverage_bar(merged["mahalle"], merged["toplam_kapsama"], target_vals,
                                  weight_label(job['weight_type']), chart_out,
                                  title=f"Kapsama vs {weight_label(job['weight_type'])}")
                chart_file = f"{prefix}_coverage.png"
        except Exception as e:
            pass  # Görselleştirme hatası modeli durdurmaz
    
    # Metadata kaydet
    meta = {
        "run_id": prefix,
        "timestamp": timestamp,
        "parameters": {
            "k_total": job['k_total'],
            "weight_type": job['weight_type'],
            "beta": job['beta'],
            "sigma": job['sigma'],
            "kept_mevcut": job['kept_mevcut'],
            "fixed_aday": job.get('fixed_aday', []),
            "scenario_tag": scenario_tag,
            "model": model_key,
            "model_label": model_info['label']
        },
        "files": {
            "ip_file": latest_ip.name if latest_ip else None,
            "summary_file": latest_summary.name if latest_summary else None,
            "map_file": map_file,
            "chart_file": chart_file
        },
        "stdout": res.stdout
    }
    meta_path = MODELS_DIR / f"{prefix}_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4, ensure_ascii=False)
    
    return {"success": True, "meta": meta, "stdout": res.stdout}


# ==========================================
# ANA UYGULAMA
# ==========================================
adaylar, mevcut = load_data()

st.title("🏗️ Sultanbeyli Acil Durum Konteyner Optimizasyonu")

tab_single, tab_queue, tab_results, tab_compare, tab_sensitivity, tab_profile = st.tabs([
    "1. Deney Tasarımı", 
    "2. İş Kuyruğu (Job Queue)", 
    "3. Çözüm Detayları",
    "4. Çoklu Karşılaştırma",
    "5. Hassasiyet Analizi",
    "6. Mahalle Profili"
])

# ==========================================
# TAB 1: DENEY TASARIMI
# ==========================================
with tab_single:
    st.header("Deney Konfigüratörü")
    st.markdown("Parametreleri ayarlayın, ardından **doğrudan çalıştırın** veya **kuyruğa ekleyin**.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Model & Parametreler")
        model_choice = st.selectbox("Optimizasyon Modeli:",
                                     options=list(MODEL_OPTIONS.keys()),
                                     format_func=lambda k: MODEL_OPTIONS[k]['label'])
        selected_model = MODEL_OPTIONS[model_choice]
        
        weight_type = st.radio("Optimizasyon Hedefi:", 
                               options=["risk", "population", "shelter"], 
                               format_func=weight_label)
        
        if selected_model['has_beta']:
            beta = st.slider("MCDA Kalite Ağırlığı (β)", 0.0, 1.0, 0.3, 0.05)
        else:
            beta = 0.0
            st.caption("ℹ️ Bu model β parametresi kullanmaz.")
        
        if selected_model['has_sigma']:
            sigma = st.selectbox("Fuzzy Kapsama Dağılımı", ["Adaptive", "800", "RoadNetwork"])
        else:
            sigma = "800"
            st.caption("ℹ️ Bu model sigma parametresi kullanmaz.")
        
    with col2:
        st.subheader("Kapasite Yönetimi")
        k_total = st.number_input("Toplam Konteyner (Mevcut+Yeni)", min_value=1, max_value=140, value=20, step=1)
        
        st.markdown("**Korunacak Mevcut Konteynerler**")
        kept_mevcut_flags = []
        for i, row in mevcut.iterrows():
            is_kept = st.checkbox(f"{i}: {row['mahalle']} (Mevcut)", value=True, key=f"mevcut_{i}")
            if is_kept:
                kept_mevcut_flags.append(i)
                
    with col3:
        st.subheader("Zorunlu Aday Alanlar")
        st.markdown("Modele *kesinlikle seçilecek* şekilde sabitleyin.")
        fixed_aday_flags = []
        with st.expander("Zorunlu Aday Listesi (140 parsel)"):
            for i, row in adaylar.iterrows():
                is_fixed = st.checkbox(f"Aday {row['S_No']}: {row['Mahalle']}", value=False, key=f"aday_{i}")
                if is_fixed:
                    fixed_aday_flags.append(i)
    
    # Doğru hesaplama: Model sum(X) = K_TOTAL - len(kept) olarak çalışır
    # Fixed adaylar bu X'lerin bir kısmıdır (sabittir ama toplam içinde sayılır)
    k_from_pool = k_total - len(kept_mevcut_flags)
    k_free = k_from_pool - len(fixed_aday_flags)
    
    if k_from_pool < 0:
        st.error("⛔ Korunan mevcut sayısı toplam konteyner sayısından büyük olamaz!")
    elif k_free < 0:
        st.error("⛔ Korunan + Zorunlu sayısı toplam konteyner sayısından büyük olamaz!")
    else:
        st.info(f"**Model:** Aday havuzundan toplam **{k_from_pool}** konteyner seçilecek "
                f"(bunların **{len(fixed_aday_flags)}**'i zorunlu sabitlenmiş, **{k_free}**'i serbest optimizasyon). "
                f"Toplam = {len(kept_mevcut_flags)} Mevcut + {k_from_pool} Yeni = **{k_total}**")
        
        col_btn1, col_btn2 = st.columns(2)
        
        job_def = {
            "id": f"Job_{int(time.time())}",
            "model": model_choice,
            "k_total": k_total,
            "weight_type": weight_type,
            "beta": beta,
            "sigma": sigma,
            "kept_mevcut": kept_mevcut_flags,
            "fixed_aday": fixed_aday_flags if selected_model['has_fixed'] else []
        }
        
        with col_btn1:
            if st.button("▶️ Hemen Çalıştır", type="primary"):
                with st.spinner("Model çözülüyor..."):
                    result = run_single_job(job_def)
                if result["success"]:
                    st.success("✅ Model başarıyla çözüldü!")
                    with st.expander("Terminal Çıktısı", expanded=True):
                        st.code(result["stdout"])
                    st.info("📊 Sonuçlar sekmesinden harita ve tabloları inceleyebilirsiniz.")
                else:
                    st.error("❌ Model çözülürken hata oluştu!")
                    st.code(result.get("error", "Bilinmeyen hata"))
                    
        with col_btn2:
            if st.button("📋 Kuyruğa Ekle"):
                jobs = load_jobs()
                jobs.append(job_def)
                save_jobs(jobs)
                st.success(f"İş kuyruğa eklendi! (K={k_total}, {weight_label(weight_type)})")

# ==========================================
# TAB 2: İŞ KUYRUĞU
# ==========================================
with tab_queue:
    st.header("İş Yönetimi (Job Queue)")
    
    jobs = load_jobs()
    
    col_q1, col_q2 = st.columns([3, 1])
    with col_q1:
        if jobs:
            rows = []
            for j in jobs:
                m_key = j.get("model", "05_ip")
                rows.append({
                    "ID": j["id"],
                    "Model": MODEL_OPTIONS.get(m_key, {}).get("label", m_key),
                    "Hedef": weight_label(j["weight_type"]),
                    "K": j["k_total"],
                    "Beta": j["beta"],
                    "Sigma": j["sigma"],
                    "Korunan": len(j["kept_mevcut"]),
                    "Senaryo": "Ekleme" if j["kept_mevcut"] else "Baştan"
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Kuyrukta bekleyen iş yok. Deney Tasarımı sekmesinden iş ekleyin veya standart deneyleri yükleyin.")
            
    with col_q2:
        st.subheader("Hızlı İşlemler")
        
        if st.button("📦 Standart Tez Deneylerini Yükle"):
            new_jobs = []
            base_ts = int(time.time())
            
            for w in ["risk", "population"]:
                for b in [0.0, 0.3, 1.0]:
                    # Senaryo 1: K=20, 12 mevcut korunuyor (8 yeni ekleme)
                    new_jobs.append({
                        "id": f"Tez_{w}_b{int(b*100)}_Ekleme",
                        "k_total": 20,
                        "weight_type": w,
                        "beta": b,
                        "sigma": "Adaptive",
                        "kept_mevcut": list(range(12)),
                        "fixed_aday": []
                    })
                    # Senaryo 2: K=20, sıfırdan kurulum
                    new_jobs.append({
                        "id": f"Tez_{w}_b{int(b*100)}_Bastan",
                        "k_total": 20,
                        "weight_type": w,
                        "beta": b,
                        "sigma": "Adaptive",
                        "kept_mevcut": [],
                        "fixed_aday": []
                    })
            
            jobs.extend(new_jobs)
            save_jobs(jobs)
            st.success(f"{len(new_jobs)} standart tez deneyi kuyruğa eklendi!")
            st.rerun()
            
        if st.button("🗑️ Kuyruğu Temizle"):
            save_jobs([])
            st.success("Kuyruk temizlendi.")
            st.rerun()
            
    if jobs:
        st.markdown("---")
        if st.button("🚀 Kuyruğu Çalıştır (Tüm İşler)", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_area = st.empty()
            
            completed = 0
            errors = 0
            
            for idx, job in enumerate(jobs):
                status_text.info(f"⏳ Çalışıyor ({idx+1}/{len(jobs)}): **{weight_label(job['weight_type'])}** | K={job['k_total']} | β={job['beta']}")
                
                result = run_single_job(job)
                
                if result["success"]:
                    completed += 1
                else:
                    errors += 1
                    
                progress_bar.progress((idx + 1) / len(jobs))
                
            # Kuyruk temizle
            save_jobs([])
def translate_scenario(tag):
    if tag == "Ekleme":
        return "Mevcutları Koru + Yeni Ekle"
    if tag == "Bastan":
        return "Tümünü Sıfırdan Yerleştir (Serbest)"
    return tag

# ==========================================
# TAB 3: ÇÖZÜM DETAYLARI
# ==========================================
with tab_results:
    st.header("🔍 Çözüm Detayları")
    st.markdown("Çözülmüş optimizasyon modellerini listeleyin, filtreleyin ve seçilen modelin parsel detaylarını, haritasını ve kapsama analizini inceleyin.")
    
    meta_files = sorted(MODELS_DIR.glob("*_metadata.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not meta_files:
        st.info("📭 Henüz çalıştırılmış sonuç bulunamadı. Deney Tasarımı sekmesinden bir model çalıştırın.")
    else:
        meta_records = []
        meta_raw = {}
        for mf in meta_files:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            p = data["parameters"]
            label = (f"{p.get('model_label', 'IP')} | K={p['k_total']} | {weight_label(p['weight_type'])} | "
                     f"β={p['beta']} | {p.get('scenario_tag','?')} | {data['timestamp']}")
            meta_records.append({
                "Etiket": label,
                "Run_ID": data["run_id"],
                "Tarih": data["timestamp"],
                "Model": p.get("model_label", "Ana IP"),
                "Toplam Konteyner Sayısı": p["k_total"],
                "Hedef": weight_label(p["weight_type"]),
                "Beta": p["beta"],
                "Sigma": p["sigma"],
                "Korunan Mevcut Konteyner Sayısı": len(p["kept_mevcut"]),
                "Zorunlu Yeni Aday Lokasyon Sayısı": len(p.get("fixed_aday", [])),
                "Senaryo": translate_scenario(p.get("scenario_tag", "?"))
            })
            meta_raw[data["run_id"]] = data
                
        df_meta = pd.DataFrame(meta_records)
        
        # Filtreleme Seçenekleri
        with st.expander("🔍 Tabloyu Filtrele", expanded=False):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                models_list = ["Tümü"] + list(df_meta["Model"].unique())
                filter_model = st.selectbox("Model Seçin:", models_list, key="detail_f_model")
            with col_f2:
                k_list = ["Tümü"] + [str(x) for x in sorted(df_meta["Toplam Konteyner Sayısı"].unique())]
                filter_k = st.selectbox("Konteyner Bütçesi:", k_list, key="detail_f_k")
            with col_f3:
                scen_list = ["Tümü"] + list(df_meta["Senaryo"].unique())
                filter_scen = st.selectbox("Senaryo Tipi:", scen_list, key="detail_f_scen")
                
        # Filtrele
        df_filtered = df_meta.copy()
        if filter_model != "Tümü":
            df_filtered = df_filtered[df_filtered["Model"] == filter_model]
        if filter_k != "Tümü":
            df_filtered = df_filtered[df_filtered["Toplam Konteyner Sayısı"] == int(filter_k)]
        if filter_scen != "Tümü":
            df_filtered = df_filtered[df_filtered["Senaryo"] == filter_scen]
            
        st.markdown("#### 📁 Çözüm Listesi")
        st.markdown("*Detaylarını görmek istediğiniz satıra tıklayarak seçebilirsiniz:*")
        
        event = st.dataframe(
            df_filtered.drop(columns=["Etiket", "Run_ID"]), 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single_row",
            key="df_detail_select"
        )
        
        # Seçili satırı bul
        selected_id = None
        if event and hasattr(event, "selection") and event.selection.get("rows"):
            selected_row_idx = event.selection["rows"][0]
            selected_id = df_filtered.iloc[selected_row_idx]["Run_ID"]
        else:
            # Seçili satır yoksa ilkini seç
            if not df_filtered.empty:
                selected_id = df_filtered.iloc[0]["Run_ID"]
                
        if selected_id is not None:
            data = meta_raw[selected_id]
            files = data["files"]
            params = data["parameters"]
            
            st.markdown("---")
            st.markdown(f"### 🔍 Seçilen Çözüm: **{selected_id}**")
            
            # Parametre Kartı
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            col_p1.metric("Toplam Konteyner", params["k_total"])
            col_p2.metric("Hedef", weight_label(params["weight_type"]))
            col_p3.metric("Beta (β)", params["beta"])
            col_p4.metric("Senaryo", translate_scenario(params.get("scenario_tag", "?")))
            
            st.markdown("---")
            
            # MCDM Skor Tablosunu yükle
            df_sum = pd.DataFrame()
            if files.get("summary_file"):
                sum_path = MODELS_DIR / files["summary_file"]
                if sum_path.exists():
                    df_sum = pd.read_excel(sum_path)
            
            if not df_sum.empty:
                st.markdown("#### 📊 Model / Karar Varyantı Seçimi")
                st.markdown(
                    "Bu çalışmada model, 12 farklı Çok Kriterli Karar Verme (MCDM) ve "
                    "hedef ağırlıklandırma kombinasyonuyla çözülmüştür. Aşağıdaki tabloda her varyantın "
                    "amaç fonksiyonu ($Z$), fayda ($RxC$) ve kapsama metrikleri listelenmektedir. **Haritayı ve "
                    "parsel yerleşim detaylarını görmek istediğiniz kombinasyonu tablonun altındaki kutudan seçebilirsiniz:**"
                )
                
                # Varyant tablosu
                display_cols = [c for c in ["version", "mcdm", "senaryo", "Z_total", "RxC", "min_mahalle_cov", "avg_mahalle_cov", "sure_s"] if c in df_sum.columns]
                col_config = {
                    "version": "Sürüm",
                    "mcdm": "MCDM Yöntemi",
                    "senaryo": "Ağırlık Varyasyonu",
                    "Z_total": "Amaç Fonksiyonu (Z)",
                    "RxC": "Fayda Skoru (RxC)",
                    "min_mahalle_cov": "Min Kapsama (Eşitlik)",
                    "avg_mahalle_cov": "Ortalama Kapsama",
                    "sure_s": "Çözüm Süresi (sn)"
                }
                st.dataframe(
                    df_sum[display_cols] if display_cols else df_sum, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config=col_config
                )
                
                # Kombinasyon seçici
                df_sum["combo"] = df_sum["mcdm"] + " / " + df_sum["senaryo"]
                combo_options = df_sum["combo"].tolist()
                
                selected_combo = st.selectbox(
                    "Detay haritasını ve parsel yerleşim listesini güncellemek için varyasyon seçin:",
                    options=combo_options,
                    key="combo_select_detail"
                )
                
                # Seçilen varyant detayları
                match_idx = combo_options.index(selected_combo)
                row = df_sum.iloc[match_idx]
                vname = row["version"]
                mcdm_sel = row["mcdm"]
                scen_sel = row["senaryo"]

                # Seçilen varyantın metrik kartları
                st.markdown("##### 📈 Seçilen Karar Varyasyonunun Metrikleri")
                col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
                
                z_val = f"{row['Z_total']:.4f}" if "Z_total" in row and pd.notna(row["Z_total"]) else "N/A"
                col_v1.metric("Amaç Değeri (Z)", z_val)
                
                rxc_val = f"{row['RxC']:.4f}" if "RxC" in row and pd.notna(row["RxC"]) else "N/A"
                col_v2.metric("Toplam Fayda (RxC)", rxc_val)
                
                min_cov = f"{row['min_mahalle_cov']*100:.1f}%" if "min_mahalle_cov" in row and pd.notna(row["min_mahalle_cov"]) else "N/A"
                col_v3.metric("Min Kapsama (Eşitlik)", min_cov)
                
                avg_cov = f"{row['avg_mahalle_cov']*100:.1f}%" if "avg_mahalle_cov" in row and pd.notna(row["avg_mahalle_cov"]) else "N/A"
                col_v4.metric("Ort. Kapsama", avg_cov)
                
                sure_val = f"{row['sure_s']:.3f} sn" if "sure_s" in row and pd.notna(row["sure_s"]) else "N/A"
                col_v5.metric("Çözüm Süresi", sure_val)
                
                # Dosya suffix oluştur
                sg_str = "" if params["sigma"] == "800" else f"_sg{params['sigma']}"
                tr_str = "_t0.15" # default truncation
                nm_str = "_nomez" if len(params["kept_mevcut"]) == 0 else ""
                wt_str = f"_{params['weight_type']}"
                file_suffix = f"S{params.get('scenario_tag','A')}{sg_str}_b{int(params['beta']*100)}_K{params['k_total']}{tr_str}{nm_str}{wt_str}"
                
                ip_name = f"ip_{vname}_{mcdm_sel}_{scen_sel}_{file_suffix}.xlsx"
                cov_name = f"coverage_{vname}_{mcdm_sel}_{scen_sel}_{file_suffix}.xlsx"
                
                ip_path = MODELS_DIR / ip_name
                cov_path = MODELS_DIR / cov_name
                
                col_left, col_right = st.columns([1, 2])
                
                with col_left:
                    st.markdown(f"#### 📍 Seçilen Konteyner Lokasyonları ({selected_combo})")
                    if ip_path.exists():
                        df_ip = pd.read_excel(ip_path)
                        show_cols = [c for c in ["S_No", "Mahalle", "Alan_Adi", "Enlem", "Boylam", "toplam_mu_saglanan", "p_access_road"] if c in df_ip.columns]
                        st.dataframe(df_ip[show_cols] if show_cols else df_ip, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Seçilen varyanta ait Excel lokasyon dosyası bulunamadı.")
                        
                with col_right:
                    st.markdown(f"#### 🗺️ İnteraktif Çözüm Haritası ({selected_combo})")
                    if ip_path.exists():
                        from visualization import plot_solution_map
                        mevcut_full = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
                        yeni_df = pd.read_excel(ip_path)
                        
                        # Kept / Removed mantığı
                        if params["kept_mevcut"]:
                            kept_df = mevcut_full.iloc[params["kept_mevcut"]].copy()
                            all_idx = set(range(len(mevcut_full)))
                            removed_idx = all_idx - set(params["kept_mevcut"])
                            removed_df = mevcut_full.iloc[list(removed_idx)].copy() if removed_idx else pd.DataFrame()
                        else:
                            kept_df = pd.DataFrame()
                            removed_df = mevcut_full.copy()
                            
                        fixed_df = pd.DataFrame()
                        
                        temp_map_path = RESULTS_DIR / "temp_detail_map.html"
                        
                        cov_df_detail = None
                        if cov_path.exists():
                            cov_df_detail = pd.read_excel(cov_path)
                            
                        plot_solution_map(
                            yeni_df, kept_df, removed_df, fixed_df, temp_map_path,
                            title=f"K={params['k_total']} | {selected_combo} | {translate_scenario(params.get('scenario_tag','?'))}",
                            cov_df=cov_df_detail,
                            sigma=int(params.get("sigma", 800))
                        )
                        
                        if temp_map_path.exists():
                            with open(temp_map_path, "r", encoding="utf-8") as f:
                                html_data = f.read()
                            import streamlit.components.v1 as components
                            components.html(html_data, height=500, scrolling=True)
                    else:
                        st.warning("Çözüm haritası çizilemedi (Dosya eksik).")
                        
                # Kapsama Grafiği ve Lorenz Eğrisi
                if cov_path.exists() and ip_path.exists():
                    st.markdown(f"#### 📈 Kapsama ve Eşitlik Analizi ({selected_combo})")
                    from visualization import plot_coverage_bar, plot_lorenz_curve
                    cov_df = pd.read_excel(cov_path)
                    
                    if params['weight_type'] == "population":
                        w_df = pd.read_excel(DATA_DIR / "mahalle_nufus.xlsx")
                        val_col = "nufus_2024"
                    elif params['weight_type'] == "shelter":
                        w_df = pd.read_excel(DATA_DIR / "mahalle_barinma.xlsx")
                        val_col = "hane_ihtiyaci"
                    else:
                        w_df = pd.read_excel(DATA_DIR / "mahalle_risk.xlsx")
                        val_col = "risk_score"
                        
                    w_df["mahalle_norm"] = w_df["mahalle"].apply(norm_mahalle)
                    cov_df["mahalle_norm"] = cov_df["mahalle"].apply(norm_mahalle)
                    merged = pd.merge(cov_df, w_df, on="mahalle_norm", how="left", suffixes=("", "_w"))
                    
                    max_val = merged[val_col].max()
                    target_vals = merged[val_col] / (max_val + 1e-9)
                    
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.markdown("##### 📊 Mahalle Kapsama vs İhtiyaç Seviyesi")
                        temp_chart_path = RESULTS_DIR / "temp_detail_chart.png"
                        plot_coverage_bar(
                            merged["mahalle"], merged["toplam_kapsama"], target_vals,
                            weight_label(params['weight_type']), temp_chart_path,
                            title=f"Kapsama vs {weight_label(params['weight_type'])} ({selected_combo})"
                        )
                        if temp_chart_path.exists():
                            st.image(str(temp_chart_path), use_container_width=True)
                            
                    with col_chart2:
                        st.markdown("##### 📈 Lorenz Eğrisi (Kapsama Dağılımı Adaleti)")
                        temp_lorenz_path = RESULTS_DIR / "temp_lorenz_chart.png"
                        
                        # Orman alanlarını Gini hesabını bozmaması için çıkar
                        non_forest_df = merged[~merged["mahalle_norm"].isin(["SALGAMLI DEVLET ORMANI", "TEFERRUC TEPE ORMANI"])]
                        
                        # Önce Gini katsayısını hesaplamak için bir kerelik çiz
                        g_coef = plot_lorenz_curve(
                            non_forest_df["toplam_kapsama"].values, temp_lorenz_path,
                            title="Lorenz Eğrisi"
                        )
                        # Başlığa Gini'yi yazarak tekrar çiz
                        plot_lorenz_curve(
                            non_forest_df["toplam_kapsama"].values, temp_lorenz_path,
                            title=f"Lorenz Eğrisi (Gini: {g_coef:.3f})"
                        )
                        
                        if temp_lorenz_path.exists():
                            st.image(str(temp_lorenz_path), use_container_width=True)
                            
                # Radar Grafiği Karşılaştırması
                st.markdown("---")
                st.markdown("#### 🕸️ Karar Varyasyonları Radar Karşılaştırması")
                st.markdown("Farklı MCDM/ağırlık varyasyonlarının güçlü/zayıf yönlerini kıyaslamak için en fazla 3 tanesini seçin:")
                
                radar_selections = st.multiselect(
                    "Karşılaştırılacak varyasyonları seçin:",
                    options=combo_options,
                    default=combo_options[:2] if len(combo_options) >= 2 else combo_options,
                    max_selections=3,
                    key="radar_variant_select"
                )
                
                if radar_selections:
                    import plotly.graph_objects as go
                    
                    fig_radar = go.Figure()
                    categories = ['Amaç Değeri (Z)', 'Toplam Fayda (RxC)', 'Min Kapsama (Eşitlik)', 'Ortalama Kapsama', 'Adalet Seviyesi (1-Gini)']
                    
                    for combo in radar_selections:
                        c_idx = combo_options.index(combo)
                        c_row = df_sum.iloc[c_idx]
                        
                        v_vname = c_row["version"]
                        v_mcdm = c_row["mcdm"]
                        v_scen = c_row["senaryo"]
                        v_suffix = f"S{params.get('scenario_tag','A')}{sg_str}_b{int(params['beta']*100)}_K{params['k_total']}{tr_str}{nm_str}{wt_str}"
                        v_cov_name = f"coverage_{v_vname}_{v_mcdm}_{v_scen}_{v_suffix}.xlsx"
                        v_cov_path = MODELS_DIR / v_cov_name
                        
                        v_gini = 0.0
                        if v_cov_path.exists():
                            v_cov_df = pd.read_excel(v_cov_path)
                            v_cov_df["mahalle_norm"] = v_cov_df["mahalle"].apply(norm_mahalle)
                            v_non_forest = v_cov_df[~v_cov_df["mahalle_norm"].isin(["SALGAMLI DEVLET ORMANI", "TEFERRUC TEPE ORMANI"])]
                            v_vals = np.sort(v_non_forest["toplam_kapsama"].values)
                            v_n = len(v_vals)
                            if v_n > 0:
                                v_sum_diffs = np.sum(np.abs(v_vals[:, None] - v_vals[None, :]))
                                v_denom = 2 * v_n * np.sum(v_vals)
                                v_gini = v_sum_diffs / v_denom if v_denom > 0 else 0.0
                        
                        z_val = c_row.get('Z_total', 0.0)
                        rxc_val = c_row.get('RxC', 0.0)
                        min_cov = c_row.get('min_mahalle_cov', 0.0)
                        avg_cov = c_row.get('avg_mahalle_cov', 0.0)
                        equality_val = 1.0 - v_gini
                        
                        r_values = [z_val, rxc_val, min_cov, avg_cov, equality_val]
                        r_values.append(r_values[0])
                        categories_closed = categories + [categories[0]]
                        
                        fig_radar.add_trace(go.Scatterpolar(
                            r=r_values,
                            theta=categories_closed,
                            fill='toself',
                            name=combo,
                            opacity=0.4
                        ))
                        
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1.1]
                            )
                        ),
                        showlegend=True,
                        title="MCDM Karar Varyasyonları Karşılaştırma Analizi",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.warning("Bu optimizasyon koşumu için varyant summary tablosu yüklenemedi.")
            
            # Epsilon Constraint model ise Pareto Cephesi Görselleştirmesi ekle
            if params.get("model") == "13_eps":
                st.markdown("---")
                st.markdown("### 🏆 Pareto Cephesi Görselleştirmesi (Trade-off Analizi)")
                
                k_total = params["k_total"]
                weight_type = params["weight_type"]
                pareto_file = RESULTS_DIR / "eps_constraint" / f"pareto_results_K{k_total}_{weight_type}.xlsx"
                
                if pareto_file.exists():
                    df_pareto = pd.read_excel(pareto_file)
                    df_pareto_opt = df_pareto[df_pareto["status"] == "Optimal"].drop_duplicates(subset=["RxC", "actual_min_cov"])
                    
                    if not df_pareto_opt.empty:
                        import plotly.express as px
                        if "avg_cov" in df_pareto_opt.columns:
                            fig_pareto = px.scatter_3d(
                                df_pareto_opt,
                                x="actual_min_cov",
                                y="RxC",
                                z="avg_cov",
                                color="RxC",
                                labels={
                                    "actual_min_cov": "Min Kapsama (Eşitlik)",
                                    "RxC": "Toplam Risk×Kapsama (Verimlilik)",
                                    "avg_cov": "Ortalama Kapsama (Genel Hizmet)"
                                },
                                title="3D Pareto Cephesi: Sosyal Eşitlik vs. Verimlilik vs. Ortalama Hizmet Seviyesi"
                            )
                            fig_pareto.update_traces(marker=dict(size=6, symbol='circle'))
                        else:
                            fig_pareto = px.scatter(
                                df_pareto_opt,
                                x="actual_min_cov",
                                y="RxC",
                                color="RxC",
                                labels={
                                    "actual_min_cov": "Minimum Mahalle Kapsaması (Eşitlik)",
                                    "RxC": "Toplam Risk×Kapsama Skoru (Verimlilik)"
                                },
                                title="2D Pareto Cephesi: Sosyal Eşitlik vs. Verimlilik"
                            )
                            fig_pareto.update_traces(mode='lines+markers', marker=dict(size=10))
                        
                        st.plotly_chart(fig_pareto, use_container_width=True)
                        
                        show_pareto_cols = ["eps_target", "RxC", "actual_min_cov"]
                        if "avg_cov" in df_pareto_opt.columns:
                            show_pareto_cols.append("avg_cov")
                        st.dataframe(df_pareto_opt[show_pareto_cols], use_container_width=True, hide_index=True)
                    else:
                        st.warning("Pareto Excel dosyasında çözülmüş optimal nokta bulunamadı.")
                else:
                    st.info(f"Pareto sonuç Excel dosyası bulunamadı: `{pareto_file.name}`.")
            
            # PDF Rapor Butonu
            st.markdown("---")
            st.markdown("### 📥 PDF Çözüm Raporu")
            pdf_path = RESULTS_DIR / f"{selected_id}_report.pdf"
            
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                if st.button("📄 PDF Raporu Oluştur / Güncelle"):
                    with st.spinner("PDF oluşturuluyor..."):
                        cmd_pdf = [
                            sys.executable,
                            str(PROJECT_ROOT / "src" / "report_generator.py"),
                            str(MODELS_DIR / f"{selected_id}_metadata.json"),
                            str(pdf_path)
                        ]
                        res_pdf = subprocess.run(cmd_pdf, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
                        if res_pdf.returncode == 0:
                            st.success("✅ PDF raporu başarıyla oluşturuldu!")
                        else:
                            st.error("PDF oluşturulurken hata!")
                            st.code(res_pdf.stderr)
            with col_pdf2:
                if pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        pdf_data = f.read()
                    st.download_button(
                        label="📥 PDF Raporunu İndir",
                        data=pdf_data,
                        file_name=f"{selected_id}_report.pdf",
                        mime="application/pdf"
                    )
            
            # Terminal çıktısı
            if data.get("stdout"):
                with st.expander("🖥️ Terminal Çıktısı"):
                    st.code(data["stdout"])
                    
        # ==========================================
        # RAPOR ÜRETİMİ (SENTEZ)
        # ==========================================
        st.markdown("---")
        st.markdown("### 📝 Final Rapor Üretimi (Tüm Çözümlerin Sentezi)")
        st.markdown("Tüm koşumların toplu analizini içeren akademik rapor ve Excel dosyasını üretin.")
        
        if st.button("📄 Final Sentez Raporu Üret (FINAL_REPORT.xlsx + FINAL_RAPOR.md)", type="primary"):
            with st.spinner("Sentez yapılıyor..."):
                res = subprocess.run(
                    [sys.executable, str(PROJECT_ROOT / "src" / "07_reporting.py")],
                    capture_output=True, text=True, cwd=str(PROJECT_ROOT)
                )
            if res.returncode == 0:
                st.success("✅ Sentez raporu başarıyla üretildi!")
                st.code(res.stdout)
            else:
                st.error("Sentez raporu üretiminde hata!")
                st.code(res.stderr)

# ==========================================
# TAB 4: ÇOKLU KARŞILAŞTIRMA (MULTI-COMPARE)
# ==========================================
with tab_compare:
    st.header("⚖️ Çoklu Karşılaştırma (Multi-Compare)")
    st.markdown("Farklı bütçe, model ve senaryoların amaç fonksiyonu (Z) değerlerini ve kapsama oranlarını yan yana kıyaslayın.")
    
    meta_files = sorted(MODELS_DIR.glob("*_metadata.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not meta_files:
        st.info("📭 Henüz çalıştırılmış sonuç bulunamadı. Deney Tasarımı sekmesinden bir model çalıştırın.")
    else:
        # Load all metadatas
        meta_records = []
        meta_raw = {}
        for mf in meta_files:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            p = data["parameters"]
            label = (f"{p.get('model_label', 'IP')} | K={p['k_total']} | {weight_label(p['weight_type'])} | "
                     f"β={p['beta']} | {p.get('scenario_tag','?')} | {data['timestamp']}")
            meta_records.append({
                "Etiket": label,
                "Run_ID": data["run_id"],
                "Tarih": data["timestamp"],
                "Model": p.get("model_label", "Ana IP"),
                "Toplam Konteyner Sayısı": p["k_total"],
                "Hedef": weight_label(p["weight_type"]),
                "Beta": p["beta"],
                "Sigma": p["sigma"],
                "Korunan Mevcut Konteyner Sayısı": len(p["kept_mevcut"]),
                "Zorunlu Yeni Aday Lokasyon Sayısı": len(p.get("fixed_aday", [])),
                "Senaryo": translate_scenario(p.get("scenario_tag", "?"))
            })
            meta_raw[data["run_id"]] = data
            
        df_meta = pd.DataFrame(meta_records)
        
        # Filtreleme Seçenekleri (Multi-Compare için)
        with st.expander("🔍 Karşılaştırma Listesini Filtrele", expanded=False):
            col_cf1, col_cf2 = st.columns(2)
            with col_cf1:
                filter_c_k = st.selectbox("Toplam Konteyner Filtresi:", ["Tümü"] + [str(x) for x in sorted(df_meta["Toplam Konteyner Sayısı"].unique())], key="cf_k")
            with col_cf2:
                filter_c_scen = st.selectbox("Senaryo Tipi Filtresi:", ["Tümü"] + list(df_meta["Senaryo"].unique()), key="cf_scen")
                
        df_c_filtered = df_meta.copy()
        if filter_c_k != "Tümü":
            df_c_filtered = df_c_filtered[df_c_filtered["Toplam Konteyner Sayısı"] == int(filter_c_k)]
        if filter_c_scen != "Tümü":
            df_c_filtered = df_c_filtered[df_c_filtered["Senaryo"] == filter_c_scen]
            
        compare_selection = st.multiselect(
            "Karşılaştırmak istediğiniz analizleri seçin (En fazla 6 adet):",
            options=df_c_filtered["Run_ID"].tolist(),
            format_func=lambda rid: df_c_filtered[df_c_filtered["Run_ID"] == rid]["Etiket"].values[0] if rid in df_c_filtered["Run_ID"].values else rid,
            max_selections=6,
            key="compare_select_multiselect"
        )
        
        if len(compare_selection) >= 2:
            compare_dfs = []
            for rid in compare_selection:
                rd = meta_raw[rid]
                sf = rd["files"].get("summary_file")
                if sf:
                    sp = MODELS_DIR / sf
                    if sp.exists():
                        df_s = pd.read_excel(sp)
                        df_s["run_label"] = f"K={rd['parameters']['k_total']}|{rd['parameters']['weight_type']}|β={rd['parameters']['beta']}|{translate_scenario(rd['parameters'].get('scenario_tag','?'))}"
                        df_s["run_id"] = rid
                        compare_dfs.append(df_s)
            
            if compare_dfs:
                merged = pd.concat(compare_dfs, ignore_index=True)
                
                col_c1, col_c2 = st.columns(2)
                
                with col_c1:
                    st.markdown("#### Z (Amaç Fonksiyonu) Karşılaştırması")
                    if "Z_total" in merged.columns and "mcdm" in merged.columns:
                        best_z = merged.groupby("run_label")["Z_total"].max().reset_index()
                        best_z = best_z.sort_values("Z_total", ascending=True)
                        
                        import matplotlib.pyplot as plt
                        fig_z, ax_z = plt.subplots(figsize=(8, max(3, len(best_z)*0.6)))
                        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(best_z)))
                        ax_z.barh(best_z["run_label"], best_z["Z_total"], color=colors, edgecolor="black", linewidth=0.5)
                        ax_z.set_xlabel("Z (Amaç Fonksiyonu)")
                        ax_z.set_title("Senaryolar Arası Z Karşılaştırması", fontweight="bold")
                        ax_z.grid(axis="x", alpha=0.3)
                        fig_z.tight_layout()
                        st.pyplot(fig_z)
                        plt.close(fig_z)
                
                with col_c2:
                    st.markdown("#### Min Kapsama Karşılaştırması")
                    if "min_mahalle_cov" in merged.columns:
                        best_cov = merged.groupby("run_label")["min_mahalle_cov"].max().reset_index()
                        best_cov = best_cov.sort_values("min_mahalle_cov", ascending=True)
                        
                        import matplotlib.pyplot as plt
                        fig_c, ax_c = plt.subplots(figsize=(8, max(3, len(best_cov)*0.6)))
                        colors_c = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(best_cov)))
                        ax_c.barh(best_cov["run_label"], best_cov["min_mahalle_cov"], color=colors_c, edgecolor="black", linewidth=0.5)
                        ax_c.set_xlabel("Min Mahalle Kapsama")
                        ax_c.set_title("En Düşük Mahalle Kapsaması", fontweight="bold")
                        ax_c.grid(axis="x", alpha=0.3)
                        fig_c.tight_layout()
                        st.pyplot(fig_c)
                        plt.close(fig_c)
                
                # Koşumlar Arası Radar Karşılaştırma
                st.markdown("---")
                st.markdown("#### 🕸️ Koşumlar Arası Radar Karşılaştırma Analizi")
                st.markdown("Seçilen tüm koşumların en iyi (Maksimum RxC) varyantlarının performanslarını kıyaslar:")
                
                import plotly.graph_objects as go
                fig_radar_c = go.Figure()
                categories_c = ['Maks Amaç Değeri (Z)', 'Maks Toplam Fayda (RxC)', 'Maks Min Kapsama', 'Maks Ort. Kapsama', 'Min Gini Eşitsizliği (Ters)']
                
                for rid in compare_selection:
                    rd = meta_raw[rid]
                    sf = rd["files"].get("summary_file")
                    if sf:
                        sp = MODELS_DIR / sf
                        if sp.exists():
                            df_s = pd.read_excel(sp)
                            # Maksimum RxC değerine sahip satırı bul
                            best_row = df_s.loc[df_s["RxC"].idxmax()]
                            
                            # Bu varyantın Gini katsayısını hesaplamak için kapsama dosyasını yükle
                            v_vname = best_row["version"]
                            v_mcdm = best_row["mcdm"]
                            v_scen = best_row["senaryo"]
                            
                            sg_str = "" if rd['parameters']["sigma"] == "800" else f"_sg{rd['parameters']['sigma']}"
                            tr_str = "_t0.15" # default
                            nm_str = "_nomez" if len(rd['parameters']["kept_mevcut"]) == 0 else ""
                            wt_str = f"_{rd['parameters']['weight_type']}"
                            v_suffix = f"S{rd['parameters'].get('scenario_tag','A')}{sg_str}_b{int(rd['parameters']['beta']*100)}_K{rd['parameters']['k_total']}{tr_str}{nm_str}{wt_str}"
                            
                            v_cov_name = f"coverage_{v_vname}_{v_mcdm}_{v_scen}_{v_suffix}.xlsx"
                            v_cov_path = MODELS_DIR / v_cov_name
                            
                            v_gini = 0.0
                            if v_cov_path.exists():
                                v_cov_df = pd.read_excel(v_cov_path)
                                v_cov_df["mahalle_norm"] = v_cov_df["mahalle"].apply(norm_mahalle)
                                v_non_forest = v_cov_df[~v_cov_df["mahalle_norm"].isin(["SALGAMLI DEVLET ORMANI", "TEFERRUC TEPE ORMANI"])]
                                v_vals = np.sort(v_non_forest["toplam_kapsama"].values)
                                v_n = len(v_vals)
                                if v_n > 0:
                                    v_sum_diffs = np.sum(np.abs(v_vals[:, None] - v_vals[None, :]))
                                    v_denom = 2 * v_n * np.sum(v_vals)
                                    v_gini = v_sum_diffs / v_denom if v_denom > 0 else 0.0
                                    
                            z_val = best_row.get('Z_total', 0.0)
                            rxc_val = best_row.get('RxC', 0.0)
                            min_cov = best_row.get('min_mahalle_cov', 0.0)
                            avg_cov = best_row.get('avg_mahalle_cov', 0.0)
                            equality_val = 1.0 - v_gini
                            
                            r_values = [z_val, rxc_val, min_cov, avg_cov, equality_val]
                            r_values.append(r_values[0])
                            categories_c_closed = categories_c + [categories_c[0]]
                            
                            fig_radar_c.add_trace(go.Scatterpolar(
                                r=r_values,
                                theta=categories_c_closed,
                                fill='toself',
                                name=f"K={rd['parameters']['k_total']} | {rd['parameters']['weight_type']}",
                                opacity=0.4
                            ))
                            
                fig_radar_c.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1.1]
                        )
                    ),
                    showlegend=True,
                    title="Koşumlar Arası Performans Karşılaştırması (En İyi RxC Varyantları)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_radar_c, use_container_width=True)
                
                # Harita Karşılaştırması (Yan Yana)
                if len(compare_selection) == 2:
                    st.markdown("---")
                    st.markdown("#### 🗺️ Yan Yana Harita Karşılaştırması")
                    
                    rid_1, rid_2 = compare_selection[0], compare_selection[1]
                    rd_1, rd_2 = meta_raw[rid_1], meta_raw[rid_2]
                    
                    lbl_1 = f"{rd_1['parameters'].get('model_label', 'IP')} | K={rd_1['parameters']['k_total']} | {weight_label(rd_1['parameters']['weight_type'])} | β={rd_1['parameters']['beta']} | {translate_scenario(rd_1['parameters'].get('scenario_tag','?'))}"
                    lbl_2 = f"{rd_2['parameters'].get('model_label', 'IP')} | K={rd_2['parameters']['k_total']} | {weight_label(rd_2['parameters']['weight_type'])} | β={rd_2['parameters']['beta']} | {translate_scenario(rd_2['parameters'].get('scenario_tag','?'))}"
                    
                    map_f1 = rd_1["files"].get("map_file")
                    map_f2 = rd_2["files"].get("map_file")
                    
                    col_m1, col_m2 = st.columns(2)
                    
                    with col_m1:
                        st.markdown(f"**Sol Çözüm:** {lbl_1}")
                        if map_f1:
                            mp1 = MAPS_DIR / map_f1
                            if mp1.exists():
                                with open(mp1, "r", encoding="utf-8") as f:
                                    html_data1 = f.read()
                                import streamlit.components.v1 as components
                                components.html(html_data1, height=450, scrolling=True)
                            else:
                                st.warning("Harita 1 bulunamadı.")
                        else:
                            st.warning("Harita 1 yok.")
                            
                    with col_m2:
                        st.markdown(f"**Sağ Çözüm:** {lbl_2}")
                        if map_f2:
                            mp2 = MAPS_DIR / map_f2
                            if mp2.exists():
                                with open(mp2, "r", encoding="utf-8") as f:
                                    html_data2 = f.read()
                                import streamlit.components.v1 as components
                                components.html(html_data2, height=450, scrolling=True)
                            else:
                                st.warning("Harita 2 bulunamadı.")
                        else:
                            st.warning("Harita 2 yok.")
                
                # Detaylı MCDM karşılaştırma tablosu
                st.markdown("---")
                st.markdown("#### Detaylı MCDM Skor Tablosu (Tüm Seçilenler)")
                show = [c for c in ["run_label", "mcdm", "senaryo", "Z_total", "RxC", "min_mahalle_cov", "avg_mahalle_cov"] if c in merged.columns]
                st.dataframe(merged[show].round(4), use_container_width=True, hide_index=True)
        elif len(compare_selection) == 1:
            st.info("Karşılaştırmak için en az 2 analiz seçin.")

# ==========================================
# TAB 4: HASSASİYET ANALİZİ
# ==========================================
with tab_sensitivity:
    st.header("⚡ Otomatik Hassasiyet Analizi (Sensitivity Analysis)")
    st.markdown("Farklı β (kalite ağırlığı) ve K (konteyner sayısı) parametrelerinin çözümlere etkisini inceleyin.")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.subheader("Hassasiyet Taraması Başlat")
        s_K = st.number_input("Beta Taraması için Sabit K Değeri:", min_value=8, max_value=32, value=20, step=4)
        s_beta = st.slider("K Taraması için Sabit Beta Değeri (β):", 0.0, 1.0, 0.3, 0.05)
        s_weight = st.selectbox("Hassasiyet Analizi Hedefi:", ["risk", "population", "shelter"], format_func=weight_label)
        
        if st.button("🚀 Hassasiyet Analizini Çalıştır", type="primary"):
            with st.spinner("Grid taraması ve tekil grafikler hesaplanıyor (Bu işlem 15-20 sn sürebilir)..."):
                # 1. Grid hesaplamasını yap (--grid ile)
                cmd_sens = [
                    sys.executable, 
                    str(PROJECT_ROOT / "src" / "sensitivity.py"),
                    "--grid",
                    "--weight", s_weight
                ]
                res_sens = subprocess.run(cmd_sens, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
                
                # 2. Tekil beta/K grafiklerini üret
                cmd_charts = [
                    sys.executable,
                    str(PROJECT_ROOT / "src" / "sensitivity.py"),
                    "--K", str(s_K),
                    "--beta", str(s_beta),
                    "--weight", s_weight
                ]
                res_charts = subprocess.run(cmd_charts, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
                
                if res_sens.returncode == 0 and res_charts.returncode == 0:
                    st.success("✅ Hassasiyet analizi ve karar paneli başarıyla güncellendi!")
                    st.rerun()
                else:
                    st.error("Hassasiyet analizi çalışırken hata oluştu.")
                    st.code((res_sens.stderr or "") + "\n" + (res_charts.stderr or ""))
                    
    with col_s2:
        st.subheader("📈 Analiz Raporları")
        st.markdown("Sabit bütçe (K) ve ağırlık (β) kesitlerinde modelin davranış trendleri:")
        
    st.markdown("---")
    
    # Grafikleri Göster
    col_img1, col_img2 = st.columns(2)
    
    beta_img_path = CHARTS_DIR / f"sensitivity_beta_K{s_K}_{s_weight}.png"
    k_img_path = CHARTS_DIR / f"sensitivity_K_b{int(s_beta*100)}_{s_weight}.png"
    
    with col_img1:
        st.markdown(f"#### 1. MCDA Ağırlığı (β) Hassasiyeti (Sabit K={s_K})")
        if beta_img_path.exists():
            st.image(str(beta_img_path), use_container_width=True)
        else:
            st.info("Bu parametre kümesi için henüz trend grafiği üretilmemiş. Sol taraftan analizi çalıştırın.")
            
    with col_img2:
        st.markdown(f"#### 2. Konteyner Sayısı (K) Hassasiyeti (Sabit β={s_beta:.2f})")
        if k_img_path.exists():
            st.image(str(k_img_path), use_container_width=True)
        else:
            st.info("Bu parametre kümesi için henüz trend grafiği üretilmemiş. Sol taraftan analizi çalıştırın.")

    # İnteraktif Karar Paneli (What-If)
    grid_file = MODELS_DIR / f"sensitivity_grid_{s_weight}.xlsx"
    
    st.markdown("---")
    st.subheader("💡 İnteraktif 'What-If' Karar Paneli (Anlık Cache Sorgulama)")
    st.markdown(
        "Aşağıdaki sürgüler yardımıyla Konteyner Bütçesi (K) ve Kalite Ağırlığı (β) değerlerini anlık olarak değiştirerek "
        "modelin genel performans metriklerindeki değişimi **milisaniyeler içinde** görün. Bu panel, arka planda önceden çözülmüş "
        "77 farklı kombinasyonlu veri havuzunu sorgulamaktadır."
    )
    
    if grid_file.exists():
        df_grid = pd.read_excel(grid_file)
        
        # Sürgüler
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            w_K = st.select_slider(
                "Konteyner Bütçesi (Toplam Konteyner K sayısı):",
                options=[8, 12, 16, 20, 24, 28, 32],
                value=int(s_K) if int(s_K) in [8, 12, 16, 20, 24, 28, 32] else 20,
                key="whatif_K"
            )
        with col_w2:
            w_beta = st.select_slider(
                "MCDA Kalite Ağırlığı (β):",
                options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                value=round(float(s_beta), 1) if round(float(s_beta), 1) in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] else 0.3,
                key="whatif_beta"
            )
            
        # Filtrele
        row_match = df_grid[(df_grid["K"] == w_K) & (np.abs(df_grid["beta"] - w_beta) < 1e-5)]
        
        if not row_match.empty:
            rdata = row_match.iloc[0]
            
            # Göstergeler
            col_g1, col_g2, col_g3, col_g4 = st.columns(4)
            col_g1.metric("Amaç Değeri (Z)", f"{rdata['Z_total']:.4f}")
            col_g2.metric("Toplam Kapsama Faydası (RxC)", f"{rdata['RxC']:.4f}")
            col_g3.metric("Minimum Kapsama (Eşitlik)", f"{rdata['min_cov']*100:.1f}%")
            col_g4.metric("Ortalama Kapsama", f"{rdata['avg_cov']*100:.1f}%")
            
            # İnteraktif Grafikler
            import plotly.graph_objects as go
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                # Sabit K için beta değişimi
                df_fixed_k = df_grid[df_grid["K"] == w_K].sort_values("beta")
                fig_pk = go.Figure()
                fig_pk.add_trace(go.Scatter(x=df_fixed_k["beta"], y=df_fixed_k["RxC"], name="Fayda (RxC)", line=dict(color="#FF6B35", width=2.5)))
                fig_pk.add_trace(go.Scatter(x=df_fixed_k["beta"], y=df_fixed_k["min_cov"], name="Min Kapsama (Eşitlik)", line=dict(color="#2EC4B6", width=2.5)))
                fig_pk.add_trace(go.Scatter(x=df_fixed_k["beta"], y=df_fixed_k["avg_cov"], name="Ortalama Kapsama", line=dict(color="#011627", width=2.5)))
                
                # Dikey kesit çizgisi (seçili beta)
                fig_pk.add_vline(x=w_beta, line_width=1.5, line_dash="dash", line_color="red", annotation_text=f"Seçili β={w_beta}")
                
                fig_pk.update_layout(
                    title=f"MCDA Ağırlığı (β) Hassasiyeti (Sabit K={w_K})",
                    xaxis_title="MCDA Kalite Ağırlığı (β)",
                    yaxis_title="Metrik Değeri",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_pk, use_container_width=True)
                
            with col_p2:
                # Sabit beta için K değişimi
                df_fixed_b = df_grid[np.abs(df_grid["beta"] - w_beta) < 1e-5].sort_values("K")
                fig_pb = go.Figure()
                fig_pb.add_trace(go.Scatter(x=df_fixed_b["K"], y=df_fixed_b["RxC"], name="Fayda (RxC)", line=dict(color="#FF6B35", width=2.5)))
                fig_pb.add_trace(go.Scatter(x=df_fixed_b["K"], y=df_fixed_b["min_cov"], name="Min Kapsama (Eşitlik)", line=dict(color="#2EC4B6", width=2.5)))
                fig_pb.add_trace(go.Scatter(x=df_fixed_b["K"], y=df_fixed_b["avg_cov"], name="Ortalama Kapsama", line=dict(color="#011627", width=2.5)))
                
                # Dikey kesit çizgisi (seçili K)
                fig_pb.add_vline(x=w_K, line_width=1.5, line_dash="dash", line_color="red", annotation_text=f"Seçili K={w_K}")
                
                fig_pb.update_layout(
                    title=f"Bütçe (K) Hassasiyet Analizi (Sabit β={w_beta})",
                    xaxis_title="Toplam Konteyner Sayısı (K)",
                    yaxis_title="Metrik Değeri",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_pb, use_container_width=True)
        else:
            st.warning("Seçilen kombinasyon için veri bulunamadı.")
    else:
        st.info("💡 Karar Paneli için önbellek dosyası bulunamadı. Lütfen sol taraftan '🚀 Hassasiyet Analizini Çalıştır' diyerek taramayı gerçekleştirin veya aşağıdaki buton ile tüm gridi oluşturun.")
        if st.button("🚀 Tüm Hassasiyet Grid Önbelleğini Oluştur (77 Kombinasyon, ~15 sn)", key="build_grid_button"):
            with st.spinner("Tüm parametre kombinasyonları çözülüyor..."):
                cmd_grid = [
                    sys.executable, 
                    str(PROJECT_ROOT / "src" / "sensitivity.py"),
                    "--grid",
                    "--weight", s_weight
                ]
                res_grid = subprocess.run(cmd_grid, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
                if res_grid.returncode == 0:
                    st.success("✅ Hassasiyet grid önbelleği başarıyla oluşturuldu! Sayfayı yeniliyoruz...")
                    st.rerun()
                else:
                    st.error("Grid hesaplanırken hata oluştu.")
                    st.code(res_grid.stderr)

# ==========================================
# TAB 6: MAHALLE PROFİLİ
# ==========================================
with tab_profile:
    st.header("🏡 Mahalle Afet Profili ve Detay Analizi")
    
    # ----------------------------------------------------
    # MAKRO GÖRÜNÜM (İLÇE GENELİ ANALİZ)
    # ----------------------------------------------------
    st.markdown("### 🗺️ İlçe Geneli Makro Görünüm (12 Mevcut Konteyner Dağılımı ve Göstergeler)")
    
    # Verileri yükle
    df_nuf, df_risk, df_bar, df_mevcut = load_profile_data()
    
    # Mevcut konteyner sayısını mahalle bazlı hesapla
    df_mevcut["mahalle_norm"] = df_mevcut["mahalle"].apply(norm_mahalle)
    container_counts = df_mevcut.groupby("mahalle_norm").size().reset_index(name="Mevcut Konteyner Sayısı")
    
    # Normalleştir
    df_nuf["mahalle_norm"] = df_nuf["mahalle"].apply(norm_mahalle)
    df_risk["mahalle_norm"] = df_risk["mahalle"].apply(norm_mahalle)
    df_bar["mahalle_norm"] = df_bar["mahalle"].apply(norm_mahalle)
    
    # Tabloları birleştir
    df_macro = df_nuf.merge(df_risk, on="mahalle_norm", suffixes=("", "_risk"))
    df_macro = df_macro.merge(df_bar, on="mahalle_norm", suffixes=("", "_bar"))
    df_macro = df_macro.merge(container_counts, on="mahalle_norm", how="left")
    df_macro["Mevcut Konteyner Sayısı"] = df_macro["Mevcut Konteyner Sayısı"].fillna(0).astype(int)
    
    # Görsel tabloyu oluştur
    df_macro_presentation = df_macro.rename(columns={
        "mahalle": "Mahalle Adı",
        "nufus_2024": "Gece Nüfusu (2024)",
        "risk_score": "Deprem Risk Skoru (İBB)",
        "hane_ihtiyaci": "Barınma İhtiyacı (Hane)"
    })[["Mahalle Adı", "Gece Nüfusu (2024)", "Deprem Risk Skoru (İBB)", "Barınma İhtiyacı (Hane)", "Mevcut Konteyner Sayısı"]]
    
    df_macro_presentation = df_macro_presentation.sort_values(by="Mahalle Adı").reset_index(drop=True)
    
    # Yan yana göster
    col_macro_left, col_macro_right = st.columns([1, 1])
    
    with col_macro_left:
        st.markdown("#### 🗺️ Sultanbeyli Mevcut Konteyner Haritası")
        st.markdown("İlçe genelindeki 12 mevcut konteyner kırmızı işaretçilerle (red markers) gösterilmektedir:")
        
        sultanbeyli_center = [40.966, 29.268]
        macro_map = folium.Map(location=sultanbeyli_center, zoom_start=12)
        
        for _, r in df_mevcut.iterrows():
            folium.Marker(
                location=[r["enlem"], r["boylam"]],
                popup=f"Mevcut Konteyner - {r['mahalle']}",
                icon=folium.Icon(color="red", icon="home")
            ).add_to(macro_map)
            
        import streamlit_folium as sf
        sf.st_folium(macro_map, height=400, use_container_width=True, key="macro_district_map")
        
    with col_macro_right:
        st.markdown("#### 📊 Mahalle Bazlı Makro Göstergeler")
        st.markdown("Sultanbeyli ilçesindeki tüm mahallelerin temel demografi, afet risk ve mevcut konteyner durumları:")
        st.dataframe(
            df_macro_presentation, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Gece Nüfusu (2024)": st.column_config.NumberColumn(format="%d"),
                "Deprem Risk Skoru (İBB)": st.column_config.NumberColumn(format="%.2f"),
                "Barınma İhtiyacı (Hane)": st.column_config.NumberColumn(format="%d"),
                "Mevcut Konteyner Sayısı": st.column_config.NumberColumn(format="%d")
            }
        )
        
    st.markdown("---")
    
    # ----------------------------------------------------
    # MİKRO DETAY GÖRÜNÜMÜ (SEÇİLEN MAHALLE)
    # ----------------------------------------------------
    st.markdown("### 🔍 Mahalle Detay Analizi (Mikro Görünüm)")
    st.markdown("Spesifik bir mahalleyi seçerek o mahalledeki tüm aday alanları ve mevcut konteynerleri detaylı olarak inceleyebilirsiniz.")
    
    mahalle_listesi = sorted(df_nuf["mahalle"].unique())
    selected_mah = st.selectbox("İncelemek istediğiniz mahalleyi seçin:", mahalle_listesi)
    
    if selected_mah:
        norm_selected = norm_mahalle(selected_mah)
        
        # Filtrele
        r_row = df_risk[df_risk["mahalle_norm"] == norm_selected]
        n_row = df_nuf[df_nuf["mahalle_norm"] == norm_selected]
        b_row = df_bar[df_bar["mahalle_norm"] == norm_selected]
        
        risk_val = r_row["risk_score"].values[0] if not r_row.empty else 0.0
        nuf_val = n_row["nufus_2024"].values[0] if not n_row.empty else 0.0
        bar_val = b_row["hane_ihtiyaci"].values[0] if not b_row.empty else 0.0
        
        # Aday konteynerleri bul
        adaylar["Mahalle_norm"] = adaylar["Mahalle"].apply(norm_mahalle)
        mah_adaylar = adaylar[adaylar["Mahalle_norm"] == norm_selected]
        
        # Mevcut konteynerleri bul
        mah_mevcut = df_mevcut[df_mevcut["mahalle_norm"] == norm_selected]
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.subheader("📊 Mahalle Demografi ve Afet Risk Göstergeleri")
            st.markdown(f"<div class='glass-card'>", unsafe_allow_html=True)
            
            c_d1, c_d2 = st.columns(2)
            c_d1.metric("Gece Nüfusu (2024)", f"{nuf_val:,.0f}")
            c_d2.metric("Deprem Risk Skoru (İBB)", f"{risk_val:.2f}")
            
            c_d3, c_d4 = st.columns(2)
            c_d3.metric("Barınma İhtiyacı (Hane)", f"{bar_val:,.0f}")
            c_d4.metric("Mevcut Konteyner Sayısı", len(mah_mevcut))
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("##### 📍 Mahalle Aday Konteyner Parselleri")
            if not mah_adaylar.empty:
                st.dataframe(mah_adaylar[["S_No", "Alan_Adi", "Enlem", "Boylam", "p_access_road"]], use_container_width=True, hide_index=True)
            else:
                st.info("Bu mahallede aday konteyner parseli bulunmamaktadır.")
                
        with col_m2:
            st.subheader("🗺️ Mahalle Konteyner Yerleşim Haritası")
            # Aday ve mevcutları folium haritasında çiz
            if not mah_adaylar.empty:
                m_center = [mah_adaylar["Enlem"].mean(), mah_adaylar["Boylam"].mean()]
            elif not mah_mevcut.empty:
                m_center = [mah_mevcut["enlem"].mean(), mah_mevcut["boylam"].mean()]
            else:
                m_center = [40.966, 29.268]
                
            m_folium = folium.Map(location=m_center, zoom_start=14)
            
            # Adayları çiz (Mavi Marker)
            for _, r in mah_adaylar.iterrows():
                folium.Marker(
                    location=[r["Enlem"], r["Boylam"]],
                    popup=f"Aday No: {r['S_No']} - {r['Alan_Adi']}",
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(m_folium)
                
            # Mevcutları çiz (Kırmızı Marker)
            for _, r in mah_mevcut.iterrows():
                folium.Marker(
                    location=[r["enlem"], r["boylam"]],
                    popup=f"Mevcut Konteyner - {r['mahalle']}",
                    icon=folium.Icon(color="red", icon="home")
                ).add_to(m_folium)
                
            import streamlit_folium as sf
            sf.st_folium(m_folium, height=400, use_container_width=True, key=f"micro_map_{norm_selected}")



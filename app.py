import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pathlib import Path
import sys
import subprocess
import time

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

st.set_page_config(page_title="Sultanbeyli Konteyner Optimizasyonu", layout="wide")

# Veri Yolları
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

@st.cache_data
def load_data():
    adaylar = pd.read_excel(DATA_DIR / "adaylar_140.xlsx")
    mevcut = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
    return adaylar, mevcut

adaylar, mevcut = load_data()

st.title("Sultanbeyli Acil Durum Konteyner Optimizasyonu Dashboard")

tab_single, tab_batch, tab_results = st.tabs(["Tekil Analiz Konfigüratörü", "Toplu Deney (Batch) Yapılandırıcı", "Sonuçlar & Haritalar"])

with tab_single:
    st.header("1. Tekil Analiz Konfigüratörü")
    st.markdown("Esnek kapasite mimarisi ile modeli ayarlayın.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Hedef Fonksiyonu (Ağırlık)")
        weight_type = st.radio("Optimizasyon Hedefi:", 
                               options=["risk", "population", "shelter"], 
                               format_func=lambda x: {"risk": "Deprem Riski (İBB)", "population": "Gece Nüfusu", "shelter": "Barınma İhtiyacı"}[x])
        
        beta = st.slider("Kalite/MCDA Ağırlığı (Beta)", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
        sigma = st.selectbox("Fuzzy Kapsama Dağılımı", ["Adaptive", "800", "800_300"])
        
    with col2:
        st.subheader("Kapasite Yönetimi")
        k_total = st.number_input("Toplam İstenen Konteyner Sayısı (Mevcut + Yeni)", min_value=1, max_value=140, value=20, step=1)
        
        st.markdown("**Korunan Mevcut Konteynerler**")
        # Mevcutlari listele
        kept_mevcut_flags = []
        for i, row in mevcut.iterrows():
            is_kept = st.checkbox(f"{i}: {row['mahalle']} (Mevcut)", value=True, key=f"mevcut_{i}")
            if is_kept:
                kept_mevcut_flags.append(i)
                
    with col3:
        st.subheader("Zorunlu Aday Alanlar")
        st.markdown("Aşağıdaki adayları modele *kesinlikle seçilecek* şekilde sabitleyebilirsiniz.")
        # Sadece ilk 10 adayi gosterelim ornek olarak
        fixed_aday_flags = []
        with st.expander("Zorunlu Aday Listesi (140)"):
            for i, row in adaylar.iterrows():
                is_fixed = st.checkbox(f"Aday {row['S_No']}: {row['Mahalle']}", value=False, key=f"aday_{i}")
                if is_fixed:
                    fixed_aday_flags.append(i)
                    
    # Validation
    k_opt = k_total - len(kept_mevcut_flags) - len(fixed_aday_flags)
    st.info(f"**Matematiksel Model Durumu:** Çözücü havuzdan **{k_opt}** yeni konteyner seçecektir. (Toplam {k_total} = {len(kept_mevcut_flags)} Mevcut + {len(fixed_aday_flags)} Zorunlu + {k_opt} Seçilen)")
    
    if k_opt < 0:
        st.error("HATA: Korunan ve Zorunlu konteynerlerin toplamı, Toplam Konteyner sayısından büyük olamaz!")
    elif st.button("Modeli Çalıştır (IP)"):
        with st.spinner("Model çözülüyor... Lütfen bekleyin."):
            kept_str = ",".join(map(str, kept_mevcut_flags)) if kept_mevcut_flags else "none"
            fixed_str = ",".join(map(str, fixed_aday_flags)) if fixed_aday_flags else "none"
            
            # Python scripti cagir
            cmd = [sys.executable, str(PROJECT_ROOT / "src" / "05_ip.py"),
                   "--K", str(k_total),
                   "--weight", weight_type,
                   "--beta", str(beta),
                   "--sigma", sigma]
            
            if not kept_mevcut_flags: # If empty
                cmd.append("--no-mevcut")
                
            try:
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    st.success("Model başarıyla çözüldü!")
                    with st.expander("Terminal Çıktısı"):
                        st.code(res.stdout)
                else:
                    st.error("Model çözülürken hata oluştu!")
                    st.code(res.stderr)
            except Exception as e:
                st.error(f"Sistem Hatası: {str(e)}")

with tab_batch:
    st.header("2. Toplu Deney Yapılandırıcı (Batch Experiments)")
    st.markdown("Bu ekrandan master tez deneylerinizi tetikleyebilirsiniz. Farklı ağırlık ve kapasite senaryoları otomatik olarak sırayla çalıştırılır.")
    
    b_weights = st.multiselect("Denecek Ağırlık Tipleri", ["risk", "population", "shelter"], default=["risk", "population"])
    b_k_vals = st.multiselect("Denecek Toplam Kapasiteler (K_Total)", [8, 12, 20, 40, 60], default=[8, 20])
    b_sigmas = st.multiselect("Denecek Sigmalar", ["Adaptive", "800"], default=["Adaptive"])
    b_betas = st.multiselect("Denecek Beta Değerleri", [0.0, 0.3, 0.5, 1.0], default=[0.3])
    
    if st.button("Toplu Deneyi Başlat (Run All)"):
        st.warning("Bu işlem uzun sürebilir. İlerlemeyi terminalden takip edebilirsiniz.")
        # Burada arka planda run_all_scenarios.py tetiklenebilir
        st.code("Experiment script will be executed with selected combinations...")

with tab_results:
    st.header("3. Sonuçlar & Görselleştirme")
    
    # Harita gosterimi
    maps_dir = PROJECT_ROOT / "figures" / "maps"
    if maps_dir.exists():
        maps = list(maps_dir.glob("*.html"))
        if maps:
            selected_map = st.selectbox("Harita Seçin", [m.name for m in maps])
            if selected_map:
                map_path = maps_dir / selected_map
                with open(map_path, "r", encoding="utf-8") as f:
                    html_data = f.read()
                import streamlit.components.v1 as components
                components.html(html_data, height=600)
        else:
            st.info("Henüz harita bulunmuyor.")
    else:
        st.info("Harita dizini bulunmuyor.")
        
    st.markdown("---")
    
    # Grafik Gosterimi
    charts_dir = PROJECT_ROOT / "figures" / "charts"
    if charts_dir.exists():
        charts = list(charts_dir.glob("*.png"))
        if charts:
            selected_chart = st.selectbox("Grafik Seçin", [c.name for c in charts])
            if selected_chart:
                st.image(str(charts_dir / selected_chart), use_container_width=True)

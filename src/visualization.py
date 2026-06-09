# -*- coding: utf-8 -*-
"""
visualization.py

Harita (Folium) ve Grafik (Matplotlib/Seaborn) motorlarının standartlaştırıldığı modül.
Streamlit dashboard ve raporlama scriptleri tarafından ortak kullanılır.
"""

import json
import functools
import folium
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from config import norm_mahalle

# Plot style — seaborn-v0_8-* deprecated in seaborn >= 0.12
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except ValueError:
    plt.style.use("seaborn-whitegrid")
sns.set_context("paper", font_scale=1.2)


@functools.lru_cache(maxsize=1)
def _load_geojson() -> dict | None:
    """Load and cache the Sultanbeyli neighbourhood GeoJSON (static file)."""
    geojson_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "sultanbeyli_mahalleler_clean.geojson"
    if not geojson_path.exists():
        return None
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_color(val: float) -> str:
    """Kapsama seviyesine göre kırmızıdan yeşile renk gradyanı döndürür (0.50 hedef eşik)."""
    # 0.50 ve üzeri tam yeşil, 0.25 sarı, 0.0 tam kırmızı
    v = max(0.0, min(0.5, val)) / 0.5  # 0.0 - 1.0 aralığına normalleştir
    if v < 0.5:
        # Kırmızı -> Sarı gradyanı
        r = 255
        g = int(255 * (v / 0.5))
        b = 0
    else:
        # Sarı -> Yeşil gradyanı
        r = int(255 * (1.0 - (v - 0.5) / 0.5))
        g = 255
        b = 0
    return f"#{r:02x}{g:02x}{b:02x}"

def plot_solution_map(selected_df: pd.DataFrame, 
                      kept_df: pd.DataFrame, 
                      removed_df: pd.DataFrame, 
                      fixed_df: pd.DataFrame, 
                      out_path: Path | str, 
                      title: str = "Konteyner Yerleşim Planı",
                      cov_df: pd.DataFrame = None,
                      sigma: int = 800):
    """
    Folium kullanarak interaktif çözüm haritası oluşturur. 
    Eğer cov_df verilmişse mahalle sınırlarını ve kapsama ısı haritasını (Choropleth) overlay eder.
    """
    m = folium.Map(location=[40.97, 29.27], zoom_start=13, tiles="CartoDB positron")
    
    # 0. Mahalle Sınırları ve Kapsama Isı Haritası (Choropleth)
    if cov_df is not None and not cov_df.empty:
        geojson_data = _load_geojson()
        if geojson_data is not None:
            import copy
            geojson_data = copy.deepcopy(geojson_data)
            
            # Kapsama değerlerini haritala
            cov_df_copy = cov_df.copy()
            cov_df_copy["mahalle_norm"] = cov_df_copy["mahalle"].apply(norm_mahalle)
            cov_dict = cov_df_copy.set_index("mahalle_norm")["toplam_kapsama"].to_dict()
            
            # GeoJSON özelliklerine kapsama yüzdesini ekle
            for feature in geojson_data["features"]:
                mah = feature["properties"]["mahalle"]
                val = cov_dict.get(mah, 0.0)
                feature["properties"]["coverage_pct"] = f"%{val*100:.1f}"
                
            def style_function(feature):
                mah = feature["properties"]["mahalle"]
                val = cov_dict.get(mah, 0.0)
                color = get_color(val)
                return {
                    "fillColor": color,
                    "color": "#7f8c8d",  # Kenarlık rengi (gri)
                    "weight": 1.5,
                    "fillOpacity": 0.25
                }
                
            def highlight_function(feature):
                return {
                    "weight": 3,
                    "color": "#2c3e50",
                    "fillOpacity": 0.4
                }
                
            # GeoJson katmanını ekle
            geojson_layer = folium.GeoJson(
                geojson_data,
                style_function=style_function,
                highlight_function=highlight_function,
                tooltip=folium.GeoJsonTooltip(
                    fields=["mahalle", "coverage_pct"],
                    aliases=["Mahalle:", "Kapsama Oranı:"],
                    localize=True,
                    sticky=False,
                    labels=True,
                    style="""
                        background-color: #F0F2F6;
                        border: 2px solid #31333F;
                        border-radius: 3px;
                        font-family: sans-serif;
                        font-size: 12px;
                        padding: 8px;
                    """
                )
            )
            geojson_layer.add_to(m)

    # 1. Kaldırılan Mevcutlar (Gri, küçük)
    if not removed_df.empty:
        for _, r in removed_df.iterrows():
            folium.Marker(
                location=[r["enlem"], r["boylam"]],
                popup=f"İPTAL EDİLEN Mevcut Konteyner<br>Mahalle: {r['mahalle']}",
                icon=folium.Icon(color="lightgray", icon="remove-sign"),
                tooltip="İptal Edildi"
            ).add_to(m)

    # 2. Korunan Mevcutlar (Yeşil)
    if not kept_df.empty:
        for _, r in kept_df.iterrows():
            folium.Marker(
                location=[r["enlem"], r["boylam"]],
                popup=f"KORUNAN Mevcut Konteyner<br>Mahalle: {r['mahalle']}",
                icon=folium.Icon(color="green", icon="info-sign"),
                tooltip="Korunan Mevcut"
            ).add_to(m)
            
            # Etki Alanı (Mevcut) - Adaptif Sigma yarıçapı ile
            folium.Circle(
                location=[r["enlem"], r["boylam"]],
                radius=sigma, color="green", fill=True, fill_opacity=0.04, weight=1
            ).add_to(m)

    # 3. Zorunlu Adaylar (Mavi)
    if not fixed_df.empty:
        for _, r in fixed_df.iterrows():
            folium.Marker(
                location=[r["Enlem"], r["Boylam"]],
                popup=f"ZORUNLU Seçilen Aday<br>Mahalle: {r['Mahalle']}",
                icon=folium.Icon(color="blue", icon="pushpin"),
                tooltip="Zorunlu Aday"
            ).add_to(m)
            
            folium.Circle(
                location=[r["Enlem"], r["Boylam"]],
                radius=sigma, color="blue", fill=True, fill_opacity=0.04, weight=1
            ).add_to(m)

    # 4. Yeni Seçilen Adaylar (Kırmızı)
    if not selected_df.empty:
        for _, r in selected_df.iterrows():
            # Eğer zaten fixed_df içindeyse atla
            if not fixed_df.empty and r["S_No"] in fixed_df["S_No"].values:
                continue
                
            folium.Marker(
                location=[r["Enlem"], r["Boylam"]],
                popup=f"YENİ Seçilen Konteyner (No: {int(r['S_No'])})<br>Mahalle: {r['Mahalle']}",
                icon=folium.Icon(color="red", icon="star"),
                tooltip=f"Yeni Seçilen: {int(r['S_No'])}"
            ).add_to(m)
            
            folium.Circle(
                location=[r["Enlem"], r["Boylam"]],
                radius=sigma, color="red", fill=True, fill_opacity=0.08, weight=1
            ).add_to(m)
            
    title_html = f'''<h3 align="center" style="font-size:16px; margin-top:10px;"><b>{title}</b></h3>'''
    m.get_root().html.add_child(folium.Element(title_html))
    
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out_p))
    return m


def plot_coverage_bar(mahalleler: list, 
                      coverage_vals: list, 
                      target_vals: list, 
                      target_label: str,
                      out_path: Path | str, 
                      title: str = "Mahalle Kapsama vs İhtiyaç"):
    """
    Mahalle bazlı kapsama oranlarını hedeflenen risk veya nüfus ile karşılaştıran bar grafiği.
    """
    df = pd.DataFrame({
        "Mahalle": mahalleler,
        "Kapsama": coverage_vals,
        target_label: target_vals
    })
    
    # Hedef değişkene göre sırala (azalan)
    df = df.sort_values(by=target_label, ascending=False).reset_index(drop=True)
    
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    x = np.arange(len(df))
    width = 0.35
    
    ax1.bar(x - width/2, df[target_label], width, color='#3498db', label=f'İhtiyaç ({target_label})')
    ax1.set_xlabel('Mahalleler', fontweight='bold')
    ax1.set_ylabel(f'İhtiyaç Değeri ({target_label})', color='#3498db', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#3498db')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df["Mahalle"], rotation=45, ha="right")
    
    ax2 = ax1.twinx()
    ax2.bar(x + width/2, df["Kapsama"], width, color='#e74c3c', label='Kapsama (Coverage)')
    ax2.set_ylabel('Kapsama (Fuzzy Üyelik Toplamı)', color='#e74c3c', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#e74c3c')
    
    # Eşik çizgisi (Örn: 0.5 minimum kapsama)
    ax2.axhline(y=0.5, color='gray', linestyle='--', alpha=0.7, label="Minimum Eşik (0.5)")
    
    plt.title(title, fontweight='bold', fontsize=14)
    fig.tight_layout()
    
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out_p), dpi=300, bbox_inches='tight')
    plt.close()


def plot_lorenz_curve(values: np.ndarray, 
                      out_path: Path | str, 
                      title: str = "Lorenz Eğrisi (Kapsama Dağılımı Adaleti)"):
    """
    Kapsama vektörü için Lorenz Eğrisi çizer ve Gini katsayısını hesaplayıp döndürür.
    """
    vals = np.sort(values)
    n = len(vals)
    
    # Gini Katsayısı
    sum_diffs = np.sum(np.abs(vals[:, None] - vals[None, :]))
    denom = 2 * n * np.sum(vals)
    gini_coef = sum_diffs / denom if denom > 0 else 0.0
    
    cum_vals = np.cumsum(vals)
    cum_share = cum_vals / cum_vals[-1] if cum_vals[-1] > 0 else np.zeros_like(vals)
    
    # Başlangıç noktası (0,0) ekleme
    x_lorenz = np.linspace(0, 1, n + 1)
    y_lorenz = np.insert(cum_share, 0, 0.0)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Mükemmel Eşitlik Çizgisi
    ax.plot([0, 1], [0, 1], color='#7f8c8d', linestyle='--', label='Mükemmel Eşitlik Çizgisi (45°)')
    
    # Lorenz Eğrisi
    ax.plot(x_lorenz, y_lorenz, color='#e67e22', marker='o', markersize=4, linewidth=2, label=f'Mevcut Dağılım (Gini: {gini_coef:.3f})')
    
    # Eşitlik alanı doldurma
    ax.fill_between(x_lorenz, x_lorenz, y_lorenz, color='#e67e22', alpha=0.15)
    
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("Kümülatif Mahalle Oranı", fontweight='bold')
    ax.set_ylabel("Kümülatif Kapsama Oranı", fontweight='bold')
    ax.set_title(title, fontweight='bold', fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out_p), dpi=300, bbox_inches='tight')
    plt.close()
    return gini_coef


def compute_gini(values: np.ndarray) -> float:
    """Compute Gini coefficient without generating a plot."""
    vals = np.sort(values)
    n = len(vals)
    if n == 0 or np.sum(vals) == 0:
        return 0.0
    sum_diffs = np.sum(np.abs(vals[:, None] - vals[None, :]))
    denom = 2 * n * np.sum(vals)
    return float(sum_diffs / denom) if denom > 0 else 0.0

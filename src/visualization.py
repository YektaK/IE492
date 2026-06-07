# -*- coding: utf-8 -*-
"""
visualization.py

Harita (Folium) ve Grafik (Matplotlib/Seaborn) motorlarının standartlaştırıldığı modül.
Streamlit dashboard ve raporlama scriptleri tarafından ortak kullanılır.
"""

import folium
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Plot style
plt.style.use("seaborn-v0_8-whitegrid")
sns.set_context("paper", font_scale=1.2)

def plot_solution_map(selected_df: pd.DataFrame, 
                      kept_df: pd.DataFrame, 
                      removed_df: pd.DataFrame, 
                      fixed_df: pd.DataFrame, 
                      out_path: Path | str, 
                      title: str = "Konteyner Yerleşim Planı"):
    """
    Folium kullanarak interaktif çözüm haritası oluşturur.
    """
    m = folium.Map(location=[40.97, 29.27], zoom_start=13, tiles="CartoDB positron")
    
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
            
            # Etki Alanı (Mevcut)
            folium.Circle(
                location=[r["enlem"], r["boylam"]],
                radius=800, color="green", fill=True, fill_opacity=0.05, weight=1
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
                radius=800, color="blue", fill=True, fill_opacity=0.05, weight=1
            ).add_to(m)

    # 4. Yeni Seçilen Adaylar (Kırmızı)
    if not selected_df.empty:
        # Zorunlu adaylar selected_df içinde de olabilir, çakışmayı önlemek için id bazlı filtre yapabiliriz
        # Şimdilik direkt ekliyoruz.
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
                radius=800, color="red", fill=True, fill_opacity=0.1, weight=1
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

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx

# Proje yollarını ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_DIR, RESULTS_DIR, norm_mahalle
from scenario_utils import haversine_m

def main():
    print("[1/4] Sultanbeyli yol agi indiriliyor (osmnx)...")
    try:
        # Sultanbeyli yürüyüş ağını indir
        G = ox.graph_from_place("Sultanbeyli, Istanbul, Turkey", network_type="walk")
        print("  [+] Yol agi basariyla indirildi.")
    except Exception as e:
        print(f"  [-] Yol agi indirilirken hata: {e}")
        print("  [-] Lutfen internet baglantinizi kontrol edin.")
        sys.exit(1)
        
    # Verileri oku
    adaylar = pd.read_excel(DATA_DIR / "adaylar_140.xlsx")
    mevcut = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
    centroids = pd.read_excel(DATA_DIR / "mahalle_centroids.xlsx")
    p_road = pd.read_excel(DATA_DIR / "p_road_open.xlsx")
    
    centroids["mahalle_norm"] = centroids["mahalle"].apply(norm_mahalle)
    p_road["mahalle_norm"] = p_road["mahalle"].apply(norm_mahalle)
    
    ana_mahalleler = sorted(
        m for m in p_road["mahalle_norm"].unique()
        if "DEVLET ORMANI" not in m and "TEPE ORMANI" not in m
    )
    
    centroids_clean = centroids.drop_duplicates(subset=["mahalle_norm"], keep="first").set_index("mahalle_norm")
    
    mahalle_lat = centroids_clean.loc[ana_mahalleler, "lat"].values
    mahalle_lon = centroids_clean.loc[ana_mahalleler, "lon"].values
    
    aday_lat = adaylar["Enlem"].values
    aday_lon = adaylar["Boylam"].values
    
    mevcut_lat = mevcut["enlem"].values
    mevcut_lon = mevcut["boylam"].values
    
    print("[2/4] Noktalarin en yakin yol dugumleri (nodes) bulunuyor...")
    # Centroid, aday ve mevcutların en yakın yol düğümlerini bul
    centroid_nodes = [ox.nearest_nodes(G, lon, lat) for lat, lon in zip(mahalle_lat, mahalle_lon)]
    aday_nodes = [ox.nearest_nodes(G, lon, lat) for lat, lon in zip(aday_lat, aday_lon)]
    mevcut_nodes = [ox.nearest_nodes(G, lon, lat) for lat, lon in zip(mevcut_lat, mevcut_lon)]
    
    print("[3/4] Yol agi uzerinden en kisa mesafeler hesaplaniyor (Dijkstra)...")
    
    D_aday = np.zeros((len(adaylar), len(ana_mahalleler)))
    D_mevcut = np.zeros((len(mevcut), len(ana_mahalleler)))
    
    # Adaylar için mesafe matrisi
    for i, a_node in enumerate(aday_nodes):
        for j, c_node in enumerate(centroid_nodes):
            try:
                dist = nx.shortest_path_length(G, a_node, c_node, weight="length")
                # Eğer yol mesafesi haversine'den çok çok farklı veya mantıksızsa / izole ise fallback yap
                hav = haversine_m(aday_lat[i], aday_lon[i], mahalle_lat[j], mahalle_lon[j])
                # Yol mesafesi kuş uçuşunun en az 1 katı olmalıdır. Bağlantı yoksa veya aşırı uzunsa fallback.
                if dist < hav or dist > hav * 5.0:
                    dist = hav * 1.30 # Yüzde 30 dolambaçlılık faktörü
            except nx.NetworkXNoPath:
                # Bağlantı yoksa Haversine + %30 dolambaçlılık payı kullan
                dist = haversine_m(aday_lat[i], aday_lon[i], mahalle_lat[j], mahalle_lon[j]) * 1.30
            D_aday[i, j] = dist
            
    # Mevcutlar için mesafe matrisi
    for i, m_node in enumerate(mevcut_nodes):
        for j, c_node in enumerate(centroid_nodes):
            try:
                dist = nx.shortest_path_length(G, m_node, c_node, weight="length")
                hav = haversine_m(mevcut_lat[i], mevcut_lon[i], mahalle_lat[j], mahalle_lon[j])
                if dist < hav or dist > hav * 5.0:
                    dist = hav * 1.30
            except nx.NetworkXNoPath:
                dist = haversine_m(mevcut_lat[i], mevcut_lon[i], mahalle_lat[j], mahalle_lon[j]) * 1.30
            D_mevcut[i, j] = dist
            
    print("[4/4] Mesafe matrisleri Excel formatinda kaydediliyor...")
    FUZZY_COV_DIR = RESULTS_DIR / "fuzzy_coverage"
    FUZZY_COV_DIR.mkdir(parents=True, exist_ok=True)
    
    # DataFrame'e dönüştür ve kaydet
    df_aday = pd.DataFrame(D_aday, columns=ana_mahalleler)
    df_aday.insert(0, "S_No", adaylar["S_No"])
    df_aday.to_excel(FUZZY_COV_DIR / "distance_road_aday_140x17.xlsx", index=False)
    
    df_mev = pd.DataFrame(D_mevcut, columns=ana_mahalleler)
    df_mev.insert(0, "container_no", mevcut["container_no"])
    df_mev.to_excel(FUZZY_COV_DIR / "distance_road_mevcut_12x17.xlsx", index=False)
    
    print("  [+] distance_road_aday_140x17.xlsx kaydedildi.")
    print("  [+] distance_road_mevcut_12x17.xlsx kaydedildi.")
    print("== Yol agi hesaplama basariyla tamamlandi! ==")

if __name__ == "__main__":
    main()

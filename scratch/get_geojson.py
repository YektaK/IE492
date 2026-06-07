import osmnx as ox
import json
from pathlib import Path

try:
    print("Fetching boundaries from OSM...")
    # admin_level 10 in Turkey corresponds to Mahalle (neighborhood) boundaries
    gdf = ox.features_from_place("Sultanbeyli, Istanbul, Turkey", tags={"boundary": "administrative", "admin_level": "10"})
    print(f"Success! Found {len(gdf)} boundaries.")
    
    # Select columns and clean up
    gdf_clean = gdf[["name", "geometry"]].copy()
    
    # Save as GeoJSON
    out_dir = Path("d:/IE492/data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sultanbeyli_mahalleler.geojson"
    
    gdf_clean.to_file(out_path, driver="GeoJSON")
    print(f"Saved to {out_path}")
except Exception as e:
    print(f"Error occurred: {e}")

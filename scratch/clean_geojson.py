import geopandas as gpd
from pathlib import Path
import sys

# Add src to path to use norm_mahalle
sys.path.insert(0, "d:/IE492/src")
from config import norm_mahalle

# Read raw geojson
gdf = gpd.read_file("d:/IE492/data/processed/sultanbeyli_mahalleler.geojson")

# Clean neighborhood names
def clean_osm_name(name):
    if not name or not isinstance(name, str):
        return None
    # Remove " Mahallesi" suffix
    if name.endswith(" Mahallesi"):
        name = name[:-10]
    return norm_mahalle(name)

gdf["mahalle_norm"] = gdf["name"].apply(clean_osm_name)

# List of neighborhoods in our dataset
dataset_mahalles = [
    'ABDURRAHMANGAZI', 'ADIL', 'AHMET YESEVI', 'AKSEMSETTIN', 'BATTALGAZI',
    'FATIH', 'HAMIDIYE', 'HASANPASA', 'MECIDIYE', 'MEHMET AKIF',
    'MIMAR SINAN', 'NECIP FAZIL', 'ORHANGAZI', 'TURGUT REIS', 'YAVUZ SELIM'
]

# Filter
gdf_filtered = gdf[gdf["mahalle_norm"].isin(dataset_mahalles)].copy()

# Keep only necessary columns
gdf_filtered = gdf_filtered[["mahalle_norm", "geometry"]]
gdf_filtered = gdf_filtered.rename(columns={"mahalle_norm": "mahalle"})

# Drop duplicates if any (due to OSM way/node differences)
gdf_filtered = gdf_filtered.drop_duplicates(subset=["mahalle"])

print(f"Filtered to {len(gdf_filtered)} neighborhoods.")
print("Neighborhoods in clean GeoJSON:")
print(gdf_filtered["mahalle"].tolist())

# Save clean GeoJSON
out_path = Path("d:/IE492/data/processed/sultanbeyli_mahalleler_clean.geojson")
gdf_filtered.to_file(out_path, driver="GeoJSON")
print(f"Saved to {out_path}")

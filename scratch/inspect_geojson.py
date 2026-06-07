import geopandas as gpd

gdf = gpd.read_file("d:/IE492/data/processed/sultanbeyli_mahalleler.geojson")
print(f"Columns: {gdf.columns}")
print(f"Total features: {len(gdf)}")
print("Unique names:")
print(gdf["name"].dropna().unique())

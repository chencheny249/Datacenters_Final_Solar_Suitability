import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np
import os

# 1. Configuration
# Bounding box for Boulder County area
lat_min, lat_max = 39.91, 40.26
lon_min, lon_max = -105.62, -105.05
grid_size_degree = 0.036  # Roughly 4km in decimal degrees

output_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\boulder_grid.geojson'

# 2. Generate Grid Cells
cols = np.arange(lon_min, lon_max, grid_size_degree)
rows = np.arange(lat_min, lat_max, grid_size_degree)

polygons = []
tile_ids = []
counter = 0

for lat in rows:
    for lon in cols:
        # Create a square polygon
        polygons.append(Polygon([
            (lon, lat),
            (lon + grid_size_degree, lat),
            (lon + grid_size_degree, lat + grid_size_degree),
            (lon, lat + grid_size_degree)
        ]))
        tile_ids.append(f"TILE_{counter:03d}")
        counter += 1

# 3. Create GeoDataFrame
grid = gpd.GeoDataFrame({'tile_id': tile_ids, 'geometry': polygons}, crs="EPSG:4326")

# 4. Save the grid
os.makedirs(os.path.dirname(output_path), exist_ok=True)
grid.to_file(output_path, driver='GeoJSON')

print(f"--- SUCCESS ---")
print(f"Created {len(grid)} tiles of 4km x 4km.")
print(f"Grid saved to: {output_path}")
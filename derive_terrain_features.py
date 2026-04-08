import rasterio
import rasterio.mask
import geopandas as gpd
import numpy as np
import pandas as pd
import os

# 1. Paths
dem_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\n40w106.hgts'
grid_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\boulder_grid.geojson'
output_csv = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\terrain_features.csv'

grid = gpd.read_file(grid_path)
terrain_results = []

with rasterio.open(dem_path) as src:
    print(f"Processing {len(grid)} tiles...")
    
    for index, row in grid.iterrows():
        try:
            out_image, out_transform = rasterio.mask.mask(src, [row['geometry']], crop=True, nodata=np.nan)
            elevation = out_image[0].astype('float32')
            elevation[elevation <= 0] = np.nan # Handle data holes
            
            if np.isnan(elevation).all():
                continue

            # B. Calculate Slope
            res = 30.0
            dy, dx = np.gradient(elevation, res)
            slope = np.rad2deg(np.arctan(np.sqrt(dx**2 + dy**2)))
            
            # C. Calculate Aspect
            aspect = np.rad2deg(np.arctan2(-dx, dy)) % 360

            # D. ADDED: Ruggedness Metrics
            terrain_results.append({
                'tile_id': row['tile_id'],
                'mean_elevation': float(np.nanmean(elevation)),
                'std_elevation': float(np.nanstd(elevation)), # High std = high ruggedness
                'mean_slope': float(np.nanmean(slope)),
                'std_slope': float(np.nanstd(slope)),         # Variability in slope
                'mean_aspect': float(np.nanmean(aspect)),
                'max_slope': float(np.nanmax(slope))
            })

        except ValueError:
            continue # Skip non-overlapping tiles
            
        if index % 20 == 0:
            print(f"Processed through tile index {index}...")

# Save results
df = pd.DataFrame(terrain_results)
df.to_csv(output_csv, index=False)
print(f"\n--- SUCCESS ---")
print(f"Terrain features with ruggedness saved to {output_csv}")
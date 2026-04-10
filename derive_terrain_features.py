import rasterio
import rasterio.mask
import geopandas as gpd
import numpy as np
import pandas as pd
import os

# Dynamic path anchoring
project_name = "Datacenters_Final_Solar_Suitability"
current_path = os.path.abspath(__file__)

if project_name in current_path:
    base_dir = current_path.split(project_name)[0] + project_name
else:
    base_dir = os.path.dirname(current_path)

dem_path = os.path.join(base_dir, 'data','raw', 'n40w106.hgts')
grid_path = os.path.join(base_dir, 'processed', 'boulder_grid.geojson')
output_csv = os.path.join(base_dir, 'processed', 'terrain_features.csv')

os.makedirs(os.path.dirname(output_csv), exist_ok=True)

#read file
grid = gpd.read_file(grid_path)
terrain_results = []

# process tiles
with rasterio.open(dem_path) as src:
    print(f"Processing {len(grid)} tiles...")
    
    for index, row in grid.iterrows():
        try:
            # Mask DEM to tile polygon
            out_image, out_transform = rasterio.mask.mask(src, [row['geometry']], crop=True, nodata=np.nan)
            elevation = out_image[0].astype('float32')
            #deal with noData values
            elevation[elevation <= 0] = np.nan
            
            if np.isnan(elevation).all():
                continue

            # Calculate slope
            res = 30.0
            dy, dx = np.gradient(elevation, res)
            slope = np.rad2deg(np.arctan(np.sqrt(dx**2 + dy**2)))
            
            #Calculate aspect
            aspect = np.rad2deg(np.arctan2(-dx, dy)) % 360

            # Define ruggedness
            terrain_results.append({
                'tile_id': row['tile_id'],
                'mean_elevation': float(np.nanmean(elevation)),
                #High std = high ruggedness
                'std_elevation': float(np.nanstd(elevation)), 
                'mean_slope': float(np.nanmean(slope)),
                # Variability in slope = high ruggedness
                'std_slope': float(np.nanstd(slope)),         
                'mean_aspect': float(np.nanmean(aspect)),
                'max_slope': float(np.nanmax(slope))
            })
        # Skip non-overlapping tiles
        except ValueError:
            continue 
            
        if index % 20 == 0:
            print(f"Processed through tile index {index}...")

# Save results
df = pd.DataFrame(terrain_results)
df.to_csv(output_csv, index=False)
print(f"\n SUCCESS: Terrain features with ruggedness saved to {output_csv}")
import pandas as pd
import geopandas as gpd
import os

# 1. Paths
grid_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\boulder_grid.geojson'
terrain_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\terrain_features.csv'
solar_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\solar_averages.csv'
output_parquet = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\boulder_tiles.parquet'

# 2. Load Data
grid = gpd.read_file(grid_path)
terrain = pd.read_csv(terrain_path)
solar = pd.read_csv(solar_path)

# 3. Merge Terrain and perform Nearest Neighbor Join for Solar
# Link terrain features to the grid first
merged = grid.merge(terrain, on='tile_id', how='inner')

# Convert solar CSV to a GeoDataFrame
solar_gdf = gpd.GeoDataFrame(
    solar, 
    geometry=gpd.points_from_xy(solar['longitude'], solar['latitude']), 
    crs="EPSG:4326"
)

# NEAREST NEIGHBOR JOIN: This ensures NO BLANK SPOTS.
# For every terrain tile, find the nearest solar point.
final_df = gpd.sjoin_nearest(merged, solar_gdf, how="left", distance_col="dist")

# 4. ENHANCED SCORING LOGIC
# A. Normal Score Components
# Aspect: 180 (South) is best (1.0), 0/360 is worst (0.0)
final_df['aspect_score'] = 1 - (abs(final_df['mean_aspect'] - 180) / 180)

# Slope: Flat is best. We use 20 degrees as the limit for utility-scale solar
final_df['slope_score'] = final_df['mean_slope'].apply(lambda x: max(0, 1 - (x / 20)))

# Solar: Normalize based on the highest proxy GHI in the county
max_ghi = final_df['mean_ghi_proxy'].max()
final_df['solar_score'] = final_df['mean_ghi_proxy'] / max_ghi

# B. Ruggedness Penalty
# We penalize tiles that are internally too varied (mountainous) or too steep
final_df['rugged_penalty'] = 0
final_df.loc[final_df['std_elevation'] > 100, 'rugged_penalty'] += 20
final_df.loc[final_df['max_slope'] > 25, 'rugged_penalty'] += 30

# C. Weighted Calculation
# 40% Aspect, 30% Slope, 30% Radiation
final_df['suitability_score'] = (
    (final_df['aspect_score'] * 0.4) + 
    (final_df['slope_score'] * 0.3) + 
    (final_df['solar_score'] * 0.3)
) * 100 - final_df['rugged_penalty']

# Final Polish: Keep 0-100 range
final_df['suitability_score'] = final_df['suitability_score'].clip(0, 100)

# 5. Save
# Dropping the temporary join columns like 'dist' and 'index_right' before saving
final_df = final_df.drop(columns=['dist', 'index_right'], errors='ignore')
final_df.to_parquet(output_parquet)

print(f"--- SUCCESS ---")
print(f"Final Score computed with Ruggedness Penalty and No Blank Spots.")
print(final_df[['tile_id', 'suitability_score', 'rugged_penalty']].sort_values(by='suitability_score', ascending=False).head())


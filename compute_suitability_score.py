import pandas as pd
import geopandas as gpd
import os

# Dynamic path anchoring
project_name = "Datacenters_Final_Solar_Suitability"
current_path = os.path.abspath(__file__)

if project_name in current_path:
    base_dir = current_path.split(project_name)[0] + project_name
else:
    base_dir = os.getcwd()

grid_path = os.path.join(base_dir, 'processed', 'boulder_grid.geojson')
terrain_path = os.path.join(base_dir, 'processed', 'terrain_features.csv')
solar_path = os.path.join(base_dir, 'processed', 'solar_averages.csv')
output_parquet = os.path.join(base_dir, 'processed', 'boulder_tiles.parquet')

#Check path
for path in [grid_path, terrain_path, solar_path]:
    if not os.path.exists(path):
        print(f"ERROR: Missing required file at {path}")

# Load data
grid = gpd.read_file(grid_path)
terrain = pd.read_csv(terrain_path)
solar = pd.read_csv(solar_path)

# Link terrain features to grid, merge terrain, do nearest neighbor join for solar
merged = grid.merge(terrain, on='tile_id', how='inner')

# Convert solar CSV to GeoDataFrame
solar_gdf = gpd.GeoDataFrame(
    solar, 
    geometry=gpd.points_from_xy(solar['longitude'], solar['latitude']), 
    crs="EPSG:4326"
)

# For every terrain tile find the nearest solar point for NN join
final_df = gpd.sjoin_nearest(merged, solar_gdf, how="left", distance_col="dist")

# Scoring
# Aspect: 180 (South) is best (1.0), 0/360 is worst (0.0)
final_df['aspect_score'] = 1 - (abs(final_df['mean_aspect'] - 180) / 180)

# Slope: Flat is best. Set 20 deg as limit for utility-scale solar
final_df['slope_score'] = final_df['mean_slope'].apply(lambda x: max(0, 1 - (x / 20)))

# Solar: Normalize based on the highest proxy GHI in the county
max_ghi = final_df['mean_ghi_proxy'].max()
final_df['solar_score'] = final_df['mean_ghi_proxy'] / max_ghi

# Include ruggedness penalty - penalize tiles that are internally too varied/mtnous or steep
final_df['rugged_penalty'] = 0
final_df.loc[final_df['std_elevation'] > 100, 'rugged_penalty'] += 20
final_df.loc[final_df['max_slope'] > 25, 'rugged_penalty'] += 30

# Weighted calcs - 40% Aspect, 30% Slope, 30% Radiation
final_df['suitability_score'] = (
    (final_df['aspect_score'] * 0.4) + 
    (final_df['slope_score'] * 0.3) + 
    (final_df['solar_score'] * 0.3)
) * 100 - final_df['rugged_penalty']

# Clip to 0 to 100 range
final_df['suitability_score'] = final_df['suitability_score'].clip(0, 100)

# Drop unnecessary columns and save
final_df = final_df.drop(columns=['dist', 'index_right'], errors='ignore')
final_df.to_parquet(output_parquet)

print(f"Success! Final Score computed. Saved to {output_parquet}")
print(final_df[['tile_id', 'suitability_score', 'rugged_penalty']].sort_values(by='suitability_score', ascending=False).head())


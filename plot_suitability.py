import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os

# 1. Path to your file
parquet_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\boulder_tiles.parquet'

if not os.path.exists(parquet_path):
    print("Error: File not found.")
else:
    # 2. Load and Convert CRS
    # Contextily needs data in Web Mercator (EPSG:3857) to align with web maps
    gdf = gpd.read_parquet(parquet_path)
    gdf = gdf.to_crs(epsg=3857)

    # 3. Create the plot
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    
    # Plot the tiles with transparency (alpha) so you can see the map below
    gdf.plot(column='suitability_score', 
             ax=ax, 
             legend=True, 
             cmap='YlOrRd', 
             alpha=0.6,  # 60% transparency
             edgecolor='white', 
             linewidth=0.8,
             legend_kwds={'label': "Solar Suitability Score"})

    # 4. Add the Basemap
    # You can change source to ctx.providers.Esri.WorldImagery for satellite
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    # Clean up labels
    plt.title('Boulder County Solar Suitability Overlay', fontsize=18)
    ax.set_axis_off() # Hide lat/lon numbers for a cleaner look
    
    plt.show()
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os

# 1. Path to your file and output
parquet_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\boulder_tiles.parquet'
output_dir = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed'
output_filename = os.path.join(output_dir, 'suitability_map.png')

if not os.path.exists(parquet_path):
    print(f"Error: File not found at {parquet_path}")
else:
    # 2. Load and Convert CRS
    # Contextily needs Web Mercator (EPSG:3857)
    gdf = gpd.read_parquet(parquet_path)
    gdf = gdf.to_crs(epsg=3857)

    # 3. Create the plot
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    
    # Plot the tiles with transparency (alpha)
    gdf.plot(column='suitability_score', 
             ax=ax, 
             legend=True, 
             cmap='YlOrRd', 
             alpha=0.6, 
             edgecolor='white', 
             linewidth=0.8,
             legend_kwds={'label': "Solar Suitability Score"})

    # 4. Add the Basemap
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    # Clean up labels and title
    plt.title('Boulder County Solar Suitability Overlay', fontsize=18)
    ax.set_axis_off()
    
    # 5. Save the plot
    # bbox_inches='tight' ensures the legend doesn't get cut off
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"--- SUCCESS ---")
    print(f"Map successfully saved to: {output_filename}")

    # 6. Show the plot
    plt.show()
    
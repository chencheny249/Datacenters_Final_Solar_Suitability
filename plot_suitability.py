import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os

#Path
script_dir = os.path.dirname(os.path.abspath(__file__))

path_options = [
    os.path.join(script_dir, "processed", "boulder_tiles.parquet"),
    os.path.join(script_dir, "..", "processed", "boulder_tiles.parquet")
]

parquet_path = None
for path in path_options:
    if os.path.exists(path):
        parquet_path = path
        break

if not parquet_path:
    print(f"Error: Could not find boulder_tiles.parquet in {script_dir} or parent.")
    output_dir = os.path.join(script_dir, "processed")
else:
    output_dir = os.path.dirname(parquet_path)

output_filename = os.path.join(output_dir, 'suitability_map.png')


#parquet_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\boulder_tiles.parquet'
#output_dir = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed'
#output_filename = os.path.join(output_dir, 'suitability_map.png')

if not os.path.exists(parquet_path):
    print(f"Error: File not found at {parquet_path}")
else:
    #Load and Convert CRS (Contextily needs Web Mercator (EPSG:3857))
    gdf = gpd.read_parquet(parquet_path)
    gdf = gdf.to_crs(epsg=3857)

    # Create plot
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

    # Add Basemap
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    # Clean up
    plt.title('Boulder County Solar Suitability Overlay', fontsize=18)
    ax.set_axis_off()
    
    # save
    # bbox_inches='tight' so legend doesn't get cut off
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Map successfully saved to: {output_filename}")

    # Show plot
    plt.show()
    
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os

# Set paths so more general
project_name = "Datacenters_Final_Solar_Suitability"
full_path = os.path.abspath(__file__)

if project_name in full_path:
    # Slices path to stop right at your project folder
    base_dir = full_path.split(project_name)[0] + project_name
    file_path = os.path.join(base_dir, "data", "raw", "n40w106.hgts")
else:
    # Fallback if  folder name isn't found
    file_path = os.path.join("data", "raw", "n40w106.hgts")

print(f"Looking for file at: {file_path}")

#file_path = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\data\raw\n40w106.hgts'
#file_path = r'..\..\Datacenters_Final_Solar_Suitability\data\raw\n40w106.hgts' 



with rasterio.open(file_path) as src:
    # Read the elevation data
    elevation = src.read(1).astype('float32')
    
    # Handle NASA NoData values
    elevation[elevation < -1000] = np.nan
    
    # Get resolution (1 arc-second = roughly 30 meters)
    res = 30.0 

# Calculate Terrain Features
# dy is change in Latitude, dx is change in Longitude
dy, dx = np.gradient(elevation, res)

# Slope calc
slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
slope_deg = np.rad2deg(slope_rad)

# Aspect calc - use -dx bc Longitude increases East but Aspect measured from North
aspect_rad = np.arctan2(-dx, dy)
aspect_deg = np.rad2deg(aspect_rad) % 360

# Solar Suitability Logic
# Best: South-facing (150°-210°), relatively flat (< 15° slope)
suitable = (aspect_deg > 150) & (aspect_deg < 210) & (slope_deg < 15)

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

# Left: Elevation Map
im1 = ax1.imshow(elevation, cmap='terrain')
ax1.set_title("Boulder Elevation (DEM)")
plt.colorbar(im1, ax=ax1, label="Meters")

# Right: Suitable Areas
im2 = ax2.imshow(suitable, cmap='viridis')
ax2.set_title("Solar Suitability (South-Facing + Low Slope)")
plt.colorbar(im2, ax=ax2, label="1 = Suitable")

plt.tight_layout()
plt.show()

print(f"Max Elevation in tile: {np.nanmax(elevation):.2f}m")
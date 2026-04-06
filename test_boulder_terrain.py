import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 1. Load your HGT file
file_path = 'n40w106.hgts' 


with rasterio.open(file_path) as src:
    # Read the elevation data
    elevation = src.read(1).astype('float32')
    
    # Handle NASA NoData values
    elevation[elevation < -1000] = np.nan
    
    # Get resolution (1 arc-second is roughly 30 meters)
    res = 30.0 

# 2. Calculate Terrain Features using NumPy
# dy is change in Latitude, dx is change in Longitude
dy, dx = np.gradient(elevation, res)

# Slope: how steep the land is (in degrees)
slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
slope_deg = np.rad2deg(slope_rad)

# Aspect: which direction the slope faces (0=North, 180=South)
# We use -dx because Longitude increases East, but Aspect is measured from North
aspect_rad = np.arctan2(-dx, dy)
aspect_deg = np.rad2deg(aspect_rad) % 360

# 3. Solar Suitability Logic
# Ideal: South-facing (150°-210°) and relatively flat (< 15° slope)
suitable = (aspect_deg > 150) & (aspect_deg < 210) & (slope_deg < 15)

# 4. Visualize the Boulder Area
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

# Left: Elevation Map
im1 = ax1.imshow(elevation, cmap='terrain')
ax1.set_title("Boulder Elevation (DEM)")
plt.colorbar(im1, ax=ax1, label="Meters")

# Right: Suitable Areas (Yellow = Good)
im2 = ax2.imshow(suitable, cmap='viridis')
ax2.set_title("Solar Suitability (South-Facing + Low Slope)")
plt.colorbar(im2, ax=ax2, label="1 = Suitable")

plt.tight_layout()
plt.show()

print(f"Max Elevation in tile: {np.nanmax(elevation):.2f}m")
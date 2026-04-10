import pandas as pd
import glob
import os
import sys

# 1. Define where your solar CSVs are stored - USE THE RAW STRING 'r'
input_folder = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\data\raw\solar_raw'

#TODO 
input_folder = r'...\Datacenters_Final_Solar_Suitability\solar_raw'
output_file = r'C:\Users\chenc\Documents\Datacenters_Final_Solar_Suitability\processed\solar_averages.csv'

# Create the output directory immediately so Pandas doesn't complain
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# 2. Identify the CSV files
csv_files = glob.glob(os.path.join(input_folder, "*.csv"))

# --- SAFETY CHECK ---
if len(csv_files) == 0:
    print(f"!!! ERROR: No CSV files found in {input_folder}")
    print("Please check that:")
    print(f"1. The folder actually exists at: {os.path.abspath(input_folder)}")
    print("2. The files inside end in precisely '.csv' (not .csv.txt or .xlsx)")
    sys.exit() # Stop the script here
# --------------------

print(f"Found {len(csv_files)} solar files. Processing...")

solar_results = []

for file_path in csv_files:
    try:
        # Read only the first row to get location info
        metadata = pd.read_csv(file_path, nrows=1)
        lat = metadata['Latitude'].iloc[0]
        lon = metadata['Longitude'].iloc[0]
        elevation = metadata['Elevation'].iloc[0]

        # Skip the first 2 rows to get the data
        df = pd.read_csv(file_path, skiprows=2)

        avg_dni = df['DNI'].mean()
        avg_dhi = df['DHI'].mean()
        avg_temp = df['Temperature'].mean()
        avg_ghi_proxy = avg_dni + avg_dhi 

        solar_results.append({
            'latitude': lat,
            'longitude': lon,
            'elevation_m': elevation,
            'mean_dni': avg_dni,
            'mean_dhi': avg_dhi,
            'mean_ghi_proxy': avg_ghi_proxy,
            'mean_temp': avg_temp
        })
    except Exception as e:
        print(f"Skipping {os.path.basename(file_path)} due to error: {e}")

# 3. Create the lookup table and save
if solar_results:
    solar_summary_df = pd.DataFrame(solar_results)
    solar_summary_df.to_csv(output_file, index=False)
    print(f"--- SUCCESS ---")
    print(f"Saved averages for {len(solar_summary_df)} locations to {output_file}")
else:
    print("No data was processed.")
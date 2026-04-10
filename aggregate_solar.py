import pandas as pd
import glob
import os
import sys

# Path config w/ dynamic anchoring to the project folder
project_name = "Datacenters_Final_Solar_Suitability"
current_path = os.path.abspath(__file__)

if project_name in current_path:
    # Anchor to project root dir
    base_dir = current_path.split(project_name)[0] + project_name
else:
    # Fallback to current working dir
    base_dir = os.getcwd()


input_folder = os.path.join(base_dir, 'data', 'raw', 'solar_raw')
output_file = os.path.join(base_dir, 'processed', 'solar_averages.csv')

# Create the output dir
os.makedirs(os.path.dirname(output_file), exist_ok=True)

#Identify CSV files
csv_files = glob.glob(os.path.join(input_folder, "*.csv"))

# check paths are working
if len(csv_files) == 0:
    print(f"!!! ERROR: No CSV files found in {input_folder}")
    print("Please check that:")
    print(f"The folder exists at: {os.path.abspath(input_folder)}")
    print("The files inside end in precisely '.csv' (not .csv.txt or .xlsx)")
    sys.exit() 

print(f"Found {len(csv_files)} files. Processing.")

solar_results = []
# Loop through csv files and get location info and avgs
for file_path in csv_files:
    try:
        # Read only first row to get location info
        metadata = pd.read_csv(file_path, nrows=1)
        lat = metadata['Latitude'].iloc[0]
        lon = metadata['Longitude'].iloc[0]
        elevation = metadata['Elevation'].iloc[0]

        # Skip first 2 rows to get the data
        df = pd.read_csv(file_path, skiprows=2)

        avg_dni = df['DNI'].mean()
        avg_dhi = df['DHI'].mean()
        avg_temp = df['Temperature'].mean()
        avg_ghi_proxy = avg_dni + avg_dhi 

        # Append to final df
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

# Make lookup table and save
if solar_results:
    solar_summary_df = pd.DataFrame(solar_results)
    solar_summary_df.to_csv(output_file, index=False)
    print(f"success!")
    print(f"Saved averages for {len(solar_summary_df)} locations to {output_file}")
else:
    print("No data was processed.")
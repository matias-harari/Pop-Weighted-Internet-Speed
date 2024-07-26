import pandas as pd
import os
import getpass

speed_data_path = '/media/matias/Elements SE/WB/ookla'

username = getpass.getuser()
base_path = f'/home/{username}/GitHub/Pop-Weighted-Internet-Speed/raw_data'

#----------------------------------#
# SET PARAMETERS
year = 2023
zoom_level = 13
d_type = 'fixed'  # mobile or fixed

#----------------------------------#
# READ AND AGRREGATE DATA AT ZOOM L

# Define the quarter indices in file paths
qs = ["01", "04", "07", "10"]

agg_funcs = {
    'avg_d_kbps': 'sum',
    'avg_u_kbps': 'sum',
    'avg_lat_ms': 'sum',
    'tests': 'sum',
    'devices': 'sum'
}

# Initialize an empty DataFrame for all data
all_data_list = []

for q in qs:
    tiles_path = os.path.join(speed_data_path, f"{year}-{q}-01_performance_{d_type}_tiles.parquet")
    
    # Read the Parquet file into a DataFrame
    tiles = pd.read_parquet(tiles_path)
    
    # Ensure numeric columns are correctly typed
    tiles['avg_d_kbps'] = pd.to_numeric(tiles['avg_d_kbps'], errors='coerce')
    tiles['avg_u_kbps'] = pd.to_numeric(tiles['avg_u_kbps'], errors='coerce')
    tiles['avg_lat_ms'] = pd.to_numeric(tiles['avg_lat_ms'], errors='coerce')
    tiles['tests'] = pd.to_numeric(tiles['tests'], errors='coerce')
    tiles['devices'] = pd.to_numeric(tiles['devices'], errors='coerce')
    
    # Extract first x characters from quadkey
    tiles['quadkey'] = tiles['quadkey'].str[:zoom_level]
    
    # Compute weighted columns
    tiles['avg_d_kbps'] = tiles['avg_d_kbps'] * tiles['tests']
    tiles['avg_u_kbps'] = tiles['avg_u_kbps'] * tiles['tests']
    tiles['avg_lat_ms'] = tiles['avg_lat_ms'] * tiles['tests']

    tiles = tiles.groupby('quadkey').agg(agg_funcs).reset_index()

    # Compute weighted averages
    tiles['avg_d_kbps'] = tiles['avg_d_kbps'] / tiles['tests']
    tiles['avg_u_kbps'] = tiles['avg_u_kbps'] / tiles['tests']
    tiles['avg_lat_ms'] = tiles['avg_lat_ms'] / tiles['tests']
    
    # Append to all_data
    all_data_list.append(tiles)

#----------------------------------#
# CONCAT DATA

all_data = pd.concat(all_data_list, ignore_index=True)

# Compute weighted columns
all_data['avg_d_kbps'] = all_data['avg_d_kbps'] * all_data['tests']
all_data['avg_u_kbps'] = all_data['avg_u_kbps'] * all_data['tests']
all_data['avg_lat_ms'] = all_data['avg_lat_ms'] * all_data['tests']

all_data = all_data.groupby('quadkey').agg(agg_funcs).reset_index()

# Compute weighted averages
all_data['avg_d_kbps'] = all_data['avg_d_kbps'] / all_data['tests']
all_data['avg_u_kbps'] = all_data['avg_u_kbps'] / all_data['tests']
all_data['avg_lat_ms'] = all_data['avg_lat_ms'] / all_data['tests']


#----------------------------------#
# APPEND POPULATION DATA

pop_data = pd.read_parquet(f"{base_path}/pop_2020_quadkey_{zoom_level}.parquet")
all_data = pd.merge(all_data, pop_data, on='quadkey', how='left')

#----------------------------------#
# EXPORT
                    
# Export all_data as a Parquet file
output_file = f"{base_path}/internet_speed_{d_type}_{year}_by_quadkey_{zoom_level}.parquet"
all_data.to_parquet(output_file, index=False)

# Display the first few rows of the annual average data
print(f"Data exported to {output_file}. \n Head: \n")
print(all_data.head())
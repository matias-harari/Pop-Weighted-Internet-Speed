import argparse
import pandas as pd
import os

# Parser
def parse_args():
    parser = argparse.ArgumentParser(description='Process Ookla speed data.')
    parser.add_argument('--year', type=int, default=2023, help='Year of the data')
    parser.add_argument('--zoom_level', type=int, default=13, help='Zoom level of the data')
    parser.add_argument('--d_type', type=str, choices=['mobile', 'fixed'], default='fixed', help='Data type: mobile or fixed')
    parser.add_argument('--speed_data_path', type=str, required=True, help='Path to the speed raw data')
    parser.add_argument('--base_path', type=str, required=True, help='Base path for output data')
    return parser.parse_args()

# Main function
def main():
    args = parse_args()

    # Set parameters from command-line arguments
    year = args.year
    zoom_level = args.zoom_level
    d_type = args.d_type
    speed_data_path = args.speed_data_path
    base_path = args.base_path
    pop_data_path = f'{base_path}/raw_data/pop_2020_quadkey_13.parquet.gz'

    #----------------------------------#
    # READ AND AGGREGATE DATA AT ZOOM LEVEL

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
        try:
            tiles = pd.read_parquet(tiles_path)
        
            # Ensure numeric columns are correctly typed
            tiles['avg_d_kbps'] = pd.to_numeric(tiles['avg_d_kbps'], errors='coerce')
            tiles['avg_u_kbps'] = pd.to_numeric(tiles['avg_u_kbps'], errors='coerce')
            tiles['avg_lat_ms'] = pd.to_numeric(tiles['avg_lat_ms'], errors='coerce')
            tiles['tests'] = pd.to_numeric(tiles['tests'], errors='coerce')
            tiles['devices'] = pd.to_numeric(tiles['devices'], errors='coerce')
        
            # Extract first x characters from quadkey
            tiles['quadkey'] = tiles['quadkey'].str[:zoom_level]
        
            #Compute weighted columns
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

        except FileNotFoundError:
            print(f'File not found (skipped): {tiles_path}')

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

    pop_data = pd.read_parquet(pop_data_path, engine='pyarrow')
    all_data = pd.merge(all_data, pop_data, on='quadkey', how='left')

    #----------------------------------#
    # EXPORT
                    
    # Export all_data as a Parquet file
    output_file = f"{base_path}/data/internet_speed_{d_type}_{year}_by_quadkey_{zoom_level}.parquet.gz"
    all_data.to_parquet(output_file, index=False, compression='gzip')

    # Display the first few rows of the annual average data
    print(f"Data exported to {output_file}. \nHead: \n")
    print(all_data.head())

if __name__ == '__main__':
    main()

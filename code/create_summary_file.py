import geopandas as gpd
import pandas as pd
import getpass
from pyquadkey2.quadkey import QuadKey
from shapely.geometry import Point

username = getpass.getuser()
base_path = f'/home/{username}/GitHub/Pop-Weighted-Internet-Speed'

# Read WB Boundaries
gdf = gpd.read_file(f'{base_path}/raw_data/wb_countries/WB_countries_Admin0_10m.shp')
gdf = gdf.rename(columns={'NAME_EN': 'Country'})
gdf['ISO_N3'] = gdf['ISO_N3'].astype(int)

#----------------------------------#
# SET PARAMETERS

zoom_level = 13
years = [2023]
types = ['mobile', 'fixed'] 

#----------------------------------#
# CALCULATE COUNTRY METRICS

all_data = []

for year in years:
    for d_type in types:
        # Read Internet Data
        input_internet = f"{base_path}/raw_data/internet_speed_{d_type}_{year}_by_quadkey_{zoom_level}.parquet"
        input_internet = pd.read_parquet(input_internet)

        # Get Coordinates of Quadkey        
        input_internet['coordinates'] = input_internet['quadkey'].apply(lambda qk: QuadKey(qk).to_geo())
        input_internet['geometry'] = input_internet['coordinates'].apply(lambda x: Point(x[1], x[0]))

        # Perform spatial join to find which country each point falls into
        points = gpd.GeoDataFrame(input_internet, geometry='geometry', crs=4326)
        result = gpd.sjoin(points, gdf, how='left', op='within').set_index('Country')

        # Get Internet country avg weighted by Pop and weighted by tests
        result['pop_2020'] = result['pop_2020'].fillna(0)
        result['avg_d_kbps_w'] = result['avg_d_kbps'] * result['pop_2020'] # pop weight
        result['avg_d_kbps'] = result['avg_d_kbps'] * result['tests'] # tests weight
        
        avg_d_kbps_by_country = result.groupby('Country').agg({
            'avg_d_kbps': 'sum',
            'avg_d_kbps_w': 'sum',
            'tests': 'sum',
            'pop_2020': 'sum',
        })

        # Format variables
        avg_d_kbps_by_country[f'{year}_{d_type}_avg_d_mbps'] = round(avg_d_kbps_by_country['avg_d_kbps'] / avg_d_kbps_by_country['tests'] / 1000, 1)
        avg_d_kbps_by_country[f'{year}_{d_type}_avg_d_mbps_w'] = round(avg_d_kbps_by_country['avg_d_kbps_w'] / avg_d_kbps_by_country['pop_2020'] / 1000, 1)
        avg_d_kbps_by_country[f'{year}_{d_type}_k_tests'] = round(avg_d_kbps_by_country['tests'] / 1000, 1)
        
        # Append
        avg_d_kbps_by_country = avg_d_kbps_by_country[[f'{year}_{d_type}_avg_d_mbps', f'{year}_{d_type}_avg_d_mbps_w', f'{year}_{d_type}_k_tests']]
        all_data.append(avg_d_kbps_by_country)
        
#----------------------------------#
# CONCAT AND EXPORT

# Add Data to GDF and export
concat_data = pd.concat(all_data, axis=1)
gdf_w_data = gdf.merge(concat_data, left_on='Country', right_index=True, how='left')

gdf_w_data.to_file(f'{base_path}/data/summary_by_country.geojson', driver='GeoJSON')


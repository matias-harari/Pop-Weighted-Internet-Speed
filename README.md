# Pop-Weighted-Internet-Speed

## Project Overview

This project leverages high-resolution internet test data from [Ookla®](https://github.com/teamookla/ookla-open-data) to calculate mean download speeds by country and year. High-resolution population data from the [WorldPop Project](https://hub.worldpop.org/project/categories?id=3) is incorporated to weight internet speeds according to the population residing in each tile.

### Visualizations

1. **Interactive Web Application**: Explore the results through the interactive Shiny App available at https://matias-harari.shinyapps.io/Pop-Weighted-Internet-Speed/ 

   ![image-20240806164951877](./assets/3/image-20240806164951877.png)

   ![image-20240806172537825](./assets/3/image-20240806172537825.png)

2. **Jupyter Notebook**: For Python users, additional analysis is available in a [notebook](https://github.com/matias-harari/Pop-Weighted-Internet-Speed/tree/main/notebooks/), which can be accessed in Google Colab from [here](https://colab.research.google.com/github/matias-harari/Pop-Weighted-Internet-Speed/blob/main/notebooks/internet_speed_notebook.ipynb). The aggregated data by country, internet type, and year can be downloaded from [this link](https://github.com/matias-harari/Pop-Weighted-Internet-Speed/tree/main/summary_data/). 

   <img src="./assets/3/region_panel_vis_example.png" alt="Region Panel Visualization Example" style="zoom:100%;" /> 

### Comparison with Global Index

Ookla publishes download speed estimates by country on their [Global Index](https://www.speedtest.net/global-index). As of August 2024, their data is limited to the most recent year and does not account for population weights. 

:warning: The Global Index reports median speeds, which I cannot replicate using the open data provided (see [Methodology](methodology) for more details). 

### Impact of Population Weights

The incorporation of population weights significantly impacts internet speed calculations. For example, when population weights are applied, the average fixed internet speed in India in 2023 was found to be 37% lower compared to the unweighted calculation.

<img src="./assets/3/discrepancy_using_w.png" alt="discrepancy_using_w" style="zoom:80%;" />

## Methodology

### Data Sources

**Internet Speed Data**: [Speedtest® by Ookla®](https://github.com/teamookla/ookla-open-data) Global Fixed and Mobile Network Performance Maps was accessed from AWS. It includes internet speed measurements at the tile level, where each tile is identified by a unique `quadkey`, a standard spatial index developed by [Bing Maps](https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system). The dataset includes metrics on average download speed, average upload speed, average latency, number of tests, and number of devices. Data is aggregated quarterly, starting from Q1 2019.  The code to download the raw data is available in the project.

**Population Data**:  Population data at the tile level is obtained from the [WorldPop Project](https://hub.worldpop.org/project/categories?id=3), which provides population estimates for 2020 at a 1 km resolution using unconstrained top-down methods. The raw data is available in GeoTIFF format and can be downloaded from [humdata.org](https://humdata.org). WorldPop does not provide a spatial index for each pixel, so I determine the corresponding `quadkey` for each pixel employing the `pyquadkey2` library. The replication code to find the `quadkey` is not shared in this repository, but I share the output file in the `raw_data` folder. 

<img src="./assets/3/5cff54de-5133-4369-8680-52d2723eb756.jpg" alt="Screenshot of three Mercator projection images displaying the quadkey relationships between each level." style="zoom:67%;" />

*Source: example of the `quadkey` system by [Bing Maps](https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system)*

**Country Boundaries**: Country polygons from [The World Bank](https://datacatalog.worldbank.org/search/dataset/0038272/World-Bank-Official-Boundaries).

- [To Do: Add polygons for disputed areas]

### Data Aggregation

**Spatial Aggregation**: The code aggregates population data and internet speed metrics in quadkeys at zoom level 13, corresponding to tiles with a side length of approximately 4,892 meters. 

-  In the case of internet speed, new average metrics are calculated using the number of tests from tiles of lower resolution as weights. We cannot calculate other statistics such as percentiles (Ookla reports the median in their Global Index) because the raw values are averages for the tiles. 
- In the case of population, aggregation consists in summing the population values from tiles of lower resolution. As an example, in the next plot I show the distribution of population using a zoom level of 9, which is more aggregated than level 13.

<img src="./assets/3/AD_4nXcFm65EJ7vXcgqaOvoUXB9sv9JeShAG4ZlB07CbiCtSnhE4aVOiZrsbAM7cRkMTUe78fERY8Cu3eAdGqrpPig9j72NZb9K_mUzNGWxCLv9AMvIxpCeuJfaEoKW1_giJzSGxjYP-dOUd_-ibgcK6l1A8gTIB.png" alt="img" style="zoom:60%;" />

**Year Aggregation**: Internet speed metrics are aggregated at the year level using data from multiple quarters. Again, metrics are weighted based on the number of tests conducted within each quarter.

**Country-Level Aggregation**: Internet speed and population data at the tile level are mapped to specific countries using a spatial join with the [World Bank’s country boundaries](https://datacatalog.worldbank.org/search/dataset/0038272/World-Bank-Official-Boundaries). This step involves translating tile coordinates into geographic points and associating them with corresponding countries. For each year and internet type (mobile or fixed), the data is aggregated by country using population data from each tile as weights.

**Summary of Metrics**

- **Number of Tests**: The total number of tests conducted. In the [Shiny App](https://matias-harari.shinyapps.io/Pop-Weighted-Internet-Speed/ ) the number of test per 1,000 people is reported using the population levels from the World Bank in 2020.
- **Population-Weighted Average Download Speed**: The average download speed  in megabits per second, adjusted on the population size of each tile in the country.
- **Average Download Speed**: The average download speed in megabits per second, weighted by the number of tests in each tile of the country.

## Replication

 This project involves downloading raw data from AWS, processing it, and aggregating it for further analysis.

### 1. Synchronize Ookla Data

The script `main.sh` handles the synchronization of raw data from Ookla using the AWS CLI to download data for specified years, quarters, and data types. 

The next command shows an example of how to synchronize the data using the `main.sh` file. Data is stored in a local folder (`/path/to/raw_speed`), since each parquet file (quarter and internet type) can weight ~300 MB.

```bash
./main.sh --base_path "/path/to/base" --raw_speed_folder "/path/to/raw_speed" --years "2019,2020,2021" --sync_internet_data 1 --aggregate_data 0

```

### 2. Aggregate Data

Once the data is synchronized, the script `main.sh` processes and aggregates the raw data. It reads data from the specified folder, performs necessary calculations, and produces aggregated results.

To execute data aggregation, take the following command as an example:

```bash
./main.sh --base_path "/path/to/base" --raw_speed_folder "/path/to/raw_speed" --years "2019,2020,2021" --sync_internet_data 0 --aggregate_data 1
```

### Requirements

- **AWS CLI**: Ensure you have the AWS CLI installed and configured.
- **Python**: Ensure you have Python installed with the necessary packages (`geopandas`, `pyarrow`, etc.).

## Contact

For questions or feedback, please contact **matias.harari@gmail.com**.

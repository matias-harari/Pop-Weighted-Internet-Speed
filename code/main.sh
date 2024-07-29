#!/usr/bin/env bash

# Example to run this command:
# ./main.sh --base_path "/path/to/base" --raw_speed_folder "/path/to/raw_speed" --years "2019,2020,2021" --sync_internet_data 1 --aggregate_data 0
# ./code/main.sh --base_path "/home/$USER/GitHub/Pop-Weighted-Internet-Speed" --raw_speed_folder "/media/matias/Elements SE/WB/ookla" --years "2019,2020,2021,2022,2023,2024" --sync_internet_data 1 --aggregate_data 0

# Default values
base_path="/home/$USER/GitHub/Pop-Weighted-Internet-Speed"
raw_speed_folder="/media/matias/Elements SE/WB/ookla" # ~1GB of data by year and internet type 
years="2019,2020,2021,2022,2023,2024"  # Comma-separated list of years
sync_internet_data=0
aggregate_data=1

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --base_path)
      base_path="$2"
      shift
      shift
      ;;
    --raw_speed_folder)
      raw_speed_folder="$2"
      shift
      shift
      ;;
    --years)
      years="$2"
      shift
      shift
      ;;
    --sync_internet_data)
      sync_internet_data="$2"
      shift
      shift
      ;;
    --aggregate_data)
      aggregate_data="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Convert comma-separated list of years into an array
IFS=',' read -r -a year_array <<< "$years"

#------------------------------------------------#
# SYNC OOKLA DATA 

if [ "$sync_internet_data" -eq 1 ]; then
  echo "Starting data synchronization..."

  export FORMAT='parquet' # (shapefiles|parquet)

  for year in "${year_array[@]}"; do
    for Q in 1 2 3 4; do
      for TYPE in 'fixed' 'mobile'; do
        echo "Synchronizing data for year ${year}, quarter ${Q}, type ${TYPE}..."
        aws s3 sync "s3://ookla-open-data/${FORMAT}/performance/type=${TYPE}/year=${year}/quarter=${Q}/" "$raw_speed_folder" \
        --exact-timestamps \
        --no-sign-request
      done
    done
  done

  echo "Data synchronization complete."
fi

#------------------------------------------------#
# AGGREGATE RAW DATA 

if [ "$aggregate_data" -eq 1 ]; then
  echo "Starting data aggregation..."

  for year in "${year_array[@]}"; do
    for d_type in 'mobile' 'fixed'; do
      echo "Aggregating data for year $year, type $d_type..."
      python "${base_path}"/code/read_and_group_ookla.py \
            --year "$year" --d_type "$d_type" \
            --speed_data_path "${raw_speed_folder}" \
            --base_path "${base_path}"
    done
  done

  echo "Data aggregation complete."
fi
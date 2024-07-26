#!/usr/bin/env bash

export FORMAT='parquet' # (shapefiles|parquet)

for YYYY in 2019 2020 2021 2022 2023; do
  for Q in 1 2 3 4; do
    for TYPE in 'fixed' 'mobile'; do
      aws s3 cp s3://ookla-open-data/${FORMAT}/performance/type=${TYPE}/year=${YYYY}/quarter=${Q}/ . \
      --recursive \
      --no-sign-request
    done
  done
done

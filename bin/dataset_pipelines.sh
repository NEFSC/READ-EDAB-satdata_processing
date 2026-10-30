#!/bin/bash

# Exit immediately if any pipeline step fails
set -e 

echo "================================================================================"
echo "🚀 1. Running OCCCI stats/anomalies (at NWA)"
echo "================================================================================"
python3 src/satprocessing/satdata_processing_pipeline.py \
        --dataset OCCCI --map_subset NWA \
        --run_stats --stat_prods CHL --stat_periods D3 D7 W M A DOY WEEK MONTH \
        --run_anom --anom_prods CHL --anom_periods W M \
        --run_extract --extract_prods CHL --extract_periods W D7 M A --extract_shapefile NES_EPU_NOESTUARIES \
        --parallel_runs 6 --logfile

echo "================================================================================"
echo "🚀 2. Running OCCCI (PSC at NES)"
echo "================================================================================"
python3 src/satprocessing/satdata_processing_pipeline.py \
        --dataset OCCCI --sst_dataset CORALSST --run_psc --map_subset NES \
        --run_stats --stat_prods PSC --stat_periods D3 D7 W M A DOY WEEK MONTH \
        --parallel_runs 6 --logfile

echo "================================================================================"
echo "🚀 3. Running OCCCI (PPD at NWA)"
echo "================================================================================"
python3 src/satprocessing/satdata_processing_pipeline.py \
        --dataset GLOBCOLOUR --run_globcolour --map_subset NWA --globcolour_prods PAR --parallel_runs 6 --logfile --delete_corrupt
python3 src/satprocessing/satdata_processing_pipeline.py \
        --dataset OCCCI --sst_dataset CORALSST --par_dataset GLOBCOLOUR --map_subset NWA \
        --run_pp \
        --run_stats --stat_prods PPD --stat_periods D3 D7 W M A DOY WEEK MONTH \
        --parallel_runs 6 --logfile

echo "================================================================================"
echo "🚀 4. Running Stats and Anomalies for ACSPO"
echo "================================================================================"
python3 src/satprocessing/satdata_processing_pipeline.py \
        --dataset ACSPO --prods SST --periods W D7 M A DOY WEEK MONTH --map_subset NWA --run_stats --run_anom --parallel_runs 6 --logfile

echo "================================================================================"
echo "🚀 5. Preprocessing GLOBCOLOUR (for PAR data)"
echo "================================================================================"
python3 src/satprocessing/satdata_processing_pipeline.py \
        --dataset GLOBCOLOUR --run_globcolour --map_subset NWA --parallel_runs 6 --logfile --delete_corrupt


echo "================================================================================"
echo "🎉 ALL SEQUENTIAL DATASETS COMPLETED SUCCESSFULLY!"
echo "================================================================================"
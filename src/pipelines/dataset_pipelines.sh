#!/bin/bash

# Exit immediately if any pipeline step fails
set -e 

eecho "================================================================================"
echo "🚀 1. Preprocessing GLOBCOLOUR (for PAR data)"
echo "================================================================================"
python3 satdata_processing_pipeline.py --dataset GLOBCOLOUR --run_globcolour --map_subset NWA --logfile

echo "================================================================================"
echo "🚀 2. Running OCCCI (PSC at NES)"
echo "================================================================================"
python3 satdata_processing_pipeline.py --dataset OCCCI --sst_dataset CORALSST --run_psc --map_subset NES --run_stats --stat_prods PSC --stat_periods D3 D7 W M A DOY WEEK MONTH --logfile

echo "================================================================================"
echo "🚀 3. Running OCCCI (at NWA)"
echo "================================================================================"
python3 satdata_processing_pipeline.py --dataset OCCCI --sst_dataset CORALSST --par_dataset GLOBCOLOUR --map_subset NWA \
        --run_pp \
        --run_stats --stat_prods CHL PPD --stat_periods D3 D7 W M A DOY WEEK MONTH \
        --run_anom --anom_prods CHL --anom_periods W M \
        --logfile
echo "================================================================================"
echo "🚀 4. Running Stats and Anomalies for ACSPO"
echo "================================================================================"
#python3 satdata_processing_pipeline.py --dataset ACSPO --prods SST --periods D8 M A --map_subset NWA --run_stats --run_anom --parallel_runs 6 --logfile

echo "================================================================================"
echo "🚀 5. Running Daily Products for GLOBCOLOUR"
echo "================================================================================"
#python3 satdata_processing_pipeline.py --dataset GLOBCOLOUR --sst_dataset ACSPONRT --par_dataset MODIS_PAR --map_subset NES --run_psc --run_pp --batch_size 6 --logfile

echo "================================================================================"
echo "🎉 ALL SEQUENTIAL DATASETS COMPLETED SUCCESSFULLY!"
echo "================================================================================"
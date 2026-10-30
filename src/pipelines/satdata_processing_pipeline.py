# satdata_processing_pipeline.py
import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def run_command(cmd, step_name):
    """
    Executes a shell command via subprocess and checks for errors.
    """
    print(f"\n{'='*80}")
    print(f"🚀 STARTING PROCESSING STEP: {step_name.upper()} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_cmd = [str(x) for x in cmd if x is not None]
    print(f"💻 Command: {' '.join(safe_cmd)}")
    print(f"{'='*80}\n")
    
    # Run the process and stream output directly to the terminal
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n❌ CRITICAL FAILURE IN STEP: {step_name.upper()}")
        print("Processing pipeline halted.")
        sys.exit(result.returncode)
        
    print(f"\n✅ PROCESSING STEP COMPLETED: {step_name.upper()}\n")

def parse_args():
    parser = argparse.ArgumentParser(description="Processing Execution Script for SatProcessing Pipelines")
    
    # 🎯 Primary Configuration
    parser.add_argument("--dataset", type=str, required=True, help="Main dataset to process (e.g., OCCCI, GLOBCOLOUR, ACSPO)")
    parser.add_argument("--map_subset", type=str, default=None, help="Subset region (default: NWA)")
    
    # 🎯 Execution Steps (Toggle which pipelines to run)
    parser.add_argument("--run_psc", action="store_true", help="Run the Phytoplankton Size Class pipeline")
    parser.add_argument("--run_pp", action="store_true", help="Run the Primary Productivity pipeline")
    parser.add_argument("--run_stats", action="store_true", help="Run the Statistics pipeline")
    parser.add_argument("--run_anom", action="store_true", help="Run the Anomaly pipeline")
    parser.add_argument("--run_globcolour", action="store_true", help="Run the GlobColour Preprocessing pipeline")
    parser.add_argument("--run_extract", action="store_true", help="Run the Regional Data Extraction pipeline")

    # 🎯 Pipeline Specific Arguments
    parser.add_argument("--sst_dataset", type=str, help="SST dataset required for PSC and PP (e.g., CORALSST, ACSPO)")
    parser.add_argument("--par_dataset", type=str, help="PAR dataset required for PP (e.g., GLOBCOLOUR)")
    
    # 🎯 Separated Stats and Anomaly Targets
    parser.add_argument("--globcolour_prods", type=str, nargs='+', default=None, help="Products to run for Globcolour processing")
    parser.add_argument("--stat_prods", type=str, nargs='+', default=None, help="Products to run for Statistics")
    parser.add_argument("--stat_periods", type=str, nargs='+', default=None, help="Periods for Statistics")
    parser.add_argument("--anom_prods", type=str, nargs='+', default=None, help="Products to run for Anomalies")
    parser.add_argument("--anom_periods", type=str, nargs='+', default=None, help="Periods for Anomalies")
    
    # 🎯 Extraction Specific Arguments
    parser.add_argument("--extract_prods", type=str, nargs='+', default=None, help="Products to run for Extraction")
    parser.add_argument("--extract_periods", type=str, nargs='+', default=None, help="Periods for Extraction")
    parser.add_argument("--extract_shapefile", type=str, default=None, help="Shapefile name to extract")
    parser.add_argument("--extract_stat_type", type=str, default=None, help="Target statistic type (e.g., mean, median)")
   
    # 🎯 File Handling
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--delete_corrupt", action="store_true", help="Delete identified corrupt source files")
    parser.add_argument("--verify_existing", action=argparse.BooleanOptionalAction, default=True, help="If false, engages Fast Mode for Stats/Anomalies by trusting mtime.")
    
    # 🎯 Hardware and Logging
    parser.add_argument("--parallel_runs", type=int, default=4, help="Number of parallel workers for Stats/Anomalies (default: 4)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--logfile", nargs='?', const="auto", default=None, help="Generate logfiles for all executed steps")

    return parser.parse_args()

if __name__ == "__main__":
# Force multiprocessing to 'spawn' instead of 'fork' to prevent HDF5 core dumps
    import multiprocessing
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass  # Catch if it's already been set
    
    args = parse_args()
    
    python_exe = sys.executable
    script_dir = Path(__file__).resolve().parent

    # Ensure at least one step was selected 
    if not any([args.run_globcolour, args.run_psc, args.run_pp, args.run_stats, args.run_anom, args.run_extract]):
        print("⚠️ No execution steps selected! Use --run_globcolour, --run_psc, --run_pp, --run_stats, --run_anom, and/or --run_extract.")
        sys.exit(1)

    print(f"\n{'*'*80}")
    print(f"🌟 PROCESSING PIPELINE INITIALIZED FOR DATASET: {args.dataset.upper()}")
    print(f"{'*'*80}")

    # ==========================================
    # 1. PHYTOPLANKTON SIZE CLASS (PSC)
    # ==========================================
    if args.run_psc:
        cmd = [
            python_exe, str(script_dir / "psc_pipeline.py"),
            "--pipeline", "psc",
            "--chl_dataset", args.dataset,
            "--batch_size", str(args.parallel_runs)
        ]
        if args.map_subset: cmd.extend(["--map_subset", args.map_subset])
        if args.sst_dataset: cmd.extend(["--sst_dataset", args.sst_dataset])
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
            
        run_command(cmd, "Phytoplankton Size Class (PSC)")

    # ==========================================
    # 2. PRIMARY PRODUCTIVITY (PP)
    # ==========================================
    if args.run_pp:
        cmd = [
            python_exe, str(script_dir / "pp_pipeline.py"),
            "--pipeline", "pp",
            "--chl_dataset", args.dataset,
            "--parallel_runs", str(args.parallel_runs)
        ]
        if args.map_subset: cmd.extend(["--map_subset", args.map_subset])
        if args.sst_dataset: cmd.extend(["--sst_dataset", args.sst_dataset])
        if args.par_dataset: cmd.extend(["--par_dataset", args.par_dataset])
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
            
        run_command(cmd, "Primary Productivity (PP)")

    # ==========================================
    # 3. STATISTICS
    # ==========================================
    if args.run_stats:
        cmd = [
            python_exe, str(script_dir / "stats_pipeline.py"),
            "--dataset", args.dataset,
            "--parallel_runs", str(args.parallel_runs)
        ]
        # Only append if provided
        if args.map_subset: cmd.extend(["--map_subset", args.map_subset])
        if args.stat_prods: cmd.extend(["--prods"] + args.stat_prods)
        if args.stat_periods: cmd.extend(["--periods"] + args.stat_periods)
        if not args.verify_existing: cmd.append("--no-verify_existing")
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
            
        run_command(cmd, "Statistics")

    # ==========================================
    # 4. ANOMALIES
    # ==========================================
    if args.run_anom:
        cmd = [
            python_exe, str(script_dir / "anomaly_pipeline.py"),
            "--dataset", args.dataset,
            "--parallel_runs", str(args.parallel_runs)
        ]
        # Only append if provided
        if args.map_subset: cmd.extend(["--map_subset", args.map_subset])
        if args.anom_prods: cmd.extend(["--prods"] + args.anom_prods)
        if args.anom_periods: cmd.extend(["--periods"] + args.anom_periods)
        if not args.verify_existing: cmd.append("--no-verify_existing")
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
            
        run_command(cmd, "Anomalies")

    # ==========================================
    # 5. GLOBCOLOUR PREPROCESSING
    # ==========================================
    if args.run_globcolour:
        if args.dataset.upper() != "GLOBCOLOUR":
            print("⚠️ Skipping GlobColour preprocessing because the target dataset is not GLOBCOLOUR.")
        else:
            cmd = [
                python_exe, str(script_dir / "globcolour_pipeline.py"),
                "--parallel_runs", str(args.parallel_runs)
            ]
            if args.map_subset: cmd.extend(["--map_subset", args.map_subset])
            if args.globcolour_prods: cmd.extend(["--prods"] + args.globcolour_prods)
            if args.overwrite: cmd.append("--overwrite")
            if args.delete_corrupt: cmd.append("--delete_corrupt")
            if args.verbose: cmd.append("--verbose")
            if args.logfile: cmd.extend(["--logfile", "auto"])
                
            run_command(cmd, "GlobColour Preprocessing")

    # ==========================================
    # 6. DATA EXTRACTION
    # ==========================================
    if args.run_extract:
        if not args.extract_shapefile:
            print("⚠️ Skipping Data Extraction: A --shapefile must be provided.")
        else:
            cmd = [
                python_exe, str(script_dir / "extraction_pipeline.py"),
                "--dataset", args.dataset,
                "--shapefile", args.extract_shapefile,
                "--parallel_runs", str(args.parallel_runs)
            ]
            if args.map_subset: cmd.extend(["--map_subset", args.map_subset])
            if args.extract_prods: cmd.extend(["--prods"] + args.extract_prods)
            if args.extract_periods: cmd.extend(["--periods"] + args.extract_periods)
            if args.extract_stat_type: cmd.extend(["--stat_type", args.extract_stat_type])
            
            if args.verbose: cmd.append("--verbose")
            if args.logfile: cmd.extend(["--logfile", "auto"])
                
            run_command(cmd, "Data Extraction")

    print(f"{'*'*80}")
    print(f"🎉 ALL REQUESTED PROCESSING PIPELINE STEPS COMPLETED SUCCESSFULLY!")
    print(f"{'*'*80}\n")

# Examples 
# 1. The Full Suite (Derived Products + Aggregations)
# python3 satdata_processing_pipeline.py --dataset OCCCI --sst_dataset CORALSST --par_dataset MODIS_PAR --run_psc --run_pp --run_stats --run_anom --logfile
# 
# 2. Stats and Anomalies Only (Physical Datasets
# python3 satdata_processing_pipeline.py --dataset ACSPO --stat_prods SST --stat_periods D8 M A --anom_prods SST --anom_periods W M --map_subset NWA --run_stats --run_anom --parallel_runs 6 --logfile
#
# 3. Derived Daily Products Only (Batch Processing)
# python3 satdata_processing_pipeline.py --dataset GLOBCOLOUR --sst_dataset ACSPONRT --par_dataset MODIS_PAR --map_subset NES --run_psc --run_pp --batch_size 6 --logfile
#
# 4. Targeted Debugging Run
# python3 satdata_processing_pipeline.py --dataset OCCCI --prods PPD --periods A --run_stats --run_anom --verbose --logfile
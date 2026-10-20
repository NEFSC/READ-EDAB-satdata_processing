# satdata_processing_pipeline.py
import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utilities.bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=False)

def run_command(cmd, step_name):
    """
    Executes a shell command via subprocess and checks for errors.
    """
    print(f"\n{'='*80}")
    print(f"🚀 STARTING PROCESSING STEP: {step_name.upper()} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Command: {' '.join(cmd)}")
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
    parser.add_argument("--map_subset", type=str, default="NES", help="Subset region (default: NES)")
    
    # 🎯 Execution Steps (Toggle which pipelines to run)
    parser.add_argument("--run_psc", action="store_true", help="Run the Phytoplankton Size Class pipeline")
    parser.add_argument("--run_pp", action="store_true", help="Run the Primary Productivity pipeline")
    parser.add_argument("--run_stats", action="store_true", help="Run the Statistics pipeline")
    parser.add_argument("--run_anom", action="store_true", help="Run the Anomaly pipeline")
    parser.add_argument("--run_globcolour", action="store_true", help="Run the GlobColour Preprocessing pipeline")
    
    # 🎯 Pipeline Specific Arguments
    parser.add_argument("--sst_dataset", type=str, help="SST dataset required for PSC and PP (e.g., CORALSST, ACSPO)")
    parser.add_argument("--par_dataset", type=str, help="PAR dataset required for PP (e.g., MODIS)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")

    # 🎯 Separated Stats and Anomaly Targets
    parser.add_argument("--stat_prods", type=str, nargs='+', default=["CHL", "PSC", "PPD"], help="Products to run for Statistics (default: CHL PSC PPD)")
    parser.add_argument("--stat_periods", type=str, nargs='+', default=["M", "A", "SEASON"], help="Periods for Statistics (default: M A SEASON)")
    parser.add_argument("--anom_prods", type=str, nargs='+', default=["CHL", "PSC", "PPD"], help="Products to run for Anomalies (default: CHL PSC PPD)")
    parser.add_argument("--anom_periods", type=str, nargs='+', default=["M", "A", "SEASON"], help="Periods for Anomalies (default: M A SEASON)")
    
    # 🎯 Hardware and Logging
   # parser.add_argument("--batch_size", type=int, default=4, help="Number of years to run in parallel for PSC/PP (default: 4)")
    parser.add_argument("--parallel_runs", type=int, default=4, help="Number of parallel workers for Stats/Anomalies (default: 4)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--logfile", nargs='?', const="auto", default=None, help="Generate logfiles for all executed steps")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    python_exe = sys.executable
    script_dir = Path(__file__).resolve().parent

    # Ensure at least one step was selected 
    if not any([args.run_globcolour, args.run_psc, args.run_pp, args.run_stats, args.run_anom]):
        print("⚠️ No execution steps selected! Use --run_globcolour, --run_psc, --run_pp, --run_stats, and/or --run_anom.")
        sys.exit(1)

    print(f"\n{'*'*80}")
    print(f"🌟 PROCESSING PIPELINE INITIALIZED FOR DATASET: {args.dataset.upper()}")
    print(f"{'*'*80}")

    # ==========================================
    # 1. PHYTOPLANKTON SIZE CLASS (PSC)
    # ==========================================
    if args.run_psc:
        cmd = [
            python_exe, str(script_dir / "psc_pp_parallel_pipeline.py"),
            "--pipeline", "psc",
            "--chl_dataset", args.dataset,
            "--map_subset", args.map_subset,
            "--batch_size", str(args.parallel_runs)
        ]
        if args.sst_dataset: cmd.extend(["--sst_dataset", args.sst_dataset])
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
            
        run_command(cmd, "Phytoplankton Size Class (PSC)")

    # ==========================================
    # 2. PRIMARY PRODUCTIVITY (PP)
    # ==========================================
    if args.run_pp:
        cmd = [
            python_exe, str(script_dir / "psc_pp_parallel_pipeline.py"),
            "--pipeline", "pp",
            "--chl_dataset", args.dataset,
            "--map_subset", args.map_subset,
            "--batch_size", str(args.parallel_runs)
        ]
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
            "--prods", *args.stat_prods,
            "--periods", *args.stat_periods,
            "--dataset", args.dataset,
            "--map_subset", args.map_subset,
            "--parallel_runs", str(args.parallel_runs)
        ]
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
            
        run_command(cmd, "Statistics")

    # ==========================================
    # 4. ANOMALIES
    # ==========================================
    if args.run_anom:
        cmd = [
            python_exe, str(script_dir / "anomaly_pipeline.py"),
            "--prods", *args.anom_prods,
            "--periods", *args.anom_periods,
            "--dataset", args.dataset,
            "--map_subset", args.map_subset,
            "--parallel_runs", str(args.parallel_runs)
        ]
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
                "--map_subset", args.map_subset,
                "--parallel_runs", str(args.parallel_runs)
            ]
            if args.overwrite: cmd.append("--overwrite")
            if args.verbose: cmd.append("--verbose")
            if args.logfile: cmd.extend(["--logfile", "auto"])
                
            run_command(cmd, "GlobColour Preprocessing")

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
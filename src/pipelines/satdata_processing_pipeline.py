# satdata_processing_pipeline.py
import argparse
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# ==========================================
# EARLY ARGUMENT PARSING FOR PATH CONFIG
# ==========================================
# Extract just the config argument before doing anything else
config_parser = argparse.ArgumentParser(add_help=False)
config_parser.add_argument("--config", type=str, required=True, help="Path to JSON config dictionary")
early_args, remaining_argv = config_parser.parse_known_args()

# Load explicit paths from the dictionary
with open(early_args.config, "r") as f:
    paths = json.load(f)

# Explicitly set the project root for imports so it isn't relative to where the script is located
sys.path.insert(0, paths["project_root"])

# Now that the path is set, safely import your utilities
from utilities.environment import bootstrap_environment, configure_mount_points

# Inject the explicit drive paths directly into the bootstrapper memory
configure_mount_points(
    resources=paths["resources"],
    datasets=paths["datasets"],
    projects=paths["projects"]
)
# ==========================================


def run_command(cmd, step_name):
    """
    Executes a shell command via subprocess and checks for errors.
    """
    print(f"\n{'='*80}")
    print(f" STARTING PROCESSING STEP: {step_name.upper()} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")
    
    # Run the process and stream output directly to the terminal
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n CRITICAL FAILURE IN STEP: {step_name.upper()}")
        print("Processing pipeline halted.")
        sys.exit(result.returncode)
        
    print(f"\n PROCESSING STEP COMPLETED: {step_name.upper()}\n")


def parse_args(args_list):
    parser = argparse.ArgumentParser(description="Processing Execution Script for SatProcessing Pipelines")
    
    #  Primary Configuration
    parser.add_argument("--dataset", type=str, required=True, help="Main dataset to process (e.g., OCCCI, GLOBCOLOUR, ACSPO)")
    parser.add_argument("--map_subset", type=str, default="NWA", help="Subset region (default: NWA)")
    
    #  Execution Steps
    parser.add_argument("--run_psc", action="store_true", help="Run the Phytoplankton Size Class pipeline")
    parser.add_argument("--run_pp", action="store_true", help="Run the Primary Productivity pipeline")
    parser.add_argument("--run_stats", action="store_true", help="Run the Statistics pipeline")
    parser.add_argument("--run_anom", action="store_true", help="Run the Anomaly pipeline")
    parser.add_argument("--run_globcolour", action="store_true", help="Run the GlobColour Preprocessing pipeline")
    
    #  Pipeline Specific Arguments
    parser.add_argument("--sst_dataset", type=str, help="SST dataset required for PSC and PP (e.g., CORALSST, ACSPO)")
    parser.add_argument("--par_dataset", type=str, help="PAR dataset required for PP (e.g., GLOBCOLOUR)")
    
    #  Separated Stats and Anomaly Targets
    parser.add_argument("--globcolour_prods", type=str, nargs='+', default=None, help="Products to run for Globcolour processing")
    parser.add_argument("--stat_prods", type=str, nargs='+', default=None, help="Products to run for Statistics")
    parser.add_argument("--stat_periods", type=str, nargs='+', default=None, help="Periods for Statistics")
    parser.add_argument("--anom_prods", type=str, nargs='+', default=None, help="Products to run for Anomalies")
    parser.add_argument("--anom_periods", type=str, nargs='+', default=None, help="Periods for Anomalies")
    
    #  File Handling
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--delete_corrupt", action="store_true", help="Delete identified corrupt source files")
    
    #  Hardware and Logging
    parser.add_argument("--parallel_runs", type=int, default=4, help="Number of parallel workers for Stats/Anomalies (default: 4)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--logfile", nargs='?', const="auto", default=None, help="Generate logfiles for all executed steps")

    # Parse the remaining arguments passed from the early parser
    return parser.parse_args(args_list)


def main():
    # Force multiprocessing to 'spawn' instead of 'fork' to prevent HDF5 core dumps
    import multiprocessing
    try:
        multiprocessing.set_start_method('spawn')
        print("current process id:", multiprocessing.current_process().pid)
    except RuntimeError:
        pass  
    
    args = parse_args(remaining_argv)


    
    python_exe = sys.executable
    script_dir = Path(__file__).resolve().parent

    # Ensure at least one step was selected 
    if not any([args.run_globcolour, args.run_psc, args.run_pp, args.run_stats, args.run_anom]):
        print("No execution steps selected! Use --run_globcolour, --run_psc, --run_pp, --run_stats, and/or --run_anom.")
        sys.exit(1)

    print(f"\n{'*'*80}")
    print(f"PROCESSING PIPELINE INITIALIZED FOR DATASET: {args.dataset.upper()}")
    print(f"{'*'*80}")

    if args.run_psc:
        cmd = [
            python_exe, str(script_dir / "psc_pp_parallel_pipeline.py"),
            "--pipeline", "psc", "--chl_dataset", args.dataset,
            "--map_subset", args.map_subset, "--batch_size", str(args.parallel_runs)
        ]
        if args.sst_dataset: cmd.extend(["--sst_dataset", args.sst_dataset])
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
        run_command(cmd, "Phytoplankton Size Class (PSC)")

    if args.run_pp:
        cmd = [
            python_exe, str(script_dir / "psc_pp_parallel_pipeline.py"),
            "--pipeline", "pp", "--chl_dataset", args.dataset,
            "--map_subset", args.map_subset, "--batch_size", str(args.parallel_runs)
        ]
        if args.sst_dataset: cmd.extend(["--sst_dataset", args.sst_dataset])
        if args.par_dataset: cmd.extend(["--par_dataset", args.par_dataset])
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
        run_command(cmd, "Primary Productivity (PP)")

    if args.run_stats:
        cmd = [
            python_exe, str(script_dir / "stats_pipeline.py"),
            "--dataset", args.dataset, "--map_subset", args.map_subset,
            "--parallel_runs", str(args.parallel_runs)
        ]
        if args.stat_prods: cmd.extend(["--prods"] + args.stat_prods)
        if args.stat_periods: cmd.extend(["--periods"] + args.stat_periods)
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
        run_command(cmd, "Statistics")

    if args.run_anom:
        cmd = [
            python_exe, str(script_dir / "anomaly_pipeline.py"),
            "--dataset", args.dataset, "--map_subset", args.map_subset,
            "--parallel_runs", str(args.parallel_runs)
        ]
        if args.anom_prods: cmd.extend(["--prods"] + args.anom_prods)
        if args.anom_periods: cmd.extend(["--periods"] + args.anom_periods)
        if args.verbose: cmd.append("--verbose")
        if args.logfile: cmd.extend(["--logfile", "auto"])
        run_command(cmd, "Anomalies")

    if args.run_globcolour:
        if args.dataset.upper() != "GLOBCOLOUR":
            print("️ Skipping GlobColour preprocessing because the target dataset is not GLOBCOLOUR.")
        else:
            cmd = [
                python_exe, str(script_dir / "globcolour_pipeline.py"),
                "--map_subset", args.map_subset, "--parallel_runs", str(args.parallel_runs)
            ]
            if args.globcolour_prods: cmd.extend(["--prods"] + args.globcolour_prods)
            if args.overwrite: cmd.append("--overwrite")
            if args.delete_corrupt: cmd.append("--delete_corrupt")
            if args.verbose: cmd.append("--verbose")
            if args.logfile: cmd.extend(["--logfile", "auto"])
            run_command(cmd, "GlobColour Preprocessing")

    print(f"{'*'*80}")
    print(f"ALL REQUESTED PROCESSING PIPELINE STEPS COMPLETED SUCCESSFULLY!")
    print(f"{'*'*80}\n")

if __name__ == "__main__":
    try:
        # Bootstrap triggers here and automatically applies the explicitly mounted paths
        env = bootstrap_environment(verbose=False)
        main()
    except Exception as e:
        print(f"\n FATAL ERROR: {e}")
        print("Please review the error message above and contact support if necessary.")
        sys.exit(1)
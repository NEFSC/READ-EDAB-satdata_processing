import argparse
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utilities.bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=False)

from utilities.src.utilities.globcolour_utilities import run_globcolour_dataset

class LoggerWriter:
    """
    Redirects standard print statements and errors to both the terminal and a log file.
    """
    def __init__(self, log_path):
        self.terminal = sys.stdout
        self.log_file = open(log_path, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()
        
    def close(self):
        self.log_file.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Run the GLOBCOLOUR preprocessing pipeline")
    parser.add_argument("--map_subset", type=str, default="NWA", help="Name of the map_region (e.g. NES, NWA) to subset the data to.")
    parser.add_argument("--verbose", action="store_true", help="Include detailed debugging steps in the output.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite the output files if they already exist.")
    parser.add_argument("--logfile", type=str, help="Optional override path to log file for this run.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # --- 1. Dynamic Logfile Setup ---
    pipeline_name = "globcolour_preprocessing"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    if args.logfile:
        log_path = Path(args.logfile)
    else:
        log_root = Path(env["satlogs_path"])
        log_dir = log_root / pipeline_name
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{pipeline_name}_{args.map_subset}_{timestamp}.log"

    # --- 2. Intercept Output ---
    logger = LoggerWriter(log_path)
    sys.stdout = logger
    sys.stderr = logger  # Captures unhandled tracebacks in the same log file

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting {pipeline_name.upper()} pipeline...")
    print(f"Log file: {log_path}")
    print(f"Parameters: map_subset={args.map_subset}, overwrite={args.overwrite}, verbose={args.verbose}")
    print("-" * 60)

    # --- 3. Execute Pipeline ---
    try:
        # Note: We tie 'debug' to 'args.verbose' so tracebacks are hidden during clean runs 
        # but exposed when the verbose flag is used.
        run_globcolour_dataset(
            subset_map=args.map_subset, 
            overwrite=args.overwrite, 
            verbose=True,
            debug=args.verbose, 
            dry_run=False  
        )
        print("-" * 60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline completed successfully.")
        
    except Exception as e:
        print("-" * 60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Pipeline failed with a critical error:")
        traceback.print_exc()
        
    finally:
        # --- 4. Clean Up ---
        logger.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

# Examples
# Standard
    # python3 globcolour_pipeline.py --map_subset NWA
# With detailed logfile and overwrite set
    # python3 globcolour_pipeline.py --map_subset NWA --verbose --overwrite
import argparse
import sys
import traceback
from datetime import datetime

from utilities import run_annual_pp_pipeline 

def main():
    parser = argparse.ArgumentParser(description="Run the Annual Primary Productivity pipeline.")
    
    parser.add_argument("--dataset", type=str, required=True, help="Base dataset (e.g., OCCCI, GLOBCOLOUR)")
    parser.add_argument("--map_subset", type=str, help="Regional subset (e.g., NWA, NES, GLOBAL)")
    parser.add_argument("--daterange", type=str, help="Flexible date input. Examples: '2025', \"['2025', '2026']\"")
    parser.add_argument("--parallel_runs", type=int, default=1, help="Number of parallel workers")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress")
    parser.add_argument("--debug", action="store_true", help="Print debug tracebacks")
    parser.add_argument("--logfile", nargs='?', const='auto', default=None, help="Path to logfile or 'auto'")

    args = parser.parse_args()

    try:
        run_annual_pp_pipeline(
            dataset=args.dataset,
            map_subset=args.map_subset,
            daterange=args.daterange,
            parallel_runs=args.parallel_runs,
            overwrite=args.overwrite,
            verbose=args.verbose,
            debug=args.debug,
            logfile=args.logfile
        )
    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE IN STEP: ANNUAL PRIMARY PRODUCTIVITY")
        print(f"Error: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
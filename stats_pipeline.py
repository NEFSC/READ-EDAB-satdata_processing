# run_stats.py
import argparse
import sys
from pathlib import Path
import ast

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utilities.bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=False)

from utilities.statanom_utilities import run_stats_pipeline

def flatten_dates(d):
    # Flatten nested lists like [[1997]] → [1997]
    if isinstance(d, list):
        flat = []
        for item in d:
            if isinstance(item, list):
                flat.extend(flatten_dates(item))
            else:
                flat.append(item)
        return flat
    return [d]

def parse_args():
    parser = argparse.ArgumentParser(description="Run statistics pipeline")
    parser.add_argument("--prods", type=str, nargs='+', required=True, help="Name of product(s)")
    parser.add_argument("--periods", type=str, nargs='+', required=True, help="Period code(s) of the output statistics (e.g. W, M, A)")
    parser.add_argument("--dataset", type=str, required=False, help="Name of product dataset (e.g. CHL, SST, PSC)")
    parser.add_argument("--version", type=str, required=False, help="Name of dataset version (e.g. V6.0)")
    parser.add_argument("--subset", type=str, required=False, help="Name of the region (e.g. NES, NWA) to subset the data to")
    parser.add_argument("--daterange", type=str, help="Flexible date input: year(s), date(s), or range")
    parser.add_argument("--climatology_range", type=str, help="The year range for the climatology (e.g. 1991,2020)")
    parser.add_argument("--parallel_runs", type=int, help="The number of stats jobs to run in parallel")
    parser.add_argument("--logfile", type=str, help="Optional path to log file for this run")  
    args = parser.parse_args()

    if args.daterange:
        try:
            parsed = ast.literal_eval(args.daterange)
            args.daterange = flatten_dates(parsed)
        except Exception:
            args.daterange = [args.daterange]

    return args

if __name__ == "__main__":
    args = parse_args()
    run_stats_pipeline(prods=args.prods,
                       periods=args.periods,
                       dataset=args.dataset,
                       version=args.version,
                       subset=args.subset,
                       daterange=args.daterange,
                       climatology_range=args.climatology_range,
                       parallel_runs=args.parallel_runs,
                       logfile=args.logfile)

   # ==========================================
    # 💻 Example terminal window commands:
    # ==========================================
    #
    # 1. Standard Run:
    # python3 run_stats.py --prods SST --periods W M A --subset NWA --parallel_runs 4
    #
    # 2. Multi-Product Run with a Logfile:
    # python3 run_stats.py --prods SST CHL PSC --periods MONTH --subset NES --logfile /path/to/log.txt
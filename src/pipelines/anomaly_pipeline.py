# anomaly_pipeline.py
import argparse
import sys
from pathlib import Path
import ast

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent.parent
print(f"Project Root = {project_root}")
sys.path.insert(0, str(project_root))

from utilities.bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=False)

from utilities.src.utilities.anomaly_utilities import run_anomaly_pipeline

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
    parser = argparse.ArgumentParser(description="Run anomaly pipeline")
    parser.add_argument("--prods", type=str, nargs='+', required=False, default=None, help="Name of product(s)")
    parser.add_argument("--periods", type=str, nargs='+', required=False, default=None, help="Period code(s) of the output statistics (e.g. W, M, A)")
    parser.add_argument("--dataset", type=str, required=False, help="Name of product dataset (e.g. CHL, SST, PSC)")
    parser.add_argument("--version", type=str, required=False, help="Name of dataset version (e.g. V6.0)")
    parser.add_argument("--map_subset", type=str, required=False, help="Name of the map region (e.g. NES, NWA) to subset the data to")
    parser.add_argument("--daterange", type=str, help="Flexible date input: year(s), date(s), or range")
    parser.add_argument("--climatology_range", type=str, help="The year range for the climatology (e.g. 1991,2020)")
    parser.add_argument("--stat_var", type=str, required=False, help="The specific statistic to base the anomaly on (e.g., mean, median, max)")
    parser.add_argument("--parallel_runs", type=int, default=1, help="The number of anomaly jobs to run in parallel")
    parser.add_argument("--verify_existing", action=argparse.BooleanOptionalAction, default=True, help="If false, blindly trusts mtime instead of opening NetCDF files to check attributes (Fast Mode)")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress logs")
    parser.add_argument("--debug", action="store_true", help="Enter debug mode")
    parser.add_argument("--logfile", nargs='?', const="auto", default=None, 
                        help="Path to log file. Use flag without a path to autogenerate.")
    args = parser.parse_args()

    if args.daterange:
        try:
            parsed = ast.literal_eval(args.daterange)
            args.daterange = flatten_dates(parsed)
        except Exception:
            args.daterange = [args.daterange]

    if args.climatology_range:
        try:
            parsed_clim = ast.literal_eval(args.climatology_range)
            if isinstance(parsed_clim, (list, tuple)):
                args.climatology_range = tuple(flatten_dates(list(parsed_clim)))
            elif isinstance(parsed_clim, int):
                args.climatology_range = (parsed_clim,)
        except Exception:
            # Fallback to string split if it's not a valid Python literal (e.g. "1991,2020")
            args.climatology_range = tuple(int(x.strip()) for x in args.climatology_range.replace('(', '').replace(')', '').split(','))

    return args

if __name__ == "__main__":
# Force multiprocessing to 'spawn' instead of 'fork' to prevent HDF5 core dumps
    import multiprocessing
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass  # Catch if it's already been set
    
    args = parse_args()
    run_anomaly_pipeline(prods=args.prods,
                         periods=args.periods,
                         dataset=args.dataset,
                         dataset_version=args.version,
                         map_subset=args.map_subset,
                         daterange=args.daterange,
                         climatology_range=args.climatology_range,
                         stat_var=args.stat_var,
                         parallel_runs=args.parallel_runs,
                         verify_existing=args.verify_existing,
                         logfile=args.logfile,
                         verbose=args.verbose,
                         debug=args.debug)

    # ==========================================
    # 💻 Example terminal window commands:
    # ==========================================
    #
    # 1. Standard Run:
    # python3 anomaly_pipeline.py --prods SST --periods W M A --map_subset NWA --parallel_runs 4
    #
    # 2. Multi-Product Run and Custom Statistic:
    # python3 anomaly_pipeline.py --prods CHL PSC --periods M --stat_var median --map_subset NES 
    #
    # 3. Auto-generated logfile:
    # Auto-generated log: python3 anomaly_pipeline.py --prods SST --periods M --logfile
    #
    # 4. Custom logfile:
    # python3 anomaly_pipeline.py --prods SST --periods M --logfile /custom/path/test_anomaly.log
    
# run_psc.py
import argparse
import sys
import multiprocessing
from pathlib import Path
import ast

from utilities import run_psc_pipeline

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
    parser = argparse.ArgumentParser(description="Run phytoplankton size class pipeline")
    parser.add_argument("--chl_dataset", type=str, required=False, help="Name of CHL dataset")
    parser.add_argument("--sst_dataset", type=str, required=False, help="Name of SST dataset")
    parser.add_argument("--map_subset", type=str, required=False, help="Name of the map region (e.g. NES, NWA) to subset the data to")
    parser.add_argument("--daterange", type=str, help="Flexible date input: year(s), date(s), or range")
    parser.add_argument("--parallel_runs", type=int, default=1, help="The number of stats jobs to run in parallel")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress logs")
    parser.add_argument("--debug", action="store_true", help="Enter debug mode")
    parser.add_argument("--logfile", nargs='?', const="auto", default=None, 
                        help="Path to log file. Use flag without a path to autogenerate.")
    args = parser.parse_args()

    for key, val in vars(args).items():
        if isinstance(val, str) and val.strip().lower() == "none":
            setattr(args, key, None)

    if args.daterange:
        try:
            parsed = ast.literal_eval(args.daterange)
            args.daterange = flatten_dates(parsed)
        except Exception:
            args.daterange = [args.daterange]

    return args

if __name__ == "__main__":
    # Force multiprocessing to 'spawn' instead of 'fork' to prevent HDF5 core dumps
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass  # Catch if it's already been set

    args = parse_args()

    run_psc_pipeline(
        chl_dataset=args.chl_dataset, 
        sst_dataset=args.sst_dataset, 
        map_subset=args.map_subset, 
        daterange=args.daterange, 
        parallel_runs=args.parallel_runs,
        overwrite=args.overwrite,
        verbose=args.verbose,
        debug=args.debug,
        logfile=args.logfile
    )

    # Example terminal window command
    # python3 run_psc_pipeline.py --sst_dataset CORALSST --daterange 1998

# run_pp.py
import argparse
import sys
from pathlib import Path
import ast

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=False)

from utilities.calc_primprod import run_pp_pipeline

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
    parser.add_argument("--sst_dataset", type=str, required=True, help="Name of SST dataset")
    parser.add_argument("--daterange", type=str, help="Flexible date input: year(s), date(s), or range")
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
    run_pp_pipeline(sst_dataset=args.sst_dataset, daterange=args.daterange)

    # Example terminal window command
    # python3 run_pp_pipeline.py --sst_dataset CORALSST --daterange 1998
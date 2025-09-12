# run_pp.py
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=False)

from utilities.calc_phytosizeclass import run_psc_pipeline

def parse_args():
    parser = argparse.ArgumentParser(description="Run phytoplankton size class pipeline")
    parser.add_argument("--sst_dataset", type=str, required=True, help="Name of SST dataset")
    parser.add_argument("--daterange", nargs="+", help="Flexible date input: year(s), date(s), or range")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_psc_pipeline(sst_dataset=args.sst_dataset, daterange=args.daterange)

    # Example terminal window command
    # python3 run_pp_pipeline.py --sst_dataset CORALSST --daterange 1998
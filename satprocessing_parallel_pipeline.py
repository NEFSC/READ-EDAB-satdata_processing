# run_psc_parallel.py
import argparse
import sys
from pathlib import Path
import subprocess
import argparse
from pathlib import Path
import time
from datetime import datetime


# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utilities.bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=False)

from utilities.file_utilities import get_prod_files
from utilities.date_utilities import get_source_file_dates

import time

def run_rolling(pipeline, prod, dataset, chl_dataset=None, sst_dataset=None, par_dataset=None, rrs_dataset=None,
                subset=None, max_parallel=5, verbose=False, log_dir=None, summary_log=None, timestamp=None):

    dataset = resolve_dataset(prod, chl_dataset, sst_dataset, par_dataset, rrs_dataset)
    if verbose and not dataset:
        print(f"ℹ No dataset provided for '{prod}' — using default from product_defaults()")

    years = discover_years(prod=prod, dataset=dataset, verbose=verbose)
    if not years:
        return

    queue = list(years)
    active = {}
    completed = []

    with open(summary_log, "w") as summary:
        summary.write(f"📝 Rolling pipeline summary: {pipeline.upper()} — {timestamp}\n")
        summary.write(f"📁 Log directory: {log_dir}\n\n")

        while queue or active:
            # Launch new jobs if slots are available
            while queue and len(active) < max_parallel:
                y = queue.pop(0)
                proc = run_year(
                    pipeline=pipeline,
                    year=y,
                    sst_dataset=sst_dataset,
                    chl_dataset=chl_dataset,
                    par_dataset=par_dataset,
                    rrs_dataset=rrs_dataset,
                    subset=subset,
                    log_dir=log_dir,
                    timestamp=timestamp
                )
                active[y] = proc
                log_path = log_dir / f"{pipeline}_{y}_{timestamp}.log"
                summary.write(f"🚀 Launched year {y}: {log_path.name}\n")

            # Check for completed jobs
            for y in list(active.keys()):
                if active[y].poll() is not None:
                    code = active[y].returncode
                    if code == 0:
                        summary.write(f"✅ Completed year: {y}\n")
                    else:
                        summary.write(f"❌ Failed year: {y} (return code {code})\n")
                    completed.append(y)
                    del active[y]

            time.sleep(1)

        summary.write(f"\n🎯 All years processed: {completed}\n")

def resolve_dataset(prod, chl_dataset, sst_dataset, par_dataset, rrs_dataset):
    prod = prod.lower().strip()
    return {
        "chl": chl_dataset,
        "sst": sst_dataset,
        "par": par_dataset,
        "rrs": rrs_dataset
    }.get(prod)

def discover_years(prod, dataset, verbose=False):
    files = get_prod_files(prod=prod, dataset=dataset, verbose=verbose)
    if not files:
        print(f"⚠ No files found for product '{prod}' in dataset '{dataset}'")
        return []
    dates = get_source_file_dates(files, format="yyyy")
    years = sorted(set(y for y in dates if y and y.isdigit()))
    if verbose:
        print(f"📅 Discovered {len(years)} unique years: {years}")
    return years

def chunk_years(years, batch_size):
    return [years[i:i + batch_size] for i in range(0, len(years), batch_size)]

def build_command(pipeline, year, chl_dataset=None, sst_dataset=None, par_dataset=None, rrs_dataset=None, 
                  subset=None, log_dir=None, timestamp=None):
    pipeline = pipeline.lower().strip()
    script_map = {
        "psc": "psc_pipeline.py",
        "pp": "psc_pipeline.py"
    }

    if pipeline not in script_map:
        raise ValueError(f"Unsupported pipeline: {pipeline}")

    python_exe = sys.executable  # This ensures you use the current Python interpreter
    cmd = [python_exe, script_map[pipeline]]
    if sst_dataset:
        cmd += ["--sst_dataset", sst_dataset]
    if chl_dataset:
        cmd += ["--chl_dataset", chl_dataset]
    if par_dataset:
        cmd += ["--par_dataset", par_dataset]
    if rrs_dataset:
        cmd += ["--rrs_dataset", rrs_dataset]
    if subset:
        cmd += ["--subset", subset]
    cmd += ["--daterange", str(year)]

    if log_dir:
        log_path = Path(log_dir) / f"{pipeline}_{year}_{timestamp}.log"
        cmd += ["--logfile", str(log_path)]

    return cmd

def run_year(pipeline, year, chl_dataset=None, sst_dataset=None, par_dataset=None, rrs_dataset=None, subset=None, log_dir=None, timestamp=None):
    cmd = build_command(
        pipeline=pipeline,
        year=year,
        chl_dataset=chl_dataset,
        sst_dataset=sst_dataset,
        par_dataset=par_dataset,
        rrs_dataset=rrs_dataset,
        subset=subset,
        log_dir=log_dir,
        timestamp=timestamp
    )
    print("Pipeline command:", cmd)
    return subprocess.Popen(cmd)

import time

def run_batches(pipeline, prod, dataset, chl_dataset=None, sst_dataset=None, par_dataset=None, rrs_dataset=None,
                subset=None, batch_size=5, verbose=False, log_dir=None, summary_log=None, timestamp=None):

    dataset = resolve_dataset(prod, chl_dataset, sst_dataset, par_dataset, rrs_dataset)
    if verbose and not dataset:
        print(f"ℹ No dataset provided for '{prod}' — using default from product_defaults()")

    years = discover_years(prod=prod, dataset=dataset, verbose=verbose)
    if not years:
        return

    batches = chunk_years(years, batch_size)
    with open(summary_log, "w") as summary:
        summary.write(f"📝 Pipeline summary: {pipeline.upper()} — {timestamp}\n")
        summary.write(f"📁 Log directory: {log_dir}\n\n")

        for batch in batches:
            summary.write(f"🚀 Launching batch: {batch}\n")
            procs = {}

            # Launch all jobs in the batch
            for y in batch:
                proc = run_year(
                    pipeline=pipeline,
                    year=y,
                    sst_dataset=sst_dataset,
                    chl_dataset=chl_dataset,
                    par_dataset=par_dataset,
                    rrs_dataset=rrs_dataset,
                    subset=subset,
                    log_dir=log_dir,
                    timestamp=timestamp
                )
                procs[y] = proc
                log_path = log_dir / f"{pipeline}_{y}_{timestamp}.log"
                summary.write(f"  • Year {y}: {log_path.name}\n")

            # Poll until all jobs finish
            while procs:
                for y in list(procs.keys()):
                    if procs[y].poll() is not None:  # Finished
                        code = procs[y].returncode
                        if code == 0:
                            summary.write(f"✅ Completed year: {y}\n")
                        else:
                            summary.write(f"❌ Failed year: {y} (return code {code})\n")
                        del procs[y]
                time.sleep(1)  # Avoid tight loop

            summary.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a satprocessing pipelines in parallel by detected years")
    parser.add_argument("--pipeline", type=str, required=True,choices=["psc","pp"],help="Name of the pipeline (e.g. 'psc' or 'pp') to run")
    parser.add_argument("--main_prod",type=str, default="chl", choices=["chl","sst","par","rrs"],help="The name of the product (e.g. chl, sst, rrs) to determine the number of available years")
    parser.add_argument("--chl_dataset", type=str, help="Name of CHL dataset")
    parser.add_argument("--sst_dataset", type=str, help="Name of SST dataset")
    parser.add_argument("--par_dataset", type=str, help="Name of PAR dataset")
    parser.add_argument("--rrs_dataset", type=str, help="Name of RRS dataset")
    parser.add_argument("--subset", type=str, help="Region subset (e.g. NES, NWA)")
    parser.add_argument("--logfile", type=str, help="Optional path to log file for this run")
    parser.add_argument("--batch_size", type=int, default=4, help="Number of years to run in parallel")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--dry_run", action="store_true", help="Preview commands without executing")
    args = parser.parse_args()

    log_root = env["satlogs_path"]
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    summary_log_path = log_root / f"{args.pipeline.lower()}_summary_{timestamp}.log"

    log_dir = log_root / args.pipeline.lower()
    log_dir.mkdir(parents=True, exist_ok=True)

    """
    run_batches(
        pipeline=args.pipeline.lower().strip(),
        prod=args.main_prod.lower().strip(),
        dataset=args.sst_dataset,
        chl_dataset=args.chl_dataset,
        sst_dataset=args.sst_dataset,
        par_dataset=args.par_dataset,
        rrs_dataset=args.rrs_dataset,
        subset=args.subset,
        batch_size=args.batch_size,
        verbose=args.verbose,
        log_dir=log_dir,
        summary_log=summary_log_path,
        timestamp=timestamp
    )
    """
    run_rolling(
        pipeline=args.pipeline.lower().strip(),
        prod=args.main_prod.lower().strip(),
        dataset=args.sst_dataset,
        chl_dataset=args.chl_dataset,
        sst_dataset=args.sst_dataset,
        par_dataset=args.par_dataset,
        rrs_dataset=args.rrs_dataset,
        subset=args.subset,
        max_parallel=args.batch_size,  # reuse batch_size as parallel limit
        verbose=args.verbose,
        log_dir=log_dir,
        summary_log=summary_log_path,
        timestamp=timestamp
    )
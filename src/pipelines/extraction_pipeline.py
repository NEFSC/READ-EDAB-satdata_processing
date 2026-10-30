# extraction_pipeline.py
import argparse
import sys
from pathlib import Path
import traceback

from utilities import run_extraction_pipeline


def parse_args():
    parser = argparse.ArgumentParser(description="Headless Regional Data Extraction Pipeline")
    
    # Primary Configuration
    parser.add_argument("--prods", type=str, nargs='+', help="Product(s) to extract (e.g., CHL SST)")
    parser.add_argument("--periods", type=str, nargs='+', help="Period(s) to extract (e.g., M A DOY)")
    parser.add_argument("--dataset", type=str, default=None, help="Specific dataset to extract from")
    parser.add_argument("--map_subset", type=str, default="NWA", help="Map subset for the source files (default: NWA)")
    
    # Spatial Extraction Parameters
    parser.add_argument("--shapefile", type=str, default=None, help="Name or path of the shapefile to use for subarea extraction")
    parser.add_argument("--subareas", type=str, nargs='+', default=None, help="Specific subareas to extract (if omitted, extracts all)")
    parser.add_argument("--subarea_column", type=str, default=None, help="The attribute column containing subarea names")
    parser.add_argument("--merge_all", action="store_true", help="Merge all shapefile subareas into a single geometry")
    parser.add_argument("--bbox", type=float, nargs=4, metavar=('MINX', 'MINY', 'MAXX', 'MAXY'), help="Bounding box extraction")
    
    # Analytical Targets
    parser.add_argument("--stat_type", type=str, default=None, help="The target statistic (e.g., mean, median, max)")
    parser.add_argument("--data_type", type=str, nargs='+', default=["STATS"], help="The type of data to extract (e.g., STATS, ANOM). Defaults to STATS.")
    
    # File Handling & Logging
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output data")
    parser.add_argument("--delete_corrupt", action="store_true", help="Delete identified corrupt source files")
    parser.add_argument("--parallel_runs", type=int, default=1, help="Number of parallel workers (default: 1)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--debug", action="store_true", help="Enable detailed tracebacks and troubleshooting output")
    parser.add_argument("--logfile", nargs='?', const="auto", default=None, help="Generate persistent logs (or path to logfile)")

    return parser.parse_args()

if __name__ == "__main__":
    # Force multiprocessing to 'spawn' instead of 'fork' to prevent HDF5 core dumps
    import multiprocessing
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass 
        
    args = parse_args()

    # We must have at least one spatial method defined if not running the full GLOBAL map_subset
    if not args.shapefile and not args.bbox and args.map_subset == "GLOBAL":
        print("❌ Error: Must provide a --shapefile, --bbox, or non-GLOBAL --map_subset.")
        sys.exit(1)

    # Convert args Namespace to dictionary so we can cleanly unpack it as **kwargs
    kwargs = vars(args)

    # Pop explicit arguments to pass separately to the function signature
    prods = kwargs.pop('prods')
    periods = kwargs.pop('periods')
    shapefile = kwargs.pop('shapefile')
    bbox = kwargs.pop('bbox')
    stat_type = kwargs.pop('stat_type')
    data_type = kwargs.pop('data_type')
    
    try:
        run_extraction_pipeline(
            prods=prods, 
            periods=periods, 
            shapefile=shapefile, 
            bbox=bbox, 
            stat_type=stat_type,
            data_type=data_type, 
            **kwargs
        )
    except Exception as e:
        print(f"\n❌ FATAL PIPELINE CRASH: {e}")
        if args.debug: traceback.print_exc()
        sys.exit(1)
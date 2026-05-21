import sys
import os
import argparse
import xarray as xr
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utilities.bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=False)

from utilities.statanom_utilities import build_stats_map

def run_map_diagnostic(prod, period, dataset, subset):
    print("\n" + "="*80)
    print(f"🚀 DIAGNOSTICS FOR build_stats_map: {prod} | {period} | {dataset}")
    print("="*80)

    # 1. Run the map builder
    stats_map = build_stats_map(
        prod=prod, 
        period=period, 
        dataset=dataset, 
        subset=subset, 
        verbose=False, 
        overwrite=False
    )

    if not stats_map:
        print("❌ Map returned empty. Cannot diagnose freshness.")
        return

    # 2. Find a file that exists but is marked as needing an update
    target_task = None
    target_period = None
    
    for out_period, task in stats_map.items():
        if not task['is_up_to_date'] and os.path.exists(task['output']):
            target_task = task
            target_period = out_period
            break

    if not target_task:
        print("✅ All existing files are correctly marked as up-to-date!")
        return

    # 3. Perform the Deep Dive on the failure
    out_path = target_task['output']
    input_files = target_task['inputs']
    
    print(f"\n🔍 DEEP DIVE: Why does '{target_period}' need an update?")
    print(f"📁 Output File: {out_path}")
    
    # --- Check 1: Modification Times ---
    out_mtime = os.path.getmtime(out_path)
    newest_input_mtime = max(os.path.getmtime(f) for f in input_files)
    
    print("\n--- TEST 1: Modification Times (mtime) ---")
    print(f"Output mtime:        {out_mtime}")
    print(f"Newest Input mtime:  {newest_input_mtime}")
    
    mtime_ok = out_mtime > newest_input_mtime
    if mtime_ok:
        print("✅ PASS: Output is newer than all inputs.")
    else:
        print("❌ FAIL: One or more inputs are newer than the output file!")
        # Find which one
        for f in input_files:
            if os.path.getmtime(f) >= out_mtime:
                print(f"   ↳ Newer Input: {os.path.basename(f)}")

    # --- Check 2: Metadata Match ---
    print("\n--- TEST 2: Internal Metadata Match ---")
    try:
        with xr.open_dataset(out_path, engine='netcdf4', decode_times=False, decode_coords=False) as existing_ds:
            stored_files_str = existing_ds.attrs.get('source_files', '')
            
        if not stored_files_str:
            print("❌ FAIL: 'source_files' attribute is missing or empty in the NetCDF.")
        else:
            stored_basenames = set(f.strip() for f in stored_files_str.split(','))
            current_basenames = set(os.path.basename(f) for f in input_files)
            
            if stored_basenames == current_basenames:
                print("✅ PASS: Internal source_files match current inputs.")
            else:
                print("❌ FAIL: Internal source_files DO NOT match current inputs.")
                print("\n   Missing from Output (New inputs added):")
                print(f"   {current_basenames - stored_basenames}")
                print("\n   Missing from Current (Inputs removed):")
                print(f"   {stored_basenames - current_basenames}")
                
    except Exception as e:
        print(f"❌ FAIL: Could not read NetCDF attributes. Error: {e}")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test stats map freshness logic")
    parser.add_argument("--prod", type=str, required=True)
    parser.add_argument("--period", type=str, required=True)
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--subset", type=str, required=False, default="GLOBAL")
    
    args = parser.parse_args()
    run_map_diagnostic(args.prod, args.period, args.dataset, args.subset)

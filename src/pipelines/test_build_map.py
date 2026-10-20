import sys
import gc
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utilities.bootstrap.environment import bootstrap_environment
env = bootstrap_environment(verbose=True)

from utilities.src.utilities.stats_utilities import build_stats_map

def run_test():
    print("\n" + "="*80)
    print("🧪 ISOLATED TEST: build_stats_map()")
    print("="*80)
    
    # 🎯 Match the parameters from your crashing run
    prod = "PSC"
    period = "D3"
    dataset = "OCCCI"
    map_subset = "NES"
    
    # Limit to a 3-month block that covers the crash point (Feb 5, 1998)
    daterange = ["19980101", "19980331"] 
    
    try:
        # Force garbage collection before we start the tight loop
        gc.collect() 
        
        stats_map = build_stats_map(
            prod=prod,
            period=period,
            dataset=dataset,
            map_subset=map_subset,
            daterange=daterange,
            verbose=True,
            debug=True
        )
        
        print("\n" + "="*80)
        print(f"✅ TEST SUCCESSFUL: Successfully mapped {len(stats_map)} tasks without segfaulting.")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ STANDARD EXCEPTION CAUGHT: {e}")
        import traceback
        traceback.print_exc()
        print("="*80)

if __name__ == "__main__":
    run_test()
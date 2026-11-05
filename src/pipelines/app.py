import sys
from pathlib import Path
import subprocess

print("**************************************************** Starting EDAB Satellite Data Processing Pipeline ****************************************************", flush=True)
print(f"Current working directory: {Path.cwd()}", flush=True)

try:
    print("Attempting installation of EDAB Utilities Package...", flush=True)

    # Bypass Git completely by using the direct ZIP download link.
    # This prevents the Windows Git Credential Manager from hanging the subprocess.
    github_zip_url = "https://github.com/NEFSC/READ-EDAB-Utilities-py/archive/refs/heads/main.zip"

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", github_zip_url],
        check=True,
        timeout=120,          
        stdout=sys.stdout,    
        stderr=subprocess.STDOUT
    )
    
except subprocess.TimeoutExpired:
    print("Failed to install EDAB Utilities Package: The installation timed out.", file=sys.stderr, flush=True)
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"Failed to install EDAB Utilities Package. Error: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

print("Running EDAB Satellite Data Processing Pipeline...", flush=True)
try:
    import satdata_processing_pipeline
except ImportError:
    print("The 'satdata_processing_pipeline' module is not installed.", file=sys.stderr, flush=True)
    sys.exit(1)

print("Starting main pipeline execution...", flush=True)
#satdata_processing_pipeline.main()
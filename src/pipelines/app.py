import sys
import os
import platform
import json
import yaml
from pathlib import Path
import subprocess

def source_assets(yaml_file="assets.yaml"):
    """Reads paths and URLs from a YAML configuration file."""
    yaml_path = Path.cwd() / yaml_file
    if not yaml_path.exists():
        print(f"FATAL: Configuration file {yaml_path} not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)

def install_custom_package(pkg_name, package_config):
    """Helper to install a package dynamically from local editable path or GitHub."""
    print(f"Attempting installation of {pkg_name} via pip...", flush=True)
    
    local_path = package_config.get("local_path")
    github_url = package_config.get("github_url")
    
    pip_cmd = [sys.executable, "-m", "pip", "install"]

    # Check if local path is provided and actually exists
    if local_path and Path(local_path).exists():
        print(f"Installing {pkg_name} from local path in editable mode: {local_path}", flush=True)
        pip_cmd.extend(["-e", local_path])
    elif github_url:
        print(f"Installing {pkg_name} from GitHub ZIP URL...", flush=True)
        pip_cmd.append(github_url)
    else:
        print(f"Skipping {pkg_name}: No valid local_path or github_url provided in config.", flush=True)
        return

    subprocess.run(
        pip_cmd,
        check=True,
        timeout=120,          
        stdout=sys.stdout,    
        stderr=subprocess.STDOUT
    )

print("**************************************************** new Starting EDAB Satellite Data Processing Pipeline ****************************************************", flush=True)
print(f"Current working directory: {Path.cwd()}", flush=True)

# 0. Load assets from YAML
config = source_assets("assets.yaml")

try:
    print("Attempting to install complex dependencies via Conda...", flush=True)
    
    # 1. Dynamically locate the conda executable for the current environment
    if platform.system() == "Windows":
        conda_exe = Path(sys.prefix) / "Scripts" / "conda.exe"
    else:
        conda_exe = Path(sys.prefix) / "bin" / "conda"
        
    if not conda_exe.exists():
        conda_exe = "conda"

    # 2. Install any required Conda packages (e.g., esmpy)
    subprocess.run(
        [str(conda_exe), "install", "-y", "-c", "conda-forge", "esmpy"],
        check=True,
        timeout=300,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT
    )

    # 3. Install custom packages via pip using the config dictionary
    install_custom_package("Resources Package", config["packages"]["resources"])
    install_custom_package("EDAB Utilities Package", config["packages"]["utilities"])

except subprocess.TimeoutExpired:
    print("Failed to install dependencies: The installation timed out.", file=sys.stderr, flush=True)
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"Failed to install dependencies. Error: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

print("Starting main pipeline execution...", flush=True)

# 4. Define the path to the pipeline script
pipeline_script_path = Path.cwd() / "satdata_processing_pipeline.py"

if not pipeline_script_path.exists():
    print(f"FATAL: Could not find {pipeline_script_path}", file=sys.stderr, flush=True)
    sys.exit(1)

# ==========================================
# EXPLICIT PATH DICTIONARY CONFIGURATION
# ==========================================
# Write config to a JSON file to pass to the subprocess
config_file = Path.cwd() / "run_config.json"
with open(config_file, "w") as f:
    # We pass the path_config section from the YAML directly into the JSON
    json.dump(config["path_config"], f)
# ==========================================

# 5. Build the command with the required arguments
pipeline_cmd = [
    sys.executable,  
    str(pipeline_script_path),
    "--config", str(config_file),  # Inject the explicit paths dictionary here
    "--dataset", "OCCCI",        
    "--map_subset", "NWA",
    "--run_stats"                
]

print(f"Executing: {' '.join(pipeline_cmd)}", flush=True)

# 6. Run the pipeline script
try:
    result = subprocess.run(
        pipeline_cmd,
        check=True,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT
    )
except subprocess.CalledProcessError as e:
    print(f"Pipeline execution failed with Exit Code: {e.returncode}", file=sys.stderr, flush=True)
    sys.exit(e.returncode)

print("Pipeline wrapper finished successfully.", flush=True)
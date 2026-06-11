#!/bin/bash
set -e # Exit immediately if any command fails

ENV_NAME="satprocessing"
YML_PATH="./satprocessing.yml"

# 2. Parse command-line flags (-n for name, -f for file, -h for help)
while getopts "n:f:h" opt; do
  case $opt in
    n) ENV_NAME="$OPTARG" ;;
    f) YML_PATH="$OPTARG" ;;
    h) 
      echo "Usage: $0 [-n env_name] [-f yml_path]"
      echo "  -n  Name of the Conda environment (default: satprocessing)"
      echo "  -f  Path to the environment YAML file (default: ./satprocessing.yml)"
      exit 0 
      ;;
    *) 
      echo "Usage: $0 [-n env_name] [-f yml_path]" >&2
      exit 1 
      ;;
  esac
done

echo "🔧 Setting up Conda environment: $ENV_NAME"

# 1. Verify the YAML exists
if [ ! -f "$YML_PATH" ]; then
  echo "❌ Environment file not found: $YML_PATH"
  exit 1
fi

# 2. Verify Conda is installed and accessible
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed or not in your system PATH."
    exit 1
fi

# 3. Check if the environment already exists
# This extracts the first column of the env list and checks for an exact match
if conda info --envs | awk '{print $1}' | grep -Fxq "$ENV_NAME"; then
    echo "🔄 Environment '$ENV_NAME' found! Syncing packages with $YML_PATH..."
    echo "📋 Calculating differences... Check the transaction report below for added/removed packages:"
    # The --prune flag ensures the environment matches the YAML exactly (removing extra packages)
    conda env update --name "$ENV_NAME" --file "$YML_PATH" --prune
else
    echo "📦 Environment '$ENV_NAME' not found. Creating it from scratch..."
    conda env create --name "$ENV_NAME" --file "$YML_PATH"
fi

# 4. Safely test the environment without activating the shell
echo "🧪 Testing environment setup..."
if conda run -n "$ENV_NAME" python -c "import numpy; print('✅ NumPy version:', numpy.__version__)"; then
    echo "🎉 Setup complete! To start using it, run: conda activate $ENV_NAME"
else
    echo "❌ NumPy not found or environment test failed!"
    exit 1
fi

# 7. Export the exact environment state to a date-stamped file
echo "💾 Saving environment state..."
LOG_DIR="./env_logs"
mkdir -p "$LOG_DIR" # Create the directory if it doesn't exist

# Generate a timestamp (e.g., 2026-06-11_17-00-24)
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
EXPORT_FILE="${LOG_DIR}/${ENV_NAME}_${TIMESTAMP}.yml"

# Export the exact environment details
conda env export -n "$ENV_NAME" > "$EXPORT_FILE"

echo "✅ Environment state saved to: $EXPORT_FILE"
echo "🎉 Setup complete! To start using the environment, run: conda activate $ENV_NAME"

# To run with the default environment and file, simply execute:
# ./setup_env.sh

# To change the environment name
# ./setup_env.sh -n my_new_env

# To change the yml file
# ./setup_env.sh -n data_science_env -f ./other_project.yml

# To change both the environment name and yml file
# ./setup_env.sh -f ./other_project.yml

# To see the help menu if you forget the flags
# ./setup_env.sh -h
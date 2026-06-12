#!/bin/bash
set -e # Exit immediately if any command fails

# 1. Set default values
ENV_NAME="satprocessing"
YML_PATH="./satprocessing.yml"
OVERWRITE=false

# 2. Parse command-line flags (-n for name, -f for file, -h for help)
while getopts "n:f:oh" opt; do
  case $opt in
    n) ENV_NAME="$OPTARG" ;;
    f) YML_PATH="$OPTARG" ;;
    o) OVERWRITE=true ;;
    h) 
      echo "Usage: $0 [-n env_name] [-f yml_path] [-o]"
      echo "  -n  Name of the Conda environment (default: satprocessing)"
      echo "  -f  Path to the environment YAML file (default: ./satprocessing.yml)"
      echo "  -o  Overwrite: completely remove the existing environment and start fresh"
      exit 0 
      ;;
    *) 
      echo "Usage: $0 [-n env_name] [-f yml_path] [-o]" >&2
      exit 1 
      ;;
  esac
done

echo "🔧 Setting up Conda environment: $ENV_NAME"
echo "📄 Using environment file: $YML_PATH"

if [ "$OVERWRITE" = true ]; then
    echo "⚠️  Overwrite mode activated. The environment will be completely rebuilt."
fi

# 3. Verify the YAML exists
if [ ! -f "$YML_PATH" ]; then
  echo "❌ Error: Environment file not found: $YML_PATH. Setup is incomplete."
  exit 1
fi

# 4. Verify Conda is installed and accessible
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed or not in your system PATH."
    exit 1
fi

# 5. Check if the environment already exists and catch installation errors
# This extracts the first column of the env list and checks for an exact match
if conda info --envs | awk '{print $1}' | grep -Fxq "$ENV_NAME"; then
    if [ "$OVERWRITE" = true ]; then
        echo "🗑️  Removing existing environment '$ENV_NAME' for a fresh start..."
        conda env remove --name "$ENV_NAME" -y
        
        echo "📦 Creating '$ENV_NAME' from scratch..."
        if ! conda env create --name "$ENV_NAME" --file "$YML_PATH"; then
            echo "❌ ERROR: Conda failed to resolve or download packages. Setup is incomplete."
            exit 1
        fi
    else
        echo "🔄 Environment '$ENV_NAME' found! Syncing packages with $YML_PATH..."
        echo "📋 Calculating differences... Check the transaction report below for added/removed packages:"
    
        # If the update fails, print the custom error and exit
        # The --prune flag ensures the environment matches the YAML exactly (removing extra packages)
        if ! conda env update --name "$ENV_NAME" --file "$YML_PATH" --prune; then
            echo "❌ ERROR: Conda failed to update the packages. Setup is incomplete."
            exit 1
        fi  
    fi 
else
    echo "📦 Environment '$ENV_NAME' not found. Creating it from scratch..."
# If the creation fails, print the custom error and exit
    if ! conda env create --name "$ENV_NAME" --file "$YML_PATH"; then
        echo "❌ ERROR: Conda failed to resolve or download packages. Setup is incomplete."
        exit 1
    fi
fi

# 6. Safely test the environment without activating the shell
echo "🧪 Testing environment setup..."
if conda run -n "$ENV_NAME" python -c "import numpy; print('✅ NumPy version:', numpy.__version__)"; then
    echo "🎉 Setup complete! To start using it, run: conda activate $ENV_NAME"
else
    echo "❌ ERROR: NumPy not found or environment test failed!"
    exit 1
fi

# 7. Export the exact environment state to a date-stamped file
echo "💾 Saving environment state..."
LOG_DIR="./env_logs"
mkdir -p "$LOG_DIR" # Create the directory if it doesn't exist

# Generate a timestamp (e.g., 2026-06-11_17-00-24)
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
EXPORT_FILE="${LOG_DIR}/${ENV_NAME}_${TIMESTAMP}.yml"

# 8. Export the exact environment details
if conda env export -n "$ENV_NAME" > "$EXPORT_FILE"; then
    echo "✅ Environment state saved to: $EXPORT_FILE"
    echo "🎉 Setup complete! To start using the environment, run: conda activate $ENV_NAME"
else
    echo "⚠ WARNING: Environment was created, but failed to save the log file to $EXPORT_FILE."
fi

# To run with the default environment and file, simply execute:
# ./setup_env.sh

# To replace/overwrite an exisiting environement
# ./setup_env.sh -o

# To change the environment name
# ./setup_env.sh -n my_new_env

# To change the yml file
# ./setup_env.sh -n data_science_env -f ./other_project.yml

# To change both the environment name and yml file
# ./setup_env.sh -f ./other_project.yml

# To see the help menu if you forget the flags
# ./setup_env.sh -h
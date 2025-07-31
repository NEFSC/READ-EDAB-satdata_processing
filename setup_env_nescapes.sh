#!/bin/bash

ENV_NAME="satprocessing"
YML_PATH="./satprocessing.yml"
REQUIREMENTS="./requirements.txt"

echo "🔧 Creating Conda environment: $ENV_NAME"

# Check if yml file exists
if [ ! -f "$YML_PATH" ]; then
  echo "❌ Environment file not found: $YML_PATH"
  exit 1
fi

# Make sure Conda can activate environments
if ! conda info --envs &>/dev/null; then
  echo "🔄 Running conda init to enable activation..."
  conda init bash
  exec "$SHELL"
fi

# Create environment
conda env create -f "$YML_PATH" --name "$ENV_NAME"

# Activate environment
source activate "$ENV_NAME"

# Optional pip install — only if requirements.txt exists
if [ -f "$REQUIREMENTS" ]; then
  echo "📦 Installing pip packages from $REQUIREMENTS"
  pip install -r "$REQUIREMENTS"
else
  echo "✅ Skipping pip install: no requirements.txt found"
fi

# Quick environment test
echo "🧪 Testing environment setup..."
python -c "import numpy; print('NumPy version:', numpy.__version__)" || echo "❌ NumPy not found!"

echo "🎉 Setup complete! To activate later: conda activate $ENV_NAME"

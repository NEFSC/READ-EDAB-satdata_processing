#!/usr/bin/env bash
set -euo pipefail

# === CONFIG ===
ENV_NAME="satprocessing"
ENV_YML="env/satprocessing.yml"
REQ_FILE="env/requirements.txt"
CREATE_LISTS_SCRIPT="scripts/create_env_lists.py"
SNAPSHOT_SCRIPT="scripts/snapshot_env.py"
DRY_RUN="${DRY_RUN:-0}"

# === UTILITY ===
run_cmd() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "🔍 [DRY RUN] $*"
  else
    echo "🚀 Running: $*"
    eval "$@"
  fi
}

# === Activate Conda ===
run_cmd "source \"\$(conda info --base)/etc/profile.d/conda.sh\""

# === Check if environment exists ===
ENV_EXISTS=$(conda info --envs | awk '{print $1}' | grep -Fx "$ENV_NAME" || true)

if [[ -z "$ENV_EXISTS" ]]; then
  echo "🆕 Environment '$ENV_NAME' does not exist. Creating from $ENV_YML..."
  run_cmd "conda env create -n \"$ENV_NAME\" -f \"$ENV_YML\""
else
  echo "✅ Environment '$ENV_NAME' already exists."
fi

# === Activate environment ===
run_cmd "set +u; conda activate \"$ENV_NAME\"; set -u"

# === Install pip packages ===
if [[ -f "$REQ_FILE" ]]; then
  echo "📦 Installing pip packages from $REQ_FILE..."
  run_cmd "pip install -r \"$REQ_FILE\""
else
  echo "⚠️ No requirements.txt found at $REQ_FILE"
fi

# === Regenerate environment lists ===
echo "🔄 Updating .yml and requirements.txt..."
run_cmd "python \"$CREATE_LISTS_SCRIPT\" $( [[ \"$DRY_RUN\" == \"1\" ]] && echo \"--dry-run\" )"

# === Snapshot environment ===
echo "📸 Archiving environment state..."
run_cmd "python \"$SNAPSHOT_SCRIPT\" $( [[ \"$DRY_RUN\" == \"1\" ]] && echo \"--dry-run\" )"

echo "✅ Environment setup complete."

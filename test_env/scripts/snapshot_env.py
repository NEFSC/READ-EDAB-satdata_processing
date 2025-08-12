import subprocess
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# === CONFIG ===
BASE_DIR = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = BASE_DIR / "env" / "snapshots"
timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
snapshot_path = SNAPSHOT_DIR / f"snapshot_{timestamp}"
conda_file = snapshot_path / "conda_list.txt"
pip_file = snapshot_path / "pip_list.txt"

# === ARGUMENTS ===
parser = argparse.ArgumentParser(description="Snapshot current Conda and pip environment.")
parser.add_argument("--dry-run", action="store_true", help="Simulate snapshot without writing files.")
args = parser.parse_args()

# === UTILITY ===
def run_export(cmd, output_path):
    if args.dry_run:
        print(f"🔍 [DRY RUN] Would run: {' '.join(cmd)} > {output_path}")
    else:
        with output_path.open("w") as f:
            subprocess.run(cmd, stdout=f, check=True)

# === MAIN WORKFLOW ===
print("📸 Starting environment snapshot...")

if args.dry_run:
    print(f"🔍 [DRY RUN] Would create snapshot directory: {snapshot_path}")
else:
    snapshot_path.mkdir(parents=True, exist_ok=True)

run_export(["conda", "list"], conda_file)
run_export(["pip", "freeze"], pip_file)

print("✅ Snapshot complete.")

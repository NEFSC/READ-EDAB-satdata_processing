import subprocess
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# === CONFIG ===
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_DIR = BASE_DIR / "env"
REQ_FILE = ENV_DIR / "requirements.txt"
YML_FILE = ENV_DIR / "satprocessing.yml"
timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

# === ARGUMENTS ===
parser = argparse.ArgumentParser(description="Export Conda and pip environment lists.")
parser.add_argument("--dry-run", action="store_true", help="Simulate actions without modifying files.")
args = parser.parse_args()

# === BACKUP FUNCTION ===
def backup_file(path: Path):
    if path.exists():
        backup = path.with_suffix(path.suffix + f".bak.{timestamp}")
        print(f"📦 Backing up {path.name} → {backup.name}")
        if not args.dry_run:
            shutil.copy(path, backup)

# === EXPORT FUNCTION ===
def export_env():
    print("📜 Exporting Conda environment to .yml...")
    if args.dry_run:
        print(f"🔍 [DRY RUN] Would run: conda env export --no-builds > {YML_FILE}")
    else:
        with YML_FILE.open("w") as f:
            subprocess.run(["conda", "env", "export", "--no-builds"], stdout=f, check=True)

    print("📜 Exporting pip packages to requirements.txt...")
    if args.dry_run:
        print(f"🔍 [DRY RUN] Would run: pip freeze > {REQ_FILE}")
    else:
        with REQ_FILE.open("w") as f:
            subprocess.run(["pip", "freeze"], stdout=f, check=True)

# === MAIN WORKFLOW ===
print("🔧 Starting environment list update...")
backup_file(REQ_FILE)
backup_file(YML_FILE)
export_env()
print("✅ Environment lists updated.")

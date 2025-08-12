import yaml
import subprocess
from datetime import datetime
from pathlib import Path

# === Config ===
env_file = Path("environment.yml")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = env_file.with_name(f"{env_file.stem}_backup_{timestamp}.yml")
new_file = env_file.with_name("environment_updated.yml")

# === Step 1: Backup original ===
env_file.rename(backup_file)

# === Step 2: Load original spec ===
with open(backup_file, "r") as f:
    original = yaml.safe_load(f)

orig_conda = set(pkg.split("=")[0] for pkg in original.get("dependencies", []) if isinstance(pkg, str))
orig_pip = set()
for dep in original.get("dependencies", []):
    if isinstance(dep, dict) and "pip" in dep:
        orig_pip.update(pkg.split("==")[0].lower() for pkg in dep["pip"])

# === Step 3: Get current installed packages ===
def get_conda_list():
    output = subprocess.run(["conda", "list"], capture_output=True, text=True).stdout
    return {line.split()[0]: line.split()[1] for line in output.splitlines() if line and not line.startswith("#")}

def get_pip_list():
    output = subprocess.run(["pip", "freeze"], capture_output=True, text=True).stdout
    return {line.split("==")[0].lower(): line.split("==")[1] for line in output.splitlines() if "==" in line}

current_conda = get_conda_list()
current_pip = get_pip_list()

# === Step 4: Determine new packages ===
new_conda = {k: v for k, v in current_conda.items() if k not in orig_conda}
new_pip = {k: v for k, v in current_pip.items() if k not in orig_pip}

# === Step 5: Build new environment spec ===
new_spec = {
    "name": original.get("name", "updated_env"),
    "channels": original.get("channels", ["defaults"]),
    "dependencies": [f"{k}={v}" for k, v in new_conda.items()]
}

if new_pip:
    new_spec["dependencies"].append({"pip": [f"{k}=={v}" for k, v in new_pip.items()]})

# === Step 6: Write new spec ===
with open(new_file, "w") as f:
    yaml.dump(new_spec, f, sort_keys=False)

print(f"✅ Original backed up to: {backup_file}")
print(f"✅ New environment spec written to: {new_file}")

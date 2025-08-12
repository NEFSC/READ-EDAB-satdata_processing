from pathlib import Path

def parse_explicit(file_path):
    lines = Path(file_path).read_text().splitlines()
    return {
        line.split('#')[0].strip(): line
        for line in lines
        if line and not line.startswith(('#', '@'))
    }

initial = parse_explicit("env_initial.txt")
current = parse_explicit("env_current.txt")

added = {pkg: current[pkg] for pkg in current if pkg not in initial}
removed = {pkg: initial[pkg] for pkg in initial if pkg not in current}
changed = {
    pkg: (initial[pkg], current[pkg])
    for pkg in current
    if pkg in initial and initial[pkg] != current[pkg]
}

print("\n✅ Added Packages:")
for pkg in added.values():
    print(f"  {pkg}")

print("\n❌ Removed Packages:")
for pkg in removed.values():
    print(f"  {pkg}")

print("\n🔄 Changed Versions:")
for old, new in changed.values():
    print(f"  {old}  →  {new}")

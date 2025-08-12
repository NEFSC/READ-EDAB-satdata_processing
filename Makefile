# === ENVIRONMENT SETUP ===
ENV_NAME := satprocessing
SETUP_SCRIPT := setup_scripts/setup_env.sh

.PHONY: setup_env clean_env help

## setup_env: Create or activate the Conda environment, install packages, update .yml and requirements.txt
setup_env:
	@echo "🔧 Running full environment setup for '$(ENV_NAME)'..."
	bash $(SETUP_SCRIPT)

## clean_env: Remove the Conda environment (use with caution!)
clean_env:
	@echo "⚠️ Removing Conda environment '$(ENV_NAME)'..."
	conda remove -n $(ENV_NAME) --all -y

## help: Show available Makefile targets
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "🛠️  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

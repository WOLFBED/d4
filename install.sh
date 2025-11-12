#!/usr/bin/env bash
set -euo pipefail


# Top-level installer that orchestrates checks, venv creation, dependency verification,
# optional external binary installs (with signature verification), desktop entry creation,
# and initial app run.


REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$REPO_ROOT/scripts"


echo "=== MyApp installer ==="


if ! command -v python3 >/dev/null 2>&1; then
echo "python3 not found. Please install Python 3.10+ and re-run."
exit 1
fi


# Ensure we run scripts with python3 from system (not the yet-to-be-created venv)
PY=python3


# 1) Check system-level dependencies (and optionally install them)
$PY "$SCRIPTS/check_dependencies.py"


# 2) Create venv and install Python deps
$PY "$SCRIPTS/setup_venv.py" --repo-root "$REPO_ROOT"


# 3) Optionally install external binaries (with signature verification)
$PY "$SCRIPTS/install_externals.py" --repo-root "$REPO_ROOT"


# 4) Create desktop entry
$PY "$SCRIPTS/create_desktop_entry.py" --repo-root "$REPO_ROOT"


# 5) Perform a first run to create config files
echo "Launching app once to initialize user config..."
VENV_BIN="$HOME/.local/share/myapp/venv/bin"
"$VENV_BIN/python" "$REPO_ROOT/src/myapp/main.py" &


echo "Installation complete. If you used a graphical installer, the app should appear in your desktop's application menu."
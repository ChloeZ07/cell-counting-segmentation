#!/bin/zsh
cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

if [ -z "$PYTHON" ]; then
  echo "Python 3 was not found. Please install Python 3 first."
  read -n 1 -s -r "?Press any key to close."
  exit 1
fi

mkdir -p .mplconfig uploads web_results
echo "Starting cell counter with: $PYTHON"
echo "If this fails because packages are missing, run:"
echo "  $PYTHON -m pip install -r requirements.txt"
echo ""
MPLCONFIGDIR="$PWD/.mplconfig" "$PYTHON" app.py

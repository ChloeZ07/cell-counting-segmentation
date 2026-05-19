#!/bin/zsh
cd "$(dirname "$0")"
mkdir -p .mplconfig uploads web_results
MPLCONFIGDIR="$PWD/.mplconfig" /opt/anaconda3/bin/python app.py

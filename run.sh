#!/bin/bash
# ==============================================================================
# OIL SIF Precursor Detection AI/NLP Platform - One-Click Launcher
# Problem Statement ID: 26165 | Oil India Limited
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================================================"
echo " OIL INDIA LIMITED — AI/NLP SIF PRECURSOR DETECTION SYSTEM"
echo " Problem Statement ID: 26165 | HSE Decision Support Platform"
echo "========================================================================"

# Choose python from .venv or venv or system python
if [ -f ".venv/bin/python3" ]; then
    PY_BIN=".venv/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PY_BIN="venv/bin/python3"
else
    echo "[+] Creating virtual environment '.venv'..."
    python3 -m venv .venv
    PY_BIN=".venv/bin/python3"
fi

echo "[+] Using Python: $($PY_BIN --version)"
echo "[+] Ensuring dependencies are installed..."
$PY_BIN -m pip install -q -r backend/requirements.txt

export PYTHONPATH="$DIR/backend"

echo ""
echo "[+] Starting FastAPI server at http://localhost:8000 ..."
echo "[+] Interactive HSE Dashboard: http://localhost:8000/"
echo "[+] Swagger API Documentation: http://localhost:8000/docs"
echo ""

$PY_BIN -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir "$DIR/backend"

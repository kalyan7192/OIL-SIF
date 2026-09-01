#!/usr/bin/env python3
"""
OIL SIF Precursor AI/NLP Decision Support Engine
Cross-platform Launcher Script
"""
import sys
import subprocess
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BASE_DIR / "data"

def get_python_executable():
    venv_py = BASE_DIR / ".venv" / "bin" / "python3"
    if venv_py.exists():
        return str(venv_py)
    alt_venv_py = BASE_DIR / "venv" / "bin" / "python3"
    if alt_venv_py.exists():
        return str(alt_venv_py)
    return sys.executable

def main():
    print("=" * 70)
    print(" OIL INDIA LIMITED — AI/NLP SIF PRECURSOR DETECTION SYSTEM")
    print(" Problem Statement ID: 26165 | HSE Decision Support Platform")
    print("=" * 70)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["PYTHONPATH"] = str(BACKEND_DIR)
    py_exec = get_python_executable()

    print("\n[+] Starting FastAPI Application Server on http://localhost:8000 ...")
    print("[+] API Docs available at: http://localhost:8000/docs")
    print("[+] HSE Dashboard available at: http://localhost:8000/\n")

    cmd = [
        py_exec,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
        "--app-dir",
        str(BACKEND_DIR)
    ]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[*] Server shutdown gracefully.")

if __name__ == "__main__":
    main()
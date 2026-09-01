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

def is_valid_executable(py_path):
    try:
        res = subprocess.run([str(py_path), "-c", "import sys"], capture_output=True, timeout=2)
        return res.returncode == 0
    except Exception:
        return False

def get_python_executable():
    if sys.platform == "win32":
        candidates = [
            BASE_DIR / ".venv" / "Scripts" / "python.exe",
            BASE_DIR / "venv" / "Scripts" / "python.exe",
        ]
    else:
        candidates = [
            BASE_DIR / ".venv" / "bin" / "python3",
            BASE_DIR / "venv" / "bin" / "python3",
        ]
    for candidate in candidates:
        if candidate.exists() and is_valid_executable(candidate):
            return str(candidate)
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
        "--reload-dir",
        str(BACKEND_DIR / "app"),
        "--reload-dir",
        str(BASE_DIR / "frontend"),
        "--reload-exclude",
        "*.pyc",
        "--reload-exclude",
        ".venv/*",
        "--reload-exclude",
        "venv/*",
        "--reload-exclude",
        "data/*",
        "--app-dir",
        str(BACKEND_DIR)
    ]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[*] Server shutdown gracefully.")

if __name__ == "__main__":
    main()
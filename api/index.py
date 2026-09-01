import sys
from pathlib import Path

# Set up module path for backend
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.main import app

# Vercel entrypoint
app = app

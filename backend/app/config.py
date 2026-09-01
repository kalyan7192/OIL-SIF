import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    PROJECT_NAME: str = "OIL SIF Precursor AI/NLP Engine"
    VERSION: str = "2.1.0"
    API_V1_STR: str = "/api"
    
    # Base directories
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    SEED_CSV_PATH: Path = BASE_DIR / "data" / "sample_safety_observations_20.csv"
    
    # Confidence threshold for routing to HSE review queue
    REVIEW_CONFIDENCE_THRESHOLD: float = float(os.getenv("REVIEW_CONFIDENCE_THRESHOLD", "0.75"))
    
    # Enterprise Cloud Database
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "oil_sif_db")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()

# Ensure data directory exists
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
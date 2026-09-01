import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes import analysis_router, dashboard_router, reports_router, reviews_router
from app.database import db
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[*] Starting OIL SIF Precursor AI Engine v{settings.VERSION}")
    print(f"[*] Enterprise Database Connected: {db.use_mongo} (Records in database: {db.count()})")
    yield

app = FastAPI(
    title="OIL SIF Precursor AI & NLP Platform",
    description="AI-driven industrial safety intelligence, SIF classification, and precursor extraction for Oil India Limited.",
    version="2.1.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(analysis_router, prefix="/api", tags=["Analysis"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(reviews_router, prefix="/api/reviews", tags=["Reviews"])

# Locate frontend directory relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

@app.get("/api/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "OIL SIF Precursor AI Engine",
        "version": settings.VERSION,
        "total_reports": db.count(),
        "database": "Enterprise Safety Database"
    }

# Mount frontend static assets
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    if (FRONTEND_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    if (FRONTEND_DIR / "js").exists():
        app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

@app.get("/", include_in_schema=False)
async def serve_index():
    if FRONTEND_DIR.exists():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    return {"message": "Frontend not found. Please ensure frontend directory exists."}
import os
import csv
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes import analysis_router, dashboard_router, reports_router, reviews_router
from app.database import db
from app.config import settings

def seed_database_if_empty():
    """Automatically seeds the database with initial observations if collection is empty"""
    try:
        current_count = db.count()
        if current_count == 0:
            print("[*] Enterprise Database is empty. Seeding initial comprehensive safety dataset directly into database...")
            from app.services.sif_classifier import sif_classifier
            from app.services.rule_classifier import rule_classifier
            from app.services.precursor_extractor import precursor_extractor
            from app.models.schemas import AIResult, HSEReview
            
            csv_path = settings.BASE_DIR / "data" / "sample_safety_observations_20.csv"
            if not csv_path.exists():
                csv_path = settings.BASE_DIR / "data" / "oil_safety_reports_seed.csv"

            if csv_path.exists():
                records = []
                with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for idx, row in enumerate(reader):
                        desc = row.get("Description") or row.get("description") or row.get("Observation") or row.get("text")
                        if not desc:
                            continue
                        site = row.get("Site") or row.get("site") or "General Field Operations"
                        loc = row.get("Location") or row.get("location")
                        act = row.get("Activity") or row.get("activity")
                        rep_type = row.get("Report Type") or row.get("report_type") or "Near Miss"
                        dt = row.get("Date") or row.get("date") or "2026-06-01"

                        sif_pred, conf, is_uncertain, _ = sif_classifier.predict(desc)
                        top_rule_id, top_rule_name, sec_rules, _ = rule_classifier.classify(desc)
                        precursor = precursor_extractor.extract(desc, given_activity=act, given_location=loc)

                        ai_res = AIResult(
                            sif_potential=sif_pred,
                            sif_confidence=conf,
                            life_saving_rule_id=top_rule_id,
                            life_saving_rule_name=top_rule_name,
                            secondary_rules=sec_rules,
                            precursor=precursor,
                            is_uncertain=is_uncertain,
                            model_version="sif-nlp-v1.0-calibrated"
                        )

                        review_status = "PENDING_REVIEW" if is_uncertain else "NOT_REQUIRED"

                        rec = {
                            "report_id": f"OIL-2026-{idx+1:04d}",
                            "date": dt,
                            "site": site,
                            "location": loc or precursor.location,
                            "activity": act or precursor.activity,
                            "report_type": rep_type,
                            "description": desc,
                            "ai": ai_res.model_dump(),
                            "review": HSEReview(status=review_status).model_dump(),
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        records.append(rec)

                if records:
                    db.insert_many(records)
                    print(f"[✓] Successfully seeded {len(records)} safety records directly into Enterprise Database.")
    except Exception as e:
        print(f"[!] Seeding warning: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[*] Starting OIL SIF Precursor AI Engine v{settings.VERSION}")
    seed_database_if_empty()
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
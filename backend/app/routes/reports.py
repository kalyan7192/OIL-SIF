import io
import csv
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse

from app.database import db
from app.models.schemas import (
    SafetyReport,
    ReportCreateRequest,
    PaginatedReportsResponse,
    AIResult,
    HSEReview,
    PrecursorDetails
)
from app.services.sif_classifier import sif_classifier
from app.services.rule_classifier import rule_classifier
from app.services.precursor_extractor import precursor_extractor

router = APIRouter(prefix="", tags=["Reports"])

class BatchDeleteRequest(BaseModel):
    report_ids: List[str]

@router.get("", response_model=PaginatedReportsResponse)
def get_reports(
    site: Optional[str] = Query(None, description="Filter by site name"),
    activity: Optional[str] = Query(None, description="Filter by activity"),
    sif_potential: Optional[bool] = Query(None, description="Filter by SIF potential"),
    is_uncertain: Optional[bool] = Query(None, description="Filter by uncertain predictions"),
    rule_id: Optional[str] = Query(None, description="Filter by Life-Saving Rule ID"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    search: Optional[str] = Query(None, description="Search query across text and fields"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort_by: str = Query("date", description="Field to sort by: date, confidence, site"),
    sort_desc: bool = Query(True)
):
    items, total = db.filter_reports(
        site=site,
        activity=activity,
        sif_potential=sif_potential,
        is_uncertain=is_uncertain,
        rule_id=rule_id,
        review_status=review_status,
        search_query=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    
    report_objects = []
    for item in items:
        report_objects.append(SafetyReport(**item))
    
    return PaginatedReportsResponse(
        items=report_objects,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{report_id}", response_model=SafetyReport)
def get_report_by_id(report_id: str):
    report = db.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report with ID '{report_id}' not found.")
    return SafetyReport(**report)

@router.delete("/all")
def delete_all_reports():
    """Delete all reports from database"""
    count = db.delete_all()
    return {"status": "success", "deleted_count": count}

@router.post("/delete-batch")
def delete_reports_batch(payload: BatchDeleteRequest):
    """Delete multiple reports by list of IDs"""
    count = db.delete_many(payload.report_ids)
    return {"status": "success", "deleted_count": count, "deleted_ids": payload.report_ids}

@router.delete("/{report_id}")
def delete_single_report(report_id: str):
    """Delete a single report by ID"""
    success = db.delete(report_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Report with ID '{report_id}' not found.")
    return {"status": "success", "deleted_id": report_id}

@router.post("", response_model=SafetyReport)
def create_report(payload: ReportCreateRequest):
    # Run AI/NLP Engine
    sif_pred, conf, is_uncertain, reasons = sif_classifier.predict(payload.description)
    top_rule_id, top_rule_name, sec_rules, _ = rule_classifier.classify(payload.description)
    precursor_details = precursor_extractor.extract(
        payload.description,
        given_activity=payload.activity,
        given_location=payload.location
    )

    ai_res = AIResult(
        sif_potential=sif_pred,
        sif_confidence=conf,
        life_saving_rule_id=top_rule_id,
        life_saving_rule_name=top_rule_name,
        secondary_rules=sec_rules,
        precursor=precursor_details,
        is_uncertain=is_uncertain,
        model_version="sif-nlp-v1.0-calibrated"
    )

    review_status = "PENDING_REVIEW" if is_uncertain else "NOT_REQUIRED"
    review_obj = HSEReview(status=review_status)

    count = db.count() + 1
    now_utc = datetime.now(timezone.utc)
    report_id = f"OIL-{now_utc.strftime('%Y')}-{count:04d}"
    rec_date = payload.date or now_utc.strftime("%Y-%m-%d")

    report_data = {
        "report_id": report_id,
        "date": rec_date,
        "site": payload.site,
        "location": payload.location or precursor_details.location,
        "activity": payload.activity or precursor_details.activity,
        "report_type": payload.report_type,
        "description": payload.description,
        "ai": ai_res.model_dump(),
        "review": review_obj.model_dump(),
        "created_at": now_utc.isoformat()
    }

    db.insert(report_data)
    return SafetyReport(**report_data)

@router.post("/upload")
async def upload_batch_csv(file: UploadFile = File(...)):
    """
    Ingests CSV file with safety observations and runs AI analysis on all rows into database.
    """
    contents = await file.read()
    decoded = contents.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))

    created_reports = []
    base_count = db.count()
    now_utc = datetime.now(timezone.utc)

    for idx, row in enumerate(reader):
        description = row.get("Description") or row.get("description") or row.get("Observation") or row.get("text")
        if not description:
            continue

        site = row.get("Site") or row.get("site") or "General Field Operations"
        location = row.get("Location") or row.get("location")
        activity = row.get("Activity") or row.get("activity")
        report_type = row.get("Report Type") or row.get("report_type") or "Near Miss"
        date_val = row.get("Date") or row.get("date") or now_utc.strftime("%Y-%m-%d")

        # Run AI Pipeline
        sif_pred, conf, is_uncertain, reasons = sif_classifier.predict(description)
        top_rule_id, top_rule_name, sec_rules, _ = rule_classifier.classify(description)
        precursor_details = precursor_extractor.extract(description, given_activity=activity, given_location=location)

        ai_res = AIResult(
            sif_potential=sif_pred,
            sif_confidence=conf,
            life_saving_rule_id=top_rule_id,
            life_saving_rule_name=top_rule_name,
            secondary_rules=sec_rules,
            precursor=precursor_details,
            is_uncertain=is_uncertain
        )

        review_status = "PENDING_REVIEW" if is_uncertain else "NOT_REQUIRED"
        report_id = f"OIL-UP-{base_count + idx + 1:04d}"

        report_data = {
            "report_id": report_id,
            "date": date_val,
            "site": site,
            "location": location or precursor_details.location,
            "activity": activity or precursor_details.activity,
            "report_type": report_type,
            "description": description,
            "ai": ai_res.model_dump(),
            "review": HSEReview(status=review_status).model_dump(),
            "created_at": now_utc.isoformat()
        }
        created_reports.append(report_data)

    if created_reports:
        db.insert_many(created_reports)

    return {
        "status": "success",
        "processed_records": len(created_reports),
        "sif_detected": sum(1 for r in created_reports if r["ai"]["sif_potential"]),
        "pending_reviews": sum(1 for r in created_reports if r["review"]["status"] == "PENDING_REVIEW")
    }

@router.get("/export/csv")
def export_reports_csv(
    site: Optional[str] = Query(None),
    sif_potential: Optional[bool] = Query(None),
    rule_id: Optional[str] = Query(None)
):
    items, _ = db.filter_reports(
        site=site,
        sif_potential=sif_potential,
        rule_id=rule_id,
        page=1,
        page_size=10000
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Report ID", "Date", "Site", "Location", "Activity", "Report Type",
        "Description", "SIF Potential", "Confidence", "Life Saving Rule",
        "Barrier Failure", "Review Status"
    ])

    for r in items:
        effective_sif = r["review"]["expert_sif_label"] if r["review"]["is_override"] and r["review"]["expert_sif_label"] is not None else r["ai"]["sif_potential"]
        effective_rule = r["review"]["expert_rule_name"] if r["review"]["is_override"] and r["review"]["expert_rule_name"] else r["ai"]["life_saving_rule_name"]
        writer.writerow([
            r["report_id"],
            r["date"],
            r["site"],
            r["location"],
            r["activity"],
            r["report_type"],
            r["description"],
            "YES" if effective_sif else "NO",
            f"{r['ai']['sif_confidence'] * 100:.1f}%",
            effective_rule,
            r["ai"]["precursor"]["barrier_failure"],
            r["review"]["status"]
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=oil_sif_precursor_reports.csv"}
    )
from typing import List
from fastapi import APIRouter, HTTPException, Query

from app.database import db
from app.models.schemas import SafetyReport, ReviewUpdateRequest

router = APIRouter(prefix="", tags=["Human-in-the-Loop Review Queue"])

@router.get("/queue", response_model=List[SafetyReport])
def get_review_queue(
    limit: int = Query(50, ge=1, le=200)
):
    """
    Returns safety reports flagged as uncertain (confidence < threshold)
    or explicitly marked PENDING_REVIEW for HSE expert validation.
    """
    items, _ = db.filter_reports(
        review_status="PENDING_REVIEW",
        page=1,
        page_size=limit,
        sort_by="date",
        sort_desc=False
    )
    return [SafetyReport(**item) for item in items]

@router.get("/history", response_model=List[SafetyReport])
def get_review_history(
    limit: int = Query(50, ge=1, le=200)
):
    """
    Returns audit trail of safety reports validated or corrected by HSE experts.
    """
    all_reports = db.get_all()
    reviewed = [r for r in all_reports if r["review"]["status"] in ("APPROVED", "REJECTED")]
    reviewed.sort(key=lambda x: x["review"]["reviewed_at"] or x["date"], reverse=True)
    return [SafetyReport(**r) for r in reviewed[:limit]]

@router.post("/{report_id}", response_model=SafetyReport)
def submit_expert_review(report_id: str, payload: ReviewUpdateRequest):
    """
    Updates report review status, records expert SIF/Rule override, and persists audit log.
    """
    existing = db.get_report(report_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Report with ID '{report_id}' not found.")
    
    from datetime import datetime
    updates = {
        "review": {
            **existing["review"],
            "status": payload.status,
            "reviewer_name": payload.reviewer_name or "HSE Officer",
            "reviewed_at": datetime.utcnow().isoformat() + "Z",
            "expert_sif_label": payload.expert_sif_label,
            "expert_rule_id": payload.expert_rule_id,
            "expert_rule_name": payload.expert_rule_name,
            "expert_notes": payload.expert_notes or "Verified by HSE expert.",
            "is_override": payload.expert_sif_label is not None or payload.expert_rule_id is not None
        }
    }
    
    updated = db.update(report_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Report with ID '{report_id}' not found.")
    
    return SafetyReport(**updated)
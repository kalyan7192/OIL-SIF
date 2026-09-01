from typing import List
from fastapi import APIRouter
from app.models.schemas import AnalyzeTextRequest, AIResult
from app.services.sif_classifier import sif_classifier
from app.services.rule_classifier import rule_classifier
from app.services.precursor_extractor import precursor_extractor

router = APIRouter(prefix="", tags=["Real-time Analysis"])

@router.post("/analyze", response_model=AIResult)
@router.post("/analysis/analyze", response_model=AIResult)
def analyze_single_text(payload: AnalyzeTextRequest):
    """
    Performs real-time multi-task NLP inference on a safety observation description.
    Returns:
    - SIF potential (Yes/No) + Calibrated Confidence
    - IOGP Life-Saving Rules mapping
    - Activity, Location, Barrier Failure, and Evidence Snippets
    """
    text = payload.text
    sif_pred, conf, is_uncertain, reasons = sif_classifier.predict(text)
    top_rule_id, top_rule_name, sec_rules, _ = rule_classifier.classify(text)
    precursor_details = precursor_extractor.extract(
        text,
        given_activity=payload.activity,
        given_location=payload.location
    )

    # If any specific high-energy reasons were found, merge them into evidence snippets
    for r in reasons:
        if r not in precursor_details.evidence_snippets:
            precursor_details.evidence_snippets.append(r)

    return AIResult(
        sif_potential=sif_pred,
        sif_confidence=conf,
        life_saving_rule_id=top_rule_id,
        life_saving_rule_name=top_rule_name,
        secondary_rules=sec_rules,
        precursor=precursor_details,
        is_uncertain=is_uncertain,
        model_version="sif-nlp-v1.0-calibrated"
    )

@router.post("/analyze/batch", response_model=List[AIResult])
@router.post("/analysis/analyze/batch", response_model=List[AIResult])
def analyze_batch(payloads: List[AnalyzeTextRequest]):
    results = []
    for p in payloads:
        results.append(analyze_single_text(p))
    return results
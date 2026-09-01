from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# =============================================================================
# AI/NLP Analysis Models
# =============================================================================

class PrecursorDetails(BaseModel):
    activity: str = "General Operation"
    location: str = "Site Facility"
    barrier_failure: str = "No specific barrier failure detected"
    evidence_snippets: List[str] = Field(default_factory=list)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)

class AIResult(BaseModel):
    sif_potential: bool
    sif_confidence: float
    life_saving_rule_id: str
    life_saving_rule_name: str
    secondary_rules: List[str] = Field(default_factory=list)
    precursor: PrecursorDetails
    is_uncertain: bool = False
    model_version: str = "sif-nlp-v1.0-calibrated"
    analyzed_at: Optional[str] = None

class AnalyzeTextRequest(BaseModel):
    text: str
    site: Optional[str] = None
    report_type: Optional[str] = "Near Miss"
    activity: Optional[str] = None
    location: Optional[str] = None

# =============================================================================
# Safety Report Models
# =============================================================================

class HSEReview(BaseModel):
    status: str = "NOT_REQUIRED"  # PENDING_REVIEW, APPROVED, REJECTED, NOT_REQUIRED
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[str] = None
    expert_sif_label: Optional[bool] = None
    expert_rule_id: Optional[str] = None
    expert_rule_name: Optional[str] = None
    expert_notes: Optional[str] = None
    is_override: bool = False

class SafetyReport(BaseModel):
    report_id: str
    date: str
    site: str
    location: str
    activity: str
    report_type: str
    description: str
    ai: AIResult
    review: HSEReview = Field(default_factory=HSEReview)
    created_at: Optional[str] = None

class ReportCreateRequest(BaseModel):
    description: str
    site: str = "General Field Operations"
    location: Optional[str] = None
    activity: Optional[str] = None
    report_type: str = "Near Miss"
    date: Optional[str] = None

class ReviewUpdateRequest(BaseModel):
    status: str
    reviewer_name: Optional[str] = "HSE Officer"
    expert_sif_label: Optional[bool] = None
    expert_rule_id: Optional[str] = None
    expert_rule_name: Optional[str] = None
    expert_notes: Optional[str] = None

# =============================================================================
# Pagination & Dashboard Models
# =============================================================================

class PaginatedReportsResponse(BaseModel):
    items: List[SafetyReport]
    total: int
    page: int
    page_size: int
    total_pages: int

class DashboardSummaryResponse(BaseModel):
    total_reports: int
    sif_reports: int
    non_sif_reports: int
    overall_sif_density: float
    pending_reviews: int
    approved_reviews: int
    total_sites: int
    high_risk_sites_count: int
    model_version: str

class SiteRankingItem(BaseModel):
    site: str
    total_reports: int
    sif_reports: int
    sif_density: float

class ActivityRankingItem(BaseModel):
    activity: str
    total_reports: int
    sif_reports: int
    sif_density: float

class RuleDistributionItem(BaseModel):
    rule_id: str
    rule_name: str
    count: int
    sif_count: int
    percentage: float
    color: Optional[str] = "#64748b"

class BarrierDistributionItem(BaseModel):
    barrier_failure: str
    count: int
    percentage: float
    cumulative_percentage: float

class TrendItem(BaseModel):
    period: str
    total_reports: int
    sif_reports: int
    sif_density: float
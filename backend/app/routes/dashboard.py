from typing import List, Optional
from fastapi import APIRouter, Query

from app.models.schemas import (
    DashboardSummaryResponse,
    SiteRankingItem,
    ActivityRankingItem,
    RuleDistributionItem,
    BarrierDistributionItem,
    TrendItem
)
from app.services.analytics import analytics_service
from app.database import db

router = APIRouter(prefix="", tags=["Dashboard Analytics"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    site: Optional[str] = Query(None),
    activity: Optional[str] = Query(None)
):
    return analytics_service.get_summary(site=site, activity=activity)

@router.get("/sites", response_model=List[SiteRankingItem])
def get_site_rankings(
    min_reports: int = Query(1, ge=1),
    site: Optional[str] = Query(None),
    activity: Optional[str] = Query(None)
):
    return analytics_service.get_site_rankings(min_reports=min_reports, site=site, activity=activity)

@router.get("/activities", response_model=List[ActivityRankingItem])
def get_activity_rankings(
    min_reports: int = Query(1, ge=1),
    site: Optional[str] = Query(None),
    activity: Optional[str] = Query(None)
):
    return analytics_service.get_activity_rankings(min_reports=min_reports, site=site, activity=activity)

@router.get("/rules", response_model=List[RuleDistributionItem])
def get_rule_distribution(
    site: Optional[str] = Query(None),
    activity: Optional[str] = Query(None)
):
    return analytics_service.get_rule_distribution(site=site, activity=activity)

@router.get("/barriers", response_model=List[BarrierDistributionItem])
def get_barrier_distribution(
    site: Optional[str] = Query(None),
    activity: Optional[str] = Query(None)
):
    return analytics_service.get_barrier_distribution(site=site, activity=activity)

@router.get("/trends", response_model=List[TrendItem])
def get_trends(
    site: Optional[str] = Query(None),
    activity: Optional[str] = Query(None)
):
    return analytics_service.get_trends(site=site, activity=activity)


@router.get("/filters")
def get_available_filters():
    reports = db.get_all()
    sites = sorted(list(set(r.get("site") for r in reports if r.get("site"))))
    activities = sorted(list(set(r.get("activity") for r in reports if r.get("activity"))))
    rules = analytics_service.get_rule_distribution()
    return {
        "sites": sites,
        "activities": activities,
        "rules": [{"id": r.rule_id, "name": r.rule_name} for r in rules]
    }
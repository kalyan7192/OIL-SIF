from typing import List, Dict, Any
from collections import defaultdict
from app.database import db
from app.models.schemas import (
    DashboardSummaryResponse,
    SiteRankingItem,
    ActivityRankingItem,
    RuleDistributionItem,
    BarrierDistributionItem,
    TrendItem
)
from app.services.rule_classifier import rule_classifier

class AnalyticsService:
    """
    Analytics Aggregation Engine:
    - Calculates SIF Precursor Density (%)
    - Computes site and activity risk rankings
    - Aggregates Life-Saving Rules and Barrier Failures distributions
    - Generates temporal risk trends
    """
    
    def __init__(self):
        pass
    
    def _filter_reports(self, reports: List[Dict[str, Any]], site: str = None, activity: str = None) -> List[Dict[str, Any]]:
        if site and site.lower() != "all":
            reports = [r for r in reports if (r.get("site") or "").lower() == site.lower()]
        if activity and activity.lower() != "all":
            reports = [r for r in reports if (r.get("activity") or "").lower() == activity.lower()]
        return reports

    def get_summary(self, site: str = None, activity: str = None) -> DashboardSummaryResponse:
        reports = self._filter_reports(db.get_all(), site=site, activity=activity)
        
        total = len(reports)
        if total == 0:
            return DashboardSummaryResponse(
                total_reports=0,
                sif_reports=0,
                non_sif_reports=0,
                overall_sif_density=0.0,
                pending_reviews=0,
                approved_reviews=0,
                total_sites=0,
                high_risk_sites_count=0,
                model_version="sif-nlp-v1.0"
            )
        
        sif_count = 0
        pending_reviews = 0
        approved_reviews = 0
        site_counts = defaultdict(lambda: {"total": 0, "sif": 0})
        
        for r in reports:
            is_sif = r["review"]["expert_sif_label"] if r["review"]["is_override"] and r["review"]["expert_sif_label"] is not None else r["ai"]["sif_potential"]
            if is_sif:
                sif_count += 1
                site_counts[r.get("site", "Unknown")]["sif"] += 1
            site_counts[r.get("site", "Unknown")]["total"] += 1
            
            if r["review"]["status"] == "PENDING_REVIEW":
                pending_reviews += 1
            elif r["review"]["status"] in ("APPROVED", "REJECTED"):
                approved_reviews += 1
        
        non_sif = total - sif_count
        density = round((sif_count / total) * 100.0, 2) if total > 0 else 0.0
        
        high_risk_sites = sum(
            1 for s_data in site_counts.values()
            if s_data["total"] >= 3 and (s_data["sif"] / s_data["total"]) >= 0.45
        )
        
        return DashboardSummaryResponse(
            total_reports=total,
            sif_reports=sif_count,
            non_sif_reports=non_sif,
            overall_sif_density=density,
            pending_reviews=pending_reviews,
            approved_reviews=approved_reviews,
            total_sites=len(site_counts),
            high_risk_sites_count=high_risk_sites,
            model_version="sif-nlp-v1.0"
        )
    
    def get_site_rankings(self, min_reports: int = 1, site: str = None, activity: str = None) -> List[SiteRankingItem]:
        reports = self._filter_reports(db.get_all(), site=site, activity=activity)
        site_map = defaultdict(lambda: {"total": 0, "sif": 0})
        
        for r in reports:
            is_sif = r["review"]["expert_sif_label"] if r["review"]["is_override"] and r["review"]["expert_sif_label"] is not None else r["ai"]["sif_potential"]
            st = r.get("site", "Unknown")
            site_map[st]["total"] += 1
            if is_sif:
                site_map[st]["sif"] += 1
        
        items = []
        for st, counts in site_map.items():
            if counts["total"] >= min_reports:
                density = round((counts["sif"] / counts["total"]) * 100.0, 2) if counts["total"] > 0 else 0.0
                items.append(SiteRankingItem(
                    site=st,
                    total_reports=counts["total"],
                    sif_reports=counts["sif"],
                    sif_density=density
                ))
        
        items.sort(key=lambda x: (x.sif_density, x.sif_reports), reverse=True)
        return items
    
    def get_activity_rankings(self, min_reports: int = 1, site: str = None, activity: str = None) -> List[ActivityRankingItem]:
        reports = self._filter_reports(db.get_all(), site=site, activity=activity)
        act_map = defaultdict(lambda: {"total": 0, "sif": 0})
        
        for r in reports:
            is_sif = r["review"]["expert_sif_label"] if r["review"]["is_override"] and r["review"]["expert_sif_label"] is not None else r["ai"]["sif_potential"]
            act = r.get("activity") or r["ai"]["precursor"]["activity"]
            act_map[act]["total"] += 1
            if is_sif:
                act_map[act]["sif"] += 1
        
        items = []
        for act, counts in act_map.items():
            if counts["total"] >= min_reports:
                density = round((counts["sif"] / counts["total"]) * 100.0, 2) if counts["total"] > 0 else 0.0
                items.append(ActivityRankingItem(
                    activity=act,
                    total_reports=counts["total"],
                    sif_reports=counts["sif"],
                    sif_density=density
                ))
        
        items.sort(key=lambda x: (x.sif_density, x.sif_reports), reverse=True)
        return items
    
    def get_rule_distribution(self, site: str = None, activity: str = None) -> List[RuleDistributionItem]:
        reports = self._filter_reports(db.get_all(), site=site, activity=activity)
        total = len(reports)
        if total == 0:
            return []
        
        rule_counts = defaultdict(lambda: {"total": 0, "sif": 0})
        for r in reports:
            rule_id = r["review"]["expert_rule_id"] if r["review"]["is_override"] and r["review"]["expert_rule_id"] else r["ai"]["life_saving_rule_id"]
            is_sif = r["review"]["expert_sif_label"] if r["review"]["is_override"] and r["review"]["expert_sif_label"] is not None else r["ai"]["sif_potential"]
            rule_counts[rule_id]["total"] += 1
            if is_sif:
                rule_counts[rule_id]["sif"] += 1
        
        colors = {
            "ENERGY_ISOLATION": "#ef4444",
            "CONFINED_SPACE": "#f97316",
            "WORKING_AT_HEIGHT": "#f59e0b",
            "LINE_OF_FIRE": "#eab308",
            "HOT_WORK": "#dc2626",
            "SAFE_MECHANICAL_LIFTING": "#3b82f6",
            "DRIVING_SAFETY": "#4f46e5",
            "TOXIC_GAS_H2S": "#8b5cf6",
            "SYSTEM_BYPASS": "#9333ea",
            "GENERAL_UA_UC": "#10b981"
        }
        
        items = []
        for rule_id, counts in rule_counts.items():
            r_info = rule_classifier.get_rule_info(rule_id)
            percentage = round((counts["total"] / total) * 100.0, 2) if total > 0 else 0.0
            items.append(RuleDistributionItem(
                rule_id=rule_id,
                rule_name=r_info.get("name", rule_id),
                count=counts["total"],
                sif_count=counts["sif"],
                percentage=percentage,
                color=colors.get(rule_id, "#64748b")
            ))
        
        items.sort(key=lambda x: x.count, reverse=True)
        return items
    
    def get_barrier_distribution(self, site: str = None, activity: str = None) -> List[BarrierDistributionItem]:
        reports = self._filter_reports(db.get_all(), site=site, activity=activity)
        total = len(reports)
        if total == 0:
            return []
        
        counts = defaultdict(int)
        for r in reports:
            barrier = r["ai"]["precursor"]["barrier_failure"]
            counts[barrier] += 1
        
        sorted_barriers = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        items = []
        cum = 0.0
        for barrier, c in sorted_barriers[:10]:
            pct = round((c / total) * 100.0, 2) if total > 0 else 0.0
            cum = round(cum + pct, 2)
            items.append(BarrierDistributionItem(
                barrier_failure=barrier,
                count=c,
                percentage=pct,
                cumulative_percentage=min(cum, 100.0)
            ))
        return items
    
    def get_trends(self, site: str = None, activity: str = None) -> List[TrendItem]:
        reports = self._filter_reports(db.get_all(), site=site, activity=activity)
        period_map = defaultdict(lambda: {"total": 0, "sif": 0})
        
        for r in reports:
            date_str = r.get("date", "2026-01-01")
            period = date_str[:7] if len(date_str) >= 7 else "2026-01"
            is_sif = r["review"]["expert_sif_label"] if r["review"]["is_override"] and r["review"]["expert_sif_label"] is not None else r["ai"]["sif_potential"]
            period_map[period]["total"] += 1
            if is_sif:
                period_map[period]["sif"] += 1
        
        sorted_periods = sorted(period_map.keys())
        items = []
        for period in sorted_periods:
            counts = period_map[period]
            density = round((counts["sif"] / counts["total"]) * 100.0, 2) if counts["total"] > 0 else 0.0
            items.append(TrendItem(
                period=period,
                total_reports=counts["total"],
                sif_reports=counts["sif"],
                sif_density=density
            ))
        return items

analytics_service = AnalyticsService()
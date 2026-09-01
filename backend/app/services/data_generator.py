import random
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from app.config import settings
from app.models.schemas import SafetyReport, AIResult, HSEReview, PrecursorDetails
from app.services.sif_classifier import sif_classifier
from app.services.rule_classifier import rule_classifier
from app.services.precursor_extractor import precursor_extractor
from app.database import db

OIL_SITES = [
    "Duliajan Central Workshop",
    "Moran Gas Gathering Station (GGS-1)",
    "Naharkatiya Drilling Rig D-14",
    "Digboi Production Facility & Tank Farm",
    "Jorajan Wellhead Installation W-22",
    "Madhuban EPS & Separation Plant",
    "Shalmari Workover Rig WR-05",
    "Dikom Pipeline Manifold & Pigging Area",
    "Tengakhat Compressor Station",
    "Kusijan Water Injection Plant",
    "Baghjan Well Area B-02",
    "Moran Substation & Switchgear Unit"
]

SAMPLE_SCENARIOS = [
    # 1. Energy Isolation / LOTO (SIF Potential)
    {
        "type": "Near Miss",
        "activity": "Mechanical Maintenance & Piping",
        "description": "During scheduled maintenance of crude booster pump P-102B at Moran GGS, technician began unbolting the pump casing before verifying that the 415V electrical breaker had been locked out and tagged. The circuit was still energized.",
        "site": "Moran Gas Gathering Station (GGS-1)"
    },
    {
        "type": "Unsafe Act",
        "activity": "Mechanical Maintenance & Piping",
        "description": "Fitter opened high-pressure drain valve on separator V-301 without depressurizing the manifold. 85 psi trapped hydrocarbon condensate escaped near operators. No LOTO applied on upstream isolation valve.",
        "site": "Digboi Production Facility & Tank Farm"
    },
    {
        "type": "Near Miss",
        "activity": "Electrical Maintenance",
        "description": "Electrician was replacing contacts on 11kV busbar in Duliajan Central Substation without applying earthing switch or verifying zero energy state with a calibrated voltage detector.",
        "site": "Duliajan Central Workshop"
    },

    # 2. Confined Space Entry (SIF Potential)
    {
        "type": "Near Miss",
        "activity": "Vessel & Tank Cleaning",
        "description": "Contract cleaning crew entered Crude Storage Tank T-04 through bottom manhole without conducting continuous multi-gas atmospheric testing. Oxygen level was later tested at 18.2% and standby watch was absent.",
        "site": "Digboi Production Facility & Tank Farm"
    },
    {
        "type": "Unsafe Act",
        "activity": "Vessel & Tank Cleaning",
        "description": "Technician climbed inside cellar pit on Rig D-14 to retrieve dropped wrench without an entry permit, gas test, or forced ventilation while drilling mud was degassing nearby.",
        "site": "Naharkatiya Drilling Rig D-14"
    },

    # 3. Working at Height (SIF Potential)
    {
        "type": "Unsafe Act",
        "activity": "Scaffolding & Rigging",
        "description": "Derrickman was observed working on the monkey board at 28 meters elevation during pipe racking with his full-body safety harness lifeline unclipped from the certified anchor point.",
        "site": "Naharkatiya Drilling Rig D-14"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Scaffolding & Rigging",
        "description": "Scaffold erected for high-pressure gas header inspection at Tengakhat Compressor Station had missing middle guard rails, loose wooden planks, and no toe-boards at a working height of 7.5 meters.",
        "site": "Tengakhat Compressor Station"
    },

    # 4. Line of Fire & Dropped Objects (SIF Potential)
    {
        "type": "Near Miss",
        "activity": "Drilling & Well Construction",
        "description": "While hoisting drill collars on Rig WR-05, an unlatched 4-inch casing tong jaw weighing 18 kg slipped from the derrick and fell 12 meters, landing 1.5 meters from the floor roughneck in the line of fire.",
        "site": "Shalmari Workover Rig WR-05"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Pressure Testing & Purging",
        "description": "High-pressure hydrotest manifold pressurized to 4500 psi was missing safety whipchecks and securing safety cables on the flexible hose connections in the main crew walkway.",
        "site": "Dikom Pipeline Manifold & Pigging Area"
    },

    # 5. Hot Work (SIF Potential)
    {
        "type": "Unsafe Act",
        "activity": "Hot Work & Fabrication",
        "description": "Fabrication crew commenced cutting torch operation on pipe support bracket 4 meters from an active hydrocarbon condensate drainage trench without conducting explosive gas test (LEL) and with no fire watch present.",
        "site": "Madhuban EPS & Separation Plant"
    },
    {
        "type": "Near Miss",
        "activity": "Hot Work & Fabrication",
        "description": "Welder initiated hot work arc welding on test separator skid while flammable hydrocarbon vapors were venting from nearby atmospheric vent pipe. Fire blanket was not deployed.",
        "site": "Moran Gas Gathering Station (GGS-1)"
    },

    # 6. Safe Mechanical Lifting (SIF Potential)
    {
        "type": "Unsafe Condition",
        "activity": "Crane & Mechanical Lifting",
        "description": "Mobile 25-ton hydraulic crane was lifting a 6-ton mud pump skid using a severely frayed synthetic webbing sling showing cut fibers and without third-party load test certification. Crew was standing directly under suspended load.",
        "site": "Naharkatiya Drilling Rig D-14"
    },
    {
        "type": "Near Miss",
        "activity": "Crane & Mechanical Lifting",
        "description": "During offloading of casing pipes from trailer, lifting shackle pin backed out due to missing split pin. One 2-ton casing pipe slipped out of the sling assembly, narrowly missing the banksman.",
        "site": "Duliajan Central Workshop"
    },

    # 7. Driving & Transportation (SIF Potential)
    {
        "type": "Unsafe Act",
        "activity": "Crude & Material Transportation",
        "description": "Crude oil bowser tanker was tracked on IVMS speeding at 78 km/h in a 30 km/h restricted oilfield unpaved corridor during heavy rain. Driver was observed using mobile phone without wearing seatbelt.",
        "site": "Jorajan Wellhead Installation W-22"
    },
    {
        "type": "Near Miss",
        "activity": "Crude & Material Transportation",
        "description": "Heavy pipe delivery flatbed truck suffered brake failure while descending steep grade near Digboi bypass due to unperformed pre-trip brake inspection, narrowly avoiding rollover into pipeline easement.",
        "site": "Digboi Production Facility & Tank Farm"
    },

    # 8. Toxic Gas & H2S Exposure (SIF Potential)
    {
        "type": "Near Miss",
        "activity": "Well Intervention & Workover",
        "description": "Wireline crew opened wellhead swab valve on sour gas well B-02 without wearing personal multi-gas detectors or keeping 30-minute positive pressure SCBA units ready at the staging area. H2S concentration registered 15 ppm shortly after.",
        "site": "Baghjan Well Area B-02"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Fixed toxic gas detector at Moran GGS compressor hall had power cable disconnected, disabling early detection alarm for hazardous gas leak in confined compressor shed.",
        "site": "Moran Gas Gathering Station (GGS-1)"
    },

    # 9. System Bypass / Safety Critical Controls (SIF Potential)
    {
        "type": "Unsafe Act",
        "activity": "Mechanical Maintenance & Piping",
        "description": "Control room operator installed a manual mechanical lock on emergency shutdown valve ESDV-101 to prevent recurring production line shutdown without obtaining signed Management of Change (MOC) bypass permit.",
        "site": "Madhuban EPS & Separation Plant"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Drilling & Well Construction",
        "description": "Blowout preventer (BOP) hydraulic control accumulator low-pressure audible alarm buzzer was silenced and wire disconnected on the remote control panel on rig floor.",
        "site": "Naharkatiya Drilling Rig D-14"
    },

    # 10. Routine Low-Risk / Non-SIF Reports
    {
        "type": "Unsafe Condition",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Small puddle of rainwater and spilled detergent noticed near the workshop main entrance hallway, posing minor slipping hazard to office staff.",
        "site": "Duliajan Central Workshop"
    },
    {
        "type": "Unsafe Act",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Store helper was not wearing protective leather gloves while unboxing cardboard cartons containing paper stationery in the administrative warehouse.",
        "site": "Duliajan Central Workshop"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Inspection tag on 5 kg CO2 fire extinguisher in the lunchroom was expired by two weeks. Pressure gauge indicator was within normal green range.",
        "site": "Moran Gas Gathering Station (GGS-1)"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Routine Inspection & Housekeeping",
        "description": "One fluorescent ceiling light tube in the field instrumentation tool room was flickering, causing slightly dim lighting over the workbench.",
        "site": "Digboi Production Facility & Tank Farm"
    },
    {
        "type": "Unsafe Act",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Operator discarded used oily cleaning cotton rags in standard general waste bin instead of designated red hazardous waste container.",
        "site": "Madhuban EPS & Separation Plant"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Emergency eye wash station dust covers were missing in the water testing laboratory. Water flow testing confirmed unit operates normally.",
        "site": "Kusijan Water Injection Plant"
    },
    {
        "type": "Unsafe Act",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Technician walked across non-operational asphalt parking lot without wearing clear safety spectacles in broad daylight.",
        "site": "Dikom Pipeline Manifold & Pigging Area"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Loose computer monitor power cable trailing across walkway behind reception desk in field office administration room.",
        "site": "Duliajan Central Workshop"
    },
    {
        "type": "Unsafe Condition",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Muster point directional sign board paint was faded and weathered by sunlight near the perimeter fence gate.",
        "site": "Jorajan Wellhead Installation W-22"
    },
    {
        "type": "Unsafe Act",
        "activity": "Routine Inspection & Housekeeping",
        "description": "Contractor employee was carrying two small 2-meter plastic conduit pipes across the yard without a helper.",
        "site": "Shalmari Workover Rig WR-05"
    }
]

class DataGenerator:
    """
    Generates realistic domain-specific OIL safety observations,
    runs AI inference, seeds the database, and creates CSV exports.
    """
    def __init__(self):
        pass

    def generate_dataset(self, num_records: int = 260) -> List[SafetyReport]:
        random.seed(42)
        base_date = datetime.now() - timedelta(days=240)
        reports: List[SafetyReport] = []

        for i in range(1, num_records + 1):
            report_id = f"OIL-2026-{i:04d}"
            template = random.choice(SAMPLE_SCENARIOS)
            site = template.get("site") or random.choice(OIL_SITES)
            activity = template.get("activity")
            report_type = template.get("type", "Near Miss")
            description = template["description"]

            # Add minor date offset
            days_offset = random.randint(0, 240)
            rec_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")

            # Run NLP Engine
            sif_pred, conf, is_uncertain, reasons = sif_classifier.predict(description)
            top_rule_id, top_rule_name, sec_rules, _ = rule_classifier.classify(description)
            precursor_details = precursor_extractor.extract(description, given_activity=activity)

            # Build AI Result
            ai_res = AIResult(
                sif_potential=sif_pred,
                sif_confidence=conf,
                life_saving_rule_id=top_rule_id,
                life_saving_rule_name=top_rule_name,
                secondary_rules=sec_rules,
                precursor=precursor_details,
                is_uncertain=is_uncertain,
                model_version="sif-nlp-v1.0-calibrated",
                analyzed_at=f"{rec_date}T08:30:00Z"
            )

            # Review status
            review_status = "PENDING_REVIEW" if is_uncertain else "NOT_REQUIRED"
            review_obj = HSEReview(status=review_status)

            # For some non-uncertain reports, mark approved for history
            if not is_uncertain and random.random() < 0.25:
                review_obj = HSEReview(
                    status="APPROVED",
                    reviewer_name="Sr. HSE Officer - Duliajan",
                    reviewed_at=f"{rec_date}T14:00:00Z",
                    expert_sif_label=sif_pred,
                    expert_rule_id=top_rule_id,
                    expert_notes="AI prediction verified against site incident log."
                )

            report = SafetyReport(
                report_id=report_id,
                date=rec_date,
                site=site,
                location=precursor_details.location,
                activity=precursor_details.activity,
                report_type=report_type,
                description=description,
                ai=ai_res,
                review=review_obj,
                created_at=f"{rec_date}T08:30:00Z"
            )
            reports.append(report)

        return reports

    def seed_database_and_csv(self, force: bool = False):
        current_count = db.count()
        if current_count > 0 and not force:
            print(f"Database already contains {current_count} records. Skipping seed.")
            return

        print("Generating realistic OIL safety reports dataset...")
        reports = self.generate_dataset(num_records=280)
        report_dicts = [r.model_dump() for r in reports]
        db.insert_many(report_dicts)
        print(f"Successfully seeded {len(reports)} records into database.")


        # Also write CSV export for user/demo inspection
        self.export_csv(reports, settings.SEED_CSV_PATH)

    def export_csv(self, reports: List[SafetyReport], filepath: Path):
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Report ID", "Date", "Site", "Location", "Activity", "Report Type",
                    "Description", "SIF Potential", "Confidence", "Life Saving Rule",
                    "Barrier Failure", "Review Status"
                ])
                for r in reports:
                    writer.writerow([
                        r.report_id,
                        r.date,
                        r.site,
                        r.location,
                        r.activity,
                        r.report_type,
                        r.description,
                        "YES" if r.ai.sif_potential else "NO",
                        f"{r.ai.sif_confidence * 100:.1f}%",
                        r.ai.life_saving_rule_name,
                        r.ai.precursor.barrier_failure,
                        r.review.status
                    ])
            print(f"Exported seed CSV to: {filepath}")
        except Exception as e:
            print(f"Error exporting CSV: {e}")

data_generator = DataGenerator()

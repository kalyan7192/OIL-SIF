import re
from typing import Dict, Any
from app.models.schemas import PrecursorDetails

class PrecursorExtractor:
    """
    Extracts precursor details from safety observation text
    """
    
    def __init__(self):
        # Activity patterns
        self.activity_patterns = {
            "Electrical Maintenance & Power Isolation": [
                r"electrical", r"electrician", r"switchgear", r"breaker", r"busbar", r"415v", r"power switch", r"live power"
            ],
            "Mechanical Maintenance & Depressurization": [
                r"maintenance", r"repair", r"piping", r"pump", r"valve", r"flange", r"depressuriz", r"drain valve", r"bleeding"
            ],
            "Vessel & Tank Cleaning": [
                r"tank", r"vessel", r"manhole", r"cleaning", r"entry", r"tank farm"
            ],
            "Scaffolding & Work at Height": [
                r"scaffold", r"rigging", r"harness", r"height", r"elevation", r"derrickman", r"derrick", r"pipe-racking"
            ],
            "Well Intervention & Gas Testing": [
                r"well", r"sour gas", r"wellhead", r"h2s", r"toxic gas", r"gas well", r"swab"
            ],
            "Hot Work & Welding": [
                r"welding", r"grinding", r"cutting", r"torch", r"hot work", r"fire", r"flame"
            ],
            "Crane & Mechanical Lifting": [
                r"crane", r"lifting", r"sling", r"hoist", r"suspended", r"rigging", r"lifting belt"
            ],
            "Rig Operations & Dropped Objects": [
                r"drilling", r"rig floor", r"dropped", r"tong", r"wrench"
            ],
            "Safety Control Systems & Instrumentation": [
                r"esdv", r"shut-off", r"interlock", r"control room", r"bypass"
            ],
            "Vehicle Driving & Transport": [
                r"transport", r"vehicle", r"driving", r"tanker", r"bowser", r"truck", r"speeding"
            ],
            "Pressure Testing & Piping": [
                r"pressure", r"hydrotest", r"manifold", r"purging", r"whipcheck", r"3500 psi"
            ],
            "Routine Housekeeping & Facility Upkeep": [
                r"inspection", r"housekeeping", r"routine", r"walkway", r"soap", r"flickering", r"lighting", r"stationery", r"dust cover", r"waste", r"water bottle"
            ]
        }
        
        # Barrier failure patterns
        self.barrier_patterns = {
            "LOTO / Energy Isolation not verified": [
                r"loto", r"lockout", r"tagout", r"isolation", r"energized", r"live electrical", r"power switch", r"depressuriz", r"bleeding off", r"trapped pressure"
            ],
            "Confined Space Entry Protocol Violated": [
                r"confined", r"entry", r"manhole", r"atmospheric", r"tank cleaning", r"oxygen level", r"standby watchman", r"inside crude"
            ],
            "Fall Protection / Guardrails Inadequate": [
                r"harness", r"fall", r"guardrail", r"scaffold", r"lifeline unhooked", r"toe-board", r"mid-guardrail", r"without guardrail"
            ],
            "Gas Monitoring / Detection System Failure": [
                r"gas detector", r"h2s", r"toxic", r"alarm", r"breathing apparatus", r"sour gas"
            ],
            "Hot Work Controls & Fire Watch Deficient": [
                r"hot work", r"fire watch", r"fire extinguisher", r"cutting torch", r"flammable"
            ],
            "Rigging & Sling Integrity Compromised": [
                r"sling", r"rigging", r"shackle", r"lifting", r"torn", r"broken fibers", r"underneath the load"
            ],
            "Line of Fire & Dropped Object Prevention Failed": [
                r"dropped", r"drop", r"tong", r"wrench", r"line of fire", r"dropped 12 meters"
            ],
            "Safety Critical Interlock / ESDV Bypassed": [
                r"bypass", r"tied a wire", r"tied with a wire", r"esdv", r"shut-off valve", r"safety control"
            ],
            "Driver Safety & Journey Control Non-Compliance": [
                r"speeding", r"seatbelt", r"driver", r"vehicle", r"tanker truck"
            ],
            "Pressure Restraint & Whip-check Missing": [
                r"whipcheck", r"whip-check", r"hydrotest", r"3500 psi", r"pressure hose"
            ]
        }
    
    def extract(self, text: str, given_activity: str = None, given_location: str = None) -> PrecursorDetails:
        if not text:
            return PrecursorDetails()
        
        text_lower = text.lower()
        
        # Determine activity
        activity = given_activity or "Routine Housekeeping & Facility Upkeep"
        if not given_activity:
            for act, patterns in self.activity_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        activity = act
                        break
                if activity != "Routine Housekeeping & Facility Upkeep":
                    break
        
        # Determine location
        location = given_location or "Plant Operational Area"
        
        # Determine barrier failure
        barrier_failure = "Standard Operational Anomaly"
        for barrier, patterns in self.barrier_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    barrier_failure = barrier
                    break
            if barrier_failure != "Standard Operational Anomaly":
                break
        
        # Extract evidence snippets
        evidence = []
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                risk_indicators = ["without", "no", "missing", "failed", "not", "improper", "inadequate", "damaged", "under", "hazard", "unsafe", "violation", "risk", "dropped", "slipped", "torn"]
                if any(indicator in sentence.lower() for indicator in risk_indicators):
                    evidence.append(sentence[:65] + ("..." if len(sentence) > 65 else ""))
        
        evidence = evidence[:5]
        
        return PrecursorDetails(
            activity=activity,
            location=location,
            barrier_failure=barrier_failure,
            evidence_snippets=evidence
        )

# Singleton instance
precursor_extractor = PrecursorExtractor()
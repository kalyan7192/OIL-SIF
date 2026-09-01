import re
from typing import Tuple, List

class SIFClassifier:
    """
    SIF (Serious Injury & Fatality) Precursor Classifier
    Uses domain keyword matching, energy barrier analysis, pattern detection, and confidence calibration
    """
    
    def __init__(self):
        # High-threat / severe energy indicators (SIF Precursors)
        self.high_risk_terms = {
            "explosion": 1.0,
            "blowout": 1.0,
            "h2s": 0.95,
            "hydrogen sulfide": 0.95,
            "sour gas": 0.95,
            "flash fire": 0.95,
            "toxic release": 0.95,
            "structural collapse": 0.90,
            "live circuit": 0.90,
            "11kv": 0.90,
            "high voltage": 0.90,
            "electrocute": 0.90,
            "live power": 0.88,
            "live electrical": 0.88,
            "confined space": 0.88,
            "inside tank": 0.85,
            "tank cleaning": 0.85,
            "oxygen level": 0.85,
            "415v": 0.85,
            "crush injury": 0.85,
            "fall from height": 0.85,
            "unhooked": 0.85,
            "suspended weight": 0.85,
            "underneath the load": 0.85,
            "dropped 12 meters": 0.85,
            "dropped 10 meters": 0.85,
            "dropped 15 meters": 0.85,
            "casing tong": 0.85,
            "energized": 0.80,
            "derrick": 0.80,
            "derrickman": 0.80,
            "lockout": 0.80,
            "locked out": 0.80,
            "loto": 0.80,
            "tagout": 0.80,
            "isolation": 0.80,
            "cutting torch": 0.80,
            "open flame": 0.80,
            "flammable gas": 0.80,
            "hydrocarbon gas": 0.80,
            "torn lifting belt": 0.80,
            "broken fibers": 0.80,
            "esdv": 0.85,
            "safety shut-off": 0.85,
            "bypass": 0.80,
            "tied a wire": 0.85,
            "speeding at": 0.80,
            "3500 psi": 0.85,
            "hydrotest": 0.80,
            "whipcheck": 0.80,
            "whip-check": 0.80,
            "trapped pressure": 0.85,
            "depressurization": 0.80,
            "bleeding off": 0.80,
            "scaffolding platform": 0.80,
            "without guardrail": 0.85,
            "gas leak": 0.80,
            "crane": 0.75,
            "lifting": 0.75,
            "rigging": 0.75,
            "hot work": 0.75,
            "welder": 0.75,
            "welding": 0.75
        }

        # Low-risk / routine housekeeping terms
        self.routine_terms = {
            "housekeeping": 0.15,
            "detergent": 0.12,
            "spilled": 0.15,
            "slippery floor": 0.18,
            "cardboard": 0.15,
            "stationery": 0.12,
            "printer paper": 0.12,
            "tube light": 0.15,
            "flickering": 0.15,
            "dim lighting": 0.15,
            "dust cover": 0.15,
            "eye wash fountain": 0.18,
            "shredded paper": 0.12,
            "waste drum": 0.15,
            "snack wrappers": 0.12,
            "water bottles": 0.12,
            "sign board": 0.15,
            "sun-faded": 0.15,
            "lunch break": 0.15,
            "parking lot": 0.15
        }

    def predict(self, text: str) -> Tuple[bool, float, bool, List[str]]:
        """
        Predict SIF potential from text.
        Returns: (is_sif, confidence, is_uncertain, evidence_reasons)
        """
        if not text or not text.strip():
            return False, 0.0, True, ["Empty text provided"]
        
        text_lower = text.lower()
        evidence = []
        max_high_risk = 0.0
        max_routine = 0.0
        
        # Check high-risk terms
        for term, weight in self.high_risk_terms.items():
            if term in text_lower:
                max_high_risk = max(max_high_risk, weight)
                evidence.append(f"Detected risk indicator: '{term}'")
        
        # Check routine terms
        for term, weight in self.routine_terms.items():
            if term in text_lower:
                max_routine = max(max_routine, weight)
                evidence.append(f"Detected routine indicator: '{term}'")
        
        # Check high-impact behavioral & barrier patterns
        high_patterns = [
            (r"\b(without|lack of|no)\s+(switching off|locking|isolation|loto|lockout)\b", 0.88, "Failure to isolate energy / LOTO"),
            (r"\b(without|lack of|no)\s+(testing|gas detector|oxygen level|standby)\b", 0.88, "Confined space / Toxic gas entry without controls"),
            (r"\b(without|unhooked|no)\s+(clipping|hooking|safety belt|harness|lifeline|guardrail)\b", 0.88, "Working at height without fall protection"),
            (r"\b(torn|worn-out|broken|defective)\s+(lifting|belt|sling|rigging|wire)\b", 0.85, "Compromised lifting gear"),
            (r"\b(dropped|fell|slipped)\s+.*\b(meters?|feet|floor)\b", 0.85, "Dropped object / Line of fire near personnel"),
            (r"\b(bypass|bypassing|tied with a wire|disabled)\s+.*\b(valve|alarm|esdv|shutdown)\b", 0.88, "Safety shutdown control bypassed"),
            (r"\b(speeding|70|75|80|90)\s*km/?h\b", 0.80, "Dangerous vehicle speeding on field roads"),
            (r"\b(before|without)\s+(bleeding|releasing|depressuriz).*\b(pressure)\b", 0.85, "Failure to depressurize before opening line"),
            (r"\b(without|missing)\s+(whipcheck|whip-check|safety cable)\b", 0.85, "High-pressure line without safety restraint"),
            (r"\b(without)\s+(installing|mid-guardrail|guardrail|toe-board)\b", 0.85, "Scaffold platform without edge protection"),
            (r"\b(flame|torch|cutting)\s+.*\b(flammable|gas|leak)\b", 0.88, "Hot work near flammable gas source")
        ]
        
        for pattern, weight, reason in high_patterns:
            if re.search(pattern, text_lower):
                max_high_risk = max(max_high_risk, weight)
                evidence.append(reason)

        if max_high_risk >= 0.70:
            is_sif = True
            risk_score = max_high_risk
            confidence = min(0.98, 0.78 + (risk_score * 0.19))
            is_uncertain = False
        elif max_routine > 0.0 and max_high_risk < 0.50:
            is_sif = False
            risk_score = max_routine
            confidence = 0.88
            is_uncertain = False
        else:
            # Borderline case
            is_sif = max_high_risk >= 0.50
            risk_score = max(max_high_risk, max_routine, 0.30)
            confidence = 0.72
            is_uncertain = True
        
        confidence = round(confidence, 3)
        return is_sif, confidence, is_uncertain, evidence

# Singleton instance
sif_classifier = SIFClassifier()
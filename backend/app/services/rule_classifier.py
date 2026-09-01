from typing import List, Tuple

class RuleClassifier:
    """
    IOGP Life-Saving Rules Classifier
    Maps safety observations directly to appropriate Life-Saving Rules
    """
    
    def __init__(self):
        self.rules = self._get_default_rules()
    
    def _get_default_rules(self) -> List[dict]:
        """Complete 10-rule IOGP safety taxonomy definition"""
        return [
            {
                "id": "ENERGY_ISOLATION",
                "name": "Energy Isolation",
                "short_name": "LOTO",
                "color": "#ef4444",
                "keywords": [
                    "lockout", "tagout", "loto", "isolation", "energized", "breaker",
                    "switchgear", "zero energy", "electrical", "electrician", "live electrical",
                    "switch off", "power switch", "415v", "11kv", "depressuriz", "drain valve",
                    "bleed", "bleeding off", "trapped pressure", "unbolting", "de-energiz"
                ]
            },
            {
                "id": "CONFINED_SPACE",
                "name": "Confined Space",
                "short_name": "Confined Space",
                "color": "#f97316",
                "keywords": [
                    "confined", "manhole", "vessel", "tank", "pit", "entry", "atmospheric",
                    "tank cleaning", "oxygen", "standby watchman", "inside tank", "toxic atmosphere"
                ]
            },
            {
                "id": "WORKING_AT_HEIGHT",
                "name": "Working at Height",
                "short_name": "Work at Height",
                "color": "#f59e0b",
                "keywords": [
                    "height", "scaffold", "scaffolding", "harness", "fall", "lanyard",
                    "elevation", "lifeline", "guardrail", "toe-board", "derrickman",
                    "derrick", "pipe-racking", "25 meters", "unhooked"
                ]
            },
            {
                "id": "HOT_WORK",
                "name": "Hot Work",
                "short_name": "Hot Work",
                "color": "#dc2626",
                "keywords": [
                    "hot work", "welding", "welder", "grinding", "torch", "cutting torch",
                    "flame", "spark", "fire", "fire watch", "fire extinguisher", "open flame"
                ]
            },
            {
                "id": "SAFE_MECHANICAL_LIFTING",
                "name": "Safe Mechanical Lifting",
                "short_name": "Mechanical Lifting",
                "color": "#3b82f6",
                "keywords": [
                    "crane", "lifting", "rigging", "sling", "hoist", "suspended",
                    "shackle", "lifting belt", "underneath the load", "suspended weight", "broken fibers"
                ]
            },
            {
                "id": "DRIVING_SAFETY",
                "name": "Driving & Transportation",
                "short_name": "Driving Safety",
                "color": "#4f46e5",
                "keywords": [
                    "driving", "driver", "vehicle", "speeding", "seatbelt", "tanker",
                    "truck", "bowser", "ivms", "muddy road", "km/h"
                ]
            },
            {
                "id": "TOXIC_GAS_H2S",
                "name": "Toxic Gas & H2S Exposure",
                "short_name": "Toxic Gas / H2S",
                "color": "#8b5cf6",
                "keywords": [
                    "h2s", "toxic", "gas leak", "detector", "scba", "sour gas",
                    "gas well", "breathing apparatus", "hydrogen sulfide"
                ]
            },
            {
                "id": "LINE_OF_FIRE",
                "name": "Line of Fire & Dropped Objects",
                "short_name": "Line of Fire",
                "color": "#eab308",
                "keywords": [
                    "line of fire", "dropped", "drop", "tong", "wrench", "pinch",
                    "crush", "moving", "suspended load", "falling object", "casing tong"
                ]
            },
            {
                "id": "PRESSURE_HAZARDS",
                "name": "Pressure Hazards & Piping",
                "short_name": "Pressure Hazards",
                "color": "#06b6d4",
                "keywords": [
                    "pressure", "psi", "hydrotest", "whipcheck", "whip-check", "hose",
                    "piping", "flange", "high-pressure", "pressure line"
                ]
            },
            {
                "id": "SYSTEM_BYPASS",
                "name": "Bypassing Safety Controls",
                "short_name": "System Bypass",
                "color": "#9333ea",
                "keywords": [
                    "bypass", "bypassing", "override", "interlock", "esdv", "silenced",
                    "moc", "safety shut-off", "shut-off valve", "tied a wire", "disabling"
                ]
            },
            {
                "id": "GENERAL_UA_UC",
                "name": "General UA/UC & Housekeeping",
                "short_name": "General UA/UC",
                "color": "#10b981",
                "keywords": [
                    "housekeeping", "ppe", "gloves", "safety glasses", "safety spectacles",
                    "walkway", "routine", "cleanliness", "spilled", "soap", "water bottles",
                    "paper", "trash", "lighting", "light bulb", "dust covers", "eye wash",
                    "sign board", "paint", "slippery floor", "hallway"
                ]
            }
        ]
    
    def classify(self, text: str) -> Tuple[str, str, List[str], List[str]]:
        """
        Classify text against Life-Saving Rules.
        Returns: (primary_rule_id, primary_rule_name, secondary_rules, matched_keywords)
        """
        if not text:
            return "GENERAL_UA_UC", "General UA/UC & Housekeeping", [], []
        
        text_lower = text.lower()
        matches = []
        
        for rule in self.rules:
            matched_keywords = []
            for keyword in rule.get("keywords", []):
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                matches.append({
                    "rule_id": rule.get("id", "GENERAL_UA_UC"),
                    "rule_name": rule.get("name", "General UA/UC & Housekeeping"),
                    "keywords": matched_keywords,
                    "score": sum(len(k.split()) for k in matched_keywords) + len(matched_keywords) * 0.5
                })
        
        # Sort by match strength
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        # If any high-threat specific rule matched, prefer it over GENERAL_UA_UC
        non_general = [m for m in matches if m["rule_id"] != "GENERAL_UA_UC"]
        if non_general:
            primary = non_general[0]
        elif matches:
            primary = matches[0]
        else:
            return "GENERAL_UA_UC", "General UA/UC & Housekeeping", [], []
        
        secondary = [m["rule_name"] for m in matches if m["rule_id"] != primary["rule_id"]][:2]
        all_keywords = []
        for m in matches[:3]:
            all_keywords.extend(m["keywords"])
        
        return primary["rule_id"], primary["rule_name"], secondary, all_keywords[:5]
    
    def get_rule_info(self, rule_id: str) -> dict:
        """Get rule information by ID"""
        for rule in self.rules:
            if rule.get("id") == rule_id:
                return rule
        return {"id": rule_id, "name": rule_id, "color": "#64748b"}

# Singleton instance
rule_classifier = RuleClassifier()
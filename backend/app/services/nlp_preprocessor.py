import re
import string

class NLPPreprocessor:
    def __init__(self):
        self.abbreviations = {
            r"\bLOTO\b": "Lockout Tagout",
            r"\bPTW\b": "Permit to Work",
            r"\bPPE\b": "Personal Protective Equipment",
            r"\bH2S\b": "Hydrogen Sulfide",
            r"\bGGS\b": "Gas Gathering Station",
            r"\bESDV\b": "Emergency Shutdown Valve",
            r"\bLEL\b": "Lower Explosive Limit",
            r"\bSCBA\b": "Self-Contained Breathing Apparatus",
            r"\bMOC\b": "Management of Change",
            r"\bIVMS\b": "In-Vehicle Monitoring System",
            r"\bBOP\b": "Blowout Preventer",
            r"\bEPS\b": "Early Production System",
            r"\bCPF\b": "Central Processing Facility",
            r"\bUA\b": "Unsafe Act",
            r"\bUC\b": "Unsafe Condition"
        }

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def expand_abbreviations(self, text: str) -> str:
        if not text:
            return ""
        result = text
        for pattern, expansion in self.abbreviations.items():
            result = re.sub(pattern, expansion, result, flags=re.IGNORECASE)
        return result

    def preprocess(self, text: str) -> str:
        cleaned = self.clean_text(text)
        return self.expand_abbreviations(cleaned)

nlp_preprocessor = NLPPreprocessor()
preprocessor = nlp_preprocessor
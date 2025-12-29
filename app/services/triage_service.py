from app.models.base import TriageCategory, SOAPNote, PatientProfile

class TriageService:
    @staticmethod
    def calculate_urgency(soap_note: SOAPNote, patient_profile: PatientProfile) -> tuple[int, TriageCategory]:
        """
        Calculates urgency score (0-100) and category based on SOAP note content and risk flags.
        """
        score = 0
        risk_flags = soap_note.risk_flags or []
        soap_json = soap_note.soap_json or {}
        
        subjective = soap_json.get("subjective", "").lower()
        assessment = soap_json.get("assessment", "").lower()
        
        # 1. Critical Risk Flags (Suicide, Abuse, Severe Distress)
        critical_keywords = ["suicide", "harm", "abuse", "emergency", "chest pain", "stroke", "heart attack"]
        
        # Check explicit risk flags first
        for flag in risk_flags:
            if any(k in flag.lower() for k in critical_keywords):
                score = 95
                return score, TriageCategory.CRITICAL
        
        # Check textual content for critical keywords
        if any(k in subjective for k in critical_keywords) or any(k in assessment for k in critical_keywords):
            score = 90
            return score, TriageCategory.CRITICAL

        # 2. High Urgency (Severe Pain, High Fever, Abnormal Vitals if parsed)
        high_keywords = ["severe pain", "high fever", "shortness of breath", "fainting"]
        if any(k in subjective for k in high_keywords):
            score = 75
            return score, TriageCategory.HIGH

        # 3. Moderate Urgency (Acute but manageable)
        moderate_keywords = ["pain", "infection", "vomiting", "diarrhea", "rash", "fever"]
        if any(k in subjective for k in moderate_keywords):
            score = 50
            return score, TriageCategory.MODERATE

        # 4. Low Urgency (Routine, Follow-up)
        # Default
        score = 20
        return score, TriageCategory.LOW

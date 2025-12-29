from typing import List, Dict
from app.models.base import SOAPNote, PatientProfile

class SafetyService:
    @staticmethod
    def check_drug_interactions(soap_note: SOAPNote, patient_profile: PatientProfile) -> List[Dict[str, str]]:
        """
        Analyzes the Treatment Plan against Patient History for potential contraindications.
        Returns a list of warnings.
        """
        warnings = []
        soap_json = soap_note.soap_json or {}
        plan_text = soap_json.get("plan", "").lower()
        medical_history = (patient_profile.medical_history or "").lower()
        
        # Mock Knowledge Base of Interactions
        # Format: (Drug Keyword, Condition Keyword, Warning Message)
        interactions_db = [
            ("aspirin", "ulcer", "❌ CONTRAINDICATION: Aspirin specified in plan but patient has history of Ulcers (Risk of bleeding)."),
            ("aspirin", "bleeding", "❌ CONTRAINDICATION: Aspirin specified in plan but patient has history of Bleeding disorders."),
            ("penicillin", "allergy", "❌ CONTRAINDICATION: Penicillin specified in plan but patient has reported Allergies."),
            ("ibuprofen", "kidney", "⚠️ CAUTION: Ibuprofen may be risky for patients with Kidney issues."),
            ("beta blocker", "asthma", "⚠️ CAUTION: Beta blockes may exacerbate Asthma.")
        ]
        
        for drug, condition, message in interactions_db:
            if drug in plan_text and condition in medical_history:
                warnings.append({
                    "type": "CONTRAINDICATION" if "❌" in message else "CAUTION",
                    "message": message,
                    "drug": drug,
                    "condition": condition
                })
                
        return warnings

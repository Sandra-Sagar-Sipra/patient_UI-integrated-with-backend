from app.services.triage_service import TriageService
from app.services.safety_service import SafetyService
from app.models.base import SOAPNote, PatientProfile, TriageCategory

def test_triage_logic():
    print("Testing Triage Service...")
    
    # 1. Critical Case
    critical_note = SOAPNote(
        soap_json={"subjective": "Patient expressed thoughts of suicide.", "assessment": "Major Depressive Disorder"},
        risk_flags=["Suicide Risk"]
    )
    score, category = TriageService.calculate_urgency(critical_note, PatientProfile(user_id=None, first_name="Test", last_name="User"))
    print(f"Case 1 (Critical): Score={score}, Category={category}")
    assert category == TriageCategory.CRITICAL, "Failed to detect Critical risk"

    # 2. Routine Case
    routine_note = SOAPNote(
        soap_json={"subjective": "Follow up for blood pressure check. Feel fine.", "assessment": "Stable HTN"},
        risk_flags=[]
    )
    score, category = TriageService.calculate_urgency(routine_note, PatientProfile(user_id=None, first_name="Test", last_name="User"))
    print(f"Case 2 (Routine): Score={score}, Category={category}")
    assert category == TriageCategory.LOW, "Failed to categorize as Low"
    
    print("✅ Triage Tests Passed")

def test_safety_logic():
    print("\nTesting Safety Service...")
    
    patient = PatientProfile(user_id=None, first_name="Test", last_name="User", medical_history="History of stomach ulcers.")
    
    # 1. Contraindication
    unsafe_note = SOAPNote(soap_json={"plan": "Prescribe Aspirin 81mg daily for heart health."})
    warnings = SafetyService.check_drug_interactions(unsafe_note, patient)
    
    print(f"Case 1 (Aspirin + Ulcer): Warnings found = {len(warnings)}")
    assert len(warnings) > 0, "Failed to detect Aspirin-Ulcer contraindication"
    print(f" Warning Message: {warnings[0]['message']}")
    
    # 2. Safe
    safe_note = SOAPNote(soap_json={"plan": "Prescribe Tylenol (Acetaminophen) for pain."})
    warnings = SafetyService.check_drug_interactions(safe_note, patient)
    print(f"Case 2 (Tylenol + Ulcer): Warnings found = {len(warnings)}")
    assert len(warnings) == 0, "False positive on safe drug"
    
    print("✅ Safety Tests Passed")

if __name__ == "__main__":
    test_triage_logic()
    test_safety_logic()

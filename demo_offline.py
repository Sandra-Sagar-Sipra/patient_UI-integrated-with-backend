import json
import os
from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, select, create_engine, SQLModel
from app.models.base import Consultation, AudioFile, PatientProfile, User, SOAPNote, ConsultationStatus, AudioUploaderType, UserRole, Appointment, AppointmentStatus, TriageCategory
from app.services.triage_service import TriageService
from app.services.safety_service import SafetyService

# Setup DB
DATABASE_URL = "sqlite:///demo_offline.db"
engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)

MOCK_DATA_FILE = "fixtures/mock_soap_data.json"

def run_offline_demo():
    print(f"Loading Mock Data from {MOCK_DATA_FILE}...")
    with open(MOCK_DATA_FILE, "r") as f:
        cases = json.load(f)
    
    results = []
    
    with Session(engine) as session:
        for case in cases:
            print(f"--- Processing Case: {case['filename']} ---")
            
            # 1. Seed Data
            user = User(email=f"user_{uuid4()}@example.com", password_hash="pw", role=UserRole.PATIENT)
            session.add(user)
            session.commit()
            
            p_data = case['patient_profile']
            patient = PatientProfile(
                user_id=user.id, 
                first_name=p_data['first_name'], 
                last_name=p_data['last_name'], 
                medical_history=p_data.get('medical_history'),
                date_of_birth=datetime.fromisoformat("1980-01-01")
            )
            session.add(patient)
            
            consultation = Consultation(
                doctor_id=user.id, patient_id=user.id, 
                status=ConsultationStatus.COMPLETED, 
                appointment_id=uuid4() # Mock ID
            )
            session.add(consultation)
            session.commit()
            session.refresh(consultation)
            
            # 2. Insert Mock SOAP
            soap = SOAPNote(
                consultation_id=consultation.id,
                soap_json=case['soap_note'],
                risk_flags={"flags": case.get('risk_flags', [])},
                generated_by_ai=True
            )
            session.add(soap)
            
            # 3. RUN LOGIC (The Core Test)
            print("   Running Triage & Safety Algorithms...")
            urgency, category = TriageService.calculate_urgency(soap, patient)
            consultation.urgency_score = urgency
            consultation.triage_category = category
            
            warnings = SafetyService.check_drug_interactions(soap, patient)
            consultation.safety_warnings = warnings
            
            session.add(consultation)
            session.commit()
            
            # Collect Results
            results.append({
                "patient": f"{p_data['first_name']} {p_data['last_name']}",
                "condition": case['soap_note'].get('assessment', '')[:30] + "...",
                "urgency": urgency,
                "category": category,
                "warnings": len(warnings)
            })

    # 4. Display Dashboard
    print("\n\n" + "="*80)
    print("🏥 OFFLINE TRIAGE SIMULATION (No API Tokens Used)")
    print("="*80)
    
    ranked = sorted(results, key=lambda x: x['urgency'], reverse=True)
    
    print(f"{'Rank':<5} | {'Urgency':<8} | {'Category':<10} | {'Patient':<20} | {'Condition':<30} | {'Safety'}")
    print("-" * 110)
    
    for i, p in enumerate(ranked):
        icon = "🔴" if p['category'] == TriageCategory.CRITICAL else "🟠" if p['category'] == TriageCategory.HIGH else "🟡"
        if p['category'] == TriageCategory.LOW: icon = "🟢"
        
        warn_str = f"⚠️ {p['warnings']} Warning" if p['warnings'] > 0 else "✅ Safe"
        
        print(f"#{i+1:<4} | {p['urgency']:<8} | {icon} {p['category']:<8} | {p['patient']:<20} | {p['condition']:<30} | {warn_str}")
        
    print("="*110)

if __name__ == "__main__":
    run_offline_demo()

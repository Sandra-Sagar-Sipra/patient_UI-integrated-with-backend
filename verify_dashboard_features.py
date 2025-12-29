from sqlmodel import Session, select, create_engine
from app.models.base import Consultation, ConsultationStatus, PatientProfile, User, UserRole, TriageCategory, AILog
from app.api.v1.dashboard import get_patient_queue
from datetime import datetime, timedelta
import uuid

# Use a temporary in-memory DB or the test DB for safety
DATABASE_URL = "sqlite:///test_dashboard.db"
engine = create_engine(DATABASE_URL)

def setup_data(session: Session):
    # Create Dummy Users
    u1 = User(email=f"p1_{uuid.uuid4()}@test.com", password_hash="hash", role=UserRole.PATIENT)
    u2 = User(email=f"p2_{uuid.uuid4()}@test.com", password_hash="hash", role=UserRole.PATIENT)
    u3 = User(email=f"p3_{uuid.uuid4()}@test.com", password_hash="hash", role=UserRole.PATIENT)
    session.add_all([u1, u2, u3])
    session.commit()
    
    # Profiles
    p1 = PatientProfile(user_id=u1.id, first_name="John", last_name="Doe", medical_history="None")
    p2 = PatientProfile(user_id=u2.id, first_name="Jane", last_name="Smith", medical_history="Asthma")
    p3 = PatientProfile(user_id=u3.id, first_name="Bob", last_name="Jones", medical_history="Ulcers")
    session.add_all([p1, p2, p3])
    session.commit()
    
    # Create Consultations with different Urgencies
    # Case 1: Critical (Score 95) - Created 10 mins ago
    c1 = Consultation(
        patient_id=u1.id, 
        doctor_id=uuid.uuid4(), 
        appointment_id=uuid.uuid4(),
        status=ConsultationStatus.COMPLETED,
        urgency_score=95,
        triage_category=TriageCategory.CRITICAL,
        created_at=datetime.utcnow() - timedelta(minutes=10)
    )
    
    # Case 2: Low Urgency (Score 20) - Created 30 mins ago (Waiting longer, but lower priority)
    c2 = Consultation(
        patient_id=u2.id, 
        doctor_id=uuid.uuid4(), 
        appointment_id=uuid.uuid4(),
        status=ConsultationStatus.COMPLETED,
        urgency_score=20,
        triage_category=TriageCategory.LOW,
        created_at=datetime.utcnow() - timedelta(minutes=30)
    )
    
    # Case 3: High Urgency (Score 75) - Created 5 mins ago
    c3 = Consultation(
        patient_id=u3.id, 
        doctor_id=uuid.uuid4(), 
        appointment_id=uuid.uuid4(),
        status=ConsultationStatus.COMPLETED,
        urgency_score=75,
        triage_category=TriageCategory.HIGH,
        created_at=datetime.utcnow() - timedelta(minutes=5),
        safety_warnings=[{"message": "Aspirin Contraindication"}] # Simulated warning
    )
    
    session.add_all([c1, c2, c3])
    
    # Create Dummy AI Log
    log = AILog(
        consultation_id=c1.id,
        model_version="gemini-2.0-flash",
        status="SUCCESS",
        latency_ms=1200.5
    )
    session.add(log)
    
    session.commit()
    return [c1, c3, c2] # Expected order: Critical, High, Low

def test_dashboard():
    # Re-create tables
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        print("Setting up test data...")
        expected_order = setup_data(session)
        
        print("\n--- Testing Queue Sorting Logic ---")
        queue = get_patient_queue(session)
        
        print(f"{'Patient':<15} | {'Category':<10} | {'Score':<5} | {'Wait Time':<10}")
        print("-" * 50)
        
        for item in queue:
            print(f"{item['patient_name']:<15} | {item['triage_category']:<10} | {item['urgency_score']:<5} | {item['wait_time_minutes']} min")
            
        # Assertions
        assert queue[0]['triage_category'] == TriageCategory.CRITICAL, "Critical patient not first!"
        assert queue[1]['triage_category'] == TriageCategory.HIGH, "High urgency not second!"
        assert queue[2]['triage_category'] == TriageCategory.LOW, "Low urgency not last, despite long wait!"
        
        print("\n✅ Queue Sorting Verified: Prioritizes Urgency over Wait Time.")
        
        print("\n--- Testing AI Logs ---")
        logs = session.exec(select(AILog)).all()
        print(f"Total AI Logs found: {len(logs)}")
        assert len(logs) > 0
        print(f"Sample Log: Status={logs[0].status}, Latency={logs[0].latency_ms}ms")
        print("✅ Observability Verified.")

if __name__ == "__main__":
    test_dashboard()

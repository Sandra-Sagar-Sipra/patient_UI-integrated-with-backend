from fastapi.testclient import TestClient
from sqlmodel import Session, select, SQLModel
from app.main import app
from app.core.db import engine
from app.models.base import User, PatientProfile, Consultation, ConsultationStatus, UserRole, Appointment, AppointmentStatus
from uuid import uuid4
from datetime import datetime

from sqlalchemy import text

def verify_resilience():
    client = TestClient(app)
    
    # Setup DB & Migrate Schema
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        try:
            # SQLite does not support IF NOT EXISTS for ADD COLUMN in all versions
            # We try to add it, and catch error if it exists.
            session.exec(text("ALTER TABLE consultations ADD COLUMN requires_manual_review BOOLEAN DEFAULT FALSE;"))
            session.commit()
            print("✅ Schema Migrated: Added requires_manual_review column.")
        except Exception as e:
            # Check if error is "duplicate column" which is fine
            if "duplicate column" in str(e).lower() or "no column" not in str(e).lower():
                 print(f"Schema migration note (likely already exists): {e}")
            else:
                 print(f"Schema migration FAILED: {e}")
    
    print("1. Creating Dummy Failed Consultation...")
    with Session(engine) as session:
        # User & Patient
        user = User(email=f"failtest_{uuid4()}@example.com", password_hash="pw", role=UserRole.PATIENT)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        patient = PatientProfile(
            user_id=user.id, first_name="Crash", last_name="Bandicoot", 
            date_of_birth=datetime.now()
        )
        session.add(patient)
        
        # Appointment
        appt = Appointment(patient_id=user.id, doctor_id=user.id, scheduled_at=datetime.now(), status=AppointmentStatus.SCHEDULED)
        session.add(appt)
        session.commit()
        
        # Consultation: Status=FAILED, Review=True
        consult = Consultation(
            doctor_id=user.id, patient_id=user.id, appointment_id=appt.id,
            status=ConsultationStatus.FAILED,
            requires_manual_review=True, # Simulating the processor outcome
            created_at=datetime.now()
        )
        session.add(consult)
        session.commit()
        cid = consult.id
        
    print(f"   Created Consultation {cid} in FAILED state.")
    
    # 2. Query API
    print("2. Querying GET /api/v1/dashboard/queue/failed ...")
    response = client.get("/api/v1/dashboard/queue/failed")
    
    if response.status_code != 200:
        print(f"❌ API Failed: {response.status_code} {response.text}")
        return

    data = response.json()
    print(f"   Response: {data}")
    
    # 3. Assertions
    found = False
    for item in data:
        if item["patient_name"] == "Crash Bandicoot":
            found = True
            print("✅ TEST PASSED: Found failed patient in Review Queue.")
            break
            
    if not found:
        print("❌ TEST FAILED: Patient missing from queue.")

if __name__ == "__main__":
    verify_resilience()

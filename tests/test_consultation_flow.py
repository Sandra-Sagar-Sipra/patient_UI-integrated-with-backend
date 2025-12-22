import pytest
import httpx
import time
import asyncio
from uuid import uuid4

BASE_URL = "http://localhost:8000/api/v1"

@pytest.mark.asyncio
async def test_consultation_lifecycle():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Setup: Doctor Login
        print("\n[STEP 1] Setup - Doctor Signup/Login...")
        email = f"doc_{int(time.time())}@example.com"
        password = "Password123!"
        
        # Signup
        await client.post("/auth/signup", json={
            "email": email, 
            "password": password, 
            "role": "DOCTOR", 
            "first_name": "Test", 
            "last_name": "Doc"
        })
        
        # Login
        resp = await client.post("/auth/login", data={"username": email, "password": password})
        assert resp.status_code == 200, f"Doctor login failed: {resp.text}"
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get Patient ID (Create one)
        patient_email = f"pat_{int(time.time())}@example.com"
        resp = await client.post("/auth/signup", json={
            "email": patient_email, 
            "password": "Password123!", 
            "role": "PATIENT", 
            "first_name": "Test", 
            "last_name": "Patient"
        })
        assert resp.status_code == 200, f"Patient signup failed: {resp.text}"
        patient_id = resp.json().get("user_id") 

        # ... (skipping some lines) ...

        email_d2 = f"doc_{int(time.time())}_2@example.com"
        resp = await client.post("/auth/signup", json={
            "email": email_d2, 
            "password": password, 
            "role": "DOCTOR", 
            "first_name": "Test", 
            "last_name": "Doc2"
        })
        assert resp.status_code == 200, f"Doctor 2 signup failed: {resp.text}"
        doctor_id = resp.json()["user_id"]
        
        # Login with Doc2
        resp = await client.post("/auth/login", data={"username": email_d2, "password": password})
        assert resp.status_code == 200, f"Doctor 2 login failed: {resp.text}"
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create Appointment
        print("[STEP 2] Create Appointment...")
        from datetime import datetime
        appt_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "scheduled_at": datetime.utcnow().isoformat(),
            "reason": "Test Consultation"
        }
        resp = await client.post("/appointments/", json=appt_data, headers=headers)
        assert resp.status_code == 200, f"Create Appointment failed: {resp.text}"
        appointment_id = resp.json()["id"]
        
        # 3. Create Consultation
        print("[STEP 3] Create Consultation...")
        cons_data = {
            "appointment_id": appointment_id,
            "patient_id": patient_id, # Optional but sent
            "notes": "Initial notes"
        }
        resp = await client.post("/consultations/", json=cons_data, headers=headers)
        assert resp.status_code == 200, f"Create Consultation failed: {resp.text}"
        consultation_id = resp.json()["id"]
        assert resp.json()["status"] == "SCHEDULED"
        
        # 4. Upload Audio
        print("[STEP 4] Upload Audio...")
        # Create dummy file
        dummy_content = b"fake audio content"
        files = {"file": ("test.wav", dummy_content, "audio/wav")}
        
        resp = await client.post(f"/consultations/{consultation_id}/upload", files=files, headers=headers)
        assert resp.status_code == 200, f"Upload Audio failed: {resp.text}"
        
        # 5. Poll for Status
        print("[STEP 5] Polling for Processing Completion...")
        status = "IN_PROGRESS"
        processed = False
        for _ in range(15): # Try 15 times
            await asyncio.sleep(1)
            resp = await client.get(f"/consultations/{consultation_id}", headers=headers)
            if resp.status_code != 200:
                print(f"Polling GET failed: {resp.status_code} - {resp.text}")
                continue
            data = resp.json()
            status = data["status"]
            print(f"Current Status: {status}, SOAP: {data.get('soap_note') is not None}")
            
            if data.get("soap_note") is not None:
                processed = True
                break
            if status == "CANCELLED":
                pytest.fail("Processing cancelled/failed")
        
        assert processed is True, "Processing timed out or failed to generate SOAP note"
        assert status == "IN_PROGRESS"
        
        # 6. Verify Content
        data = resp.json()
        assert data["audio_file"] is not None
        assert data["audio_file"]["transcription"] is not None
        assert data["soap_note"] is not None
        assert "Subjective" in str(data["soap_note"]) # It's a dict or str? Model says Relationship to SOAPNote object
        # The GET /consultations/{id} returns Consultation model.
        # Consultation model has: audio_file (object), soap_note (object).
        # SOAPNote object has soap_json field.
        # So data["soap_note"] is the SOAPNote record.
        # data["soap_note"]["soap_json"] is the actual JSON.
        
        print("✅ Consultation Lifecycle Verified!")

if __name__ == "__main__":
    asyncio.run(test_consultation_lifecycle())

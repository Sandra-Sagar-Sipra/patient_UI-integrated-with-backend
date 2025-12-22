from sqlmodel import Session, select
from app.core.db import engine
from app.models.base import Consultation, ConsultationStatus, AudioFile, SOAPNote
from uuid import UUID
import asyncio # For simulation/mocking

# Mock Services for now to verify flow
class AssemblyAIMock:
    @staticmethod
    async def transcribe(file_path: str):
        await asyncio.sleep(2) # Simulate processing
        return "Patient complains of severe headache and nausea for past 2 days. No history of migraine."

class GeminiMock:
    @staticmethod
    def generate_soap(text: str):
        return {
            "Subjective": "Patient reports headache and nausea.",
            "Objective": "Patient appears distressed.",
            "Assessment": "Possible tension headache or viral illness.",
            "Plan": "Prescribe analgesics and rest."
        }, {"flag": "High Pain", "severity": "Medium"}


async def process_consultation_flow(consultation_id: UUID):
    print(f"Starting processing for consultation {consultation_id}")
    with Session(engine) as session:
        consultation = session.get(Consultation, consultation_id)
        if not consultation:
            return
        
        # 1. Update Status: Transcribing
        consultation.status = ConsultationStatus.IN_PROGRESS
        session.add(consultation)
        session.commit()
        
        # 2. Get Audio File
        audio_file = session.exec(select(AudioFile).where(AudioFile.consultation_id == consultation_id)).first()
        if not audio_file:
            print("Audio file missing.")
            consultation.status = ConsultationStatus.IN_PROGRESS # Failed but valid enum
            session.add(consultation)
            session.commit()
            return

        try:
            # 3. Transcribe
            transcript = await AssemblyAIMock.transcribe(audio_file.file_url)
            
            # Update AudioFile
            audio_file.transcription = transcript
            session.add(audio_file)
            
            # Update Status: Transcribed
            consultation.status = ConsultationStatus.IN_PROGRESS
            session.add(consultation)
            session.commit()
            
            # 4. Generate SOAP
            soap_json, risk = GeminiMock.generate_soap(transcript)
            
            # Create SOAP Note
            soap_note = SOAPNote(
                consultation_id=consultation.id,
                soap_json=soap_json,
                risk_flags=risk,
                confidence=0.95,
                generated_by_ai=True
            )
            session.add(soap_note)
            
            # Update Status: SOAP Generated
            consultation.status = ConsultationStatus.IN_PROGRESS
            session.add(consultation)
            session.commit()
            
            print(f"Processing complete for {consultation_id}")
            
        except Exception as e:
            print(f"Processing failed: {e}")
            consultation.status = ConsultationStatus.IN_PROGRESS
            session.add(consultation)
            session.commit()

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.base import Consultation, ConsultationStatus, Appointment, User, UserRole, AudioFile, SOAPNote, AudioUploaderType
from app.api.deps import get_current_user, RoleChecker
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from uuid import UUID, uuid4
import os
import shutil

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class ConsultationCreate(BaseModel):
    appointment_id: UUID
    patient_id: Optional[UUID] = None # Optional if doctor creates it and patient is inferred from appointment
    notes: Optional[str] = None

class ConsultationRead(BaseModel):
    id: UUID
    status: ConsultationStatus
    patient_id: UUID
    doctor_id: UUID
    appointment_id: UUID
    audio_file: Optional[Any] = None
    soap_note: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)

@router.post("/", response_model=Consultation)
def create_consultation(
    consultation_in: ConsultationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(RoleChecker([UserRole.DOCTOR, UserRole.FRONT_DESK]))
):
    # Verify appointment
    appointment = session.get(Appointment, consultation_in.appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check if consultation already exists for this appointment
    existing = session.exec(select(Consultation).where(Consultation.appointment_id == consultation_in.appointment_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Consultation already exists for this appointment")

    # Create Consultation
    new_consultation = Consultation(
        appointment_id=consultation_in.appointment_id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        status=ConsultationStatus.SCHEDULED,
        notes=consultation_in.notes
    )
    session.add(new_consultation)
    session.commit()
    session.refresh(new_consultation)
    return new_consultation

from sqlalchemy.orm import selectinload

@router.get("/{id}", response_model=ConsultationRead) # Returning DB model direct for now, includes relationships
def get_consultation(
    id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    consultation = session.exec(
        select(Consultation)
        .where(Consultation.id == id)
        .options(selectinload(Consultation.audio_file), selectinload(Consultation.soap_note))
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    # Access Control
    if current_user.role == UserRole.PATIENT and consultation.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == UserRole.DOCTOR and consultation.doctor_id != current_user.id:
         # Doctors can view their own patients' consultations
         pass 
         
    return consultation

@router.post("/{id}/upload")
async def upload_audio(
    id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(RoleChecker([UserRole.DOCTOR]))
):
    consultation = session.get(Consultation, id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    # Validation
    if not file.filename.endswith(('.wav', '.mp3', '.m4a')):
        raise HTTPException(status_code=400, detail="Invalid file format")

    # Save File
    file_id = uuid4()
    file_ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{file_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create AudioFile Record
    uploader_type = AudioUploaderType.DOCTOR if current_user.role == UserRole.DOCTOR else AudioUploaderType.PATIENT
    audio_file = AudioFile(
        id=file_id,
        consultation_id=id,
        uploaded_by=uploader_type,
        file_name=file.filename,
        file_url=file_path,
        mime_type=file.content_type
    )
    session.add(audio_file)
    
    # Update Status
    consultation.status = ConsultationStatus.IN_PROGRESS
    session.add(consultation)
    session.commit()
    
    # Trigger Background Task
    from app.services.consultation_processor import process_consultation_flow
    background_tasks.add_task(process_consultation_flow, consultation.id)

    return {"message": "Audio uploaded, processing started", "audio_id": file_id}

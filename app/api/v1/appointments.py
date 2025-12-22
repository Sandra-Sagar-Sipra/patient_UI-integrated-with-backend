from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.base import Appointment, User, UserRole, AppointmentStatus
from app.api.deps import get_current_user, RoleChecker
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

router = APIRouter()

class AppointmentCreate(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    doctor_id: UUID
    scheduled_at: datetime
    reason: Optional[str] = None
    notes: Optional[str] = None

@router.post("/", response_model=Appointment)
def create_appointment(
    appointment_in: AppointmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(RoleChecker([UserRole.DOCTOR, UserRole.FRONT_DESK]))
):
    # Check if patient exists
    patient = session.get(User, appointment_in.patient_id)
    if not patient or patient.role != UserRole.PATIENT:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    # Check if doctor exists
    doctor = session.get(User, appointment_in.doctor_id)
    if not doctor or doctor.role != UserRole.DOCTOR:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    db_appointment = Appointment.model_validate(appointment_in)
    session.add(db_appointment)
    session.commit()
    session.refresh(db_appointment)
    return db_appointment

@router.get("/me", response_model=List[Appointment])
def get_my_appointments(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.PATIENT:
        statement = select(Appointment).where(Appointment.patient_id == current_user.id)
    elif current_user.role == UserRole.DOCTOR:
        statement = select(Appointment).where(Appointment.doctor_id == current_user.id)
    else: # FRONT_DESK see all
        statement = select(Appointment)
        
    return session.exec(statement).all()

@router.patch("/{id}/status")
def update_status(
    id: UUID,
    new_status: AppointmentStatus,
    session: Session = Depends(get_session),
    current_user: User = Depends(RoleChecker([UserRole.DOCTOR, UserRole.FRONT_DESK]))
):
    db_appointment = session.get(Appointment, id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    db_appointment.status = new_status
    db_appointment.updated_at = datetime.utcnow()
    session.add(db_appointment)
    session.commit()
    return {"message": f"Status updated to {new_status}"}

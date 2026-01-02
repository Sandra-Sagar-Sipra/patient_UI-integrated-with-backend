from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.base import Appointment, User, UserRole, AppointmentStatus
from app.api.deps import get_current_user
from app.schemas.appointment import AppointmentCreate
from datetime import datetime, timezone
from uuid import UUID

router = APIRouter()

@router.post("/", status_code=201)
def create_appointment(
    payload: AppointmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Validate user is a patient
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can book appointments")
    
    # Validate scheduled time is not in the past (allow same-day future times)
    now = datetime.now(timezone.utc)
    if payload.scheduled_at < now:
        raise HTTPException(status_code=400, detail="Cannot book appointment in the past")
    
    # Merge symptoms from reason or notes
    symptoms = payload.reason or payload.notes
    if not symptoms:
        raise HTTPException(status_code=400, detail="Symptoms required")
    
    # Validate doctor exists and is a doctor
    doctor = session.get(User, payload.doctor_id)
    if not doctor or doctor.role != UserRole.DOCTOR:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Create appointment
    appointment = Appointment(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        doctor_name=payload.doctor_name,
        scheduled_at=payload.scheduled_at,
        reason=symptoms,
        status=AppointmentStatus.SCHEDULED
    )
    
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    
    return {
        "id": str(appointment.id),
        "status": "confirmed",
        "scheduled_at": appointment.scheduled_at.isoformat(),
        "doctor_name": appointment.doctor_name
    }

@router.get("/me")
def get_my_appointments(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.PATIENT:
        statement = select(Appointment).where(Appointment.patient_id == current_user.id)
    elif current_user.role == UserRole.DOCTOR:
        statement = select(Appointment).where(Appointment.doctor_id == current_user.id)
    else:
        statement = select(Appointment)
    return session.exec(statement).all()

@router.patch("/{id}/status")
def update_status(
    id: UUID,
    new_status: AppointmentStatus,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.DOCTOR, UserRole.FRONT_DESK]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    appointment = session.get(Appointment, id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment.status = new_status
    appointment.updated_at = datetime.now(timezone.utc)
    session.add(appointment)
    session.commit()
    return {"message": f"Status updated to {new_status}"}

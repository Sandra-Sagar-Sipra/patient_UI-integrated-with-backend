from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime
from app.core.db import get_session
from app.models.base import Consultation, PatientProfile, ConsultationStatus

router = APIRouter()

@router.get("/queue/failed", response_model=List[Dict[str, Any]])
def get_failed_queue(session: Session = Depends(get_session)):
    """
    Returns patients whose AI processing failed and require manual review.
    """
    query = (
        select(Consultation, PatientProfile)
        .join(PatientProfile, Consultation.patient_id == PatientProfile.user_id)
        .where(Consultation.requires_manual_review == True)
        .order_by(Consultation.created_at.desc())
    )
    results = session.exec(query).all()
    
    queue = []
    for consult, profile in results:
        # Calculate wait time
        wait_time = "N/A"
        if consult.created_at:
             delta = datetime.utcnow() - consult.created_at
             minutes = int(delta.total_seconds() / 60)
             wait_time = f"{minutes} min"

        queue.append({
            "patient_name": f"{profile.first_name} {profile.last_name}",
            "consultation_id": str(consult.id),
            "reason": "AI Processing Failed (Quota/Error)",
            "wait_time": wait_time,
            "status": "REQUIRES_REVIEW"
        })
    return queue

@router.get("/queue", response_model=List[Dict[str, Any]])
def get_patient_queue(session: Session = Depends(get_session)):
    """
    Returns the prioritized patient queue for the dashboard.
    Sorting Logic:
    1. Urgency Score (DESC) - Critical patients first.
    2. Wait Time (ASC) - First come first served within same urgency.
    """
    query = (
        select(Consultation, PatientProfile)
        .join(PatientProfile, Consultation.patient_id == PatientProfile.user_id)
        .where(Consultation.status == ConsultationStatus.COMPLETED)
        .order_by(Consultation.urgency_score.desc(), Consultation.created_at.asc())
    )
    results = session.exec(query).all()
    
    queue = []
    for consultation, patient in results:
        # Calculate approximate wait time since creation
        wait_time_min = 0
        if consultation.created_at:
            delta = datetime.utcnow() - consultation.created_at
            wait_time_min = int(delta.total_seconds() / 60)

        queue.append({
            "consultation_id": str(consultation.id),
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "urgency_score": consultation.urgency_score or 0,
            "triage_category": consultation.triage_category,
            "wait_time_minutes": wait_time_min,
            "safety_warnings": len(consultation.safety_warnings) if consultation.safety_warnings else 0
        })
    
    return queue

from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.base import User, DoctorProfile, UserRole

router = APIRouter()

@router.get("/")
def get_doctors(session: Session = Depends(get_session)):
    """
    Get list of available doctors.
    Public endpoint - no authentication required.
    """
    # Query doctors with their profiles
    statement = (
        select(User, DoctorProfile)
        .join(DoctorProfile, User.id == DoctorProfile.user_id)
        .where(User.role == UserRole.DOCTOR)
        .where(DoctorProfile.is_available == True)
    )
    
    results = session.exec(statement).all()
    
    doctors = []
    for user, profile in results:
        doctors.append({
            "id": str(user.id),
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "specialization": profile.specialization,
            "clinic_address": profile.clinic_address
        })
    
    return doctors

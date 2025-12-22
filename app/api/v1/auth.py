from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.core.db import get_session
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.base import User, PatientProfile, DoctorProfile, UserRole
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID, uuid4

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    first_name: str
    last_name: str
    phone: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

@router.post("/signup", response_model=dict)
def signup(user_in: UserCreate, session: Session = Depends(get_session)):
    # Check if user exists
    user_db = session.exec(select(User).where(User.email == user_in.email)).first()
    if user_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create User
    new_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Create Profile based on Role
    if new_user.role == UserRole.PATIENT:
        new_profile = PatientProfile(
            user_id=new_user.id,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            phone_number=user_in.phone
        )
        session.add(new_profile)
    elif new_user.role == UserRole.DOCTOR:
        new_profile = DoctorProfile(
            user_id=new_user.id,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            phone_number=user_in.phone,
            specialization="General",    # Default to satisfy apparent DB constraint
            license_number=f"PENDING-{str(uuid4())[:8]}",   # Unique constraint
            years_of_experience=0,      # Default
            qualification="MBBS"        # Default
        )
        session.add(new_profile)
    # FRONT_DESK or others might not have a profile or a different one - skipping for now or handle as needed
    
    session.commit()
    
    return {"message": "User created successfully", "user_id": str(new_user.id)}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value
    }

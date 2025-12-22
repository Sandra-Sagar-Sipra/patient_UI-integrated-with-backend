from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session
from app.core.config import settings
from app.core.db import get_session
from app.models.base import User, UserRole
from pydantic import BaseModel

class TokenPayload(BaseModel):
    sub: str = None
    role: str = None

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def RoleChecker(allowed_roles: list[UserRole]):
    def _role_checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have sufficient permissions. Required: {[r.value for r in allowed_roles]}"
            )
        return user
    return _role_checker

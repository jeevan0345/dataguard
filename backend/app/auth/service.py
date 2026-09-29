"""
DataGuard Authentication Service
Handles user creation, credential validation, and RBAC checks.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.auth.schemas import UserRegister


class AuthService:
    """
    Manages database user operations and JWT issue.
    """

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def register_user(db: Session, payload: UserRegister) -> User:
        clean_email = payload.email.lower().strip()
        existing = db.query(User).filter(User.email == clean_email).first()
        if existing:
            raise ValueError(f"User with email '{clean_email}' already exists.")

        hashed_pwd = hash_password(payload.password)
        is_admin = payload.role.upper() == "ADMIN"

        user = User(
            email=clean_email,
            full_name=payload.full_name.strip(),
            hashed_password=hashed_pwd,
            role=payload.role.upper(),
            is_superuser=is_admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> Optional[User]:
        user = AuthService.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_token_for_user(user: User) -> str:
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.full_name,
        }
        return create_access_token(payload)

"""
DataGuard Authentication & RBAC Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.auth.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.auth.service import AuthService
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication & RBAC"],
)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new DataGuard user with a specified RBAC role.
    """
    try:
        user = AuthService.register_user(db, payload)
        token = AuthService.create_token_for_user(user)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate with email and password to receive a JWT access token.
    """
    user = AuthService.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = AuthService.create_token_for_user(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve profile and permissions for the currently authenticated user.
    """
    return current_user


@router.post(
    "/seed-demo-users",
    status_code=status.HTTP_200_OK,
)
def seed_demo_users(
    db: Session = Depends(get_db),
):
    """
    Utility endpoint to ensure default demo users exist:
    - admin@dataguard.ai (pass: admin123, Role: ADMIN)
    - engineer@dataguard.ai (pass: engineer123, Role: DATA_ENGINEER)
    - viewer@dataguard.ai (pass: viewer123, Role: VIEWER)
    """
    demo_accounts = [
        ("admin@dataguard.ai", "System Administrator", "admin123", "ADMIN"),
        ("engineer@dataguard.ai", "Lead Data Engineer", "engineer123", "DATA_ENGINEER"),
        ("viewer@dataguard.ai", "Business Stakeholder", "viewer123", "VIEWER"),
    ]

    created = []
    for email, name, pwd, role in demo_accounts:
        if not AuthService.get_by_email(db, email):
            user = AuthService.register_user(
                db,
                UserRegister(email=email, full_name=name, password=pwd, role=role),
            )
            created.append(user.email)

    return {
        "status": "SUCCESS",
        "message": f"Seeded {len(created)} demo user(s).",
        "seeded_emails": created,
    }

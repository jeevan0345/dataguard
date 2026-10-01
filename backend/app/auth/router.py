"""
DataGuard Authentication & RBAC Routes
"""

import os
from collections import defaultdict
from time import time
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

_failed_login_attempts: dict[str, list[float]] = defaultdict(list)


def _check_login_rate_limit(key: str, max_attempts: int = 10, window_seconds: int = 60) -> None:
    now = time()
    attempts = [t for t in _failed_login_attempts[key] if now - t < window_seconds]
    _failed_login_attempts[key] = attempts
    if len(attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 60 seconds before trying again.",
        )


def _record_failed_attempt(key: str) -> None:
    _failed_login_attempts[key].append(time())


def _reset_attempts(key: str) -> None:
    _failed_login_attempts.pop(key, None)


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
    Register a new DataGuard user.
    Prevents public self-elevation to ADMIN; assigns DATA_ENGINEER or VIEWER.
    """
    try:
        # Prevent self-elevation to ADMIN on public registration
        safe_role = "DATA_ENGINEER" if payload.role == "ADMIN" else (payload.role or "DATA_ENGINEER")
        safe_payload = UserRegister(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            role=safe_role,
        )
        user = AuthService.register_user(db, safe_payload)
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
    Enforces brute-force rate limiting (max 10 failed attempts/minute).
    """
    rate_key = payload.email.lower()
    _check_login_rate_limit(rate_key)

    user = AuthService.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password,
    )
    if not user:
        _record_failed_attempt(rate_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _reset_attempts(rate_key)
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
    Utility endpoint to ensure default demo users exist in development.
    Strictly forbidden in production environments.
    """
    env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).lower()
    allow_seed = os.getenv("ALLOW_SEED_DEMO_USERS", "true").lower() == "true"
    if env in ["production", "prod"] or not allow_seed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo user seeding is disabled in production environments.",
        )

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

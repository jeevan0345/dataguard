"""
DataGuard Authentication & RBAC Dependencies
Extracts and validates JWT bearer tokens, enforcing role-based permissions.
"""

from typing import Callable
from uuid import UUID
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import decode_access_token
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    token: str | None = Query(None, description="Optional JWT bearer token for direct browser file downloads"),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and authenticates the user from JWT bearer token (via Authorization Header or Query parameter).
    """
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token user identity.",
        )

    user = db.query(User).filter(User.id == user_uuid).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


def require_role(*allowed_roles: str) -> Callable[[User], User]:
    """
    Dependency factory to restrict endpoint access to specific RBAC roles.
    Example: Depends(require_role("ADMIN", "DATA_ENGINEER"))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.upper()
        allowed_upper = [r.upper() for r in allowed_roles]

        if current_user.is_superuser:
            return current_user

        if user_role not in allowed_upper:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}. Your role: {user_role}",
            )
        return current_user

    return role_checker

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_token
from app.db.models import RoleEnum, User, UserAccountStatus, UserApprovalStatus
from app.db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_BYPASS_PREFIX = "bypass-"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _resolve_bypass_user(token: str, db: Session) -> User | None:
    """When AUTH_BYPASS_ENABLED, resolve user from a bypass-<role> token."""
    settings = get_settings()
    if not settings.auth_bypass_enabled:
        return None
    if not token or not token.startswith(_BYPASS_PREFIX):
        return None

    role_str = token[len(_BYPASS_PREFIX):]
    try:
        role = RoleEnum(role_str)
    except ValueError:
        return None

    user = db.scalar(
        select(User).where(
            User.role == role,
            User.account_status == UserAccountStatus.active,
            User.approval_status == UserApprovalStatus.approved,
        ).order_by(User.created_at.asc())
    )
    return user


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # --- Auth bypass path ---
    bypass_user = _resolve_bypass_user(token, db)
    if bypass_user:
        request.state.user_id = str(bypass_user.id)
        return bypass_user

    # --- Normal JWT path ---
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.scalar(select(User).where(User.id == uuid.UUID(subject)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.account_status == UserAccountStatus.inactive:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    request.state.user_id = str(user.id)
    return user


def require_roles(*roles: RoleEnum) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return checker


def require_role(user: User, allowed_roles: list[str | RoleEnum]) -> User:
    allowed = {
        role.value if isinstance(role, RoleEnum) else str(role).strip().lower()
        for role in allowed_roles
    }
    if user.role.value not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user

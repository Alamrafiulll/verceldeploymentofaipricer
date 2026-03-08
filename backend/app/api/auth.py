from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models import RoleEnum, User, UserAccountStatus, UserApprovalStatus
from app.schemas.auth import (
    DevLoginRequest,
    LoginRequest,
    MeResponse,
    TokenResponse,
)

router = APIRouter()

DEV_LOGIN_EMAILS: dict[RoleEnum, str] = {
    RoleEnum.sales: "salesmanager@gmail.com",
    RoleEnum.approver: "salesdirector@gmail.com",
    RoleEnum.executive: "executiveviewer@gmail.com",
    RoleEnum.admin: "admin@gmail.com",
}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    identifier = payload.email.strip()
    user = db.scalar(
        select(User).where(
            or_(
                User.email == identifier.lower(),
                func.lower(User.name) == identifier.lower(),
            )
        )
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.approval_status == UserApprovalStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending admin approval",
        )
    if user.approval_status == UserApprovalStatus.rejected:
        reason = user.approval_reason or "No reason provided"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account rejected by admin: {reason}",
        )
    if user.account_status == UserAccountStatus.inactive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact admin.",
        )

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout() -> dict:
    return {"success": True}


@router.post("/dev-login", response_model=TokenResponse)
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    settings = get_settings()
    if not settings.auth_bypass_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    user = db.scalar(
        select(User)
        .where(
            User.role == payload.role,
            User.account_status == UserAccountStatus.active,
            User.approval_status == UserApprovalStatus.approved,
        )
        .order_by(User.created_at.asc())
    )
    if not user:
        role_labels: dict[RoleEnum, str] = {
            RoleEnum.sales: "Sales Manager",
            RoleEnum.approver: "Sales Director",
            RoleEnum.executive: "Executive Viewer",
            RoleEnum.admin: "Admin User",
        }
        email = DEV_LOGIN_EMAILS[payload.role]
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            existing.role = payload.role
            existing.approval_status = UserApprovalStatus.approved
            existing.account_status = UserAccountStatus.active
            user = existing
        else:
            user = User(
                name=role_labels[payload.role],
                email=email,
                password_hash=get_password_hash("123456"),
                role=payload.role,
                approval_status=UserApprovalStatus.approved,
                account_status=UserAccountStatus.active,
                approval_reason="Auto-provisioned for auth bypass mode",
            )
            db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        approval_status=user.approval_status,
        account_status=user.account_status,
    )

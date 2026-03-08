import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.core.security import get_password_hash
from app.db.models import (
    AIRecommendation,
    AuditLog,
    Campaign,
    Contract,
    CompetitorProduct,
    ModelRun,
    PolicyClause,
    PolicyDocument,
    PolicyDocumentStatus,
    PricingRule,
    PriceBook,
    RebateProgram,
    RoleEnum,
    UploadStatus,
    UploadedFile,
    User,
    UserApprovalStatus,
    now_utc,
)
from app.schemas.admin import (
    AdminResetPasswordRequest,
    AdminResetPasswordResponse,
    AIRecommendationOut,
    AuditLogOut,
    DataQualityOut,
    GovernanceSummaryOut,
    ModelRunOut,
    PendingUserOut,
    ReviewQueueItemOut,
    RuleUpsertRequest,
    UserOut,
    UserApprovalDecisionRequest,
    UserCreateRequest,
    UserStatusUpdateRequest,
)
from app.schemas.master import RuleOut
from app.services.audit_logger import log_audit

router = APIRouter()
@router.post("/rules", response_model=RuleOut)
def upsert_rule(
    payload: RuleUpsertRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> PricingRule:
    existing = db.scalar(
        select(PricingRule).where(
            PricingRule.channel == payload.channel,
            PricingRule.category == payload.category,
        )
    )

    if existing:
        old = {
            "margin_floor_percent": float(existing.margin_floor_percent),
            "max_discount_percent": float(existing.max_discount_percent),
            "approval_required_below_margin_buffer": float(existing.approval_required_below_margin_buffer),
        }
        existing.margin_floor_percent = payload.margin_floor_percent
        existing.max_discount_percent = payload.max_discount_percent
        existing.approval_required_below_margin_buffer = payload.approval_required_below_margin_buffer
        obj = existing
    else:
        old = None
        obj = PricingRule(**payload.model_dump())
        db.add(obj)
        db.flush()

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="rule_upserted",
        entity_type="pricing_rule",
        entity_id=str(obj.id) if obj.id else "pending",
        old_json=old,
        new_json=payload.model_dump(),
    )

    db.commit()
    db.refresh(obj)
    return obj


@router.get("/rules", response_model=list[RuleOut])
def get_rules(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> list[PricingRule]:
    return list(db.scalars(select(PricingRule).order_by(PricingRule.channel, PricingRule.category)).all())


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> dict:
    exists = db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        approval_status=UserApprovalStatus.approved,
        account_status=payload.account_status,
        approved_by_user_id=actor.id,
        approved_at=now_utc(),
        approval_reason="Created by admin",
    )
    db.add(user)
    db.flush()

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="user_created",
        entity_type="user",
        entity_id=str(user.id) if user.id else "pending",
        new_json={
            "email": user.email,
            "role": user.role.value,
            "account_status": user.account_status.value,
            "approval_status": user.approval_status.value,
        },
    )

    db.commit()
    db.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "approval_status": user.approval_status.value,
        "account_status": user.account_status.value,
    }


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


@router.patch("/users/{user_id}/status", response_model=UserOut)
def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == actor.id and payload.account_status.value == "inactive":
        raise HTTPException(status_code=400, detail="Admin cannot deactivate own account")

    old_status = user.account_status.value
    user.account_status = payload.account_status

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="user_status_updated",
        entity_type="user",
        entity_id=str(user.id),
        old_json={"account_status": old_status},
        new_json={"account_status": user.account_status.value},
    )

    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password", response_model=AdminResetPasswordResponse)
def admin_reset_user_password(
    user_id: uuid.UUID,
    payload: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> AdminResetPasswordResponse:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not payload.new_password:
        raise HTTPException(status_code=400, detail="New password is required")

    generated = payload.new_password
    user.password_hash = get_password_hash(generated)

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="user_password_reset",
        entity_type="user",
        entity_id=str(user.id),
        new_json={"reset_by_admin": True},
    )

    db.commit()
    return AdminResetPasswordResponse(user_id=user.id, email=user.email, generated_password=generated)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> Response:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == actor.id:
        raise HTTPException(status_code=400, detail="Admin cannot delete own account")

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="user_deleted",
        entity_type="user",
        entity_id=str(user.id),
        old_json={"email": user.email, "role": user.role.value},
    )

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/pending-users", response_model=list[PendingUserOut])
def pending_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .where(User.approval_status == UserApprovalStatus.pending)
            .order_by(User.created_at.asc())
        ).all()
    )


@router.post("/users/{user_id}/approve", response_model=PendingUserOut)
def approve_user(
    user_id: uuid.UUID,
    payload: UserApprovalDecisionRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old = {
        "approval_status": user.approval_status.value,
        "approval_reason": user.approval_reason,
    }
    user.approval_status = UserApprovalStatus.approved
    user.approved_by_user_id = actor.id
    user.approved_at = now_utc()
    user.approval_reason = payload.reason

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="user_approved",
        entity_type="user",
        entity_id=str(user.id),
        old_json=old,
        new_json={"approval_status": user.approval_status.value, "approval_reason": user.approval_reason},
        reason=payload.reason,
    )

    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reject", response_model=PendingUserOut)
def reject_user(
    user_id: uuid.UUID,
    payload: UserApprovalDecisionRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not payload.reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required")

    old = {
        "approval_status": user.approval_status.value,
        "approval_reason": user.approval_reason,
    }
    user.approval_status = UserApprovalStatus.rejected
    user.approved_by_user_id = actor.id
    user.approved_at = now_utc()
    user.approval_reason = payload.reason

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="user_rejected",
        entity_type="user",
        entity_id=str(user.id),
        old_json=old,
        new_json={"approval_status": user.approval_status.value, "approval_reason": user.approval_reason},
        reason=payload.reason,
    )

    db.commit()
    db.refresh(user)
    return user


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(500)).all())


@router.get("/model-runs", response_model=list[ModelRunOut])
def model_runs(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> list[ModelRun]:
    return list(db.scalars(select(ModelRun).order_by(ModelRun.created_at.desc()).limit(500)).all())


@router.get("/ai-recommendations", response_model=list[AIRecommendationOut])
def ai_recommendations(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> list[AIRecommendation]:
    return list(
        db.scalars(select(AIRecommendation).order_by(AIRecommendation.timestamp.desc()).limit(500)).all()
    )


@router.get("/governance-summary", response_model=GovernanceSummaryOut)
def governance_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> GovernanceSummaryOut:
    avg_confidence = db.scalar(select(func.avg(PolicyClause.confidence))) or 0
    return GovernanceSummaryOut(
        pending_upload_reviews=db.scalar(
            select(func.count(UploadedFile.id)).where(UploadedFile.status == UploadStatus.needs_review)
        )
        or 0,
        pending_policy_reviews=db.scalar(
            select(func.count(PolicyDocument.id)).where(PolicyDocument.status == PolicyDocumentStatus.draft)
        )
        or 0,
        active_pricebooks=db.scalar(select(func.count(PriceBook.id))) or 0,
        active_campaigns=db.scalar(select(func.count(Campaign.id))) or 0,
        active_contracts=db.scalar(select(func.count(Contract.id))) or 0,
        active_rebate_programs=db.scalar(select(func.count(RebateProgram.id))) or 0,
        model_run_failures=db.scalar(select(func.count(ModelRun.id)).where(ModelRun.status != "completed")) or 0,
        ai_trace_count=db.scalar(select(func.count(AIRecommendation.id))) or 0,
        unmatched_competitor_records=db.scalar(
            select(func.count(CompetitorProduct.id)).where(CompetitorProduct.matched_product_id.is_(None))
        )
        or 0,
        average_policy_confidence=round(float(avg_confidence), 2),
    )


@router.get("/document-review-queue", response_model=list[ReviewQueueItemOut])
def document_review_queue(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> list[ReviewQueueItemOut]:
    queue: list[ReviewQueueItemOut] = []

    uploads = list(
        db.scalars(
            select(UploadedFile)
            .where(UploadedFile.status.in_([UploadStatus.draft, UploadStatus.parsed, UploadStatus.needs_review]))
            .order_by(UploadedFile.created_at.desc())
            .limit(100)
        ).all()
    )
    for upload in uploads:
        queue.append(
            ReviewQueueItemOut(
                item_type="uploaded_file",
                item_id=str(upload.id),
                label=upload.file_name,
                status=upload.status.value,
                source_reference=f"UPL-{str(upload.id).split('-')[0].upper()}",
                uploaded_at=upload.created_at,
                next_step=upload.validation_issues.get("next_step") if isinstance(upload.validation_issues, dict) else None,
            )
        )

    policies = list(
        db.scalars(
            select(PolicyDocument)
            .where(PolicyDocument.status == PolicyDocumentStatus.draft)
            .order_by(PolicyDocument.uploaded_at.desc())
            .limit(100)
        ).all()
    )
    for policy in policies:
        queue.append(
            ReviewQueueItemOut(
                item_type="policy_document",
                item_id=str(policy.id),
                label=policy.title,
                status=policy.status.value,
                source_reference=policy.policy_source_reference,
                uploaded_at=policy.uploaded_at,
                next_step=policy.next_step,
            )
        )

    queue.sort(key=lambda item: item.uploaded_at or now_utc(), reverse=True)
    return queue[:150]


@router.get("/data-quality", response_model=DataQualityOut)
def data_quality(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> DataQualityOut:
    average_clause_confidence = db.scalar(select(func.avg(PolicyClause.confidence))) or 0
    return DataQualityOut(
        upload_parse_failures=db.scalar(
            select(func.count(UploadedFile.id)).where(UploadedFile.status == UploadStatus.rejected)
        )
        or 0,
        uploads_needing_review=db.scalar(
            select(func.count(UploadedFile.id)).where(UploadedFile.status == UploadStatus.needs_review)
        )
        or 0,
        reviews_pending_activation=db.scalar(
            select(func.count(PolicyDocument.id)).where(PolicyDocument.status == PolicyDocumentStatus.draft)
        )
        or 0,
        unmatched_competitor_records=db.scalar(
            select(func.count(CompetitorProduct.id)).where(CompetitorProduct.matched_product_id.is_(None))
        )
        or 0,
        recommendations_with_fallback=db.scalar(
            select(func.count(AIRecommendation.id)).where(AIRecommendation.fallback_used.is_(True))
        )
        or 0,
        model_run_failures=db.scalar(select(func.count(ModelRun.id)).where(ModelRun.status != "completed")) or 0,
        average_clause_confidence=round(float(average_clause_confidence), 2),
    )

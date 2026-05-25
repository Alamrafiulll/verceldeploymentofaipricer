import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
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
    UserAccountStatus,
    UserApprovalStatus,
    now_utc,
)
from app.schemas.admin import (
    AdminResetPasswordRequest,
    AdminResetPasswordResponse,
    AIRecommendationOut,
    AuditLogOut,
    DataQualityOut,
    EnterpriseReadinessCheckOut,
    EnterpriseReadinessOut,
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


def _count(db: Session, statement) -> int:
    return int(db.scalar(statement) or 0)


def _readiness_check(
    check_id: str,
    category: str,
    label: str,
    check_status: Literal["pass", "warning", "fail"],
    detail: str,
    action: str | None = None,
) -> EnterpriseReadinessCheckOut:
    return EnterpriseReadinessCheckOut(
        id=check_id,
        category=category,
        label=label,
        status=check_status,
        detail=detail,
        action=action,
    )


def _readiness_response(checks: list[EnterpriseReadinessCheckOut]) -> EnterpriseReadinessOut:
    weights = {"pass": 1.0, "warning": 0.55, "fail": 0.0}
    grouped: dict[str, list[float]] = {}
    for check in checks:
        grouped.setdefault(check.category, []).append(weights[check.status])

    categories = {
        category: round(sum(values) / len(values), 2)
        for category, values in sorted(grouped.items())
        if values
    }
    score = round((sum(categories.values()) / len(categories)) * 100) if categories else 0
    if score >= 85:
        readiness_status: Literal["enterprise_ready", "attention_needed", "not_ready"] = "enterprise_ready"
        summary = "Core controls are in place for an enterprise demo or controlled go-live."
    elif score >= 65:
        readiness_status = "attention_needed"
        summary = "The platform is usable, but a few controls need attention before production rollout."
    else:
        readiness_status = "not_ready"
        summary = "Critical controls are missing. Resolve the failed checks before production rollout."

    return EnterpriseReadinessOut(
        score=score,
        status=readiness_status,
        summary=summary,
        categories=categories,
        checks=checks,
    )


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
    return AdminResetPasswordResponse(
        user_id=user.id,
        email=user.email,
        message="Password reset. Share the new password through an approved channel.",
    )


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


@router.get("/enterprise-readiness", response_model=EnterpriseReadinessOut)
def enterprise_readiness(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.admin)),
) -> EnterpriseReadinessOut:
    settings = get_settings()

    active_admins = _count(
        db,
        select(func.count(User.id)).where(
            User.role == RoleEnum.admin,
            User.approval_status == UserApprovalStatus.approved,
            User.account_status == UserAccountStatus.active,
        ),
    )
    active_users = _count(
        db,
        select(func.count(User.id)).where(
            User.approval_status == UserApprovalStatus.approved,
            User.account_status == UserAccountStatus.active,
        ),
    )
    pending_upload_reviews = _count(
        db,
        select(func.count(UploadedFile.id)).where(UploadedFile.status == UploadStatus.needs_review),
    )
    pending_policy_reviews = _count(
        db,
        select(func.count(PolicyDocument.id)).where(PolicyDocument.status == PolicyDocumentStatus.draft),
    )
    upload_parse_failures = _count(
        db,
        select(func.count(UploadedFile.id)).where(UploadedFile.status == UploadStatus.rejected),
    )
    active_pricebooks = _count(db, select(func.count(PriceBook.id)))
    active_contracts = _count(db, select(func.count(Contract.id)))
    active_rebate_programs = _count(db, select(func.count(RebateProgram.id)))
    active_campaigns = _count(db, select(func.count(Campaign.id)))
    model_run_failures = _count(db, select(func.count(ModelRun.id)).where(ModelRun.status != "completed"))
    ai_trace_count = _count(db, select(func.count(AIRecommendation.id)))
    fallback_recommendations = _count(
        db,
        select(func.count(AIRecommendation.id)).where(AIRecommendation.fallback_used.is_(True)),
    )
    unmatched_competitors = _count(
        db,
        select(func.count(CompetitorProduct.id)).where(CompetitorProduct.matched_product_id.is_(None)),
    )
    clause_count = _count(db, select(func.count(PolicyClause.id)))
    average_clause_confidence = float(db.scalar(select(func.avg(PolicyClause.confidence))) or 0)

    secret = settings.secret_key or ""
    default_secret = secret == "super-secret-change-me"
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    local_cors_only = bool(cors_origins) and all(
        "localhost" in origin or "127.0.0.1" in origin for origin in cors_origins
    )
    wildcard_cors = "*" in cors_origins
    database_url = settings.database_url.lower()
    environment = settings.environment.strip().lower()
    ai_provider = settings.active_ai_provider

    checks = [
        _readiness_check(
            "auth_bypass_disabled",
            "Security",
            "Authentication bypass disabled",
            "pass" if not settings.auth_bypass_enabled else "fail",
            "Bypass tokens are disabled." if not settings.auth_bypass_enabled else "Bypass tokens are enabled.",
            None if not settings.auth_bypass_enabled else "Set AUTH_BYPASS_ENABLED=false before any shared demo or deploy.",
        ),
        _readiness_check(
            "secret_key_rotated",
            "Security",
            "JWT secret configured",
            "fail" if default_secret else "pass" if len(secret) >= 32 else "warning",
            "JWT secret is not the default value."
            if not default_secret
            else "JWT secret still uses the default development value.",
            None if not default_secret and len(secret) >= 32 else "Set SECRET_KEY to a long random value.",
        ),
        _readiness_check(
            "active_admin_present",
            "Security",
            "Active admin owner",
            "pass" if active_admins > 0 else "fail",
            f"{active_admins} active admin account(s) found.",
            None if active_admins > 0 else "Create at least one approved active admin account.",
        ),
        _readiness_check(
            "active_user_base",
            "Security",
            "Approved active users",
            "pass" if active_users >= 4 else "warning" if active_users > 0 else "fail",
            f"{active_users} approved active user account(s) found.",
            None if active_users >= 4 else "Seed or approve users for each role used in the demo.",
        ),
        _readiness_check(
            "database_runtime",
            "Deployment",
            "Production database",
            "fail" if database_url.startswith("sqlite") else "warning" if "localhost" in database_url else "pass",
            "Database points to a network service." if "localhost" not in database_url else "Database points to localhost.",
            None if "localhost" not in database_url and not database_url.startswith("sqlite") else "Use managed PostgreSQL for deployment.",
        ),
        _readiness_check(
            "cors_scope",
            "Deployment",
            "CORS origin scope",
            "fail" if wildcard_cors else "warning" if local_cors_only else "pass",
            "CORS is pinned to explicit origins." if not wildcard_cors else "CORS allows all origins.",
            None if not wildcard_cors and not local_cors_only else "Set CORS_ORIGINS to the deployed frontend domain.",
        ),
        _readiness_check(
            "environment_mode",
            "Deployment",
            "Environment mode",
            "pass" if environment in {"prod", "production", "staging"} else "warning",
            f"Backend environment is '{settings.environment}'.",
            None if environment in {"prod", "production", "staging"} else "Set ENVIRONMENT=production for production deploys.",
        ),
        _readiness_check(
            "upload_review_queue",
            "Data Governance",
            "Upload review queue clear",
            "pass" if pending_upload_reviews == 0 else "warning",
            f"{pending_upload_reviews} upload(s) need review.",
            None if pending_upload_reviews == 0 else "Review or reject pending upload records.",
        ),
        _readiness_check(
            "policy_review_queue",
            "Data Governance",
            "Policy review queue clear",
            "pass" if pending_policy_reviews == 0 else "warning",
            f"{pending_policy_reviews} draft policy document(s) need activation.",
            None if pending_policy_reviews == 0 else "Review extracted clauses and activate trusted policy documents.",
        ),
        _readiness_check(
            "upload_parse_failures",
            "Data Governance",
            "No rejected uploads",
            "pass" if upload_parse_failures == 0 else "warning",
            f"{upload_parse_failures} rejected upload(s) found.",
            None if upload_parse_failures == 0 else "Replace invalid demo files or archive rejected records.",
        ),
        _readiness_check(
            "clause_confidence",
            "Data Governance",
            "Policy extraction confidence",
            "warning" if clause_count == 0 else "pass" if average_clause_confidence >= 0.75 else "warning",
            "No extracted policy clauses found."
            if clause_count == 0
            else f"Average policy clause confidence is {average_clause_confidence:.2f}.",
            None if average_clause_confidence >= 0.75 and clause_count > 0 else "Upload and review policy documents with clear clause extraction.",
        ),
        _readiness_check(
            "ai_provider_configured",
            "AI Governance",
            "AI provider configured",
            "pass" if ai_provider != "deterministic_local" else "warning",
            f"Active provider: {ai_provider}; model: {settings.active_ai_model_name}.",
            None if ai_provider != "deterministic_local" else "Set AI_PROVIDER and provider credentials for live AI recommendations.",
        ),
        _readiness_check(
            "ai_traceability",
            "AI Governance",
            "Recommendation traceability",
            "pass" if ai_trace_count > 0 else "warning",
            f"{ai_trace_count} AI recommendation trace(s) stored.",
            None if ai_trace_count > 0 else "Run a pricing recommendation to generate an auditable trace.",
        ),
        _readiness_check(
            "model_run_health",
            "AI Governance",
            "Model run health",
            "pass" if model_run_failures == 0 else "warning",
            f"{model_run_failures} non-completed model run(s) found.",
            None if model_run_failures == 0 else "Investigate failed model runs before customer demos.",
        ),
        _readiness_check(
            "fallback_pressure",
            "AI Governance",
            "Fallback pressure",
            "pass" if fallback_recommendations == 0 else "warning",
            f"{fallback_recommendations} recommendation(s) used fallback logic.",
            None if fallback_recommendations == 0 else "Confirm provider connectivity or explain fallback behavior in the demo.",
        ),
        _readiness_check(
            "pricebooks_loaded",
            "Commercial Controls",
            "Pricebooks loaded",
            "pass" if active_pricebooks > 0 else "warning",
            f"{active_pricebooks} pricebook(s) available.",
            None if active_pricebooks > 0 else "Upload a current price list or pricebook file.",
        ),
        _readiness_check(
            "contracts_rebates_campaigns",
            "Commercial Controls",
            "Commercial terms loaded",
            "pass" if active_contracts + active_rebate_programs + active_campaigns > 0 else "warning",
            (
                f"{active_contracts} contract(s), {active_rebate_programs} rebate program(s), "
                f"and {active_campaigns} campaign(s) available."
            ),
            None
            if active_contracts + active_rebate_programs + active_campaigns > 0
            else "Load contracts, rebates, or campaign files to demonstrate margin guardrails.",
        ),
        _readiness_check(
            "competitor_matching",
            "Commercial Controls",
            "Competitor matching complete",
            "pass" if unmatched_competitors == 0 else "warning",
            f"{unmatched_competitors} competitor row(s) are unmatched.",
            None if unmatched_competitors == 0 else "Map competitor rows to products before using market comparison.",
        ),
    ]

    return _readiness_response(checks)

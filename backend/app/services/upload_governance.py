"""Role-based upload governance helpers."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.models import RoleEnum, UploadedFile, UploadStatus, UploadType, User
from app.services.audit_logger import log_audit

TABULAR_EXTENSIONS = {".csv", ".xlsx", ".pdf"}
REVIEW_STATUS_BY_UPLOAD_STATUS: dict[UploadStatus, str] = {
    UploadStatus.draft: "draft",
    UploadStatus.parsed: "parsed",
    UploadStatus.needs_review: "needs_review",
    UploadStatus.active: "active",
    UploadStatus.rejected: "rejected",
    UploadStatus.archived: "archived",
}
STATUS_UPDATE_PERMISSIONS: dict[RoleEnum, set[UploadStatus]] = {
    RoleEnum.approver: {
        UploadStatus.needs_review,
        UploadStatus.active,
        UploadStatus.rejected,
    },
    RoleEnum.admin: set(UploadStatus),
}

ROLE_UPLOAD_MATRIX: dict[RoleEnum, set[UploadType]] = {
    RoleEnum.sales: {
        UploadType.sales_history,
        UploadType.product_catalog,
        UploadType.current_price_list,
        UploadType.competitor_price_data,
        UploadType.promotion_calendar,
    },
    RoleEnum.approver: {
        UploadType.pricing_approval_sheet,
        UploadType.strategic_pricing_guideline,
        UploadType.quarterly_pricing_plan,
        UploadType.margin_target_sheet,
    },
    RoleEnum.executive: {
        UploadType.strategic_targets,
        UploadType.market_reports,
    },
    RoleEnum.admin: set(UploadType),
}

UPLOAD_TYPE_ALLOWED_EXTENSIONS: dict[UploadType, set[str]] = {
    UploadType.sales_history: TABULAR_EXTENSIONS,
    UploadType.product_catalog: TABULAR_EXTENSIONS,
    UploadType.current_price_list: TABULAR_EXTENSIONS,
    UploadType.competitor_price_data: TABULAR_EXTENSIONS,
    UploadType.promotion_calendar: TABULAR_EXTENSIONS,
    UploadType.pricing_approval_sheet: {".xlsx", ".pdf"},
    UploadType.strategic_pricing_guideline: {".pdf", ".xlsx", ".csv"},
    UploadType.quarterly_pricing_plan: {".xlsx", ".csv", ".pdf"},
    UploadType.strategic_targets: {".pdf", ".xlsx", ".csv"},
    UploadType.market_reports: {".pdf"},
    UploadType.user_role_config: {".csv", ".xlsx", ".pdf"},
    UploadType.pricing_policy: {".pdf", ".xlsx", ".csv", ".txt"},
    UploadType.audit_log_archive: {".csv", ".xlsx"},
    UploadType.model_configuration: {".json"},
    UploadType.rule_mapping_template: {".csv", ".json", ".xlsx"},
    UploadType.campaign_memo: {".pdf", ".xlsx", ".csv", ".txt"},
    UploadType.trading_terms: {".pdf", ".xlsx", ".csv", ".txt"},
    UploadType.rebate_agreement: {".pdf", ".xlsx", ".csv", ".txt"},
    UploadType.contract_pricing: {".pdf", ".xlsx", ".csv", ".txt"},
    UploadType.margin_target_sheet: {".xlsx", ".csv", ".pdf"},
}

UPLOAD_TYPE_LABELS: dict[UploadType, str] = {
    UploadType.sales_history: "Sales History",
    UploadType.product_catalog: "Product Catalog",
    UploadType.current_price_list: "Current Price List",
    UploadType.competitor_price_data: "Competitor Pricing",
    UploadType.promotion_calendar: "Promotion Calendar",
    UploadType.pricing_approval_sheet: "Pricing Approval Sheet",
    UploadType.strategic_pricing_guideline: "Strategic Pricing Guideline",
    UploadType.quarterly_pricing_plan: "Quarterly Pricing Plan",
    UploadType.strategic_targets: "Strategic Targets",
    UploadType.market_reports: "Market Reports",
    UploadType.user_role_config: "User Role Config",
    UploadType.pricing_policy: "Pricing Policy",
    UploadType.audit_log_archive: "Audit Log Archive",
    UploadType.model_configuration: "Model Configuration",
    UploadType.rule_mapping_template: "Rule Mapping Template",
    UploadType.campaign_memo: "Campaign Memo",
    UploadType.trading_terms: "Trading Terms",
    UploadType.rebate_agreement: "Rebate Agreement",
    UploadType.contract_pricing: "Contract Pricing Document",
    UploadType.margin_target_sheet: "Margin Target Sheet",
}


def parse_upload_type(raw_upload_type: str) -> UploadType:
    try:
        return UploadType(raw_upload_type.strip())
    except ValueError as exc:
        raise ValueError(f"Invalid upload type: {raw_upload_type}") from exc


def validate_upload_permission(role: RoleEnum, upload_type: UploadType) -> None:
    allowed = ROLE_UPLOAD_MATRIX.get(role, set())
    if upload_type not in allowed:
        raise ValueError(
            f"Role '{role.value}' cannot upload '{upload_type.value}'. "
            f"Allowed types: {sorted(item.value for item in allowed)}"
        )


def validate_file_extension(upload_type: UploadType, filename: str) -> str:
    ext = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""
    allowed = UPLOAD_TYPE_ALLOWED_EXTENSIONS.get(upload_type, set())
    if ext not in allowed:
        raise ValueError(
            f"File extension '{ext}' is not allowed for '{upload_type.value}'. "
            f"Accepted: {sorted(allowed)}"
        )
    return ext.lstrip(".")


def default_review_status_for_status(status: UploadStatus) -> str:
    return REVIEW_STATUS_BY_UPLOAD_STATUS.get(status, "pending")


def validate_upload_payload(
    *,
    role: RoleEnum,
    upload_type: UploadType,
    filename: str,
    file_bytes: bytes,
) -> str:
    validate_upload_permission(role, upload_type)
    if not file_bytes:
        raise ValueError("Uploaded file is empty")
    return validate_file_extension(upload_type, filename)


def validate_status_update(role: RoleEnum, new_status: UploadStatus) -> None:
    allowed_statuses = STATUS_UPDATE_PERMISSIONS.get(role, set())
    if new_status not in allowed_statuses:
        raise ValueError(
            f"Role '{role.value}' cannot set upload status to '{new_status.value}'."
        )


def get_allowed_types_for_role(role: RoleEnum) -> list[dict[str, Any]]:
    allowed = ROLE_UPLOAD_MATRIX.get(role, set())
    return [
        {
            "type": upload_type.value,
            "label": UPLOAD_TYPE_LABELS.get(upload_type, upload_type.value),
            "extensions": sorted(UPLOAD_TYPE_ALLOWED_EXTENSIONS.get(upload_type, set())),
        }
        for upload_type in sorted(allowed, key=lambda item: item.value)
    ]


def create_uploaded_file_record(
    db: Session,
    *,
    upload_type: UploadType,
    file_bytes: bytes,
    user: User | None = None,
    uploaded_by: User | None = None,
    file: UploadFile | None = None,
    file_name: str | None = None,
    mime_type: str | None = None,
    source_uri: str | None = None,
    extraction_summary: str | None = None,
    extracted_entities_count: int | None = None,
    meta_json: dict[str, Any] | None = None,
    status: UploadStatus = UploadStatus.draft,
    validation_issues: dict[str, Any] | None = None,
    review_status: str | None = None,
) -> UploadedFile:
    actor = user or uploaded_by
    if actor is None:
        raise ValueError("An uploading user is required")

    resolved_file_name = file_name or (file.filename if file else None) or "unknown"
    resolved_mime_type = mime_type or (file.content_type if file else None)

    file_ext = validate_upload_payload(
        role=actor.role,
        upload_type=upload_type,
        filename=resolved_file_name,
        file_bytes=file_bytes,
    )
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    record = UploadedFile(
        id=uuid.uuid4(),
        uploaded_by_user_id=actor.id,
        uploaded_by_role=actor.role,
        upload_type=upload_type,
        file_name=resolved_file_name,
        file_ext=file_ext,
        mime_type=resolved_mime_type,
        file_hash=file_hash,
        file_size_bytes=len(file_bytes),
        source_uri=source_uri,
        status=status,
        meta_json=meta_json or {},
        extraction_summary=extraction_summary,
        extracted_entities_count=extracted_entities_count,
        validation_issues=validation_issues,
        review_status=review_status or default_review_status_for_status(status),
    )
    db.add(record)

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="file_uploaded",
        entity_type="uploaded_file",
        entity_id=str(record.id),
        new_json={
            "file_name": record.file_name,
            "upload_type": upload_type.value,
            "file_hash": file_hash,
            "file_size_bytes": len(file_bytes),
            "status": record.status.value,
        },
    )
    return record

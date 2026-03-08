"""Universal Upload Center API."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models import (
    DocumentExtractionReview,
    RoleEnum,
    UploadedFile,
    UploadStatus,
    User,
)
from app.schemas.upload_center import UploadReviewAction, UploadReviewUpdate
from app.services.audit_logger import log_audit
from app.services.document_extraction_service import extract_document_intelligence
from app.services.file_text_extractor import extract_text_from_file
from app.services.upload_governance import (
    create_uploaded_file_record,
    default_review_status_for_status,
    get_allowed_types_for_role,
    parse_upload_type,
    validate_status_update,
    validate_upload_payload,
)

router = APIRouter(prefix="/upload-center", tags=["upload-center"])

REVIEW_ACTION_STATUS: dict[UploadReviewAction, UploadStatus] = {
    UploadReviewAction.save_draft: UploadStatus.draft,
    UploadReviewAction.confirm_and_save: UploadStatus.parsed,
    UploadReviewAction.submit_for_review: UploadStatus.needs_review,
    UploadReviewAction.activate: UploadStatus.active,
    UploadReviewAction.reject: UploadStatus.rejected,
}

REVIEW_ACTION_ALLOWED_ROLES: dict[UploadReviewAction, set[RoleEnum]] = {
    UploadReviewAction.save_draft: {
        RoleEnum.sales,
        RoleEnum.approver,
        RoleEnum.executive,
        RoleEnum.admin,
    },
    UploadReviewAction.confirm_and_save: {
        RoleEnum.sales,
        RoleEnum.approver,
        RoleEnum.executive,
        RoleEnum.admin,
    },
    UploadReviewAction.submit_for_review: {
        RoleEnum.sales,
        RoleEnum.approver,
        RoleEnum.executive,
        RoleEnum.admin,
    },
    UploadReviewAction.activate: {RoleEnum.approver, RoleEnum.admin},
    UploadReviewAction.reject: {RoleEnum.approver, RoleEnum.admin},
}


def _next_step_for_status(status: UploadStatus) -> str:
    if status == UploadStatus.draft:
        return "Review the extraction, make corrections if needed, then confirm and save."
    if status == UploadStatus.parsed:
        return "The document is confirmed. Submit it for review or activate it when governance approval is complete."
    if status == UploadStatus.needs_review:
        return "An approver or admin should review the corrected extraction and decide whether to activate or reject it."
    if status == UploadStatus.active:
        return "This document is active and can be referenced by downstream pricing decisions."
    if status == UploadStatus.rejected:
        return "Update the extraction details or upload a corrected source file before trying again."
    return "This document is archived for audit and traceability."


def _can_access_file(user: User, record: UploadedFile) -> bool:
    if user.role in {RoleEnum.admin, RoleEnum.approver}:
        return True
    return record.uploaded_by_user_id == user.id


def _serialize_extraction(
    record: UploadedFile,
    review: DocumentExtractionReview | None,
) -> dict[str, Any]:
    original = dict(review.original_extraction_json or {}) if review else {}
    corrected = dict(review.corrected_extraction_json or {}) if review and review.corrected_extraction_json else {}
    merged = {**original, **corrected}
    entities = merged.get("entities") or original.get("entities") or []
    entities_count = merged.get("entities_count")
    if entities_count is None:
        entities_count = sum(int(entity.get("count", 0)) for entity in entities if isinstance(entity, dict))
    if not entities_count:
        entities_count = record.extracted_entities_count or 0

    return {
        "summary": merged.get("summary") or record.extraction_summary or "No extraction summary available yet.",
        "detected_type": merged.get("detected_type") or record.upload_type.value.replace("_", " ").title(),
        "entities": entities,
        "entities_count": entities_count,
        "confidence": float(merged.get("confidence") or 0),
        "suggested_rules": merged.get("suggested_rules") or [],
        "text_preview": merged.get("text_preview") or original.get("text_preview") or "",
    }


def _serialize_review_payload(
    record: UploadedFile,
    review: DocumentExtractionReview | None,
) -> dict[str, Any]:
    current_extraction = _serialize_extraction(record, review)
    original_extraction = dict(review.original_extraction_json or {}) if review else {}
    corrected_extraction = dict(review.corrected_extraction_json or {}) if review and review.corrected_extraction_json else None
    return {
        "file_id": str(record.id),
        "file_name": record.file_name,
        "upload_type": record.upload_type.value,
        "status": record.status.value,
        "review_id": str(review.id) if review else None,
        "review_status": record.review_status or default_review_status_for_status(record.status),
        "review_notes": review.review_notes if review else None,
        "next_step": _next_step_for_status(record.status),
        "original_extraction": original_extraction,
        "corrected_extraction": corrected_extraction,
        "current_extraction": current_extraction,
    }


def _get_file_and_review(
    db: Session,
    file_id: str,
) -> tuple[UploadedFile, DocumentExtractionReview | None]:
    try:
        parsed_file_id = uuid.UUID(file_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid file id") from exc

    record = db.get(UploadedFile, parsed_file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    review = db.scalar(
        select(DocumentExtractionReview).where(DocumentExtractionReview.uploaded_file_id == record.id)
    )
    return record, review


@router.get("/types")
def list_allowed_types(
    user: User = Depends(get_current_user),
) -> list[dict]:
    """Return document categories and accepted formats for the current user role."""
    return get_allowed_types_for_role(user.role)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    upload_type: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Upload a business document with smart extraction."""
    try:
        parsed_upload_type = parse_upload_type(upload_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_bytes = await file.read()
    try:
        validate_upload_payload(
            role=user.role,
            upload_type=parsed_upload_type,
            filename=file.filename or "",
            file_bytes=file_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        text = extract_text_from_file(file_bytes, file.filename, file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    extraction = extract_document_intelligence(text, parsed_upload_type, file.filename or "")

    try:
        record = create_uploaded_file_record(
            db=db,
            user=user,
            upload_type=parsed_upload_type,
            file=file,
            file_bytes=file_bytes,
            extraction_summary=extraction.summary,
            extracted_entities_count=extraction.entities_count,
            status=UploadStatus.draft,
            review_status=default_review_status_for_status(UploadStatus.draft),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    review = DocumentExtractionReview(
        uploaded_file_id=record.id,
        original_extraction_json={
            "summary": extraction.summary,
            "entities": extraction.entities_found,
            "entities_count": extraction.entities_count,
            "suggested_rules": extraction.suggested_rules,
            "detected_type": extraction.detected_type,
            "confidence": extraction.confidence,
            "text_preview": extraction.raw_text_preview,
        },
        review_status=default_review_status_for_status(UploadStatus.draft),
    )
    db.add(review)

    db.commit()
    db.refresh(record)
    db.refresh(review)

    payload = _serialize_review_payload(record, review)
    return {
        **payload,
        "extraction": payload["current_extraction"],
        "message": "File uploaded and analyzed successfully. Review the extraction below before activation.",
    }


@router.get("/files")
def list_uploaded_files(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    """List uploaded files. Admins see all; others see their own."""
    query = select(UploadedFile).order_by(desc(UploadedFile.created_at)).limit(limit)
    if user.role != RoleEnum.admin:
        query = query.where(UploadedFile.uploaded_by_user_id == user.id)

    files = list(db.scalars(query).all())
    return [
        {
            "id": str(item.id),
            "file_name": item.file_name,
            "upload_type": item.upload_type.value,
            "status": item.status.value,
            "extraction_summary": item.extraction_summary,
            "extracted_entities_count": item.extracted_entities_count,
            "review_status": item.review_status,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "uploaded_by_role": item.uploaded_by_role.value,
            "next_step": _next_step_for_status(item.status),
        }
        for item in files
    ]


@router.get("/files/{file_id}/review")
def get_file_review(
    file_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Return the full extraction review payload for one uploaded file."""
    record, review = _get_file_and_review(db, file_id)
    if not _can_access_file(user, record):
        raise HTTPException(status_code=403, detail="You cannot review this uploaded file")
    return _serialize_review_payload(record, review)


@router.patch("/files/{file_id}/review")
def update_file_review(
    file_id: str,
    payload: UploadReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Save review corrections and move the uploaded file through the confirm-and-save workflow."""
    record, review = _get_file_and_review(db, file_id)
    if not _can_access_file(user, record):
        raise HTTPException(status_code=403, detail="You cannot review this uploaded file")
    if review is None:
        raise HTTPException(status_code=404, detail="Extraction review not found")

    allowed_roles = REVIEW_ACTION_ALLOWED_ROLES[payload.action]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{user.role.value}' cannot perform '{payload.action.value}' on this file",
        )

    current_extraction = _serialize_extraction(record, review)
    entities = current_extraction["entities"]
    if payload.entities is not None:
        entities = [
            {
                "type": entity.type.strip(),
                "count": entity.count,
                "samples": [sample.strip() for sample in entity.samples if sample.strip()],
            }
            for entity in payload.entities
        ]

    suggested_rules = current_extraction["suggested_rules"]
    if payload.suggested_rules is not None:
        suggested_rules = [rule.strip() for rule in payload.suggested_rules if rule.strip()]

    merged_extraction = {
        "summary": (payload.summary or current_extraction["summary"]).strip(),
        "detected_type": (payload.detected_type or current_extraction["detected_type"]).strip(),
        "confidence": payload.confidence
        if payload.confidence is not None
        else current_extraction["confidence"],
        "entities": entities,
        "entities_count": sum(int(entity.get("count", 0)) for entity in entities),
        "suggested_rules": suggested_rules,
        "text_preview": current_extraction["text_preview"],
    }

    review.corrected_extraction_json = merged_extraction
    if payload.review_notes is not None:
        review.review_notes = payload.review_notes.strip() or None

    new_status = REVIEW_ACTION_STATUS[payload.action]
    old_status = record.status.value
    old_review_status = record.review_status
    if payload.action in {UploadReviewAction.activate, UploadReviewAction.reject}:
        validate_status_update(user.role, new_status)
        review.reviewer_user_id = user.id
        review.reviewed_at = datetime.now(timezone.utc)

    review.review_status = default_review_status_for_status(new_status)
    record.status = new_status
    record.review_status = review.review_status
    record.extraction_summary = merged_extraction["summary"]
    record.extracted_entities_count = merged_extraction["entities_count"]

    log_audit(
        db=db,
        actor_user_id=str(user.id),
        action="file_review_updated",
        entity_type="uploaded_file",
        entity_id=str(record.id),
        old_json={"status": old_status, "review_status": old_review_status},
        new_json={
            "status": new_status.value,
            "review_status": review.review_status,
            "action": payload.action.value,
        },
    )
    db.commit()
    db.refresh(record)
    db.refresh(review)
    return _serialize_review_payload(record, review)


@router.patch("/files/{file_id}/status")
def update_file_status(
    file_id: str,
    status: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Update the review status of an uploaded file."""
    if user.role.value not in ("admin", "approver"):
        raise HTTPException(status_code=403, detail="Only admin or approver can update file status")

    try:
        new_status = UploadStatus(status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}") from exc

    try:
        validate_status_update(user.role, new_status)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    record, review = _get_file_and_review(db, file_id)
    old_status = record.status.value
    old_review_status = record.review_status
    record.status = new_status
    record.review_status = default_review_status_for_status(new_status)

    if review:
        review.review_status = record.review_status
        review.reviewer_user_id = user.id
        review.reviewed_at = datetime.now(timezone.utc)

    log_audit(
        db=db,
        actor_user_id=str(user.id),
        action="file_status_updated",
        entity_type="uploaded_file",
        entity_id=file_id,
        old_json={"status": old_status, "review_status": old_review_status},
        new_json={"status": new_status.value, "review_status": record.review_status},
    )
    db.commit()
    return {
        "id": file_id,
        "status": new_status.value,
        "review_status": record.review_status,
        "message": f"Status updated to {new_status.value}",
    }

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.db.models import RoleEnum, UploadedFile, UploadType, User
from app.schemas.uploads import UploadedFileOut
from app.services.audit_logger import log_audit
from app.services.upload_governance import (
    ROLE_UPLOAD_MATRIX,
    create_uploaded_file_record,
    parse_upload_type,
)

router = APIRouter()


@router.get(
    "/uploads/matrix",
    summary="Role upload matrix",
    description="Returns allowed upload document types per role.",
)
def upload_matrix(
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.approver, RoleEnum.executive, RoleEnum.admin)),
) -> dict[str, list[str]]:
    return {
        role.value: sorted(upload_type.value for upload_type in upload_types)
        for role, upload_types in ROLE_UPLOAD_MATRIX.items()
    }


@router.post(
    "/uploads",
    response_model=UploadedFileOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload role-scoped file metadata",
    description=(
        "Multipart upload endpoint for actor-specific files. "
        "Stores governance metadata and hash for traceability."
    ),
)
async def upload_file(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.approver, RoleEnum.executive, RoleEnum.admin)),
) -> UploadedFile:
    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" not in content_type:
        raise HTTPException(status_code=400, detail="Use multipart/form-data with fields upload_type and file")

    form = await request.form()
    raw_upload_type = str(form.get("upload_type") or "").strip()
    source_uri = str(form.get("source_uri") or "").strip() or None
    description = str(form.get("description") or "").strip() or None
    uploaded_file = form.get("file")
    if uploaded_file is None or not hasattr(uploaded_file, "read"):
        raise HTTPException(status_code=400, detail="Missing file for upload")

    try:
        upload_type = parse_upload_type(raw_upload_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_name = str(getattr(uploaded_file, "filename", "") or "").strip()
    mime_type = str(getattr(uploaded_file, "content_type", "") or "").strip() or None
    file_bytes = await uploaded_file.read()

    try:
        record = create_uploaded_file_record(
            db=db,
            upload_type=upload_type,
            file_bytes=file_bytes,
            user=user,
            file_name=file_name,
            mime_type=mime_type,
            source_uri=source_uri,
            meta_json={"description": description} if description else {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_audit(
        db=db,
        actor_user_id=str(user.id),
        action="role_file_uploaded",
        entity_type="uploaded_file",
        entity_id=str(record.id),
        new_json={
            "upload_type": record.upload_type.value,
            "file_name": record.file_name,
            "file_size_bytes": record.file_size_bytes,
            "file_hash": record.file_hash,
        },
    )
    db.commit()
    db.refresh(record)
    return record


@router.get(
    "/uploads",
    response_model=list[UploadedFileOut],
    summary="List uploaded files",
    description="Admin sees all by default. Other roles see their own uploads by default.",
)
def list_uploads(
    mine: bool | None = Query(default=None),
    upload_type: UploadType | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.approver, RoleEnum.executive, RoleEnum.admin)),
) -> list[UploadedFile]:
    stmt = select(UploadedFile).order_by(UploadedFile.created_at.desc())
    if upload_type:
        stmt = stmt.where(UploadedFile.upload_type == upload_type)

    if mine is None:
        mine = user.role != RoleEnum.admin

    if mine:
        stmt = stmt.where(UploadedFile.uploaded_by_user_id == user.id)

    return list(db.scalars(stmt).all())


@router.delete(
    "/uploads/{upload_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete uploaded file metadata",
    description="Admin-only deletion endpoint for governance cleanup.",
)
def delete_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> None:
    try:
        parsed = uuid.UUID(upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid upload id") from exc

    record = db.get(UploadedFile, parsed)
    if not record:
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="role_file_deleted",
        entity_type="uploaded_file",
        entity_id=str(record.id),
        old_json={
            "upload_type": record.upload_type.value,
            "file_name": record.file_name,
            "uploaded_by_user_id": str(record.uploaded_by_user_id) if record.uploaded_by_user_id else None,
        },
    )
    db.delete(record)
    db.commit()

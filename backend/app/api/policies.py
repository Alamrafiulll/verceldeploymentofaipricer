import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, require_roles
from app.db.models import (
    Campaign,
    CampaignRule,
    Contract,
    ContractStatus,
    PolicyDocument,
    PolicyDocumentStatus,
    PriceBook,
    PriceBookChannel,
    RebateProgram,
    RoleEnum,
    User,
)
from app.schemas.policy import (
    CampaignCreateRequest,
    CampaignOut,
    CampaignRuleCreateRequest,
    CampaignRuleOut,
    ContractOut,
    ContractUploadRequest,
    PolicyDocumentOut,
    PolicyReviewUpdateRequest,
    PolicyUploadRequest,
    PriceBookOut,
    PriceBookUploadRequest,
    RebateProgramOut,
)
from app.services.file_text_extractor import extract_text_from_file
from app.services.contract_ingestion import create_contract, parse_contract_lines_from_text
from app.services.policy_ingestion import (
    add_campaign_rule,
    create_campaign,
    ingest_policy_document,
    review_policy_document,
)
from app.services.pricebook_ingestion import ingest_pricebook, ingest_pricebook_from_file
from app.services.audit_logger import log_audit

router = APIRouter()


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid datetime format: {value}") from exc


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


@router.post(
    "/policies/upload",
    response_model=PolicyDocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload policy document and extract clauses",
    description=(
        "Sales/Admin endpoint. Supports JSON text payload and multipart file upload "
        "(txt/csv/pdf/doc/docx/xlsx)."
    ),
)
async def upload_policy(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin)),
) -> PolicyDocument:
    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
            uploaded_file = form.get("file")
            if uploaded_file is None or not hasattr(uploaded_file, "read"):
                raise ValueError("Missing file for multipart upload")
            file_bytes = await uploaded_file.read()
            filename = str(getattr(uploaded_file, "filename", "") or "")
            file_content_type = str(getattr(uploaded_file, "content_type", "") or "")
            extracted_text = extract_text_from_file(
                file_bytes=file_bytes,
                filename=filename,
                content_type=file_content_type,
            )
            payload = PolicyUploadRequest.model_validate(
                {
                    "title": str(form.get("title") or filename or "Uploaded Policy").strip(),
                    "doc_type": str(form.get("doc_type") or "").strip(),
                    "text": extracted_text,
                    "source_uri": (
                        str(form.get("source_uri")).strip()
                        if form.get("source_uri")
                        else (f"upload://{filename}" if filename else None)
                    ),
                    "source_uploaded_file_id": (
                        str(form.get("source_uploaded_file_id")).strip()
                        if form.get("source_uploaded_file_id")
                        else None
                    ),
                    "effective_start": _parse_optional_datetime(
                        str(form.get("effective_start")) if form.get("effective_start") else None
                    ),
                    "effective_end": _parse_optional_datetime(
                        str(form.get("effective_end")) if form.get("effective_end") else None
                    ),
                    "status": str(form.get("status") or "draft").strip(),
                    "auto_create_campaign": _parse_bool(
                        str(form.get("auto_create_campaign")) if form.get("auto_create_campaign") else None,
                        default=True,
                    ),
                }
            )
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        try:
            payload_dict = await request.json()
            payload = PolicyUploadRequest.model_validate(payload_dict)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ingest_policy_document(
        db=db,
        payload=payload,
        uploaded_by=user,
        request_id=getattr(request.state, "request_id", "policy-upload"),
    )


@router.get(
    "/policies",
    response_model=list[PolicyDocumentOut],
    summary="List policy documents",
    description="Readable by sales, admin, approver, and executive roles.",
)
def list_policies(
    status_filter: PolicyDocumentStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)),
) -> list[PolicyDocument]:
    stmt = (
        select(PolicyDocument)
        .options(selectinload(PolicyDocument.clauses))
        .order_by(PolicyDocument.uploaded_at.desc())
    )
    if status_filter:
        stmt = stmt.where(PolicyDocument.status == status_filter)
    return list(db.scalars(stmt).all())


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyDocumentOut,
    summary="Get policy document detail",
    description="Includes extracted clauses for compliance review.",
)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)),
) -> PolicyDocument:
    try:
        parsed = uuid.UUID(policy_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid policy id") from exc

    doc = db.scalar(
        select(PolicyDocument)
        .where(PolicyDocument.id == parsed)
        .options(selectinload(PolicyDocument.clauses))
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Policy document not found")
    return doc


@router.patch(
    "/policies/{policy_id}/review",
    response_model=PolicyDocumentOut,
    summary="Review and correct extracted policy clauses",
    description=(
        "Admin-only workflow to correct extracted clauses, update policy metadata, "
        "and activate or archive the policy document."
    ),
)
def review_policy(
    policy_id: str,
    payload: PolicyReviewUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.admin)),
) -> PolicyDocument:
    try:
        return review_policy_document(
            db=db,
            policy_id=policy_id,
            payload=payload,
            reviewed_by=user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/pricebooks/upload",
    response_model=PriceBookOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload price book",
    description=(
        "Sales-only endpoint. Supports JSON payload ingestion and multipart CSV/XLSX upload. "
        "For file upload, provide form fields name/channel/currency and a file with sku,list_price,notes columns."
    ),
)
async def upload_pricebook(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales)),
) -> PriceBook:
    content_type = request.headers.get("content-type", "").lower()
    try:
        if "multipart/form-data" in content_type:
            form = await request.form()
            uploaded_file = form.get("file")
            if uploaded_file is None or not hasattr(uploaded_file, "read"):
                raise ValueError("Missing file for multipart upload")
            file_bytes = await uploaded_file.read()
            return ingest_pricebook_from_file(
                db=db,
                uploaded_by=user,
                file_bytes=file_bytes,
                filename=str(getattr(uploaded_file, "filename", "") or ""),
                name=str(form.get("name") or "").strip(),
                channel=str(form.get("channel") or "").strip(),
                currency=str(form.get("currency") or "RM").strip(),
                effective_start=_parse_optional_datetime(form.get("effective_start")),
                effective_end=_parse_optional_datetime(form.get("effective_end")),
                source_document_id=(
                    str(form.get("source_document_id")).strip()
                    if form.get("source_document_id")
                    else None
                ),
            )

        payload_dict = await request.json()
        payload = PriceBookUploadRequest.model_validate(payload_dict)
        return ingest_pricebook(db=db, payload=payload, uploaded_by=user)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/pricebooks",
    response_model=list[PriceBookOut],
    summary="List price books",
    description="Readable by sales, admin, approver, and executive roles.",
)
def list_pricebooks(
    channel: PriceBookChannel | None = Query(default=None),
    mine: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)),
) -> list[PriceBook]:
    stmt = (
        select(PriceBook)
        .options(selectinload(PriceBook.items), selectinload(PriceBook.uploaded_by))
        .order_by(PriceBook.created_at.desc(), PriceBook.name.asc())
    )
    if channel:
        stmt = stmt.where(PriceBook.channel == channel)
    if mine:
        stmt = stmt.where(PriceBook.uploaded_by_user_id == user.id)
    return list(db.scalars(stmt).all())


@router.delete(
    "/pricebooks/{pricebook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete uploaded price book",
    description="Admin-only endpoint to remove uploaded product list files.",
)
def delete_pricebook(
    pricebook_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleEnum.admin)),
) -> None:
    try:
        parsed = uuid.UUID(pricebook_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid pricebook id") from exc

    pricebook = db.get(PriceBook, parsed)
    if not pricebook:
        raise HTTPException(status_code=404, detail="Price book not found")

    log_audit(
        db=db,
        actor_user_id=str(actor.id),
        action="pricebook_deleted",
        entity_type="price_book",
        entity_id=str(pricebook.id),
        old_json={
            "name": pricebook.name,
            "channel": pricebook.channel.value,
            "uploaded_by_user_id": str(pricebook.uploaded_by_user_id) if pricebook.uploaded_by_user_id else None,
        },
    )
    db.delete(pricebook)
    db.commit()


@router.get(
    "/campaigns",
    response_model=list[CampaignOut],
    summary="List campaigns",
    description="Readable by sales, admin, approver, and executive roles.",
)
def list_campaigns(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)),
) -> list[Campaign]:
    stmt = select(Campaign).options(selectinload(Campaign.rules)).order_by(Campaign.effective_start.desc())
    return list(db.scalars(stmt).all())


@router.get(
    "/rebate-programs",
    response_model=list[RebateProgramOut],
    summary="List rebate programs",
    description="Readable by sales, admin, approver, and executive roles.",
)
def list_rebate_programs(
    channel: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)),
) -> list[RebateProgram]:
    stmt = select(RebateProgram).order_by(RebateProgram.created_at.desc(), RebateProgram.name.asc())
    if channel:
        stmt = stmt.where(RebateProgram.channel == channel)
    return list(db.scalars(stmt).all())


@router.get(
    "/contracts",
    response_model=list[ContractOut],
    summary="List customer contract pricing rules",
    description="Readable by sales, admin, approver, and executive roles.",
)
def list_contracts(
    status_filter: ContractStatus | None = Query(default=None, alias="status"),
    customer_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)),
) -> list[Contract]:
    stmt = (
        select(Contract)
        .options(selectinload(Contract.lines), selectinload(Contract.customer))
        .order_by(Contract.created_at.desc(), Contract.name.asc())
    )
    if status_filter:
        stmt = stmt.where(Contract.status == status_filter)
    if customer_id:
        try:
            stmt = stmt.where(Contract.customer_id == uuid.UUID(customer_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid customer id") from exc
    return list(db.scalars(stmt).all())


@router.post(
    "/contracts/upload",
    response_model=ContractOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload or create customer contract pricing rules",
    description=(
        "Admin-only endpoint. Supports JSON payload ingestion and multipart file upload for PDF, CSV, XLSX, "
        "JSON, and TXT contract pricing documents."
    ),
)
async def upload_contract(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.admin)),
) -> Contract:
    content_type = request.headers.get("content-type", "").lower()
    try:
        if "multipart/form-data" in content_type:
            form = await request.form()
            uploaded_file = form.get("file")
            if uploaded_file is None or not hasattr(uploaded_file, "read"):
                raise ValueError("Missing file for multipart upload")

            file_bytes = await uploaded_file.read()
            filename = str(getattr(uploaded_file, "filename", "") or "")
            file_content_type = str(getattr(uploaded_file, "content_type", "") or "")
            extracted_text = extract_text_from_file(
                file_bytes=file_bytes,
                filename=filename,
                content_type=file_content_type,
            )
            parsed_lines = parse_contract_lines_from_text(db=db, text=extracted_text)
            payload = ContractUploadRequest.model_validate(
                {
                    "customer_id": str(form.get("customer_id") or "").strip(),
                    "name": str(form.get("name") or filename or "Uploaded Contract").strip(),
                    "source_document_id": (
                        str(form.get("source_document_id")).strip()
                        if form.get("source_document_id")
                        else None
                    ),
                    "source_uploaded_file_id": (
                        str(form.get("source_uploaded_file_id")).strip()
                        if form.get("source_uploaded_file_id")
                        else None
                    ),
                    "effective_start": _parse_optional_datetime(
                        str(form.get("effective_start")) if form.get("effective_start") else None
                    ),
                    "effective_end": _parse_optional_datetime(
                        str(form.get("effective_end")) if form.get("effective_end") else None
                    ),
                    "status": str(form.get("status") or ContractStatus.active.value).strip(),
                    "text": extracted_text,
                    "lines": [
                        {
                            "product_id": str(line.product_id),
                            "floor_price": line.floor_price,
                            "ceiling_price": line.ceiling_price,
                            "discount_cap_percent": line.discount_cap_percent,
                        }
                        for line in parsed_lines
                    ],
                }
            )
        else:
            payload_dict = await request.json()
            payload = ContractUploadRequest.model_validate(payload_dict)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        line_payloads = [line.model_dump(exclude_none=True) for line in payload.lines]
        if not line_payloads:
            if not payload.text:
                raise ValueError("Contract upload requires contract lines or readable text")
            parsed_lines = parse_contract_lines_from_text(db=db, text=payload.text)
            line_payloads = [
                {
                    "product_id": str(line.product_id),
                    "floor_price": line.floor_price,
                    "ceiling_price": line.ceiling_price,
                    "discount_cap_percent": line.discount_cap_percent,
                }
                for line in parsed_lines
            ]

        return create_contract(
            db=db,
            customer_id=payload.customer_id,
            name=payload.name,
            status=payload.status,
            effective_start=payload.effective_start,
            effective_end=payload.effective_end,
            source_document_id=payload.source_document_id,
            source_uploaded_file_id=payload.source_uploaded_file_id,
            line_payloads=line_payloads,
            actor_user_id=str(user.id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/campaigns",
    response_model=CampaignOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create campaign",
    description="Admin-only endpoint to create campaign metadata linked to a source policy document.",
)
def create_campaign_endpoint(
    payload: CampaignCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.admin)),
) -> Campaign:
    try:
        return create_campaign(
            db=db,
            name=payload.name,
            source_document_id=payload.source_document_id,
            status=payload.status,
            effective_start=payload.effective_start,
            effective_end=payload.effective_end,
            actor_user_id=str(user.id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/campaigns/{campaign_id}/rules",
    response_model=CampaignRuleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create campaign rule",
    description="Admin-only endpoint to add a campaign rule with eligibility/exclusion/entitlement JSON.",
)
def create_campaign_rule_endpoint(
    campaign_id: str,
    payload: CampaignRuleCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.admin)),
) -> CampaignRule:
    try:
        return add_campaign_rule(
            db=db,
            campaign_id=campaign_id,
            rule_type=payload.rule_type,
            eligibility_json=payload.eligibility_json,
            exclusion_json=payload.exclusion_json,
            entitlement_json=payload.entitlement_json,
            actor_user_id=str(user.id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

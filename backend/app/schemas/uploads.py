from datetime import datetime
import uuid

from pydantic import BaseModel

from app.db.models import RoleEnum, UploadStatus, UploadType


class UploadedFileOut(BaseModel):
    id: uuid.UUID
    uploaded_by_user_id: uuid.UUID | None
    uploaded_by_role: RoleEnum
    upload_type: UploadType
    file_name: str
    file_ext: str
    mime_type: str | None
    file_hash: str
    file_size_bytes: int
    source_uri: str | None
    status: UploadStatus
    meta_json: dict
    extraction_summary: str | None = None
    extracted_entities_count: int | None = None
    linked_policy_id: uuid.UUID | None = None
    linked_campaign_id: uuid.UUID | None = None
    linked_pricebook_id: uuid.UUID | None = None
    linked_contract_id: uuid.UUID | None = None
    linked_rebate_program_id: uuid.UUID | None = None
    validation_issues: dict | None = None
    review_status: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

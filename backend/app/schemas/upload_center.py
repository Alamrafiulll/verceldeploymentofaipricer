from enum import Enum

from pydantic import BaseModel, Field


class UploadReviewAction(str, Enum):
    save_draft = "save_draft"
    confirm_and_save = "confirm_and_save"
    submit_for_review = "submit_for_review"
    activate = "activate"
    reject = "reject"


class ExtractionEntityInput(BaseModel):
    type: str = Field(min_length=1)
    count: int = Field(ge=0)
    samples: list[str] = Field(default_factory=list)


class UploadReviewUpdate(BaseModel):
    summary: str | None = None
    detected_type: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    entities: list[ExtractionEntityInput] | None = None
    suggested_rules: list[str] | None = None
    review_notes: str | None = None
    action: UploadReviewAction = UploadReviewAction.save_draft

    model_config = {"extra": "forbid"}

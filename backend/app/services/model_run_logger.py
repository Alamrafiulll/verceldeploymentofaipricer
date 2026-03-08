from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.db.models import ModelRun


def _parse_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def log_model_run(
    db: Session,
    run_type: str,
    model_name: str,
    status: str,
    request_id: str | None = None,
    model_version: str | None = None,
    model_provider: str | None = None,
    fallback_used: bool = False,
    latency_ms: float | None = None,
    input_hash: str | None = None,
    related_quote_id: str | uuid.UUID | None = None,
    related_product_id: str | uuid.UUID | None = None,
    related_recommendation_id: str | uuid.UUID | None = None,
    meta_json: dict[str, Any] | None = None,
) -> None:
    db.add(
        ModelRun(
            run_type=run_type,
            model_name=model_name,
            model_version=model_version,
            model_provider=model_provider,
            request_id=request_id,
            status=status,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            input_hash=input_hash,
            related_quote_id=_parse_uuid(related_quote_id),
            related_product_id=_parse_uuid(related_product_id),
            related_recommendation_id=_parse_uuid(related_recommendation_id),
            meta_json=meta_json or {},
        )
    )

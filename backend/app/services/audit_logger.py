import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def log_audit(
    db: Session,
    actor_user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    old_json: dict[str, Any] | None = None,
    new_json: dict[str, Any] | None = None,
    reason: str | None = None,
    model_version: str | None = None,
) -> None:
    parsed_actor_user_id: uuid.UUID | None = None
    if actor_user_id:
        parsed_actor_user_id = (
            actor_user_id if isinstance(actor_user_id, uuid.UUID) else uuid.UUID(actor_user_id)
        )

    entry = AuditLog(
        actor_user_id=parsed_actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_json=old_json,
        new_json=new_json,
        reason=reason,
        model_version=model_version,
    )
    db.add(entry)

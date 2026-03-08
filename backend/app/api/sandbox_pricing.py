import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.db.models import RoleEnum, User
from app.schemas.pricing_schema import SandboxPriceRequest, SandboxPriceResponse
from app.services.sandbox_pricing_service import generate_price

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


@router.post("/pricing/recommend/{product_id}", response_model=SandboxPriceResponse)
def recommend_price(
    product_id: str,
    payload: SandboxPriceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(
        require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)
    ),
) -> SandboxPriceResponse:
    try:
        parsed_product_id = uuid.UUID(product_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid product id. Select a product from the list (UUID required).",
        ) from exc

    recommendation = generate_price(
        product_id=parsed_product_id,
        discount_percent=payload.discount_percent,
        channel=payload.channel,
        db=db,
        actor_user_id=str(user.id),
    )
    if not recommendation:
        raise HTTPException(status_code=404, detail="Product not found")
    return SandboxPriceResponse(**recommendation)

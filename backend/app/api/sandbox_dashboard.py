from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.db.models import Product, Recommendation, RoleEnum, User

router = APIRouter(prefix="/sandbox/dashboard", tags=["sandbox"])


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)),
) -> dict:
    total_products = db.scalar(select(func.count()).select_from(Product)) or 0
    avg_price = db.scalar(select(func.avg(Product.list_price))) or 0
    total_predictions = db.scalar(select(func.count()).select_from(Recommendation)) or 0

    return {
        "total_products": int(total_products),
        "average_price": round(float(avg_price), 2),
        "predictions_made": int(total_predictions),
    }


from fastapi import APIRouter, Depends

from app.api import (
    admin,
    analytics,
    approvals,
    auth,
    bulk_import,
    dashboard,
    master,
    market_comparison,
    policies,
    pricing,
    products,
    quotes,
    sandbox_dashboard,
    sandbox_pricing,
    sandbox_products,
    uploads,
    upload_center,
)
from app.core.deps import get_current_user
from app.db.models import User
from app.schemas.auth import MeResponse

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(master.router, tags=["master"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(policies.router, tags=["policy-governance"])
api_router.include_router(uploads.router, tags=["uploads"])
api_router.include_router(upload_center.router)
api_router.include_router(market_comparison.router)
api_router.include_router(bulk_import.router)
api_router.include_router(sandbox_products.router)
api_router.include_router(sandbox_pricing.router)
api_router.include_router(sandbox_dashboard.router)
api_router.include_router(products.router)
api_router.include_router(pricing.router)
api_router.include_router(dashboard.router)


@api_router.get("/me", response_model=MeResponse, tags=["auth"])
def me_alias(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        approval_status=user.approval_status,
        account_status=user.account_status,
    )

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.db.models import Product, RoleEnum, User
from app.schemas.product_schema import SandboxProductCreate, SandboxProductOut

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


@router.get("/products", response_model=list[SandboxProductOut])
def list_products(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver, RoleEnum.executive)),
) -> list[SandboxProductOut]:
    products = db.scalars(select(Product).order_by(Product.created_at.desc()).limit(500)).all()
    return [
        SandboxProductOut(
            id=str(product.id),
            sku=product.sku,
            name=product.name,
            category=product.category,
            base_cost=float(product.unit_cost),
            current_price=float(product.list_price),
        )
        for product in products
    ]


@router.post("/products", response_model=SandboxProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: SandboxProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin)),
) -> SandboxProductOut:
    existing = db.scalar(select(Product).where(Product.sku == payload.sku))
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    product = Product(
        sku=payload.sku.strip(),
        name=payload.name.strip(),
        category=payload.category.strip(),
        unit_cost=payload.base_cost,
        list_price=payload.current_price,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return SandboxProductOut(
        id=str(product.id),
        sku=product.sku,
        name=product.name,
        category=product.category,
        base_cost=float(product.unit_cost),
        current_price=float(product.list_price),
    )


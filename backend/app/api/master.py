import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models import Inventory, PricingRule, Product, User, Customer
from app.schemas.master import CustomerOut, InventoryOut, ProductOut, RuleOut

router = APIRouter()


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Customer]:
    return list(db.scalars(select(Customer).order_by(Customer.name)).all())


@router.get("/products", response_model=list[ProductOut])
def list_products(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.name)).all())


@router.get("/inventory", response_model=list[InventoryOut])
def list_inventory(
    product_id: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Inventory]:
    stmt = select(Inventory)
    if product_id:
        stmt = stmt.where(Inventory.product_id == uuid.UUID(product_id))
    return list(db.scalars(stmt).all())


@router.get("/rules", response_model=list[RuleOut])
def list_rules(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PricingRule]:
    return list(db.scalars(select(PricingRule).order_by(PricingRule.channel, PricingRule.category)).all())

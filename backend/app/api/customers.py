import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.db.models import Customer, CustomerTier, RoleEnum, User

router = APIRouter()


class CustomerCreate(BaseModel):
    name: str
    tier: CustomerTier = CustomerTier.core
    region: str = "North America"
    email: EmailStr | None = None


class CustomerOut(BaseModel):
    id: uuid.UUID
    name: str
    tier: CustomerTier
    region: str
    created_at: datetime


@router.get("", response_model=list[CustomerOut])
def list_customers(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Customer]:
    """
    List all customers.
    """
    return list(db.scalars(select(Customer).order_by(Customer.name)).all())


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin)),
) -> Customer:
    """
    Create a new customer (Sales Manager or Admin).
    """
    # Check if exists by name (simple duplicate check)
    existing = db.scalar(select(Customer).where(Customer.name == payload.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this name already exists",
        )

    customer = Customer(
        name=payload.name,
        tier=payload.tier,
        region=payload.region,
        # email=payload.email  # Assuming model has email, check models.py if needed
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

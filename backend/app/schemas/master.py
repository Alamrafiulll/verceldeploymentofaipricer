from datetime import datetime
import uuid

from pydantic import BaseModel

from app.db.models import CustomerTier


class CustomerOut(BaseModel):
    id: uuid.UUID
    name: str
    tier: CustomerTier
    region: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    category: str
    list_price: float
    unit_cost: float

    model_config = {"from_attributes": True}


class InventoryOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    on_hand: int
    stock_age_days_avg: int

    model_config = {"from_attributes": True}


class RuleOut(BaseModel):
    id: uuid.UUID
    channel: str
    category: str
    margin_floor_percent: float
    max_discount_percent: float
    approval_required_below_margin_buffer: float

    model_config = {"from_attributes": True}

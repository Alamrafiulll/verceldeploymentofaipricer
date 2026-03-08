from pydantic import BaseModel, Field


class SandboxProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=120)
    base_cost: float = Field(gt=0)
    current_price: float = Field(gt=0)


class SandboxProductOut(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    base_cost: float
    current_price: float


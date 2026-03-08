from pydantic import BaseModel, Field


class SandboxPriceResponse(BaseModel):
    product_id: str
    predicted_price: float
    confidence: float
    explanation: str
    model_version: str | None = None
    margin_percent: float | None = None
    rationale: str | None = None
    channel: str | None = None
    unit_cost: float | None = None
    list_price: float | None = None


class SandboxPriceRequest(BaseModel):
    discount_percent: float = Field(default=0, ge=0, le=100)
    channel: str = Field(default="direct", pattern="^(direct|distributor|project)$")


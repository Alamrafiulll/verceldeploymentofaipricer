from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.db.models import RoleEnum, UserAccountStatus, UserApprovalStatus


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=5, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_like(cls, value: str) -> str:
        identifier = value.strip()
        if not identifier:
            raise ValueError("Login identifier is required")
        return identifier


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class DevLoginRequest(BaseModel):
    role: RoleEnum


class MeResponse(BaseModel):
    id: str
    name: str
    email: str
    role: RoleEnum
    approval_status: UserApprovalStatus
    account_status: UserAccountStatus

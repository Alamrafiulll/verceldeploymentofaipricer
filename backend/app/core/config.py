from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "Chin Hin AI Pricing Strategist"
    environment: str = "dev"
    api_prefix: str = "/api"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pricing_db"

    secret_key: str = "super-secret-change-me"
    access_token_expire_minutes: int = 60 * 12
    jwt_algorithm: str = "HS256"
    auth_bypass_enabled: bool = False

    foundry_endpoint_url: str | None = None
    foundry_api_key: str | None = None
    foundry_model_name: str = "gpt-5"
    foundry_scoring_endpoint_url: str | None = None
    azure_endpoint: str | None = None
    azure_api_key: str | None = None

    win_model_version: str = "foundry-v1"
    feature_schema_version: str = "schema-v1"

    recommendation_tolerance: float = 0.98
    candidate_step_percent: float = 0.01

    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=(str(REPO_DIR / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors(cls, value: str) -> str:
        return value or "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()

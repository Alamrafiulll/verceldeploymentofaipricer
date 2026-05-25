from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "RevenueMind"
    environment: str = "dev"
    api_prefix: str = "/api"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pricing_db"

    secret_key: str = "super-secret-change-me"
    access_token_expire_minutes: int = 60 * 12
    jwt_algorithm: str = "HS256"
    auth_bypass_enabled: bool = False

    ai_provider: str = "openai"
    foundry_endpoint_url: str | None = None
    foundry_api_key: str | None = None
    foundry_model_name: str = "gpt-5.4-mini"
    foundry_scoring_endpoint_url: str | None = None
    azure_endpoint: str | None = None
    azure_api_key: str | None = None

    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_model_name: str = "gpt-5.4-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout_seconds: float = 20.0
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str | None = None
    ollama_model_name: str = "llama3.1:8b"
    ollama_timeout_seconds: float = 45.0

    gemini_api_key: str | None = None
    gemini_model: str | None = None
    gemini_model_name: str = "gemini-1.5-flash"
    gemini_timeout_seconds: float = 20.0

    win_model_version: str = "openai-gpt-5.4-mini"
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

    @property
    def effective_openai_model_name(self) -> str:
        return self.openai_model or self.openai_model_name

    @property
    def effective_ollama_model_name(self) -> str:
        return self.ollama_model or self.ollama_model_name

    @property
    def effective_gemini_model_name(self) -> str:
        return self.gemini_model or self.gemini_model_name

    @property
    def normalized_ai_provider(self) -> str:
        return self.ai_provider.strip().lower()

    @property
    def openai_enabled(self) -> bool:
        return self.normalized_ai_provider == "openai" and bool(self.openai_api_key)

    @property
    def ollama_enabled(self) -> bool:
        return self.normalized_ai_provider == "ollama"

    @property
    def gemini_enabled(self) -> bool:
        return self.normalized_ai_provider == "gemini" and bool(self.gemini_api_key)

    @property
    def active_ai_model_name(self) -> str:
        if self.ollama_enabled:
            return self.effective_ollama_model_name
        if self.openai_enabled:
            return self.effective_openai_model_name
        if self.gemini_enabled:
            return self.effective_gemini_model_name
        if self.legacy_foundry_enabled:
            return self.foundry_model_name
        return self.win_model_version

    @property
    def active_ai_provider(self) -> str:
        if self.ollama_enabled:
            return "ollama_local"
        if self.openai_enabled:
            return "openai"
        if self.gemini_enabled:
            return "gemini"
        if self.legacy_foundry_enabled:
            return "azure_foundry"
        return "deterministic_local"

    @property
    def legacy_foundry_enabled(self) -> bool:
        return self.normalized_ai_provider in {"foundry", "azure_foundry", "azure-openai"} and bool(
            self.foundry_api_key
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

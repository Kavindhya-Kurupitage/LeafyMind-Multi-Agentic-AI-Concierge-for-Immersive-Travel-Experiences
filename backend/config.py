"""Application configuration loaded from environment variables."""

from enum import Enum
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers (switch via LLM_PROVIDER in .env)."""

    GEMINI = "GEMINI"
    GROQ = "GROQ"
    OPENAI = "OPENAI"


class Settings(BaseSettings):
    """Central settings for the LeafyMind FastAPI backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    postgres_user: str = "leafymind"
    postgres_password: str = Field(default="change_me_secure_password", min_length=8)
    postgres_db: str = "leafymind"
    database_url: str = Field(
        default="postgresql+asyncpg://leafymind:leafymind@localhost:5432/leafymind"
    )

    # JWT
    jwt_secret: str = Field(
        default="change_me_to_a_long_random_secret_at_least_32_chars",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440

    # LLM (default Groq — set GROQ_API_KEY in .env)
    llm_provider: LLMProvider = LLMProvider.GROQ
    llm_model: str = "llama-3.1-8b-instant"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2048, ge=256, le=32000)

    groq_api_key: str = ""
    openai_api_key: str = ""  # optional: only for embeddings when using Groq

    # Unsplash (food guide dish images — fallback when no local file)
    unsplash_access_key: str = ""
    unsplash_base_url: str = "https://api.unsplash.com"

    # Local food photos (mounted from frontend/public/images/food in Docker)
    food_images_dir: str = "/app/food_images"
    food_images_url_prefix: str = "/images/food"

    # Static assets for PDF branding (logo under frontend/public)
    public_assets_dir: str = "/app/public_assets"

    # OpenTripMap (itinerary nearby discoveries)
    opentripmap_api_key: str = ""
    opentripmap_base_url: str = "https://api.opentripmap.com/0.1/en"
    cabana_lat: float = 6.7311
    cabana_lon: float = 81.1003
    cabana_name: str = "Leafy Cave Cabana, Wellawaya"
    max_search_radius_km: int = 100

    # Gmail SMTP (post-stay feedback emails — App Password, not account password)
    gmail_sender_address: str = ""
    gmail_app_password: str = ""
    feedback_email_delay_days: int = Field(default=1, ge=0, le=30)
    frontend_url: str = "http://localhost:5173"

    # Server
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:3001"
    backend_port: int = 8000
    node_env: str = "development"

    # Migrations (Docker: /app/migrations; local: ../db/migrations)
    migrations_dir: str = ""

    @field_validator("llm_provider", mode="before")
    @classmethod
    def normalize_llm_provider(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @model_validator(mode="after")
    def validate_required_fields(self) -> "Settings":
        """Ensure provider-specific API keys and core secrets are present."""
        if self.llm_provider == LLMProvider.GEMINI:
            raise ValueError(
                "LLM_PROVIDER=GEMINI is no longer supported. Use LLM_PROVIDER=GROQ and GROQ_API_KEY"
            )
        if self.llm_provider == LLMProvider.GROQ and not self.groq_api_key.strip():
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=GROQ")
        if self.llm_provider == LLMProvider.OPENAI and not self.openai_api_key.strip():
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=OPENAI")
        if not self.database_url.strip():
            raise ValueError("DATABASE_URL is required")
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.node_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (used by tests and lazy imports)."""
    return Settings()


settings = get_settings()

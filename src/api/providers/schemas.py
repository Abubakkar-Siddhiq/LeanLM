from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, field_validator


SUPPORTED_PROVIDERS = {"groq", "openai", "anthropic", "google"}


class ProviderKeyCreate(BaseModel):
    provider_name: str
    api_key: str

    @field_validator("provider_name")
    @classmethod
    def normalize_and_validate_provider(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider '{normalized}'. "
                f"Supported providers: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
            )
        return normalized

    @field_validator("api_key")
    @classmethod
    def reject_empty_key(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("API key cannot be empty")
        return v.strip()


class ProviderKeyResponse(BaseModel):
    id: UUID
    provider_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProviderKeyValidateResponse(BaseModel):
    provider_name: str
    valid: bool
    message: str


class ProviderAvailabilityResponse(BaseModel):
    available_providers: list[str]

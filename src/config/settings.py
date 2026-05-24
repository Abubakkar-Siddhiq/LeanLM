from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    DATABASE_URL: str
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    PROVIDER_KEY_ENCRYPTION_SECRET: str = ""
    HF_TOKEN: str = ""
    ALLOW_ENV_PROVIDER_FALLBACK: bool = True

    SUPABASE_URL: str = ""
    SUPABASE_JWT_ISSUER: str = ""
    SUPABASE_JWKS_URL: str = ""


settings = Settings()
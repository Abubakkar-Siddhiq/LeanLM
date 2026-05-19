from pathlib import Path

from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str
    HF_TOKEN: str

    class Config:
        env_file = ROOT_DIR / ".env"


settings = Settings()
import logging
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str = "sqlite:///./dev.db"
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "openrouter/free"
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    DEBUG: bool = True
    
    CORS_ALLOWED_ORIGINS: str = "*"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "pptx", "docx", "xlsx"]


def get_settings() -> Settings:
    if not hasattr(get_settings, '_instance'):
        get_settings._instance = Settings()
    return get_settings._instance


def get_engine():
    settings = get_settings()
    return create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})


def get_session_factory():
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_cors_origins() -> List[str]:
    settings = get_settings()
    origins = settings.CORS_ALLOWED_ORIGINS
    if not origins or origins == "*":
        if settings.DEBUG:
            logger.warning("CORS set to allow all origins (*) - use only in development")
            return ["*"]
        logger.error("CORS set to allow all origins in production - this is insecure!")
        return []
    return [o.strip() for o in origins.split(",")]


def get_max_file_size() -> int:
    return get_settings().MAX_FILE_SIZE


def get_allowed_file_types() -> List[str]:
    return get_settings().ALLOWED_FILE_TYPES

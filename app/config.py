from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "GameBridge Ethiopian Esports Ladder"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-gamebridge-ethiopia-2026-supersecure"
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./gamebridge.db",
        description="Async database connection string. Use postgresql+asyncpg:// in production"
    )
    SYNC_DATABASE_URL: str = Field(
        default="sqlite:///./gamebridge.db",
        description="Sync database connection string for Alembic"
    )
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = "7123456789:AAFakeTokenForLocalTestingOnly123456"
    TELEGRAM_BOT_USERNAME: str = "GameBridgeEthBot"
    TELEGRAM_WEBHOOK_SECRET: str = "gb_wh_secret_token_123456"
    
    # App base URL
    APP_URL: str = "http://localhost:8000"
    
    # External APIs
    LICHESS_API_BASE: str = "https://lichess.org"
    CHESS_COM_API_BASE: str = "https://api.chess.com/pub"
    CHESS_COM_USER_AGENT: str = "GameBridgeEsports/1.0 (contact: info@gamebridge.et)"
    API_TIMEOUT_SECONDS: float = 5.0
    
    # Localization
    DEFAULT_LOCALE: str = "en"
    SUPPORTED_LOCALES: List[str] = ["en", "am", "om"]
    
    # File Storage
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    MAX_UPLOAD_BYTES: int = 3 * 1024 * 1024  # 3MB limit
    
    # Competitive & Elo parameters
    DEFAULT_SEED_ELO: int = 1200
    K_FACTOR_PROVISIONAL: int = 40  # first 10 matches
    K_FACTOR_ESTABLISHED: int = 24  # after 10 matches
    PROVISIONAL_MATCH_THRESHOLD: int = 10
    
    # Demo Mode
    DEMO_MODE: bool = True
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

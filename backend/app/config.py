from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal
import os
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://ocr_bank_user:ocr_bank_password@localhost:5432/ocr_bank"

    def get_database_url(self) -> str:
        """Get properly URL-encoded database connection string."""
        try:
            # Parse and reconstruct URL to ensure proper encoding
            if self.database_url.startswith("postgresql://"):
                # Remove protocol
                rest = self.database_url.replace("postgresql://", "")

                # Split @ to get user:pass and host
                if "@" in rest:
                    user_pass, host = rest.split("@", 1)

                    # Split user:pass
                    if ":" in user_pass:
                        user, password = user_pass.split(":", 1)

                        # URL encode user and password
                        encoded_user = quote_plus(user)
                        encoded_password = quote_plus(password)

                        # Reconstruct URL
                        return f"postgresql://{encoded_user}:{encoded_password}@{host}"

            return self.database_url
        except Exception as e:
            print(f"⚠️  Error encoding database URL: {e}")
            return self.database_url

    # VLM (Vision Language Model for OCR)
    vlm_provider: Literal["groq", "gemini"] = "groq"

    # OCR Engine
    ocr_engine: Literal["tesseract", "paddleocr"] = "paddleocr"

    # OCR Configuration
    ocr_language: str = "th"
    ocr_device: str = "cpu"

    # VLM Fallback
    vlm_fallback_enabled: bool = True

    # LLM
    gemini_api_key: str = ""
    groq_api_key: str = ""
    llm_provider: Literal["gemini"] = "gemini"

    # Vector Store
    chromadb_persist_directory: str = "/tmp/chromadb"

    # Google Sheets
    google_sheets_credentials_path: str = ""
    google_sheets_spreadsheet_id: str = ""

    # File Storage
    image_storage_path: str = "/tmp/ocr_images"
    max_upload_size: int = 10485760  # 10MB

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"  # Comma-separated list

    # Authentication (JWT)
    secret_key: str = "your-secret-key-change-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://ocr_bank_user:ocr_bank_password@localhost:5432/ocr_bank"

    # VLM (Vision Language Model for OCR)
    vlm_provider: Literal["groq", "lm_studio"] = "groq"

    # OCR Engine
    ocr_engine: Literal["tesseract", "paddleocr"] = "paddleocr"

    # LLM
    gemini_api_key: str = ""
    groq_api_key: str = ""
    llm_provider: Literal["gemini", "local_gemma"] = "gemini"
    local_llm_url: str = "http://localhost:1234/v1"

    # Vector Store
    chromadb_persist_directory: str = "./data/chromadb"

    # Google Sheets
    google_sheets_credentials_path: str = "./config/credentials.json"
    google_sheets_spreadsheet_id: str = ""

    # File Storage
    image_storage_path: str = "./images"
    max_upload_size: int = 10485760  # 10MB

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"  # Comma-separated list

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

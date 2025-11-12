"""
Configuration management for the API server.
"""
import os
from typing import List
from pathlib import Path


class Config:
    """Application configuration."""
    
    # Server settings
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Default OCR settings
    DEFAULT_DEVICE: str = os.getenv("DEFAULT_DEVICE", "cpu")
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    DEFAULT_OUTPUT_FORMAT: str = os.getenv("DEFAULT_OUTPUT_FORMAT", "markdown")
    
    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE_MB", "100")) * 1024 * 1024  # Convert MB to bytes
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg"
    ]
    
    # Output settings
    DEFAULT_OUTPUT_DIR: str = os.getenv("DEFAULT_OUTPUT_DIR", "./api_output")
    
    # Model options defaults
    DEFAULT_USE_DOC_ORIENTATION_CLASSIFY: bool = False
    DEFAULT_USE_DOC_UNWARPING: bool = False
    DEFAULT_USE_TEXTLINE_ORIENTATION: bool = False
    DEFAULT_USE_TABLE_RECOGNITION: bool = True
    DEFAULT_USE_FORMULA_RECOGNITION: bool = True
    DEFAULT_USE_CHART_RECOGNITION: bool = True
    DEFAULT_USE_SEAL_RECOGNITION: bool = False
    DEFAULT_USE_REGION_DETECTION: bool = False
    
    @classmethod
    def ensure_output_dir(cls) -> Path:
        """Ensure output directory exists and return Path object."""
        output_path = Path(cls.DEFAULT_OUTPUT_DIR)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path


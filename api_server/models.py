"""
Pydantic models for request/response validation.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Output format options."""
    JSON = "json"
    MARKDOWN = "markdown"
    RAW = "raw"


class Language(str, Enum):
    """Language options."""
    EN = "en"
    CH = "ch"
    EN_CH = "en&ch"


class Device(str, Enum):
    """Device options."""
    CPU = "cpu"
    GPU = "gpu"


class ConvertResponse(BaseModel):
    """Response model for conversion endpoint."""
    status: str = Field(..., description="Status of the conversion: 'success' or 'error'")
    output_format: str = Field(..., description="Output format used")
    content: str = Field(..., description="The formatted text content")
    pages: int = Field(..., description="Number of pages processed")
    saved_files: Optional[List[str]] = Field(default=None, description="List of saved file paths (if save_output=true)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (processing time, file size, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "output_format": "markdown",
                "content": "# Document Title\n\nDocument content...",
                "pages": 1,
                "saved_files": None,
                "metadata": {
                    "processing_time_seconds": 2.5,
                    "file_size_bytes": 1024000
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str = Field(default="error", description="Status is always 'error'")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": "Invalid file format",
                "detail": "File must be PDF, PNG, JPG, or JPEG"
            }
        }


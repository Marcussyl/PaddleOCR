"""
FastAPI application for PP-StructureV3 OCR API.
"""
import asyncio
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from .models import ConvertResponse, ErrorResponse, OutputFormat, Language, Device
from .ocr_service import OCRService
from .utils import validate_file
from .config import Config

app = FastAPI(
    title="PP-StructureV3 OCR API",
    description="REST API for converting PDF/image files to formatted text using PP-StructureV3",
    version="1.0.0",
)

# Initialize OCR service (singleton)
ocr_service = OCRService()


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PP-StructureV3 OCR API"}


@app.post("/api/v1/ocr/convert", response_model=ConvertResponse)
async def convert_file(
    file: UploadFile = File(..., description="PDF or image file to process"),
    output_format: OutputFormat = Query(
        default=OutputFormat.MARKDOWN,
        description="Output format: json, markdown, or raw"
    ),
    language: Language = Query(
        default=Language.EN,
        description="Language: en, ch, or en&ch"
    ),
    device: Device = Query(
        default=Device.CPU,
        description="Device: cpu or gpu"
    ),
    save_output: bool = Query(
        default=False,
        description="Whether to save output files to disk"
    ),
    output_dir: Optional[str] = Query(
        default=None,
        description="Directory to save output files (if save_output=true)"
    ),
    use_doc_orientation_classify: bool = Query(
        default=False,
        description="Enable document orientation classification"
    ),
    use_doc_unwarping: bool = Query(
        default=False,
        description="Enable document unwarping/correction"
    ),
    use_textline_orientation: bool = Query(
        default=False,
        description="Enable textline orientation classification"
    ),
    use_table_recognition: bool = Query(
        default=True,
        description="Enable table recognition"
    ),
    use_formula_recognition: bool = Query(
        default=True,
        description="Enable formula recognition"
    ),
    use_chart_recognition: bool = Query(
        default=True,
        description="Enable chart recognition"
    ),
    use_seal_recognition: bool = Query(
        default=False,
        description="Enable seal recognition"
    ),
    use_region_detection: bool = Query(
        default=False,
        description="Enable region detection"
    ),
):
    """
    Convert PDF or image file to formatted text.
    
    This endpoint accepts a file upload and converts it to the requested format
    (JSON, Markdown, or raw text) using PP-StructureV3 OCR pipeline.
    
    **Parameters:**
    - **file**: PDF or image file (required)
    - **output_format**: Output format - json, markdown, or raw (default: markdown)
    - **language**: Language - en, ch, or en&ch (default: en)
    - **device**: Device - cpu or gpu (default: cpu)
    - **save_output**: Whether to save output files to disk (default: false)
    - **output_dir**: Directory to save files (optional, uses default if not specified)
    - **Model options**: Various boolean flags to enable/disable specific processing modules
    
    **Returns:**
    - Formatted text content in the requested format
    - Number of pages processed
    - List of saved file paths (if save_output=true)
    - Processing metadata
    """
    try:
        # Validate file
        file_type, file_ext = validate_file(file)
        
        # Read file content
        file_content = await file.read()
        
        # Check file size
        if len(file_content) > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({len(file_content) / (1024*1024):.1f}MB) exceeds maximum allowed size of {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Process file in thread pool (since PPStructureV3 is synchronous)
        loop = asyncio.get_event_loop()
        content, pages, saved_files, metadata = await loop.run_in_executor(
            None,
            lambda: ocr_service.process_uploaded_file(
                file_content=file_content,
                filename=file.filename or "uploaded_file",
                output_format=output_format.value,
                language=language.value,
                device=device.value,
                use_doc_orientation_classify=use_doc_orientation_classify,
                use_doc_unwarping=use_doc_unwarping,
                use_textline_orientation=use_textline_orientation,
                use_table_recognition=use_table_recognition,
                use_formula_recognition=use_formula_recognition,
                use_chart_recognition=use_chart_recognition,
                use_seal_recognition=use_seal_recognition,
                use_region_detection=use_region_detection,
                save_output=save_output,
                output_dir=output_dir,
            )
        )
        
        return ConvertResponse(
            status="success",
            output_format=output_format.value,
            content=content,
            pages=pages,
            saved_files=saved_files,
            metadata=metadata,
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Custom exception handler for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status="error",
            error=exc.detail,
            detail=None
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """General exception handler."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status="error",
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True
    )


"""
Utility functions for file handling and format conversion.
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from fastapi import UploadFile, HTTPException
from .config import Config


def validate_file(file: UploadFile) -> Tuple[str, str]:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file object
        
    Returns:
        Tuple of (file_type, file_extension)
        
    Raises:
        HTTPException: If file is invalid
    """
    # Note: File size is checked after reading the file content in main.py
    # This function only validates file type
    
    # Check file extension
    filename = file.filename or ""
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in Config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type if available
    if hasattr(file, 'content_type') and file.content_type:
        if file.content_type not in Config.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MIME type: {file.content_type}"
            )
    
    # Determine file type
    if file_ext == ".pdf":
        file_type = "pdf"
    else:
        file_type = "image"
    
    return file_type, file_ext


def get_file_type(file_path: str) -> str:
    """
    Detect if file is PDF or image.
    
    Args:
        file_path: Path to file
        
    Returns:
        "pdf" or "image"
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    return "image"


def extract_raw_text_from_json(json_data: Dict[str, Any]) -> str:
    """
    Extract plain text from JSON result structure.
    
    Args:
        json_data: JSON result from PPStructureV3
        
    Returns:
        Plain text string
    """
    text_parts = []
    
    # Navigate through the JSON structure to extract text
    res = json_data.get("res", {})
    parsing_res_list = res.get("parsing_res_list", [])
    
    for parsing_res in parsing_res_list:
        block_label = parsing_res.get("block_label", "")
        block_content = parsing_res.get("block_content", "")
        
        if block_label == "text":
            # Extract text from text blocks
            if isinstance(block_content, str):
                text_parts.append(block_content)
            elif isinstance(block_content, list):
                for item in block_content:
                    if isinstance(item, dict):
                        text = item.get("text", "")
                        if text:
                            text_parts.append(text)
        elif block_label == "title":
            # Extract title text
            if isinstance(block_content, str):
                text_parts.append(block_content)
            elif isinstance(block_content, list):
                for item in block_content:
                    if isinstance(item, dict):
                        text = item.get("text", "")
                        if text:
                            text_parts.append(text)
        elif block_label == "table":
            # Extract text from table cells
            if isinstance(block_content, dict):
                html = block_content.get("html", "")
                # Simple HTML to text conversion (remove tags)
                text = re.sub(r'<[^>]+>', ' ', html)
                text = re.sub(r'\s+', ' ', text).strip()
                if text:
                    text_parts.append(text)
        elif block_label == "equation":
            # Extract formula text
            if isinstance(block_content, dict):
                latex = block_content.get("latex", "")
                if latex:
                    text_parts.append(latex)
    
    return "\n\n".join(text_parts)


def extract_raw_text_from_markdown(markdown_text: str) -> str:
    """
    Strip markdown formatting to get plain text.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        Plain text string
    """
    # Remove markdown headers
    text = re.sub(r'^#+\s+', '', markdown_text, flags=re.MULTILINE)
    
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove markdown images
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    
    # Remove markdown bold/italic
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove markdown code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()


def save_output_files(
    content: str,
    output_format: str,
    output_dir: Path,
    filename_base: str,
    markdown_images: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    Save output files to disk.
    
    Args:
        content: Formatted text content
        output_format: Output format (json, markdown, raw)
        output_dir: Directory to save files
        filename_base: Base filename (without extension)
        markdown_images: List of dictionaries with image data (optional)
        
    Returns:
        List of saved file paths
    """
    saved_files = []
    
    # Determine file extension
    if output_format == "json":
        ext = ".json"
        # If content is already a string, try to parse it as JSON for formatting
        try:
            content_obj = json.loads(content)
            content = json.dumps(content_obj, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            pass  # Use content as-is
    elif output_format == "markdown":
        ext = ".md"
    else:  # raw
        ext = ".txt"
    
    # Save main content file
    output_file = output_dir / f"{filename_base}{ext}"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    saved_files.append(str(output_file))
    
    # Save images if provided
    if markdown_images:
        images_dir = output_dir / f"{filename_base}_images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        for page_images in markdown_images:
            if isinstance(page_images, dict):
                for img_path, img_data in page_images.items():
                    if hasattr(img_data, 'save'):  # PIL Image
                        img_file = images_dir / Path(img_path).name
                        img_data.save(img_file)
                        saved_files.append(str(img_file))
    
    return saved_files


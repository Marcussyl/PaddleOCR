"""
OCR Service for processing files with PP-StructureV3.
"""
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from paddleocr import PPStructureV3
from .config import Config
from .utils import extract_raw_text_from_json, extract_raw_text_from_markdown, save_output_files


class OCRService:
    """Service for OCR processing using PP-StructureV3."""
    
    _instance: Optional['OCRService'] = None
    _pipeline: Optional[PPStructureV3] = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super(OCRService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the service (only once due to singleton)."""
        if self._pipeline is None:
            # Pipeline will be initialized lazily with specific config
            pass
    
    def _get_pipeline(
        self,
        language: str = "en",
        device: str = "cpu",
        use_doc_orientation_classify: bool = False,
        use_doc_unwarping: bool = False,
        use_textline_orientation: bool = False,
        use_table_recognition: bool = True,
        use_formula_recognition: bool = True,
        use_chart_recognition: bool = True,
        use_seal_recognition: bool = False,
        use_region_detection: bool = False,
    ) -> PPStructureV3:
        """
        Get or create PPStructureV3 pipeline with specified configuration.
        
        Note: For simplicity, we create a new pipeline for each request.
        In production, you might want to cache pipelines based on configuration.
        
        Args:
            language: Language code ("en", "ch", or "en&ch")
            device: Device to use ("cpu" or "gpu")
            use_doc_orientation_classify: Enable document orientation classification
            use_doc_unwarping: Enable document unwarping
            use_textline_orientation: Enable textline orientation
            use_table_recognition: Enable table recognition
            use_formula_recognition: Enable formula recognition
            use_chart_recognition: Enable chart recognition
            use_seal_recognition: Enable seal recognition
            use_region_detection: Enable region detection
            
        Returns:
            PPStructureV3 pipeline instance
        """
        # Map language parameter
        lang = "ch" if language in ["ch", "en&ch"] else "en"
        
        # Create pipeline with configuration
        pipeline = PPStructureV3(
            lang=lang,
            device=device,
            use_doc_orientation_classify=use_doc_orientation_classify,
            use_doc_unwarping=use_doc_unwarping,
            use_textline_orientation=use_textline_orientation,
            use_table_recognition=use_table_recognition,
            use_formula_recognition=use_formula_recognition,
            use_chart_recognition=use_chart_recognition,
            use_seal_recognition=use_seal_recognition,
            use_region_detection=use_region_detection,
        )
        
        return pipeline
    
    def process_file(
        self,
        file_path: str,
        output_format: str = "markdown",
        language: str = "en",
        device: str = "cpu",
        use_doc_orientation_classify: bool = False,
        use_doc_unwarping: bool = False,
        use_textline_orientation: bool = False,
        use_table_recognition: bool = True,
        use_formula_recognition: bool = True,
        use_chart_recognition: bool = True,
        use_seal_recognition: bool = False,
        use_region_detection: bool = False,
        save_output: bool = False,
        output_dir: Optional[str] = None,
    ) -> Tuple[str, int, Optional[List[str]], Dict[str, Any]]:
        """
        Process a file and convert it to the requested format.
        
        Args:
            file_path: Path to the file to process
            output_format: Output format ("json", "markdown", or "raw")
            language: Language code ("en", "ch", or "en&ch")
            device: Device to use ("cpu" or "gpu")
            use_doc_orientation_classify: Enable document orientation classification
            use_doc_unwarping: Enable document unwarping
            use_textline_orientation: Enable textline orientation
            use_table_recognition: Enable table recognition
            use_formula_recognition: Enable formula recognition
            use_chart_recognition: Enable chart recognition
            use_seal_recognition: Enable seal recognition
            use_region_detection: Enable region detection
            save_output: Whether to save output files
            output_dir: Directory to save output files (if save_output=True)
            
        Returns:
            Tuple of (content, pages, saved_files, metadata)
        """
        start_time = time.time()
        
        # Initialize pipeline
        pipeline = self._get_pipeline(
            language=language,
            device=device,
            use_doc_orientation_classify=use_doc_orientation_classify,
            use_doc_unwarping=use_doc_unwarping,
            use_textline_orientation=use_textline_orientation,
            use_table_recognition=use_table_recognition,
            use_formula_recognition=use_formula_recognition,
            use_chart_recognition=use_chart_recognition,
            use_seal_recognition=use_seal_recognition,
            use_region_detection=use_region_detection,
        )
        
        # Process file
        results = pipeline.predict(input=file_path)
        num_pages = len(results)
        
        # Collect markdown images for saving
        markdown_images_list = []
        
        # Convert to requested format
        if output_format == "json":
            # Extract JSON for each page
            json_results = []
            for result in results:
                json_data = result.json
                json_results.append(json_data)
            content = json.dumps(json_results, indent=2, ensure_ascii=False, default=str)
            
        elif output_format == "markdown":
            # Extract markdown for each page
            markdown_list = []
            for result in results:
                md_info = result.markdown
                markdown_list.append(md_info)
                # Collect images
                markdown_images_list.append(md_info.get("markdown_images", {}))
            
            # Concatenate markdown pages
            content = pipeline.concatenate_markdown_pages(markdown_list)
            
        else:  # raw
            # Extract raw text from JSON
            text_parts = []
            for result in results:
                json_data = result.json
                text = extract_raw_text_from_json(json_data)
                if text:
                    text_parts.append(text)
            content = "\n\n".join(text_parts)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare metadata
        file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
        metadata = {
            "processing_time_seconds": round(processing_time, 2),
            "file_size_bytes": file_size,
            "language": language,
            "device": device,
        }
        
        # Save output files if requested
        saved_files = None
        if save_output:
            if output_dir is None:
                output_dir = Config.DEFAULT_OUTPUT_DIR
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            filename_base = Path(file_path).stem
            saved_files = save_output_files(
                content=content,
                output_format=output_format,
                output_dir=output_path,
                filename_base=filename_base,
                markdown_images=markdown_images_list if markdown_images_list else None,
            )
        
        return content, num_pages, saved_files, metadata
    
    def process_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        output_format: str = "markdown",
        language: str = "en",
        device: str = "cpu",
        use_doc_orientation_classify: bool = False,
        use_doc_unwarping: bool = False,
        use_textline_orientation: bool = False,
        use_table_recognition: bool = True,
        use_formula_recognition: bool = True,
        use_chart_recognition: bool = True,
        use_seal_recognition: bool = False,
        use_region_detection: bool = False,
        save_output: bool = False,
        output_dir: Optional[str] = None,
    ) -> Tuple[str, int, Optional[List[str]], Dict[str, Any]]:
        """
        Process an uploaded file and convert it to the requested format.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            output_format: Output format ("json", "markdown", or "raw")
            language: Language code ("en", "ch", or "en&ch")
            device: Device to use ("cpu" or "gpu")
            use_doc_orientation_classify: Enable document orientation classification
            use_doc_unwarping: Enable document unwarping
            use_textline_orientation: Enable textline orientation
            use_table_recognition: Enable table recognition
            use_formula_recognition: Enable formula recognition
            use_chart_recognition: Enable chart recognition
            use_seal_recognition: Enable seal recognition
            use_region_detection: Enable region detection
            save_output: Whether to save output files
            output_dir: Directory to save output files (if save_output=True)
            
        Returns:
            Tuple of (content, pages, saved_files, metadata)
        """
        # Save uploaded file to temporary location
        file_ext = Path(filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        try:
            # Process the temporary file
            return self.process_file(
                file_path=tmp_path,
                output_format=output_format,
                language=language,
                device=device,
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
        finally:
            # Clean up temporary file
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass


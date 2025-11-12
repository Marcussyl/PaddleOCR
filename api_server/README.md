# PP-StructureV3 OCR API Server

A FastAPI-based REST API for converting PDF/image files to formatted text using PaddleOCR's PP-StructureV3 pipeline.

## Features

- **Multiple Output Formats**: Support for JSON, Markdown, and raw text output
- **Language Support**: English (en), Chinese (ch), or both (en&ch)
- **Flexible Model Options**: Enable/disable specific processing modules:
  - Document orientation classification
  - Document unwarping/correction
  - Textline orientation
  - Table recognition
  - Formula recognition
  - Chart recognition
  - Seal recognition
  - Region detection
- **Optional File Saving**: Save output files to disk
- **Multi-page PDF Support**: Automatically handles multi-page PDF documents

## Installation

### Prerequisites

- Python 3.8 or higher
- PaddleOCR with doc-parser support

### Install Dependencies

```bash
pip install -r api_server/requirements.txt
```

Or if you already have PaddleOCR installed:

```bash
pip install fastapi uvicorn[standard] python-multipart pydantic
```

## Running the Server

### Basic Usage

```bash
# From the project root directory
cd api_server
python main.py
```

Or using uvicorn directly:

```bash
uvicorn api_server.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Endpoints

### Health Check

```http
GET /api/v1/health
```

Returns server health status.

### Convert File

```http
POST /api/v1/ocr/convert
```

Converts a PDF or image file to formatted text.

#### Request Parameters

**File Upload** (multipart/form-data):
- `file` (required): PDF or image file (PDF, PNG, JPG, JPEG)

**Query Parameters**:
- `output_format` (optional): Output format - `json`, `markdown`, or `raw` (default: `markdown`)
- `language` (optional): Language - `en`, `ch`, or `en&ch` (default: `en`)
- `device` (optional): Device - `cpu` or `gpu` (default: `cpu`)
- `save_output` (optional): Whether to save output files to disk - `true` or `false` (default: `false`)
- `output_dir` (optional): Directory to save files (if `save_output=true`)

**Model Options** (all optional, default: `false`):
- `use_doc_orientation_classify`: Enable document orientation classification
- `use_doc_unwarping`: Enable document unwarping/correction
- `use_textline_orientation`: Enable textline orientation classification
- `use_table_recognition`: Enable table recognition (default: `true`)
- `use_formula_recognition`: Enable formula recognition (default: `true`)
- `use_chart_recognition`: Enable chart recognition (default: `true`)
- `use_seal_recognition`: Enable seal recognition
- `use_region_detection`: Enable region detection

#### Response

```json
{
  "status": "success",
  "output_format": "markdown",
  "content": "# Document Title\n\nDocument content...",
  "pages": 1,
  "saved_files": null,
  "metadata": {
    "processing_time_seconds": 2.5,
    "file_size_bytes": 1024000,
    "language": "en",
    "device": "cpu"
  }
}
```

## Usage Examples

### Using cURL

```bash
# Basic conversion to markdown
curl -X POST "http://localhost:8000/api/v1/ocr/convert" \
  -F "file=@document.pdf" \
  -F "output_format=markdown" \
  -F "language=en"

# Convert to JSON with table recognition
curl -X POST "http://localhost:8000/api/v1/ocr/convert" \
  -F "file=@document.pdf" \
  -F "output_format=json" \
  -F "language=en&ch" \
  -F "use_table_recognition=true"

# Convert and save output files
curl -X POST "http://localhost:8000/api/v1/ocr/convert" \
  -F "file=@document.pdf" \
  -F "output_format=markdown" \
  -F "save_output=true" \
  -F "output_dir=./output"
```

### Using Python

```python
import requests

# Basic conversion
url = "http://localhost:8000/api/v1/ocr/convert"
files = {"file": open("document.pdf", "rb")}
params = {
    "output_format": "markdown",
    "language": "en",
    "use_table_recognition": True
}

response = requests.post(url, files=files, params=params)
result = response.json()

print(f"Status: {result['status']}")
print(f"Pages: {result['pages']}")
print(f"Content:\n{result['content']}")
```

### Using JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('document.pdf'));
form.append('output_format', 'markdown');
form.append('language', 'en');

axios.post('http://localhost:8000/api/v1/ocr/convert', form, {
  headers: form.getHeaders()
})
.then(response => {
  console.log('Status:', response.data.status);
  console.log('Pages:', response.data.pages);
  console.log('Content:', response.data.content);
})
.catch(error => {
  console.error('Error:', error);
});
```

## Configuration

The API server can be configured using environment variables:

- `API_HOST`: Server host (default: `0.0.0.0`)
- `API_PORT`: Server port (default: `8000`)
- `DEFAULT_DEVICE`: Default device (default: `cpu`)
- `DEFAULT_LANGUAGE`: Default language (default: `en`)
- `DEFAULT_OUTPUT_FORMAT`: Default output format (default: `markdown`)
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: `100`)
- `DEFAULT_OUTPUT_DIR`: Default output directory (default: `./api_output`)

## Output Formats

### JSON Format
Returns structured JSON data with detailed information about:
- Layout regions
- Text blocks with coordinates
- Tables (as HTML)
- Formulas (as LaTeX)
- Charts and images

### Markdown Format
Returns formatted Markdown text that preserves:
- Document structure (headings, paragraphs)
- Tables (as Markdown tables)
- Formulas (as LaTeX)
- Image references

### Raw Text Format
Returns plain text with:
- All formatting removed
- Basic structure preserved (paragraphs, line breaks)
- Tables converted to text
- Formulas as plain text

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid file, invalid parameters)
- `500`: Internal server error

Error responses follow this format:

```json
{
  "status": "error",
  "error": "Error message",
  "detail": "Detailed error information"
}
```

## Limitations

- Maximum file size: 100MB (configurable)
- Supported file types: PDF, PNG, JPG, JPEG
- Processing is synchronous (large files may take time)
- GPU support requires CUDA-enabled PaddlePaddle installation

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure PaddleOCR is installed with doc-parser support:
   ```bash
   pip install paddleocr[doc-parser]
   ```

2. **Out of memory**: Reduce file size or use CPU instead of GPU

3. **Slow processing**: Consider using GPU for faster processing, or disable optional features

4. **File not found errors**: Check that the output directory exists and is writable

## License

This API server is part of the PaddleOCR project and follows the same license.

## Support

For issues and questions:
- PaddleOCR GitHub: https://github.com/PaddlePaddle/PaddleOCR
- API Documentation: Available at `/docs` endpoint when server is running


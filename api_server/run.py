#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Startup script for PP-StructureV3 OCR API Server.

Run from project root:
    python -m api_server.run
"""
import uvicorn
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_server.config import Config

if __name__ == "__main__":
    uvicorn.run(
        "api_server.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
        log_level="info"
    )


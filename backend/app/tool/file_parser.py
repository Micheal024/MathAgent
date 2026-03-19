"""File parser utilities for uploaded documents.

Supports: PDF (.pdf), images (.png/.jpg/.jpeg), text (.txt/.md/.tex/.csv)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

from loguru import logger


# Supported extensions grouped by type
SUPPORTED_TYPES = {
    "pdf": [".pdf"],
    "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"],
    "text": [".txt", ".md", ".tex", ".csv", ".json", ".py", ".r", ".m"],
}

# Flat set of all allowed extensions
ALLOWED_EXTENSIONS = set()
for exts in SUPPORTED_TYPES.values():
    ALLOWED_EXTENSIONS.update(exts)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def get_file_category(filename: str) -> str | None:
    """Return 'pdf', 'image', or 'text' based on extension, or None if unsupported."""
    ext = Path(filename).suffix.lower()
    for category, extensions in SUPPORTED_TYPES.items():
        if ext in extensions:
            return category
    return None


def parse_pdf(file_path: str) -> Dict[str, Any]:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed, attempting fallback text extraction")
        return {
            "success": False,
            "error": "PyMuPDF is not installed. Run: pip install PyMuPDF",
            "content": "",
            "pages": 0,
        }

    try:
        doc = fitz.open(file_path)
        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages.append(text)

        full_text = "\n\n---\n\n".join(pages)
        num_pages = len(doc)
        doc.close()

        logger.info(f"PDF parsed: {num_pages} pages, {len(full_text)} chars")
        return {
            "success": True,
            "content": full_text,
            "pages": num_pages,
            "chars": len(full_text),
        }
    except Exception as e:
        logger.error(f"PDF parse error: {e}")
        return {
            "success": False,
            "error": str(e),
            "content": "",
            "pages": 0,
        }


def parse_image(file_path: str) -> Dict[str, Any]:
    """Return image metadata. Actual image analysis requires Vision LLM."""
    try:
        from PIL import Image

        img = Image.open(file_path)
        width, height = img.size
        fmt = img.format or Path(file_path).suffix.lstrip(".")
        img.close()

        return {
            "success": True,
            "content": f"[Image uploaded: {Path(file_path).name}, {width}×{height} px, format: {fmt}]",
            "width": width,
            "height": height,
            "format": fmt,
            "note": "Image content requires Vision LLM for analysis. The image has been saved to the workspace.",
        }
    except Exception as e:
        logger.error(f"Image parse error: {e}")
        return {
            "success": False,
            "error": str(e),
            "content": f"[Image uploaded: {Path(file_path).name}]",
        }


def parse_text(file_path: str) -> Dict[str, Any]:
    """Read text file contents directly."""
    try:
        # Try UTF-8 first, fall back to latin-1
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        return {
            "success": True,
            "content": content,
            "chars": len(content),
            "lines": content.count("\n") + 1,
        }
    except Exception as e:
        logger.error(f"Text parse error: {e}")
        return {
            "success": False,
            "error": str(e),
            "content": "",
        }


def parse_file(file_path: str) -> Dict[str, Any]:
    """Unified file parser — dispatches to the correct parser based on extension.

    Returns a dict with at least: success, content, file_type
    """
    path = Path(file_path)
    category = get_file_category(path.name)

    if category is None:
        return {
            "success": False,
            "error": f"Unsupported file type: {path.suffix}",
            "content": "",
            "file_type": "unknown",
        }

    result: Dict[str, Any]
    if category == "pdf":
        result = parse_pdf(file_path)
    elif category == "image":
        result = parse_image(file_path)
    else:
        result = parse_text(file_path)

    result["file_type"] = category
    result["filename"] = path.name
    result["size"] = os.path.getsize(file_path)
    return result

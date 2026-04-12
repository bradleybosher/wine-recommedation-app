"""Wine list parsing: PDF, images, and text."""

import base64
import io
import logging
from typing import Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageFilter

from inventory import decode_cellartracker_upload

logger = logging.getLogger("sommelier.parser")


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page in doc:
            text = page.get_text()
            if text:
                text_parts.append(text.strip())

        doc.close()

        if not text_parts:
            return "No text could be extracted from the PDF."

        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return f"Error extracting text from PDF: {str(e)}"


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using pytesseract + Pillow.

    Pre-processes image (RGB → greyscale → sharpen) before OCR.
    Returns extracted text or error message.
    """
    try:
        # Load image from bytes
        image = Image.open(io.BytesIO(image_bytes))

        # Pre-process: RGB → greyscale → sharpen
        image = image.convert("RGB").convert("L")
        image = image.filter(ImageFilter.SHARPEN)

        # Extract text
        text = pytesseract.image_to_string(image)

        # Check if OCR returned usable text
        non_whitespace_count = len(text.split())
        if non_whitespace_count < 20:
            logger.warning("OCR returned insufficient text (fewer than 20 words)")
            return "OCR returned no usable text. Try a clearer photo or upload a PDF."

        return text
    except EnvironmentError as e:
        logger.warning(f"Tesseract not installed: {e}")
        return "OCR unavailable: Tesseract not installed. Upload a PDF instead."
    except Exception as e:
        logger.warning(f"Image parsing failed: {e}")
        return f"Image parsing failed: {str(e)}"


def parse_wine_list(file_bytes: bytes, content_type: Optional[str], filename: Optional[str]) -> str:
    """
    Dispatch wine list parsing based on file type.

    Returns extracted wine list text or error message.
    Image uploads (jpg, png) are not yet implemented; returns a warning.
    """
    media_type = (content_type or "").lower()
    fname = (filename or "").lower()

    is_text_upload = media_type.startswith("text/") or fname.endswith(".txt")
    is_pdf_upload = media_type == "application/pdf" or fname.endswith(".pdf")
    is_image_upload = media_type.startswith("image/") or any(fname.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"])

    if is_pdf_upload:
        return extract_text_from_pdf(file_bytes)
    elif is_text_upload:
        return decode_cellartracker_upload(file_bytes)
    elif is_image_upload:
        return extract_text_from_image(file_bytes)
    else:
        # Attempt as text; if it fails, return a warning
        try:
            return decode_cellartracker_upload(file_bytes)
        except Exception as e:
            logger.error(f"Failed to parse unknown file type (filename={filename}): {e}")
            return f"[Could not parse file '{filename}'. Please upload a PDF or text wine list.]"

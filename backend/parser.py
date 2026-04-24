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


<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
class OCRError(ValueError):
    """Raised when OCR fails to extract usable text from an image."""


<<<<<<< HEAD
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using pytesseract + Pillow.

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
    Pre-processes image (scale to ≥2000px wide → greyscale → contrast → threshold → sharpen)
    before OCR to improve accuracy on restaurant menu photos.

    Returns extracted text.
    Raises OCRError if Tesseract is unavailable or returns insufficient text.
<<<<<<< HEAD
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        # Scale up small images — Tesseract accuracy degrades below ~150dpi equivalent.
        # Target a minimum width of 2000px while preserving aspect ratio.
        min_width = 2000
        if image.width < min_width:
            scale = min_width / image.width
            new_size = (min_width, int(image.height * scale))
            image = image.resize(new_size, Image.LANCZOS)
            logger.debug("OCR: upscaled image to %dx%d", *new_size)

        # RGB → greyscale → stretch contrast → binarise → sharpen
        image = image.convert("RGB").convert("L")

        # Autocontrast stretches the histogram to use the full 0-255 range
        from PIL import ImageOps
        image = ImageOps.autocontrast(image, cutoff=2)

        # Binarise with a fixed threshold (menu text on white/cream paper)
        image = image.point(lambda px: 255 if px > 160 else 0)

        image = image.filter(ImageFilter.SHARPEN)

        # PSM 4: assume a single column of text of variable sizes (good for menus)
        text = pytesseract.image_to_string(image, config="--psm 4")

        word_count = len(text.split())
        logger.info("OCR: extracted %d words", word_count)

        if word_count < 20:
            raise OCRError(
                f"OCR extracted only {word_count} words — image may be too blurry or low-contrast. "
                "Try a clearer photo or upload a PDF."
            )

        return text
    except OCRError:
        raise
    except EnvironmentError as e:
        logger.warning("Tesseract not installed: %s", e)
        raise OCRError("OCR unavailable: Tesseract is not installed. Upload a PDF instead.") from e
    except Exception as e:
        logger.warning("Image parsing failed: %s", e)
        raise OCRError(f"Image parsing failed: {e}") from e
=======
    Pre-processes image (RGB → greyscale → sharpen) before OCR.
    Returns extracted text or error message.
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        # Scale up small images — Tesseract accuracy degrades below ~150dpi equivalent.
        # Target a minimum width of 2000px while preserving aspect ratio.
        min_width = 2000
        if image.width < min_width:
            scale = min_width / image.width
            new_size = (min_width, int(image.height * scale))
            image = image.resize(new_size, Image.LANCZOS)
            logger.debug("OCR: upscaled image to %dx%d", *new_size)

        # RGB → greyscale → stretch contrast → binarise → sharpen
        image = image.convert("RGB").convert("L")

        # Autocontrast stretches the histogram to use the full 0-255 range
        from PIL import ImageOps
        image = ImageOps.autocontrast(image, cutoff=2)

        # Binarise with a fixed threshold (menu text on white/cream paper)
        image = image.point(lambda px: 255 if px > 160 else 0)

        image = image.filter(ImageFilter.SHARPEN)

        # PSM 4: assume a single column of text of variable sizes (good for menus)
        text = pytesseract.image_to_string(image, config="--psm 4")

        word_count = len(text.split())
        logger.info("OCR: extracted %d words", word_count)

        if word_count < 20:
            raise OCRError(
                f"OCR extracted only {word_count} words — image may be too blurry or low-contrast. "
                "Try a clearer photo or upload a PDF."
            )

        return text
    except OCRError:
        raise
    except EnvironmentError as e:
        logger.warning("Tesseract not installed: %s", e)
        raise OCRError("OCR unavailable: Tesseract is not installed. Upload a PDF instead.") from e
    except Exception as e:
<<<<<<< HEAD
        logger.warning(f"Image parsing failed: {e}")
        return f"Image parsing failed: {str(e)}"
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
        logger.warning("Image parsing failed: %s", e)
        raise OCRError(f"Image parsing failed: {e}") from e
>>>>>>> faa3422 (Commit despite broken recommendation engine)


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
<<<<<<< HEAD
<<<<<<< HEAD
        # OCRError propagates to the caller — do not catch here.
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
        # OCRError propagates to the caller — do not catch here.
>>>>>>> faa3422 (Commit despite broken recommendation engine)
        return extract_text_from_image(file_bytes)
    else:
        # Attempt as text; if it fails, return a warning
        try:
            return decode_cellartracker_upload(file_bytes)
        except Exception as e:
            logger.error(f"Failed to parse unknown file type (filename={filename}): {e}")
            return f"[Could not parse file '{filename}'. Please upload a PDF or text wine list.]"

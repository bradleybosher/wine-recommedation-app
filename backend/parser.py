"""Wine list parsing: PDF, images, and text."""

import base64
import io
import logging
import os
from typing import Optional

import fitz  # PyMuPDF
from anthropic import Anthropic
from PIL import Image
from pydantic import BaseModel

from inventory import decode_cellartracker_upload

logger = logging.getLogger("sommelier.parser")


class WineListEntry(BaseModel):
    producer: str | None = None
    wine_name: str
    vintage: int | None = None
    region: str | None = None
    varietal: str | None = None
    price: float | None = None
    bottle_size: str | None = None
    raw_text: str


class WineListExtraction(BaseModel):
    wines: list[WineListEntry]
    confidence_notes: str


OCR_SYSTEM_PROMPT = """You are extracting the WINE LIST from a restaurant menu image.

The menu may contain food items, cocktails, spirits, beer, and non-alcoholic drinks.
Extract ONLY wines. Ignore everything else.

A "wine" is a fermented grape beverage. This includes:
- Still wines (red, white, rosé)
- Sparkling wines (Champagne, Cava, Prosecco, Crémant, sparkling rosé)
- Fortified wines (Port, Sherry, Madeira, Marsala)
- Dessert wines (Sauternes, Tokaji, late harvest, ice wine)

Do NOT extract:
- Food items (even when they contain wine in the description, e.g. "Coq au Vin")
- Cocktails (even wine-based ones like Bellini or Kir Royale)
- Spirits, liqueurs, beer, cider
- Non-alcoholic beverages
- Section headers or narrative text about the wine program

For each wine, return:
{
  "producer": string or null,
  "wine_name": string,
  "vintage": integer or null (NV or non-vintage → null),
  "region": string or null,
  "varietal": string or null,
  "price": number or null,
  "bottle_size": "750ml" | "375ml" | "1.5L" | "glass" | null,
  "raw_text": "exact text from the menu"
}

Rules:
- If uncertain whether an entry is wine or something else, INCLUDE IT and add a note to confidence_notes.
- Preserve non-ASCII characters exactly (Château, Côtes, Rhône).
- If the same wine appears in multiple sizes (bottle + half-bottle), extract each as a separate entry."""

_RECORD_WINE_LIST_TOOL = {
    "name": "record_wine_list",
    "description": "Record the wines extracted from the menu image",
    "input_schema": {
        "type": "object",
        "properties": {
            "wines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "producer": {"type": ["string", "null"]},
                        "wine_name": {"type": "string"},
                        "vintage": {"type": ["integer", "null"]},
                        "region": {"type": ["string", "null"]},
                        "varietal": {"type": ["string", "null"]},
                        "price": {"type": ["number", "null"]},
                        "bottle_size": {"type": ["string", "null"]},
                        "raw_text": {"type": "string"},
                    },
                    "required": ["wine_name", "raw_text"],
                },
            },
            "confidence_notes": {"type": "string"},
        },
        "required": ["wines", "confidence_notes"],
    },
}

_FOOD_KEYWORDS = {
    "appetizer", "entrée", "entree", "starter", "salad", "soup", "pasta",
    "steak", "chicken", "fish", "dessert", "cocktail", "beer", "spirit",
    "whisky", "whiskey", "gin", "vodka", "rum", "tequila", "cider",
    "non-alcoholic", "mocktail", "juice", "coffee", "tea",
}

_WINE_TRIAGE_KEYWORDS = {
    "wine", "red", "white", "rosé", "rose", "sparkling", "champagne",
    "cabernet", "merlot", "pinot", "syrah", "grenache", "chardonnay",
    "sauvignon", "riesling", "prosecco", "cava", "crémant", "cremant",
    "port", "sherry", "madeira", "sauternes", "tokaji", "vintage",
    "producer", "varietal", "appellation", "domaine", "château", "chateau",
}


class OCRError(ValueError):
    """Raised when Haiku vision extraction fails (API error, network, etc.)."""


def prepare_image(image_bytes: bytes, max_dim: int = 2000) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((max_dim, max_dim))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _format_extraction(extraction: WineListExtraction) -> str:
    lines = []
    for w in extraction.wines:
        parts = [p for p in [w.producer, w.wine_name] if p]
        name = " ".join(parts)
        if w.vintage:
            name += f" {w.vintage}"
        meta_str = " | ".join(m for m in [w.region, w.varietal] if m)
        price_str = f"${w.price:.0f}" if w.price else ""
        lines.append(" — ".join(p for p in [name, meta_str, price_str] if p))
    return "\n".join(lines)


def _call_haiku_vision(image_bytes: bytes) -> WineListExtraction:
    """Send prepared JPEG bytes to Haiku and return structured extraction."""
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    image_data = base64.standard_b64encode(image_bytes).decode()

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8000,
        tools=[_RECORD_WINE_LIST_TOOL],
        tool_choice={"type": "tool", "name": "record_wine_list"},
        system=[{"type": "text", "text": OCR_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                {"type": "text", "text": "Extract all wines from this wine list."},
            ],
        }],
    )

    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    return WineListExtraction.model_validate(tool_use_block.input)


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract wine list text from an image using Claude Haiku vision.

    Resizes the image to ≤2000px before sending. Returns formatted text.
    Raises OCRError on API or extraction failure.
    """
    try:
        prepared = prepare_image(image_bytes)
        extraction = _call_haiku_vision(prepared)

        logger.info("Haiku OCR: extracted %d wines", len(extraction.wines))
        if extraction.confidence_notes:
            logger.info("Haiku OCR confidence notes: %s", extraction.confidence_notes)

        return _format_extraction(extraction)
    except OCRError:
        raise
    except Exception as e:
        logger.warning("Haiku vision extraction failed: %s", e)
        raise OCRError(f"Vision extraction failed: {e}") from e


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
            return ""

        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return f"Error extracting text from PDF: {str(e)}"


<<<<<<< HEAD
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
=======
def should_use_vision_extraction(pdf_bytes: bytes) -> bool:
    """Return True if a PDF should be routed through Haiku vision rather than text extraction."""
    text = extract_text_from_pdf(pdf_bytes)

    # Signal 1: combined menu with food/non-wine content
    food_hits = sum(1 for kw in _FOOD_KEYWORDS if kw in text.lower())
    if food_hits >= 3:
        logger.debug("PDF routing → vision: %d food keywords found", food_hits)
        return True

    # Signal 2: column-collapsed text (unusually long lines = PyMuPDF merged columns)
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        logger.debug("PDF routing → vision: empty text extraction")
        return True
    avg_line_len = sum(len(l) for l in lines) / len(lines)
    if avg_line_len > 120:
        logger.debug("PDF routing → vision: avg line length %.0f > 120", avg_line_len)
        return True

    # Signal 3: scanned PDF with no real text layer
    if len(text.strip()) < 100:
        logger.debug("PDF routing → vision: text too short (%d chars)", len(text.strip()))
        return True

    return False


def _extract_pdf_via_vision(pdf_bytes: bytes) -> str:
    """Render each PDF page as JPEG and extract wines via Haiku vision.

    Pages with ≥150 chars of extractable text containing wine keywords skip
    the Haiku call and contribute their raw text directly, reducing API costs.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_wines: list[WineListEntry] = []
    all_notes: list[str] = []
    seen_raw: set[str] = set()
    raw_text_pages: list[str] = []

    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text().strip()
        text_has_wine = any(kw in page_text.lower() for kw in _WINE_TRIAGE_KEYWORDS)
        if len(page_text) >= 150 and text_has_wine:
            logger.info("PDF page %d: text triage SKIP_VISION (%d chars)", page_num, len(page_text))
            raw_text_pages.append(page_text)
            continue

        logger.info("PDF page %d: text triage CALL_VISION (%d chars, has_wine_kw=%s)", page_num, len(page_text), text_has_wine)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        jpeg_bytes = pixmap.tobytes("jpeg")
        try:
            prepared = prepare_image(jpeg_bytes)
            extraction = _call_haiku_vision(prepared)
            logger.info("PDF page %d: extracted %d wines", page_num, len(extraction.wines))
            if extraction.confidence_notes:
                all_notes.append(f"Page {page_num}: {extraction.confidence_notes}")
            for wine in extraction.wines:
                if wine.raw_text not in seen_raw:
                    seen_raw.add(wine.raw_text)
                    all_wines.append(wine)
        except Exception as e:
            logger.warning("PDF page %d vision failed: %s", page_num, e)

    doc.close()
>>>>>>> 0d27b4b (Replaced OCR with Haiku vision match, routed messy PDFs to Haiku)

    if all_notes:
        logger.info("PDF vision confidence notes: %s", "; ".join(all_notes))

<<<<<<< HEAD
<<<<<<< HEAD
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
=======
    merged = WineListExtraction(wines=all_wines, confidence_notes="; ".join(all_notes))
    return _format_extraction(merged)
>>>>>>> 0d27b4b (Replaced OCR with Haiku vision match, routed messy PDFs to Haiku)
=======
    parts: list[str] = []
    if all_wines:
        merged = WineListExtraction(wines=all_wines, confidence_notes="; ".join(all_notes))
        parts.append(_format_extraction(merged))
    if raw_text_pages:
        parts.append("\n".join(raw_text_pages))
    return "\n".join(parts)
>>>>>>> 97b0c05 (Cost improvement of haiku usage)


def parse_wine_list(file_bytes: bytes, content_type: Optional[str], filename: Optional[str]) -> str:
    """Dispatch wine list parsing based on file type.

    Returns extracted wine list text or error message.
    """
    media_type = (content_type or "").lower()
    fname = (filename or "").lower()

    is_text_upload = media_type.startswith("text/") or fname.endswith(".txt")
    is_pdf_upload = media_type == "application/pdf" or fname.endswith(".pdf")
    is_image_upload = media_type.startswith("image/") or any(fname.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"])

    if is_pdf_upload:
        if should_use_vision_extraction(file_bytes):
            return _extract_pdf_via_vision(file_bytes)
        return extract_text_from_pdf(file_bytes)
    elif is_text_upload:
        return decode_cellartracker_upload(file_bytes)
    elif is_image_upload:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        # OCRError propagates to the caller — do not catch here.
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
        # OCRError propagates to the caller — do not catch here.
>>>>>>> faa3422 (Commit despite broken recommendation engine)
=======
>>>>>>> 0d27b4b (Replaced OCR with Haiku vision match, routed messy PDFs to Haiku)
        return extract_text_from_image(file_bytes)
    else:
        try:
            return decode_cellartracker_upload(file_bytes)
        except Exception as e:
            logger.error(f"Failed to parse unknown file type (filename={filename}): {e}")
            return f"[Could not parse file '{filename}'. Please upload a PDF or text wine list.]"

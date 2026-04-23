# parser.py

## Responsibility

Dispatch wine list parsing based on file type. Extract wine lists from PDFs (text or scanned), images, and plain-text uploads. Images and qualifying PDFs are routed through Claude Haiku vision for structured extraction and automatic wine/non-wine filtering.

## Dependencies

- `fitz` (PyMuPDF, PDF text extraction and page rendering)
- `anthropic` (Haiku vision API for image OCR)
- `PIL` (Pillow, image resize/JPEG conversion before vision call)
- `pydantic` (WineListEntry, WineListExtraction models)
- `inventory.decode_cellartracker_upload()` (encoding handling for text uploads)

## Inputs/Outputs

**Inputs**:
- `file_bytes`: Raw file content
- `content_type`: MIME type (e.g., "application/pdf", "text/plain", "image/jpeg")
- `filename`: Original filename (fallback type detection)

**Outputs**: Text string (formatted wine list or error message).

## Key Functions

**parse_wine_list(file_bytes, content_type, filename)** → str:
- Detect type: is_pdf_upload, is_text_upload, is_image_upload
- PDF: call `should_use_vision_extraction()` first; if True → `_extract_pdf_via_vision()`, else → `extract_text_from_pdf()`
- Image: `extract_text_from_image()`
- Text: `decode_cellartracker_upload()`
- Fallback: unknown type → attempt text decode, return error if fails

**extract_text_from_image(image_bytes)** → str:
- Resize to ≤2000px JPEG via `prepare_image()`
- Call Claude Haiku with `record_wine_list` tool (forced tool use)
- Validate response into `WineListExtraction`, format via `_format_extraction()`
- Raises `OCRError` only on API/network failure

**extract_text_from_pdf(pdf_bytes)** → str:
- PyMuPDF page-by-page text extraction
- Returns `""` (not error message) when no text found, so `should_use_vision_extraction()` can detect scanned PDFs

**should_use_vision_extraction(pdf_bytes)** → bool:
- Calls `extract_text_from_pdf()` then evaluates 3 signals:
  1. ≥3 food keywords found → combined menu, needs filtering
  2. avg line length > 120 → column-collapsed text
  3. total text < 100 chars → scanned/image PDF
- Returns True if Haiku vision should be used instead of raw text

**_extract_pdf_via_vision(pdf_bytes)** → str:
- Renders each page as JPEG via `page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("jpeg")`
- Calls `_call_haiku_vision()` per page
- Merges all `WineListEntry` lists, deduplicates by `raw_text`
- Returns formatted text

**prepare_image(image_bytes, max_dim=2000)** → bytes:
- PIL `thumbnail()` to ≤2000px, convert to RGB JPEG at quality 85

**_format_extraction(extraction)** → str:
- Converts `WineListExtraction` to one line per wine: `Producer WineName Vintage — Region | Varietal — $Price`

## Data Models

**WineListEntry**: producer (str|None), wine_name (str), vintage (int|None), region (str|None), varietal (str|None), price (float|None), bottle_size (str|None), raw_text (str)

**WineListExtraction**: wines (list[WineListEntry]), confidence_notes (str)

## Constants

- `OCR_SYSTEM_PROMPT`: Instructs Haiku to extract only wines, ignore food/cocktails/spirits; rules for null fields, NV vintages, multi-size entries
- `_RECORD_WINE_LIST_TOOL`: JSON schema for the `record_wine_list` tool passed to Haiku
- `_FOOD_KEYWORDS`: Set of ~30 terms used to detect combined menus in PDFs

## Patterns & Gotchas

- **Type detection**: MIME type first, then filename extension.
- **Vision filtering**: Haiku's system prompt explicitly excludes food, cocktails, spirits — structured extraction is also a filter pass.
- **PDF routing**: `should_use_vision_extraction()` runs a cheap text extract first to decide whether vision is needed. The extra PyMuPDF call is negligible vs. avoiding an unnecessary Haiku API call.
- **OCRError**: Only raised on Haiku API/network failure. No longer raised for low word count (Haiku is reliable enough that an empty extraction is a valid result for a blank image).
- **Confidence notes**: Logged at INFO level. Useful for debugging ambiguous menus.

## Testing

1. Upload a JPG wine list photo → verify Haiku extracts wines and returns formatted text.
2. Upload a text-only PDF → verify PyMuPDF path (no Haiku call).
3. Upload a full restaurant menu PDF (with food) → verify food keywords trigger Haiku vision + only wines returned.
4. Upload a scanned PDF → verify vision fallback renders pages and extracts wines.
5. Upload a text file → verify decoded correctly.
6. Check logs for "Haiku OCR: extracted N wines" and confidence notes.

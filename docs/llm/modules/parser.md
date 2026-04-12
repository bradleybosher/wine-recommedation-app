# parser.py

## Responsibility

Dispatch wine list parsing based on file type. Extract text from PDFs, text uploads, and images (via OCR).

## Dependencies

- `fitz` (PyMuPDF, PDF extraction)
- `pytesseract` (Tesseract OCR wrapper for image text extraction)
- `PIL` (Pillow, image pre-processing: RGB conversion, greyscale, sharpening)
- `inventory.decode_cellartracker_upload()` (encoding handling)
- `logging` (error reporting)

## Inputs/Outputs

**Inputs**: 
- `file_bytes`: Raw file content
- `content_type`: MIME type (e.g., "application/pdf", "text/plain", "image/jpeg")
- `filename`: Original filename (fallback type detection)

**Outputs**: Text string (wine list or error message).

## Key Functions

**extract_text_from_pdf(pdf_bytes)** → str:
  - Use PyMuPDF to open PDF
  - Iterate pages, extract text via `page.get_text()`
  - Return concatenated text or error message
  - Handles all PDF types (scanned, native, encrypted?)

**extract_text_from_image(image_bytes)** → str:
  - Load image from bytes via PIL
  - Pre-process: convert to RGB → greyscale → apply SHARPEN filter (improves OCR accuracy on phone photos)
  - Extract text via pytesseract
  - Validation: return error if OCR yields < 20 words
  - Error handling:
    - `EnvironmentError` (Tesseract missing): "OCR unavailable: Tesseract not installed. Upload a PDF instead."
    - Insufficient text: "OCR returned no usable text. Try a clearer photo or upload a PDF."
    - Other exceptions: return error message string
  - All errors logged at WARNING level

**parse_wine_list(file_bytes, content_type, filename)** → str:
  - Detect type: is_pdf_upload, is_text_upload, is_image_upload
  - Route: PDF → extract_text_from_pdf, text → decode_cellartracker_upload, image → extract_text_from_image
  - Fallback: unknown type → attempt text decode, return error if fails
  - Return text or error message

## Patterns & Gotchas

- **Type detection**: Check MIME type first, fallback to filename extension.
- **MIME types checked**: 
  - PDF: "application/pdf", ".pdf"
  - Text: "text/*", ".txt"
  - Image: "image/*", ".jpg/.jpeg/.png/.gif/.bmp"
- **Image pre-processing**: Greyscale + sharpening improves OCR accuracy on phone photos of wine lists.
- **OCR validation**: Returns error message if Tesseract produces < 20 words (prevents noisy/blank extractions from being passed to the recommendation engine).
- **Tesseract dependency**: pytesseract requires the Tesseract binary to be installed on the system. Missing Tesseract raises EnvironmentError, caught and returned as user-friendly error.
- **Fallback decode**: Unknown types attempted as text with encoding fallback (see inventory.decode_cellartracker_upload).
- **Error convention**: All extraction failures return error strings (not raised); logged at WARNING level.

## Known Issues / TODOs

- PDF extraction may fail on encrypted PDFs (no handling; returns error message).
- Image path is dual: OCR text is extracted here for inclusion in the text prompt; main.py also passes raw base64 to Ollama for vision-capable models. Vision path is not formally tested.
- Large PDF parsing may be slow (PyMuPDF is generally fast but no timeout).
- OCR accuracy depends on image quality and Tesseract configuration (no language packs or custom preprocessing flags set).

## Testing

1. Upload a PDF wine list → verify text extracted.
2. Upload a text file → verify decoded correctly.
3. Upload an image (clear photo or scan) → verify OCR extracts text.
4. Upload a blurry/low-quality image → verify returns "no usable text" error gracefully.
5. Test without Tesseract installed → verify returns "Tesseract not installed" error.
6. Upload an unknown file type → verify fallback behavior.

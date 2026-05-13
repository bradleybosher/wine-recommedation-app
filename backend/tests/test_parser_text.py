"""Tests for parser module: text extraction path only (no PDF/image binaries required)."""

import unittest

from parser import parse_wine_list


class ParserTextExtractionTests(unittest.TestCase):
    """Test the text extraction path of parse_wine_list."""

    def test_parse_plain_text_wine_list(self) -> None:
        """parse_wine_list with plain text should return non-empty string."""
        wine_list_bytes = b"Chateau Margaux 2015 Bordeaux\nPinot Noir Burgundy"
        content_type = "text/plain"
        filename = "wine_list.txt"

        result = parse_wine_list(wine_list_bytes, content_type, filename)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_parse_empty_text_file(self) -> None:
        """parse_wine_list with empty text file should return empty or minimal string."""
        wine_list_bytes = b""
        content_type = "text/plain"
        filename = "empty.txt"

        result = parse_wine_list(wine_list_bytes, content_type, filename)

        self.assertIsInstance(result, str)
        # Should not raise; result may be empty or contain minimal content

    def test_parse_text_file_with_wine_names(self) -> None:
        """parse_wine_list should extract text from wine list."""
        wine_list_bytes = b"Domaine de la Romanee-Conti 2010\nBarolo Cannubi 2012\nSauvignon Blanc Loire Valley"
        content_type = "text/plain"
        filename = "wines.txt"

        result = parse_wine_list(wine_list_bytes, content_type, filename)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_parse_text_mime_type_detection(self) -> None:
        """Text files with text/* MIME type should be handled correctly."""
        wine_list_bytes = b"Chablis\nCote de Nuits\nRhone Valley"
        content_type = "text/csv"  # Different text subtype
        filename = "list.csv"

        result = parse_wine_list(wine_list_bytes, content_type, filename)

        self.assertIsInstance(result, str)

    def test_parse_no_raise_on_non_pdf_non_image(self) -> None:
        """parse_wine_list should handle unknown file types without raising."""
        wine_list_bytes = b"Some wine data"
        content_type = "application/octet-stream"
        filename = "unknown_file"

        try:
            result = parse_wine_list(wine_list_bytes, content_type, filename)
            self.assertIsInstance(result, str)
        except Exception as e:
            self.fail(f"parse_wine_list raised {type(e).__name__} on unknown file type: {e}")

    def test_parse_utf8_content(self) -> None:
        """parse_wine_list should handle UTF-8 content (e.g., French accents)."""
        wine_list_bytes = "Château Margaux 2015\nCôtes du Rhône\nChâteauneuf-du-Pape".encode("utf-8")
        content_type = "text/plain"
        filename = "french_wines.txt"

        result = parse_wine_list(wine_list_bytes, content_type, filename)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_parse_txt_extension_no_content_type(self) -> None:
        """File with .txt extension should be handled even if content_type is None."""
        wine_list_bytes = b"Pinot Noir\nChardonnay"
        content_type = None
        filename = "wines.txt"

        result = parse_wine_list(wine_list_bytes, content_type, filename)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_parse_multiline_wine_list(self) -> None:
        """parse_wine_list should handle multi-line wine entries."""
        wine_list_bytes = b"""
Chateau Mouton Rothschild 2010
Bordeaux, France
$150

Domaine Leflaive Puligny-Montrachet 2015
Burgundy, France
$85

Barolo Gaja Barbaresco 2012
Piedmont, Italy
$120
""".strip()
        content_type = "text/plain"
        filename = "structured_list.txt"

        result = parse_wine_list(wine_list_bytes, content_type, filename)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()

"""Tests for backend.inventory wine-list term extraction and pre-folded keyword sets.

Covers the precomputed-fold optimization: the module-level folded keyword
constants must stay in sync with the source keyword list, and extraction must
still return the original (un-folded) canonical keyword, accent-insensitively.
"""

import inventory
from inventory import _fold_for_match, extract_terms_from_wine_list_text


def test_folded_constants_match_source_keywords():
    # Parallel folded list stays aligned with the canonical keyword list.
    assert inventory._FOLDED_WINE_STYLE_KEYWORDS == [
        _fold_for_match(kw) for kw in inventory._WINE_STYLE_KEYWORDS
    ]
    # Pairs carry the original keyword alongside its folded form.
    assert inventory._WINE_STYLE_KEYWORD_PAIRS == list(
        zip(inventory._WINE_STYLE_KEYWORDS, inventory._FOLDED_WINE_STYLE_KEYWORDS)
    )


def test_extract_returns_canonical_keyword():
    text = "2019 Domaine Leflaive Chablis\n2020 Penfolds Shiraz"
    found = extract_terms_from_wine_list_text(text)
    assert "chablis" in found
    assert "shiraz" in found


def test_extract_is_accent_insensitive():
    # Accented input must still match the canonical (accented or folded) keyword.
    found = extract_terms_from_wine_list_text("Cote-Rotie 2018, Saint-Emilion 2016")
    assert "côte-rôtie" in found
    assert "saint-émilion" in found


def test_extract_empty_text_returns_empty():
    assert extract_terms_from_wine_list_text("") == []

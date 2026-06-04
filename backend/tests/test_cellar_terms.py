"""Tests for backend.cellar_terms — frequency tokens + cellar character phrase."""

from cellar_terms import cellar_character_from_terms, inventory_terms_by_frequency


class TestInventoryTermsByFrequency:
    def test_empty_inventory_returns_empty_list(self):
        assert inventory_terms_by_frequency([]) == []

    def test_filters_stopwords(self):
        bottles = [
            {"Varietal": "Pinot Noir", "Appellation": "Burgundy"},
            {"Varietal": "Pinot Noir", "Appellation": "Burgundy"},
        ]
        terms = inventory_terms_by_frequency(bottles)
        # Stopwords like "and", "de", "du" must not appear
        assert "and" not in terms
        assert "de" not in terms
        # "noir" is a stopword in this module's lexicon
        assert "noir" not in terms

    def test_ranks_by_frequency(self):
        bottles = [
            {"Varietal": "Chardonnay", "Appellation": "Chablis"},
            {"Varietal": "Chardonnay", "Appellation": "Chablis"},
            {"Varietal": "Chardonnay", "Appellation": "Meursault"},
            {"Varietal": "Pinot Noir", "Appellation": "Burgundy"},
        ]
        terms = inventory_terms_by_frequency(bottles, limit=10)
        # chardonnay should rank above pinot (3 appearances vs 1)
        assert terms.index("chardonnay") < terms.index("pinot")

    def test_short_tokens_filtered(self):
        # tokens < 3 chars should not appear
        bottles = [{"Varietal": "AB Pinot Noir", "Appellation": ""}]
        terms = inventory_terms_by_frequency(bottles)
        assert "ab" not in terms

    def test_limit_caps_result(self):
        bottles = [{"Varietal": f"Varietal{i}", "Appellation": f"App{i}"} for i in range(50)]
        terms = inventory_terms_by_frequency(bottles, limit=5)
        assert len(terms) == 5


class TestCellarCharacterFromTerms:
    def test_empty_terms_returns_empty_string(self):
        assert cellar_character_from_terms([]) == ""

    def test_single_term(self):
        result = cellar_character_from_terms(["chardonnay"])
        assert result == "skews heavily toward Chardonnay."

    def test_two_terms(self):
        result = cellar_character_from_terms(["chardonnay", "pinot"])
        assert result == "skews heavily toward Chardonnay and Pinot."

    def test_three_terms(self):
        result = cellar_character_from_terms(["chardonnay", "pinot", "syrah"])
        assert result == "skews heavily toward Chardonnay, Pinot, and Syrah."

    def test_truncates_to_first_five(self):
        result = cellar_character_from_terms(["a", "b", "c", "d", "e", "f", "g"])
        # Only first 5 should be mentioned
        assert "F" not in result
        assert "G" not in result

    def test_hyphenated_term_capitalised_per_word(self):
        result = cellar_character_from_terms(["cote-rotie"])
        assert "Cote Rotie" in result

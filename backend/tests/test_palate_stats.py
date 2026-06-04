"""Tests for backend.palate_stats — statistical palate analysis (no LLM)."""

from palate_stats import (
    _extract_avoided_tokens,
    _note_sentiment,
    _parse_price,
    compute_palate_stats,
)


class TestNoteSentiment:
    def test_positive_keywords_classify_as_positive(self):
        assert _note_sentiment("Absolutely stunning, beautiful and elegant") == "positive"

    def test_negative_keywords_classify_as_negative(self):
        assert _note_sentiment("Flabby and disappointing, over-oaked") == "negative"

    def test_neutral_when_no_keywords(self):
        assert _note_sentiment("Drank this on Tuesday with chicken.") == "neutral"

    def test_neutral_when_balanced(self):
        # one positive ("great") + one negative ("disappointing")
        assert _note_sentiment("Was great at first but ultimately disappointing") == "neutral"


class TestParsePrice:
    def test_strips_currency_symbol(self):
        assert _parse_price("$42.50") == 42.50

    def test_handles_none(self):
        assert _parse_price(None) is None

    def test_handles_unparseable(self):
        assert _parse_price("free") is None

    def test_handles_numeric_input(self):
        assert _parse_price(15) == 15.0


class TestExtractAvoidedTokens:
    def test_distils_phrase_to_token(self):
        tokens = _extract_avoided_tokens(["Wines that are too oaky and over-ripe"])
        assert "oaky" in tokens
        assert "jammy" in tokens

    def test_empty_input_returns_empty_list(self):
        assert _extract_avoided_tokens([]) == []


class TestComputePalateStats:
    def test_empty_input_returns_empty_skeleton(self):
        stats = compute_palate_stats([])
        assert stats["note_count"] == 0
        assert stats["producer_frequency"] == {}
        assert stats["top_producers"] == []
        assert stats["aspirational_skew"] is None

    def test_frequency_tables_count_total_and_sentiment(self):
        rows = [
            {"Producer": "Domaine X", "Region": "Burgundy", "MasterVarietal": "Pinot Noir",
             "ConsumptionNote": "Stunning and elegant", "Price": "50"},
            {"Producer": "Domaine X", "Region": "Burgundy", "MasterVarietal": "Pinot Noir",
             "ConsumptionNote": "Loved this — exceptional", "Price": "55"},
            {"Producer": "Domaine X", "Region": "Burgundy", "MasterVarietal": "Pinot Noir",
             "ConsumptionNote": "Disappointing and flabby", "Price": "60"},
        ]
        stats = compute_palate_stats(rows)
        entry = stats["producer_frequency"]["Domaine X"]
        assert entry["total"] == 3
        assert entry["positive"] == 2
        assert entry["negative"] == 1
        assert entry["net"] == 1

    def test_top_producers_requires_minimum_two_appearances(self):
        rows = [
            {"Producer": "OneShot", "MasterVarietal": "X", "ConsumptionNote": "stunning"},
            {"Producer": "Repeat", "MasterVarietal": "X", "ConsumptionNote": "stunning"},
            {"Producer": "Repeat", "MasterVarietal": "X", "ConsumptionNote": "exceptional"},
        ]
        stats = compute_palate_stats(rows)
        assert "Repeat" in stats["top_producers"]
        assert "OneShot" not in stats["top_producers"]

    def test_avoided_style_tokens_from_negative_notes(self):
        rows = [
            {"Producer": "P", "ConsumptionNote": "Too oaky and disappointing"},
        ]
        stats = compute_palate_stats(rows)
        assert "oaky" in stats["avoided_style_tokens"]

    def test_style_signals_natural_wine(self):
        rows = [{"Producer": "P", "ConsumptionNote": "Beautiful pét nat from a low intervention producer"}]
        stats = compute_palate_stats(rows)
        assert stats["style_signals"]["natural_wine_affinity"] is True
        assert stats["style_signals"]["oxidative_affinity"] is False

    def test_aspirational_skew_flags_overweight_cellar_category(self):
        consumed = [
            {"Producer": "P", "MasterVarietal": "Chardonnay", "ConsumptionNote": "ok"},
            {"Producer": "P", "MasterVarietal": "Chardonnay", "ConsumptionNote": "ok"},
            {"Producer": "P", "MasterVarietal": "Chardonnay", "ConsumptionNote": "ok"},
            {"Producer": "P", "MasterVarietal": "Chardonnay", "ConsumptionNote": "ok"},
        ]
        inventory = [
            {"Varietal": "Nebbiolo", "Quantity": 10},
            {"Varietal": "Chardonnay", "Quantity": 1},
        ]
        stats = compute_palate_stats(consumed, inventory_rows=inventory)
        skew = stats["aspirational_skew"]
        assert skew is not None
        assert "Nebbiolo" in skew["over_represented"]
        assert skew["summary_line"]

    def test_aspirational_skew_none_when_no_inventory(self):
        stats = compute_palate_stats(
            [{"Producer": "P", "MasterVarietal": "X", "ConsumptionNote": "ok"}]
        )
        assert stats["aspirational_skew"] is None

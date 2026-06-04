"""Tests for backend.synonyms — grape/region synonym + sub-appellation expansion."""

from synonyms import expand_term, expand_terms


class TestExpandTerm:
    def test_grape_expansion_includes_original(self):
        result = expand_term("pinot noir")
        assert result[0] == "pinot noir"
        assert "spätburgunder" in result
        assert "pinot nero" in result

    def test_region_expansion_returns_sub_appellations(self):
        result = expand_term("burgundy")
        assert "burgundy" in result
        assert "gevrey" in result
        assert "puligny-montrachet" in result

    def test_alias_resolves_to_canonical_expansion(self):
        # "shiraz" is an alias of "syrah"; expanding it should yield the syrah cluster
        result = expand_term("shiraz")
        assert "syrah" in result
        assert "shiraz" in result

    def test_case_and_whitespace_insensitive(self):
        assert expand_term("  Pinot Noir  ") == expand_term("pinot noir")

    def test_unknown_term_passthrough(self):
        assert expand_term("zibibbo-XYZ") == ["zibibbo-xyz"]


class TestExpandTerms:
    def test_dedupes_and_preserves_first_seen_order(self):
        # Two terms that both expand to overlapping aliases — order must be first-seen
        result = expand_terms(["chardonnay", "burgundy"])
        # First-seen order: chardonnay's expansions appear before burgundy's
        assert result.index("chardonnay") < result.index("burgundy")
        # No duplicates
        assert len(result) == len(set(result))

    def test_empty_input_returns_empty(self):
        assert expand_terms([]) == []

    def test_unknown_terms_pass_through(self):
        result = expand_terms(["nope-grape", "fake-region"])
        assert result == ["nope-grape", "fake-region"]

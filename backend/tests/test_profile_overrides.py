"""Tests for backend.profile.build_taste_profile — precedence + overrides."""

from profile import apply_profile_overrides, build_taste_profile


class TestBuildTasteProfilePrecedence:
    def test_synthesized_wins_over_inferred_and_derived(self):
        data = {
            "_synthesized": {"top_varietals": ["Pinot Noir"], "profile_source": "cellartracker_synthesized"},
            "_inferred": {"top_varietals": ["Cabernet"]},
            "consumed": [{"Varietal": "Sangiovese", "Region": "Tuscany"}],
        }
        result = build_taste_profile(data)
        assert result["top_varietals"] == ["Pinot Noir"]

    def test_inferred_wins_when_no_synthesized(self):
        data = {
            "_inferred": {"top_varietals": ["Cabernet"]},
            "consumed": [{"Varietal": "Sangiovese", "Region": "Tuscany"}],
        }
        result = build_taste_profile(data)
        assert result["top_varietals"] == ["Cabernet"]

    def test_deterministic_derivation_when_no_synthesized_or_inferred(self):
        data = {
            "consumed": [
                {"Varietal": "Nebbiolo", "Region": "Piedmont", "Producer": "Domaine A", "Wine": "X", "Vintage": "2018"},
                {"Varietal": "Nebbiolo", "Region": "Piedmont", "Producer": "Domaine A", "Wine": "Y", "Vintage": "2019"},
            ],
        }
        result = build_taste_profile(data)
        # Derivation lowercases — verify Nebbiolo is in top_varietals (case-insensitive)
        assert any("nebbiolo" in v.lower() for v in result["top_varietals"])

    def test_overrides_layered_on_top_of_synthesized(self):
        data = {
            "_synthesized": {"top_varietals": ["Pinot Noir"], "avoided_styles": []},
            "_overrides": {"avoided_styles": ["over-oaked"]},
        }
        result = build_taste_profile(data)
        # Synthesized base preserved
        assert result["top_varietals"] == ["Pinot Noir"]
        # Override layered on top
        assert result["avoided_styles"] == ["over-oaked"]

    def test_overrides_layered_on_deterministic_base(self):
        data = {
            "consumed": [{"Varietal": "Nebbiolo", "Region": "Piedmont", "Producer": "A", "Wine": "X", "Vintage": "2018"}],
            "_overrides": {"avg_spend": 100},
        }
        result = build_taste_profile(data)
        assert result["avg_spend"] == 100

    def test_empty_synthesized_dict_falls_through(self):
        data = {
            "_synthesized": {},  # falsy → must fall through
            "_inferred": {"top_varietals": ["Cabernet"]},
        }
        result = build_taste_profile(data)
        assert result["top_varietals"] == ["Cabernet"]

    def test_non_dict_input_handled(self):
        assert isinstance(build_taste_profile(None), dict)
        assert isinstance(build_taste_profile("not a dict"), dict)


class TestApplyProfileOverrides:
    def test_overrides_replace_base_values(self):
        base = {"a": 1, "b": 2}
        result = apply_profile_overrides(base, {"a": 99})
        assert result["a"] == 99
        assert result["b"] == 2

    def test_empty_overrides_returns_base_copy(self):
        base = {"a": 1}
        result = apply_profile_overrides(base, {})
        assert result == base

"""Tests for backend.recommender pure helpers: _find_reference_bars + _blend_bars.

Skips the LLM `get_recommendation()` entry point — that's covered by the
llm_evals harness.
"""

import recommender
from recommender import _blend_bars, _find_reference_bars


class TestFindReferenceBars:
    def test_returns_none_when_no_reference_data(self, monkeypatch):
        monkeypatch.setattr(recommender, "_WINE_REFERENCE", [])
        assert _find_reference_bars("Burgundy", "Pinot Noir") is None

    def test_exact_match_on_appellation_and_grape(self, monkeypatch):
        ref = [{
            "appellation": "Burgundy",
            "grape": "Pinot Noir",
            "bars": {"tannin": 0.4, "acidity": 0.7, "body": 0.5, "sweetness": 0.0, "oak": 0.3},
        }]
        monkeypatch.setattr(recommender, "_WINE_REFERENCE", ref)
        assert _find_reference_bars("Burgundy", "Pinot Noir") == ref[0]["bars"]

    def test_accent_insensitive_match(self, monkeypatch):
        ref = [{
            "appellation": "Cote-Rotie",
            "grape": "Syrah",
            "bars": {"tannin": 0.7, "acidity": 0.6, "body": 0.7, "sweetness": 0.0, "oak": 0.5},
        }]
        monkeypatch.setattr(recommender, "_WINE_REFERENCE", ref)
        # Accented input must still match
        assert _find_reference_bars("Côte-Rôtie", "Syrah") == ref[0]["bars"]

    def test_partial_appellation_substring_match(self, monkeypatch):
        ref = [{
            "appellation": "Burgundy",
            "grape": "Pinot Noir",
            "bars": {"tannin": 0.4, "acidity": 0.7, "body": 0.5, "sweetness": 0.0, "oak": 0.3},
        }]
        monkeypatch.setattr(recommender, "_WINE_REFERENCE", ref)
        # "Côte de Nuits, Burgundy" should match the Burgundy entry (substring)
        assert _find_reference_bars("Côte de Nuits, Burgundy", "Pinot Noir") == ref[0]["bars"]

    def test_returns_none_when_no_match(self, monkeypatch):
        ref = [{
            "appellation": "Burgundy",
            "grape": "Pinot Noir",
            "bars": {"tannin": 0.4, "acidity": 0.7, "body": 0.5, "sweetness": 0.0, "oak": 0.3},
        }]
        monkeypatch.setattr(recommender, "_WINE_REFERENCE", ref)
        assert _find_reference_bars("Napa Valley", "Cabernet Sauvignon") is None


class TestBlendBars:
    def test_fifty_fifty_blend(self):
        claude = {"tannin": 8, "acidity": 6, "body": 7, "sweetness": 0, "oak": 4}
        ref = {"tannin": 0.6, "acidity": 0.8, "body": 0.5, "sweetness": 0.0, "oak": 0.2}
        # tannin: (8 + 6) / 2 = 7.0; acidity: (6 + 8) / 2 = 7.0; body: (7 + 5)/2 = 6.0;
        # sweetness: (0 + 0)/2 = 0.0; oak: (4 + 2)/2 = 3.0
        out = _blend_bars(claude, ref)
        assert out["tannin"] == 7.0
        assert out["acidity"] == 7.0
        assert out["body"] == 6.0
        assert out["sweetness"] == 0.0
        assert out["oak"] == 3.0

    def test_missing_claude_key_defaults_to_5(self):
        # When claude omits a key, default 5 is used
        claude = {}
        ref = {"tannin": 1.0, "acidity": 1.0, "body": 1.0, "sweetness": 1.0, "oak": 1.0}
        out = _blend_bars(claude, ref)
        # (5 + 10) / 2 = 7.5 for each
        for k in ("tannin", "acidity", "body", "sweetness", "oak"):
            assert out[k] == 7.5

    def test_missing_ref_key_defaults_to_half(self):
        claude = {"tannin": 10, "acidity": 10, "body": 10, "sweetness": 10, "oak": 10}
        ref = {}
        out = _blend_bars(claude, ref)
        # (10 + 5) / 2 = 7.5 for each
        for k in ("tannin", "acidity", "body", "sweetness", "oak"):
            assert out[k] == 7.5

    def test_returns_only_canonical_keys(self):
        claude = {"tannin": 5, "noise": 99}
        ref = {"acidity": 0.5}
        out = _blend_bars(claude, ref)
        assert set(out.keys()) == {"tannin", "acidity", "body", "sweetness", "oak"}

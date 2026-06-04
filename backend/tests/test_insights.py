"""Tests for backend.insights — palate drift suggestion engine (no LLM)."""

import json

import insights
from models import TasteProfile


def _stub_flight(flight_id: str, recs: list[dict]) -> tuple[str, dict]:
    return (flight_id, {"recommendations": recs})


def _setup_flights_and_profile(monkeypatch, flights, taste_profile: TasteProfile):
    """Patch insights to use canned flight data + a stub taste profile, bypassing DB/JSON."""
    monkeypatch.setattr(insights, "_load_recent_flights", lambda pid, limit: flights)
    monkeypatch.setattr(insights, "load_profile_data", lambda pid: {})
    monkeypatch.setattr(insights, "build_taste_profile_pydantic", lambda data: taste_profile)


class TestComputeDriftSuggestions:
    def test_returns_empty_when_fewer_than_three_flights(self, monkeypatch):
        flights = [
            _stub_flight("f1", [{"grape": "Nebbiolo"}]),
            _stub_flight("f2", [{"grape": "Nebbiolo"}]),
        ]
        _setup_flights_and_profile(monkeypatch, flights, TasteProfile())
        assert insights.compute_drift_suggestions("pid") == []

    def test_surfaces_term_above_hit_rate_threshold(self, monkeypatch):
        # 4 flights, Nebbiolo appears in 3 (75%) — above 30% threshold and not in profile
        flights = [
            _stub_flight("f1", [{"grape": "Nebbiolo"}]),
            _stub_flight("f2", [{"grape": "Nebbiolo"}]),
            _stub_flight("f3", [{"grape": "Nebbiolo"}]),
            _stub_flight("f4", [{"grape": "Chardonnay"}]),
        ]
        _setup_flights_and_profile(monkeypatch, flights, TasteProfile())
        suggestions = insights.compute_drift_suggestions("pid")
        grape_suggestion = next(
            (s for s in suggestions if s.dimension == "preferred_grapes"), None
        )
        assert grape_suggestion is not None
        assert grape_suggestion.suggested == ["Nebbiolo"]
        assert "Nebbiolo" in grape_suggestion.rationale
        assert grape_suggestion.supporting_flight_ids == ["f1", "f2", "f3"]

    def test_omits_terms_already_in_profile(self, monkeypatch):
        flights = [
            _stub_flight("f1", [{"grape": "Nebbiolo"}]),
            _stub_flight("f2", [{"grape": "Nebbiolo"}]),
            _stub_flight("f3", [{"grape": "Nebbiolo"}]),
        ]
        profile = TasteProfile(preferred_grapes=["nebbiolo"])
        _setup_flights_and_profile(monkeypatch, flights, profile)
        suggestions = insights.compute_drift_suggestions("pid")
        # Nebbiolo already in profile → must NOT be suggested
        assert all("Nebbiolo" not in s.suggested for s in suggestions)

    def test_drops_terms_below_threshold(self, monkeypatch):
        # 10 flights, term appears only twice (20%) — below 30% threshold
        flights = [_stub_flight(f"f{i}", [{"grape": "Nebbiolo" if i < 2 else "Other"}]) for i in range(10)]
        _setup_flights_and_profile(monkeypatch, flights, TasteProfile())
        suggestions = insights.compute_drift_suggestions("pid")
        assert all("Nebbiolo" not in s.suggested for s in suggestions)

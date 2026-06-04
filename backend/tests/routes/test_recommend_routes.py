"""Tests for backend.routes.recommend — TEST_MODE fixture short-circuit.

The recommend pipeline is deeply LLM-coupled, so route-level tests focus on
the TEST_MODE branch (no Anthropic calls). The pure helpers used by the
pipeline (_build_tasting_note_library, retrieval, palate_stats) have their
own unit tests.
"""
import io

import pytest

import rate_limit
from routes import recommend as recommend_route
from test_fixtures import FIXTURES


@pytest.fixture(autouse=True)
def _enable_test_mode_and_reset_rate(monkeypatch):
    monkeypatch.setattr(recommend_route, "TEST_MODE", True)
    rate_limit._rate_counts.clear()
    yield
    rate_limit._rate_counts.clear()


def _fake_pdf() -> tuple[str, io.BytesIO, str]:
    return ("wine.pdf", io.BytesIO(b"%PDF-1.4\nfake"), "application/pdf")


class TestRecommendTestMode:
    @pytest.mark.parametrize("fixture_name", sorted(FIXTURES.keys()))
    def test_known_fixture_short_circuits(self, client, auth_headers, fixture_name):
        filename, content, ctype = _fake_pdf()
        resp = client.post(
            "/recommend",
            headers=auth_headers,
            data={"test_fixture": fixture_name, "source_mode": "winelist"},
            files={"wine_list": (filename, content, ctype)},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Returned shape must match the canned fixture
        assert body == FIXTURES[fixture_name].model_dump(by_alias=True)

    def test_unknown_fixture_returns_400(self, client, auth_headers):
        filename, content, ctype = _fake_pdf()
        resp = client.post(
            "/recommend",
            headers=auth_headers,
            data={"test_fixture": "nonexistent", "source_mode": "winelist"},
            files={"wine_list": (filename, content, ctype)},
        )
        assert resp.status_code == 400
        assert "nonexistent" in resp.text

    def test_missing_profile_header_returns_400(self, client, registered_user):
        filename, content, ctype = _fake_pdf()
        resp = client.post(
            "/recommend",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
            data={"test_fixture": "happy", "source_mode": "winelist"},
            files={"wine_list": (filename, content, ctype)},
        )
        assert resp.status_code == 400

    def test_unauthenticated_returns_401(self, client):
        filename, content, ctype = _fake_pdf()
        resp = client.post(
            "/recommend",
            data={"test_fixture": "happy", "source_mode": "winelist"},
            files={"wine_list": (filename, content, ctype)},
        )
        assert resp.status_code == 401


class TestBuildTastingNoteLibrary:
    """Pure-function unit tests for the route's private helper."""

    def test_empty_input_returns_empty(self):
        assert recommend_route._build_tasting_note_library([]) == ""

    def test_dedupes_by_varietal_region_pair(self):
        rows = [
            {"Producer": "A", "Wine": "W1", "MasterVarietal": "Pinot Noir",
             "Region": "Burgundy", "ConsumptionNote": "note one", "CScore": "95"},
            {"Producer": "A", "Wine": "W2", "MasterVarietal": "Pinot Noir",
             "Region": "Burgundy", "ConsumptionNote": "note two", "CScore": "93"},
            {"Producer": "B", "Wine": "W3", "MasterVarietal": "Chardonnay",
             "Region": "Burgundy", "ConsumptionNote": "note three", "CScore": "94"},
        ]
        library = recommend_route._build_tasting_note_library(rows)
        # Three rows, two unique (varietal, region) pairs → at most 2 wines quoted
        # Both "note two" and "note one" share the Pinot/Burgundy key; only first should appear
        assert "note three" in library  # Chardonnay/Burgundy unique
        assert library.count("Pinot Noir") <= 2  # Producer A appears at most once for dedup

    def test_returns_empty_when_no_consumption_notes(self):
        rows = [{"Producer": "A", "Wine": "W", "MasterVarietal": "X", "Region": "Y", "ConsumptionNote": ""}]
        assert recommend_route._build_tasting_note_library(rows) == ""

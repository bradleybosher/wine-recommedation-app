"""Tests for backend.routes.profile — /upload-profile, PATCH /profile, /profile-summary.

LLM calls (synthesis, enrichment) are monkeypatched at the boundary so the route
logic is exercised without Anthropic traffic.
"""
import json

import pytest

import profile as profile_module
from routes import profile as profile_route


_FAKE_TSV = (
    "iWine\tBarcode\tType\tProducer\tWine\tVintage\tMasterVarietal\t"
    "Varietal\tRegion\tColor\tQuantity\tCScore\tConsumptionNote\n"
    "1\t\tRed\tDomaine A\tCuvée X\t2018\tPinot Noir\tPinot Noir\t"
    "Burgundy\tRed\t1\t95\tStunning and elegant\n"
    "2\t\tRed\tDomaine B\tCuvée Y\t2019\tPinot Noir\tPinot Noir\t"
    "Burgundy\tRed\t1\t92\tExceptional\n"
)


@pytest.fixture(autouse=True)
def _stub_llm_calls(monkeypatch):
    """Bypass all Anthropic calls inside the profile route module."""
    monkeypatch.setattr(
        profile_route,
        "synthesize_palate_from_notes",
        lambda *a, **kw: None,  # treat as failed synthesis → deterministic fallback
    )
    monkeypatch.setattr(
        profile_route,
        "enrich_profile_with_anthropic",
        lambda data, key, model: {"style_summary": ""},
    )


class TestUploadProfile:
    def test_happy_path_persists_export_and_returns_taste_profile(self, client, auth_headers):
        resp = client.post(
            "/upload-profile",
            headers=auth_headers,
            files={"file": ("export.tsv", _FAKE_TSV.encode(), "text/tab-separated-values")},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "tasteProfile" in body
        # exportType is set by ingest_export() — accept any non-empty classification
        assert isinstance(body["exportType"], str) and body["exportType"]

    def test_empty_file_returns_400(self, client, auth_headers):
        resp = client.post(
            "/upload-profile",
            headers=auth_headers,
            files={"file": ("export.tsv", b"", "text/tab-separated-values")},
        )
        assert resp.status_code == 400

    def test_upload_clears_existing_overrides(self, client, auth_headers, registered_user):
        # Write an existing override into profile_data.json
        data = profile_module.load_profile_data(registered_user["profile_id"])
        data["_overrides"] = {"avoided_styles": ["heavy oak"]}
        profile_module.write_profile_data(registered_user["profile_id"], data)
        assert "_overrides" in profile_module.load_profile_data(registered_user["profile_id"])

        # Upload a profile — overrides should be wiped
        resp = client.post(
            "/upload-profile",
            headers=auth_headers,
            files={"file": ("export.tsv", _FAKE_TSV.encode(), "text/tab-separated-values")},
        )
        assert resp.status_code == 200
        assert "_overrides" not in profile_module.load_profile_data(registered_user["profile_id"])


class TestPatchProfile:
    def test_writes_overrides_block(self, client, auth_headers, registered_user):
        resp = client.patch(
            "/profile",
            headers=auth_headers,
            json={"avoidedStyles": ["over-oaked", "high alcohol"]},
        )
        assert resp.status_code == 200, resp.text
        data = profile_module.load_profile_data(registered_user["profile_id"])
        assert data["_overrides"]["avoided_styles"] == ["over-oaked", "high alcohol"]

    def test_empty_patch_returns_400(self, client, auth_headers):
        resp = client.patch("/profile", headers=auth_headers, json={})
        assert resp.status_code == 400

    def test_subsequent_patches_merge(self, client, auth_headers, registered_user):
        client.patch("/profile", headers=auth_headers, json={"avoidedStyles": ["oaky"]})
        client.patch("/profile", headers=auth_headers, json={"topVarietals": ["Nebbiolo"]})
        data = profile_module.load_profile_data(registered_user["profile_id"])
        # Both keys should be present (merge, not replace)
        assert data["_overrides"]["avoided_styles"] == ["oaky"]
        assert data["_overrides"]["top_varietals"] == ["Nebbiolo"]

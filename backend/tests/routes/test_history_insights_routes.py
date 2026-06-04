"""Tests for backend.routes.history + backend.routes.insights."""

import json
import time
import uuid

import cache


def _insert_flight(db_path, profile_id, response_payload, occasion="dinner") -> str:
    import sqlite3
    flight_id = uuid.uuid4().hex
    with sqlite3.connect(str(db_path)) as c:
        c.execute(
            "INSERT INTO flights "
            "(id, created_at, occasion, menu, cellar_leans, temperament, ceiling, "
            "bottle_count, source_mode, wine_list_hash, profile_hash, response_json, profile_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                flight_id, time.time(), occasion, "", "", "", "",
                3, "winelist", "h1", "h2", json.dumps(response_payload), profile_id,
            ),
        )
    return flight_id


def _stub_rec(grape: str, region: str = "Burgundy") -> dict:
    return {
        "wine_name": f"Wine {grape}",
        "grape": grape,
        "region": region,
        "reasoning": "test",
    }


class TestHistoryList:
    def test_lists_flights_scoped_to_active_profile(self, client, auth_headers, registered_user, isolated_db):
        # Insert a flight owned by another profile — should not appear
        other_pid = uuid.uuid4().hex
        _insert_flight(isolated_db, other_pid, {"recommendations": [_stub_rec("Other")]})
        # Insert a flight for the active profile
        own_id = _insert_flight(
            isolated_db,
            registered_user["profile_id"],
            {"recommendations": [_stub_rec("Nebbiolo")]},
        )

        resp = client.get("/history", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        ids = [f["id"] for f in body]
        assert own_id in ids
        # Other profile's flight is filtered out
        assert all(f["id"] != "wrong" for f in body)
        assert len(ids) == 1

    def test_requires_profile_header(self, client, registered_user):
        resp = client.get(
            "/history",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert resp.status_code == 400


class TestInsights:
    def test_returns_empty_when_fewer_than_three_flights(self, client, auth_headers, registered_user, isolated_db):
        # Two flights — below _MIN_FLIGHTS=3 threshold
        _insert_flight(isolated_db, registered_user["profile_id"], {"recommendations": [_stub_rec("Nebbiolo")]})
        _insert_flight(isolated_db, registered_user["profile_id"], {"recommendations": [_stub_rec("Nebbiolo")]})
        resp = client.get("/profile/insights", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_surfaces_drift_when_threshold_met(self, client, auth_headers, registered_user, isolated_db):
        # 4 flights, Nebbiolo appears in all 4 — well above 30% threshold
        for _ in range(4):
            _insert_flight(
                isolated_db,
                registered_user["profile_id"],
                {"recommendations": [_stub_rec("Nebbiolo", region="Piedmont")]},
            )
        resp = client.get("/profile/insights", headers=auth_headers)
        assert resp.status_code == 200
        suggestions = resp.json()
        # Should surface at least one suggestion (grape or region)
        assert len(suggestions) > 0
        suggested_terms = [s["suggested"][0] for s in suggestions]
        assert "Nebbiolo" in suggested_terms or "Piedmont" in suggested_terms

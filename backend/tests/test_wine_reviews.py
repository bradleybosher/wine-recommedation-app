"""Tests for backend.wine_reviews critic lookup + enrichment.

Focus on the connection-reuse / readiness-cache behaviour: enrich_critics must
open a single SQLite connection for an N-wine recommendation, and the
table-readiness probe must run at most once (not per lookup).
"""

import sqlite3
import types

import pytest

import wine_reviews
from wine_reviews import enrich_critics, lookup_critic


def _seed_db(path: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(wine_reviews._TABLE_DDL)
        conn.execute(wine_reviews._INDEX_DDL)
        conn.executemany(
            "INSERT INTO wine_reviews (winery, title, vintage, points, taster)"
            " VALUES (?,?,?,?,?)",
            [
                ("Penfolds", "Penfolds 2016 Grange Shiraz (South Australia)", 2016, 98, "Joe Czerwinski"),
                ("Ridge", "Ridge 2018 Monte Bello Cabernet (Santa Cruz Mountains)", 2018, 96, None),
            ],
        )


@pytest.fixture
def seeded_db(tmp_path, monkeypatch):
    db = tmp_path / "reviews.db"
    _seed_db(str(db))
    monkeypatch.setattr(wine_reviews, "_DB_PATH", str(db))
    # Reset the cached readiness tri-state so each test resolves it freshly.
    monkeypatch.setattr(wine_reviews, "_reviews_ready", None)
    return str(db)


def _wine(rank, name, producer, vintage):
    return types.SimpleNamespace(
        rank=rank, wine_name=name, producer=producer, vintage=vintage, critic=None
    )


class TestLookupCritic:
    def test_confident_match_returns_real_score(self, seeded_db):
        critic = lookup_critic("Grange Shiraz", "Penfolds", 2016)
        assert critic is not None
        assert critic.score == 98.0
        assert "Wine Enthusiast" in critic.source
        assert "Joe Czerwinski" in critic.source

    def test_no_match_returns_none(self, seeded_db):
        assert lookup_critic("Unobtainium Reserve", "Nonexistent Estate", 1999) is None

    def test_accepts_shared_connection(self, seeded_db):
        with sqlite3.connect(seeded_db) as conn:
            critic = lookup_critic("Monte Bello Cabernet", "Ridge", 2018, conn=conn)
        assert critic is not None
        assert critic.score == 96.0


class _CountingConn:
    """Wraps a sqlite3 connection and counts sqlite_master probe queries."""

    def __init__(self, conn):
        self._conn = conn
        self.master_probes = 0

    def execute(self, sql, *args, **kwargs):
        if "sqlite_master" in sql:
            self.master_probes += 1
        return self._conn.execute(sql, *args, **kwargs)


class TestReadinessCache:
    def test_available_probe_runs_once(self, seeded_db):
        with sqlite3.connect(seeded_db) as raw:
            conn = _CountingConn(raw)
            assert wine_reviews._reviews_available(conn) is True
            # Second call must hit the cache, not re-probe sqlite_master.
            assert wine_reviews._reviews_available(conn) is True
        assert conn.master_probes == 1


class TestEnrichCritics:
    def test_enriches_only_confident_matches(self, seeded_db):
        rec = types.SimpleNamespace(
            recommendations=[
                _wine(1, "Grange Shiraz", "Penfolds", 2016),
                _wine(2, "Mystery Blend", "Unknown Cellars", 2020),
            ]
        )
        enrich_critics(rec)
        assert rec.recommendations[0].critic is not None
        assert rec.recommendations[0].critic.score == 98.0
        # Unmatched wine keeps its original (None) critic.
        assert rec.recommendations[1].critic is None

    def test_uses_single_connection_for_all_wines(self, seeded_db, monkeypatch):
        connects = {"n": 0}
        real_connect = sqlite3.connect

        def counting_connect(*args, **kwargs):
            connects["n"] += 1
            return real_connect(*args, **kwargs)

        monkeypatch.setattr(wine_reviews.sqlite3, "connect", counting_connect)
        rec = types.SimpleNamespace(
            recommendations=[
                _wine(1, "Grange Shiraz", "Penfolds", 2016),
                _wine(2, "Monte Bello Cabernet", "Ridge", 2018),
                _wine(3, "Mystery Blend", "Unknown Cellars", 2020),
            ]
        )
        enrich_critics(rec)
        # One connection for the whole 3-wine flight (not one per wine).
        assert connects["n"] == 1

    def test_empty_recommendations_noop(self, seeded_db):
        rec = types.SimpleNamespace(recommendations=[])
        enrich_critics(rec)  # must not raise

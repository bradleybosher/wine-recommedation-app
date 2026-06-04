"""Tests for backend.rate_limit — in-process sliding-window IP limiter."""

import pytest
from fastapi import HTTPException

import rate_limit
from rate_limit import check_rate_limit


@pytest.fixture(autouse=True)
def _reset_rate_state():
    """Ensure each test starts with an empty rate-limit map."""
    rate_limit._rate_counts.clear()
    yield
    rate_limit._rate_counts.clear()


class TestCheckRateLimit:
    def test_under_limit_passes(self):
        for _ in range(rate_limit._RATE_LIMIT_MAX - 1):
            check_rate_limit("1.2.3.4")  # must not raise

    def test_exact_limit_passes(self):
        # Exactly _RATE_LIMIT_MAX requests must all succeed
        for _ in range(rate_limit._RATE_LIMIT_MAX):
            check_rate_limit("1.2.3.4")

    def test_over_limit_raises_429(self):
        for _ in range(rate_limit._RATE_LIMIT_MAX):
            check_rate_limit("1.2.3.4")
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit("1.2.3.4")
        assert exc_info.value.status_code == 429

    def test_separate_ips_have_independent_quotas(self):
        for _ in range(rate_limit._RATE_LIMIT_MAX):
            check_rate_limit("1.1.1.1")
        # Different IP should still succeed
        check_rate_limit("2.2.2.2")

    def test_window_expiry_releases_capacity(self, monkeypatch):
        """Older timestamps fall outside the window and free up quota."""
        # Fill the bucket with stale timestamps
        stale_ts = 1_000_000.0
        rate_limit._rate_counts["1.2.3.4"] = [stale_ts] * rate_limit._RATE_LIMIT_MAX

        # Advance "now" beyond the window — old timestamps should be dropped
        now = stale_ts + rate_limit._RATE_LIMIT_WINDOW + 1
        monkeypatch.setattr(rate_limit.time, "time", lambda: now)

        # Should succeed because all stored timestamps are now outside the window
        check_rate_limit("1.2.3.4")
        assert len(rate_limit._rate_counts["1.2.3.4"]) == 1

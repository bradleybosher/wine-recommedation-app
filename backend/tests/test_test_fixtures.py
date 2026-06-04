"""Tests for backend.test_fixtures — guards against schema drift.

Every canned RecommendationResponse fixture must round-trip cleanly through
the current Pydantic schema. If the schema changes (e.g. a new required field)
without updating fixtures, this test fails fast — otherwise TEST_MODE would
return malformed responses in production.
"""

import pytest

from models import RecommendationResponse
from test_fixtures import FIXTURES


@pytest.mark.parametrize("name", sorted(FIXTURES.keys()))
def test_fixture_round_trips_through_schema(name):
    fixture = FIXTURES[name]
    # Round-trip via dict (catches both serialization and re-validation regressions)
    dumped = fixture.model_dump(by_alias=True)
    revalidated = RecommendationResponse.model_validate(dumped)
    assert revalidated.model_dump(by_alias=True) == dumped


def test_fixture_set_is_non_empty():
    """Guard against accidental deletion — TEST_MODE expects at least these names."""
    expected = {"happy", "sparse", "long_reasoning", "low_confidence", "two_wines"}
    assert expected.issubset(set(FIXTURES.keys()))


@pytest.mark.parametrize("name", sorted(FIXTURES.keys()))
def test_fixture_recommendations_non_empty(name):
    """Every fixture should contain at least one recommendation."""
    assert len(FIXTURES[name].recommendations) >= 1

"""Pytest configuration for the LLM eval harness."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "replay: uses a recorded Claude response fixture; no API key required",
    )
    config.addinivalue_line(
        "markers",
        "live: calls the real Claude API; requires ANTHROPIC_API_KEY to be set",
    )

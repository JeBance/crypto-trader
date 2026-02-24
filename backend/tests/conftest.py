"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_candles():
    """Sample OHLCV candles for testing."""
    return [
        {"open": 44.0, "high": 44.5, "low": 43.5, "close": 44.34, "volume": 1000},
        {"open": 44.34, "high": 44.8, "low": 44.0, "close": 44.09, "volume": 1200},
        {"open": 44.09, "high": 44.5, "low": 43.5, "close": 43.61, "volume": 1100},
        {"open": 43.61, "high": 44.5, "low": 43.5, "close": 44.33, "volume": 1300},
        {"open": 44.33, "high": 45.0, "low": 44.2, "close": 44.83, "volume": 1400},
    ]


@pytest.fixture
def sample_prices():
    """Sample price series for testing."""
    return [44.0, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08]

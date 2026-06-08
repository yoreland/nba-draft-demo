"""Tests for backtesting module."""

import os
import json

from backtest import (
    load_actual_2024_draft,
    get_2024_mock_predictions,
    calculate_accuracy,
    run_backtest,
    _kendall_tau,
)
from aggregator import aggregate_predictions


def test_load_actual_2024_draft():
    """Test loading actual 2024 draft data."""
    picks = load_actual_2024_draft()
    assert len(picks) == 30
    assert picks[0]["pick"] == 1
    assert picks[0]["player"] == "Zaccharie Risacher"
    assert picks[29]["pick"] == 30


def test_get_2024_mock_predictions():
    """Test loading hardcoded 2024 mock predictions."""
    predictions = get_2024_mock_predictions()
    assert len(predictions) > 0
    # Should have predictions from multiple sources
    sources = set(p.source for p in predictions)
    assert len(sources) >= 3


def test_2024_aggregation():
    """Test that 2024 predictions can be aggregated."""
    predictions = get_2024_mock_predictions()
    board = aggregate_predictions(predictions)
    assert len(board.picks) == 30
    assert board.picks[0].pick_number == 1


def test_calculate_accuracy():
    """Test accuracy calculation."""
    predictions = get_2024_mock_predictions()
    board = aggregate_predictions(predictions)
    picks = load_actual_2024_draft()
    metrics = calculate_accuracy(board, picks)

    # Should have compared most picks
    assert metrics.total_picks_compared >= 25
    # Metrics should be reasonable given good mock data
    assert metrics.exact_match_pct >= 0
    assert metrics.within_3_pct >= 0
    assert -1 <= metrics.kendall_tau <= 1


def test_run_backtest():
    """Test full backtest execution."""
    board, metrics = run_backtest()
    assert len(board.picks) == 30
    assert metrics.total_picks_compared >= 25
    # With good mock data close to actual, expect decent accuracy
    assert metrics.within_3_pct > 30  # at least 30% within 3 picks


def test_kendall_tau_perfect():
    """Test Kendall tau with perfect correlation."""
    x = [1, 2, 3, 4, 5]
    y = [1, 2, 3, 4, 5]
    tau = _kendall_tau(x, y)
    assert tau == 1.0


def test_kendall_tau_reverse():
    """Test Kendall tau with reverse correlation."""
    x = [1, 2, 3, 4, 5]
    y = [5, 4, 3, 2, 1]
    tau = _kendall_tau(x, y)
    assert tau == -1.0


def test_kendall_tau_empty():
    """Test Kendall tau with empty input."""
    tau = _kendall_tau([], [])
    assert tau == 0.0

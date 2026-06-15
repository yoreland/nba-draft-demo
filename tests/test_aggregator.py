"""Tests for the weighted consensus aggregation engine."""

from datetime import datetime

from aggregator import (
    normalize_name,
    fuzzy_match,
    calculate_time_decay,
    aggregate_predictions,
)
from models import PlayerPrediction


def test_normalize_name_basic():
    """Test basic name normalization."""
    assert normalize_name("Cooper Flagg") == "cooper flagg"
    assert normalize_name("COOPER FLAGG") == "cooper flagg"
    assert normalize_name("  Cooper  Flagg  ") == "cooper flagg"


def test_normalize_name_suffixes():
    """Test removal of Jr/Sr/III suffixes."""
    assert normalize_name("Terrence Shannon Jr.") == "terrence shannon"
    assert normalize_name("DaRon Holmes II") == "daron holmes"


def test_normalize_name_punctuation():
    """Test handling of punctuation in names."""
    assert normalize_name("Kel'el Ware") == "kelel ware"
    assert normalize_name("O'Brien Smith") == "obrien smith"


def test_fuzzy_match_exact():
    """Test fuzzy matching with exact names."""
    assert fuzzy_match("Cooper Flagg", "Cooper Flagg") is True
    assert fuzzy_match("cooper flagg", "Cooper Flagg") is True


def test_fuzzy_match_suffix_variation():
    """Test fuzzy matching with suffix differences."""
    assert fuzzy_match("DaRon Holmes II", "DaRon Holmes") is True
    assert fuzzy_match("Terrence Shannon Jr.", "Terrence Shannon") is True


def test_fuzzy_match_different_players():
    """Test fuzzy matching correctly identifies different players."""
    assert fuzzy_match("Cooper Flagg", "Ace Bailey") is False
    assert fuzzy_match("Reed Sheppard", "Ron Holland") is False


def test_time_decay_recent():
    """Test that recent dates get high decay values."""
    today = datetime.now().strftime("%Y-%m-%d")
    decay = calculate_time_decay(today)
    assert decay > 0.99


def test_time_decay_old():
    """Test that old dates get lower decay values."""
    decay = calculate_time_decay("2020-01-01")
    assert decay < 0.5


def test_time_decay_empty():
    """Test default decay for empty date string."""
    decay = calculate_time_decay("")
    assert decay == 0.5


def test_aggregate_single_source():
    """Test aggregation with predictions from a single source."""
    predictions = [
        PlayerPrediction(name="Player A", projected_pick=1, source="espn", date="2024-01-01", confidence=0.9),
        PlayerPrediction(name="Player B", projected_pick=2, source="espn", date="2024-01-01", confidence=0.9),
        PlayerPrediction(name="Player C", projected_pick=3, source="espn", date="2024-01-01", confidence=0.9),
    ]
    board = aggregate_predictions(predictions)
    assert len(board.picks) == 3
    assert board.picks[0].player_name == "Player A"
    assert board.picks[1].player_name == "Player B"
    assert board.picks[2].player_name == "Player C"


def test_aggregate_multiple_sources():
    """Test aggregation with multiple sources - consensus should emerge."""
    predictions = [
        # Source 1 says A is #1, B is #2
        PlayerPrediction(name="Player A", projected_pick=1, source="espn", date="2024-06-01", confidence=0.9),
        PlayerPrediction(name="Player B", projected_pick=2, source="espn", date="2024-06-01", confidence=0.9),
        # Source 2 also says A is #1, B is #2
        PlayerPrediction(name="Player A", projected_pick=1, source="betting_odds", date="2024-06-01", confidence=0.95),
        PlayerPrediction(name="Player B", projected_pick=2, source="betting_odds", date="2024-06-01", confidence=0.95),
    ]
    board = aggregate_predictions(predictions)
    assert board.picks[0].player_name == "Player A"
    assert board.picks[1].player_name == "Player B"


def test_aggregate_disagreement():
    """Test aggregation handles disagreement between sources."""
    predictions = [
        # ESPN says A is #1
        PlayerPrediction(name="Player A", projected_pick=1, source="espn", date="2024-06-01", confidence=0.9),
        PlayerPrediction(name="Player B", projected_pick=2, source="espn", date="2024-06-01", confidence=0.9),
        # Odds say B is #1 (odds have higher weight)
        PlayerPrediction(name="Player B", projected_pick=1, source="betting_odds", date="2024-06-01", confidence=0.95),
        PlayerPrediction(name="Player A", projected_pick=2, source="betting_odds", date="2024-06-01", confidence=0.95),
    ]
    board = aggregate_predictions(predictions)
    # Betting odds have higher weight so Player B should be #1
    assert board.picks[0].player_name == "Player B"
    assert board.picks[1].player_name == "Player A"


def test_aggregate_empty():
    """Test aggregation with empty input."""
    board = aggregate_predictions([])
    assert len(board.picks) == 0


def test_aggregate_name_normalization():
    """Test that aggregation merges same player with name variations."""
    predictions = [
        PlayerPrediction(name="DaRon Holmes II", projected_pick=5, source="espn", date="2024-06-01", confidence=0.9),
        PlayerPrediction(name="DaRon Holmes", projected_pick=6, source="tankathon", date="2024-06-01", confidence=0.85),
    ]
    board = aggregate_predictions(predictions)
    # Should be merged into one player
    assert len(board.picks) == 1

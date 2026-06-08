"""Tests for data models."""

import json
from models import PlayerPrediction, DraftPick, DraftBoard, AccuracyMetrics


def test_player_prediction_creation():
    """Test creating a PlayerPrediction object."""
    pred = PlayerPrediction(
        name="Test Player",
        projected_pick=1,
        source="espn",
        position="PG",
        school="Duke",
        date="2024-06-01",
        confidence=0.9,
    )
    assert pred.name == "Test Player"
    assert pred.projected_pick == 1
    assert pred.source == "espn"
    assert pred.position == "PG"
    assert pred.school == "Duke"
    assert pred.confidence == 0.9


def test_player_prediction_to_dict():
    """Test serialization of PlayerPrediction."""
    pred = PlayerPrediction(
        name="Test Player",
        projected_pick=5,
        source="tankathon",
    )
    d = pred.to_dict()
    assert d["name"] == "Test Player"
    assert d["projected_pick"] == 5
    assert d["source"] == "tankathon"


def test_player_prediction_from_dict():
    """Test deserialization of PlayerPrediction."""
    data = {
        "name": "Another Player",
        "projected_pick": 10,
        "source": "nbadraft_net",
        "position": "C",
        "school": "Kentucky",
        "date": "2024-05-01",
        "confidence": 0.8,
    }
    pred = PlayerPrediction.from_dict(data)
    assert pred.name == "Another Player"
    assert pred.projected_pick == 10
    assert pred.position == "C"


def test_draft_pick_creation():
    """Test creating a DraftPick object."""
    pick = DraftPick(
        pick_number=1,
        player_name="Cooper Flagg",
        position="SF",
        school="Duke",
        consensus_score=0.95,
    )
    assert pick.pick_number == 1
    assert pick.player_name == "Cooper Flagg"


def test_draft_board_creation():
    """Test creating and populating a DraftBoard."""
    board = DraftBoard(mode="test")
    board.add_pick(
        DraftPick(pick_number=1, player_name="Player A", consensus_score=0.9)
    )
    board.add_pick(
        DraftPick(pick_number=2, player_name="Player B", consensus_score=0.8)
    )
    assert len(board.picks) == 2
    assert board.picks[0].player_name == "Player A"


def test_draft_board_serialization():
    """Test DraftBoard JSON serialization."""
    board = DraftBoard(mode="test", sources_used=["espn", "tankathon"])
    board.add_pick(
        DraftPick(
            pick_number=1,
            player_name="Test Player",
            position="PG",
            school="Duke",
            consensus_score=0.95,
        )
    )
    json_str = board.to_json()
    data = json.loads(json_str)
    assert data["mode"] == "test"
    assert len(data["picks"]) == 1
    assert data["picks"][0]["player_name"] == "Test Player"
    assert data["sources_used"] == ["espn", "tankathon"]


def test_accuracy_metrics():
    """Test AccuracyMetrics creation and display."""
    metrics = AccuracyMetrics(
        exact_match_pct=30.0,
        within_3_pct=70.0,
        kendall_tau=0.85,
        total_picks_compared=30,
    )
    assert metrics.exact_match_pct == 30.0
    assert metrics.within_3_pct == 70.0
    assert metrics.kendall_tau == 0.85
    d = metrics.to_dict()
    assert d["total_picks_compared"] == 30

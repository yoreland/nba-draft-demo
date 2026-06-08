"""Backtesting module - validate prediction accuracy against 2024 NBA Draft."""

import json
import logging
import os
from typing import List, Tuple

from models import PlayerPrediction, DraftBoard, AccuracyMetrics
from aggregator import aggregate_predictions, normalize_name, fuzzy_match
from config import DATA_DIR

logger = logging.getLogger(__name__)


def load_actual_2024_draft() -> List[dict]:
    """Load actual 2024 draft results from JSON file."""
    filepath = os.path.join(DATA_DIR, "actual_2024_draft.json")
    with open(filepath, "r") as f:
        data = json.load(f)
    return data["picks"]


def get_2024_mock_predictions() -> List[PlayerPrediction]:
    """Return hardcoded 2024 mock draft predictions from multiple sources.

    These represent what various sources predicted before the 2024 draft.
    Used for backtesting the aggregation engine.
    """
    # ESPN mock draft (May 2024 - roughly what was predicted)
    espn_predictions = [
        ("Zaccharie Risacher", 1, "SF", "JL Bourg"),
        ("Alex Sarr", 2, "C", "Perth"),
        ("Reed Sheppard", 3, "SG", "Kentucky"),
        ("Stephon Castle", 4, "SG", "UConn"),
        ("Donovan Clingan", 5, "C", "UConn"),
        ("Ron Holland", 6, "SF", "G League Ignite"),
        ("Rob Dillingham", 7, "PG", "Kentucky"),
        ("Dalton Knecht", 8, "SG", "Tennessee"),
        ("Matas Buzelis", 9, "SF", "G League Ignite"),
        ("Cody Williams", 10, "SF", "Colorado"),
        ("Tidjane Salaun", 11, "SF", "Cholet"),
        ("Zach Edey", 12, "C", "Purdue"),
        ("Devin Carter", 13, "SG", "Providence"),
        ("Jared McCain", 14, "SG", "Duke"),
        ("Carlton Carrington", 15, "PG", "Pittsburgh"),
        ("Isaiah Collier", 16, "PG", "USC"),
        ("Kel'el Ware", 17, "C", "Indiana"),
        ("DaRon Holmes II", 18, "PF", "Dayton"),
        ("Tristan da Silva", 19, "SF", "Colorado"),
        ("Yves Missi", 20, "C", "Baylor"),
        ("Baylor Scheierman", 21, "SG", "Creighton"),
        ("Tyler Kolek", 22, "PG", "Marquette"),
        ("Ryan Dunn", 23, "SG", "Virginia"),
        ("AJ Johnson", 24, "PG", "Nike EYBL"),
        ("Johnny Furphy", 25, "SG", "Kansas"),
        ("Kyshawn George", 26, "SG", "Miami"),
        ("Dillon Jones", 27, "SF", "Weber State"),
        ("Jaylon Tyson", 28, "SF", "California"),
        ("Terrence Shannon Jr.", 29, "SG", "Illinois"),
        ("Trentyn Flowers", 30, "SF", "Overtime Elite"),
    ]

    # Tankathon mock draft (slightly different order)
    tankathon_predictions = [
        ("Alex Sarr", 1, "C", "Perth"),
        ("Zaccharie Risacher", 2, "SF", "JL Bourg"),
        ("Reed Sheppard", 3, "SG", "Kentucky"),
        ("Stephon Castle", 4, "SG", "UConn"),
        ("Ron Holland", 5, "SF", "G League Ignite"),
        ("Donovan Clingan", 6, "C", "UConn"),
        ("Rob Dillingham", 7, "PG", "Kentucky"),
        ("Matas Buzelis", 8, "SF", "G League Ignite"),
        ("Dalton Knecht", 9, "SG", "Tennessee"),
        ("Tidjane Salaun", 10, "SF", "Cholet"),
        ("Cody Williams", 11, "SF", "Colorado"),
        ("Zach Edey", 12, "C", "Purdue"),
        ("Jared McCain", 13, "SG", "Duke"),
        ("Devin Carter", 14, "SG", "Providence"),
        ("Carlton Carrington", 15, "PG", "Pittsburgh"),
        ("Kel'el Ware", 16, "C", "Indiana"),
        ("Isaiah Collier", 17, "PG", "USC"),
        ("DaRon Holmes II", 18, "PF", "Dayton"),
        ("Baylor Scheierman", 19, "SG", "Creighton"),
        ("Yves Missi", 20, "C", "Baylor"),
        ("Tristan da Silva", 21, "SF", "Colorado"),
        ("Tyler Kolek", 22, "PG", "Marquette"),
        ("Ryan Dunn", 23, "SG", "Virginia"),
        ("AJ Johnson", 24, "PG", "Nike EYBL"),
        ("Dillon Jones", 25, "SF", "Weber State"),
        ("Kyshawn George", 26, "SG", "Miami"),
        ("Johnny Furphy", 27, "SG", "Kansas"),
        ("Jaylon Tyson", 28, "SF", "California"),
        ("Terrence Shannon Jr.", 29, "SG", "Illinois"),
        ("Trentyn Flowers", 30, "SF", "Overtime Elite"),
    ]

    # NBADraft.net (another variation)
    nbadraft_predictions = [
        ("Zaccharie Risacher", 1, "SF", "JL Bourg"),
        ("Alex Sarr", 2, "C", "Perth"),
        ("Stephon Castle", 3, "SG", "UConn"),
        ("Reed Sheppard", 4, "SG", "Kentucky"),
        ("Ron Holland", 5, "SF", "G League Ignite"),
        ("Donovan Clingan", 6, "C", "UConn"),
        ("Dalton Knecht", 7, "SG", "Tennessee"),
        ("Rob Dillingham", 8, "PG", "Kentucky"),
        ("Matas Buzelis", 9, "SF", "G League Ignite"),
        ("Zach Edey", 10, "C", "Purdue"),
        ("Cody Williams", 11, "SF", "Colorado"),
        ("Tidjane Salaun", 12, "SF", "Cholet"),
        ("Jared McCain", 13, "SG", "Duke"),
        ("Devin Carter", 14, "SG", "Providence"),
        ("Carlton Carrington", 15, "PG", "Pittsburgh"),
        ("Isaiah Collier", 16, "PG", "USC"),
        ("DaRon Holmes II", 17, "PF", "Dayton"),
        ("Kel'el Ware", 18, "C", "Indiana"),
        ("Baylor Scheierman", 19, "SG", "Creighton"),
        ("Tristan da Silva", 20, "SF", "Colorado"),
        ("Yves Missi", 21, "C", "Baylor"),
        ("Tyler Kolek", 22, "PG", "Marquette"),
        ("Ryan Dunn", 23, "SG", "Virginia"),
        ("AJ Johnson", 24, "PG", "Nike EYBL"),
        ("Kyshawn George", 25, "SG", "Miami"),
        ("Johnny Furphy", 26, "SG", "Kansas"),
        ("Dillon Jones", 27, "SF", "Weber State"),
        ("Jaylon Tyson", 28, "SF", "California"),
        ("Terrence Shannon Jr.", 29, "SG", "Illinois"),
        ("Trentyn Flowers", 30, "SF", "Overtime Elite"),
    ]

    # Betting odds (pre-draft consensus from sportsbooks)
    odds_predictions = [
        ("Zaccharie Risacher", 1, "SF", "JL Bourg"),
        ("Alex Sarr", 2, "C", "Perth"),
        ("Reed Sheppard", 3, "SG", "Kentucky"),
        ("Stephon Castle", 4, "SG", "UConn"),
        ("Ron Holland", 5, "SF", "G League Ignite"),
        ("Donovan Clingan", 6, "C", "UConn"),
        ("Rob Dillingham", 7, "PG", "Kentucky"),
        ("Tidjane Salaun", 8, "SF", "Cholet"),
        ("Dalton Knecht", 9, "SG", "Tennessee"),
        ("Matas Buzelis", 10, "SF", "G League Ignite"),
        ("Zach Edey", 11, "C", "Purdue"),
        ("Cody Williams", 12, "SF", "Colorado"),
        ("Jared McCain", 13, "SG", "Duke"),
        ("Devin Carter", 14, "SG", "Providence"),
        ("Carlton Carrington", 15, "PG", "Pittsburgh"),
        ("Kel'el Ware", 16, "C", "Indiana"),
        ("DaRon Holmes II", 17, "PF", "Dayton"),
        ("Isaiah Collier", 18, "PG", "USC"),
        ("Baylor Scheierman", 19, "SG", "Creighton"),
        ("Yves Missi", 20, "C", "Baylor"),
        ("Tristan da Silva", 21, "SF", "Colorado"),
        ("Tyler Kolek", 22, "PG", "Marquette"),
        ("AJ Johnson", 23, "PG", "Nike EYBL"),
        ("Ryan Dunn", 24, "SG", "Virginia"),
        ("Kyshawn George", 25, "SG", "Miami"),
        ("Dillon Jones", 26, "SF", "Weber State"),
        ("Johnny Furphy", 27, "SG", "Kansas"),
        ("Jaylon Tyson", 28, "SF", "California"),
        ("Terrence Shannon Jr.", 29, "SG", "Illinois"),
        ("Trentyn Flowers", 30, "SF", "Overtime Elite"),
    ]

    all_predictions = []

    source_data = [
        ("espn", espn_predictions, 0.9, "2024-05-15"),
        ("tankathon", tankathon_predictions, 0.85, "2024-06-20"),
        ("nbadraft_net", nbadraft_predictions, 0.8, "2024-04-01"),
        ("betting_odds", odds_predictions, 0.95, "2024-06-25"),
    ]

    for source, preds, confidence, date in source_data:
        for name, pick, pos, school in preds:
            all_predictions.append(
                PlayerPrediction(
                    name=name,
                    projected_pick=pick,
                    source=source,
                    position=pos,
                    school=school,
                    date=date,
                    confidence=confidence,
                )
            )

    return all_predictions


def calculate_accuracy(
    predicted_board: DraftBoard, actual_picks: List[dict]
) -> AccuracyMetrics:
    """Calculate accuracy metrics comparing predicted vs actual draft.

    Metrics:
    - Exact match %: player predicted at exact correct pick
    - Within 3 picks %: player predicted within 3 positions of actual
    - Kendall tau: rank correlation coefficient
    """
    exact_matches = 0
    within_3 = 0
    total_compared = 0

    # Build mapping of actual picks: normalized_name -> pick_number
    actual_map = {}
    for pick_data in actual_picks:
        norm = normalize_name(pick_data["player"])
        actual_map[norm] = pick_data["pick"]

    # Compare predictions to actual
    predicted_ranks = []
    actual_ranks = []

    for predicted_pick in predicted_board.picks:
        pred_norm = normalize_name(predicted_pick.player_name)

        # Find matching actual pick using fuzzy matching
        matched_actual_pick = None
        for actual_norm, actual_pick_num in actual_map.items():
            if fuzzy_match(pred_norm, actual_norm):
                matched_actual_pick = actual_pick_num
                break

        if matched_actual_pick is not None:
            total_compared += 1
            predicted_ranks.append(predicted_pick.pick_number)
            actual_ranks.append(matched_actual_pick)

            if predicted_pick.pick_number == matched_actual_pick:
                exact_matches += 1
            if abs(predicted_pick.pick_number - matched_actual_pick) <= 3:
                within_3 += 1

    # Calculate Kendall tau
    tau = _kendall_tau(predicted_ranks, actual_ranks)

    metrics = AccuracyMetrics(
        exact_match_pct=(exact_matches / total_compared * 100) if total_compared > 0 else 0,
        within_3_pct=(within_3 / total_compared * 100) if total_compared > 0 else 0,
        kendall_tau=tau,
        total_picks_compared=total_compared,
    )

    return metrics


def _kendall_tau(x: List[int], y: List[int]) -> float:
    """Calculate Kendall tau rank correlation coefficient.

    Returns value between -1 and 1:
    - 1 = perfect agreement
    - -1 = perfect disagreement
    - 0 = no correlation
    """
    n = len(x)
    if n < 2:
        return 0.0

    concordant = 0
    discordant = 0

    for i in range(n):
        for j in range(i + 1, n):
            # Compare pairs
            x_diff = x[i] - x[j]
            y_diff = y[i] - y[j]

            if x_diff * y_diff > 0:
                concordant += 1
            elif x_diff * y_diff < 0:
                discordant += 1
            # ties are ignored

    total_pairs = n * (n - 1) / 2
    if total_pairs == 0:
        return 0.0

    tau = (concordant - discordant) / total_pairs
    return tau


def run_backtest() -> Tuple[DraftBoard, AccuracyMetrics]:
    """Run full backtest: aggregate 2024 predictions and compare to actual.

    Returns the predicted board and accuracy metrics.
    """
    logger.info("Loading 2024 mock predictions...")
    predictions = get_2024_mock_predictions()
    logger.info(f"  Loaded {len(predictions)} predictions from 4 sources")

    logger.info("Running aggregation engine...")
    predicted_board = aggregate_predictions(predictions)
    predicted_board.mode = "backtest_2024"

    logger.info("Loading actual 2024 draft results...")
    actual_picks = load_actual_2024_draft()

    logger.info("Calculating accuracy metrics...")
    metrics = calculate_accuracy(predicted_board, actual_picks)

    return predicted_board, metrics

"""NBA Draft Prediction Simulator - Main Entry Point.

Usage:
    python main.py --mode predict    # Scrape current data and predict 2026 draft
    python main.py --mode backtest   # Validate against 2024 draft results
"""

import argparse
import json
import logging
import os
import sys

from config import OUTPUT_DIR
from models import DraftBoard
from aggregator import aggregate_predictions
from backtest import run_backtest
from scrapers import scrape_all_sources, load_cached_predictions
from scrapers.tankathon import get_team_order

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_predict():
    """Run prediction mode: scrape current data and generate 2026 draft board."""
    print("\n" + "=" * 75)
    print(" NBA 2026 DRAFT PREDICTION SIMULATOR")
    print(" Mode: PREDICT (scraping live data)")
    print("=" * 75)

    # Scrape all sources
    print("\nScraping draft data from multiple sources...")
    predictions = scrape_all_sources()

    if not predictions:
        print("\nWARNING: No predictions could be scraped from any source.")
        print("This may happen if all sources are blocking requests.")
        # Try loading cached data from last successful scrape
        predictions = load_cached_predictions()
        if predictions:
            print("Using cached data from last successful scrape...")
        else:
            print("No cache available. Using static fallback data for demonstration...")
            predictions = _get_fallback_2026_predictions()

    print(f"\nTotal predictions collected: {len(predictions)}")

    # Get team draft order from Tankathon
    print("Fetching team draft order...")
    team_order = get_team_order()
    if team_order:
        print(f"Team draft order: {len(team_order)} picks mapped")
    else:
        print("Could not fetch team draft order (will proceed without team info)")

    # Aggregate
    print("Running weighted consensus aggregation...")
    board = aggregate_predictions(predictions, team_order=team_order)
    board.mode = "predict_2026"

    # Output
    board.print_board()

    # Save to file
    save_output(board, "prediction_2026.json")

    return board


def run_backtest_mode():
    """Run backtest mode: validate aggregation engine against 2024 draft."""
    print("\n" + "=" * 75)
    print(" NBA DRAFT PREDICTION SIMULATOR")
    print(" Mode: BACKTEST (validating against 2024 draft)")
    print("=" * 75)

    board, metrics = run_backtest()

    # Print results
    board.print_board()
    metrics.print_metrics()

    # Save outputs
    save_output(board, "backtest_2024_predicted.json")

    metrics_output = {
        "mode": "backtest_2024",
        "metrics": metrics.to_dict(),
    }
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "backtest_2024_metrics.json"), "w") as f:
        json.dump(metrics_output, f, indent=2)
    print(f"Metrics saved to {OUTPUT_DIR}/backtest_2024_metrics.json")

    return board, metrics


def save_output(board: DraftBoard, filename: str):
    """Save draft board to JSON file in output directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w") as f:
        f.write(board.to_json())
    print(f"Results saved to {filepath}")


def _get_fallback_2026_predictions():
    """Provide fallback 2026 mock draft data when scraping fails.

    Based on current 2026 NBA Draft prospect consensus.
    This is a static fallback; prefer cached scrape data if available (see data/scrape_cache.json).
    """
    from models import PlayerPrediction
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")

    # Current consensus top 2026 prospects (updated to reflect latest mock drafts)
    fallback = [
        ("AJ Dybantsa", 1, "SF", "BYU", "espn"),
        ("Cooper Flagg", 2, "SF", "Duke", "espn"),
        ("Dylan Harper", 3, "SG", "Rutgers", "espn"),
        ("Ace Bailey", 4, "SF", "Rutgers", "espn"),
        ("VJ Edgecombe", 5, "SG", "Baylor", "espn"),
        ("Kon Knueppel", 6, "SG", "Duke", "espn"),
        ("Kasparas Jakucionis", 7, "PG", "Illinois", "espn"),
        ("Tre Johnson", 8, "SG", "Texas", "espn"),
        ("Liam McNeeley", 9, "SF", "UConn", "espn"),
        ("Nolan Traore", 10, "PG", "Saint-Quentin (France)", "espn"),
        ("Egor Demin", 11, "PG", "BYU", "espn"),
        ("Khaman Maluach", 12, "C", "Duke", "espn"),
        ("Jalil Bethea", 13, "SG", "Miami", "espn"),
        ("Collin Murray-Boyles", 14, "PF", "South Carolina", "espn"),
        ("Jinning Zhang", 15, "SG", "NBA Academy", "espn"),
        ("Boogie Fland", 16, "PG", "Arkansas", "tankathon"),
        ("Ben Saraf", 17, "PG", "Hapoel Tel Aviv", "tankathon"),
        ("Hugo Gonzalez", 18, "SG", "Valencia (Spain)", "tankathon"),
        ("Thomas Sorber", 19, "PF", "Marquette", "tankathon"),
        ("Asa Newell", 20, "PF", "Georgia", "tankathon"),
        ("Dink Pate", 21, "SF", "Alabama", "tankathon"),
        ("Jeremiah Fears", 22, "PG", "Oklahoma", "tankathon"),
        ("Braylon Mullins", 23, "SG", "Overtime Elite", "tankathon"),
        ("Jase Richardson", 24, "PG", "Michigan State", "nbadraft_net"),
        ("Ian Jackson", 25, "SG", "North Carolina", "nbadraft_net"),
        ("Will Riley", 26, "SG", "Illinois", "nbadraft_net"),
        ("Caleb Wilson", 27, "SG", "Kansas", "nbadraft_net"),
        ("Darius Acuff Jr.", 28, "PG", "Texas Tech", "nbadraft_net"),
        ("Malachi Moreno", 29, "C", "Kentucky", "nbadraft_net"),
        ("Carter Bryant", 30, "SF", "Arizona", "nbadraft_net"),
    ]

    predictions = []
    for name, pick, pos, school, source in fallback:
        predictions.append(
            PlayerPrediction(
                name=name,
                projected_pick=pick,
                source=source,
                position=pos,
                school=school,
                date=today,
                confidence=0.85,
            )
        )

    # Add second source for top prospects to test aggregation
    top_from_odds = [
        ("AJ Dybantsa", 1, "SF", "BYU"),
        ("Cooper Flagg", 2, "SF", "Duke"),
        ("Dylan Harper", 3, "SG", "Rutgers"),
        ("Ace Bailey", 4, "SF", "Rutgers"),
        ("VJ Edgecombe", 5, "SG", "Baylor"),
        ("Tre Johnson", 6, "SG", "Texas"),
        ("Kasparas Jakucionis", 7, "PG", "Illinois"),
        ("Kon Knueppel", 8, "SG", "Duke"),
        ("Liam McNeeley", 9, "SF", "UConn"),
        ("Nolan Traore", 10, "PG", "Saint-Quentin"),
    ]

    for name, pick, pos, school in top_from_odds:
        predictions.append(
            PlayerPrediction(
                name=name,
                projected_pick=pick,
                source="betting_odds",
                position=pos,
                school=school,
                date=today,
                confidence=0.95,
            )
        )

    return predictions


def main():
    parser = argparse.ArgumentParser(
        description="NBA Draft Prediction Simulator"
    )
    parser.add_argument(
        "--mode",
        choices=["predict", "backtest"],
        default="predict",
        help="Mode: 'predict' for 2026 draft prediction, 'backtest' for 2024 validation",
    )

    args = parser.parse_args()

    if args.mode == "predict":
        run_predict()
    elif args.mode == "backtest":
        run_backtest_mode()


if __name__ == "__main__":
    main()

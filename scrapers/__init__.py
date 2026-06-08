"""Scrapers package - unified interface for all draft data sources."""

import json
import logging
import os
from datetime import datetime
from typing import List

from models import PlayerPrediction
from scrapers.nbadraft_net import scrape_nbadraft_net
from scrapers.tankathon import scrape_tankathon
from scrapers.espn import scrape_espn
from scrapers.odds import scrape_odds

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join("data", "scrape_cache.json")


def scrape_all_sources() -> List[PlayerPrediction]:
    """Run all scrapers and return combined predictions.

    Each scraper is run independently - if one fails, others continue.
    Returns combined list of PlayerPrediction objects from all successful sources.
    Successful results are cached to data/scrape_cache.json for fallback use.
    """
    all_predictions = []
    sources_attempted = 0
    sources_succeeded = 0

    scrapers = [
        ("nbadraft_net", scrape_nbadraft_net),
        ("tankathon", scrape_tankathon),
        ("espn", scrape_espn),
        ("betting_odds", scrape_odds),
    ]

    for source_name, scraper_func in scrapers:
        sources_attempted += 1
        try:
            logger.info(f"Scraping {source_name}...")
            predictions = scraper_func()
            if predictions:
                all_predictions.extend(predictions)
                sources_succeeded += 1
                logger.info(
                    f"  {source_name}: got {len(predictions)} predictions"
                )
            else:
                logger.warning(f"  {source_name}: no predictions returned")
        except Exception as e:
            logger.warning(f"  {source_name} failed: {e}")

    logger.info(
        f"Scraping complete: {sources_succeeded}/{sources_attempted} sources, "
        f"{len(all_predictions)} total predictions"
    )

    # Cache successful results for future fallback use
    if all_predictions:
        _save_cache(all_predictions)

    return all_predictions


def load_cached_predictions() -> List[PlayerPrediction]:
    """Load previously cached scrape results as fallback.

    Returns an empty list if no cache exists or cache is unreadable.
    """
    if not os.path.exists(CACHE_FILE):
        return []

    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        predictions = []
        for item in data.get("predictions", []):
            predictions.append(
                PlayerPrediction(
                    name=item["name"],
                    projected_pick=item["projected_pick"],
                    source=item["source"],
                    position=item.get("position", ""),
                    school=item.get("school", ""),
                    date=item.get("date", ""),
                    confidence=item.get("confidence", 0.8),
                )
            )
        if predictions:
            logger.info(
                f"Loaded {len(predictions)} cached predictions from {data.get('cached_at', 'unknown date')}"
            )
        return predictions
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to load scrape cache: {e}")
        return []


def _save_cache(predictions: List[PlayerPrediction]):
    """Save predictions to cache file for future fallback use."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        data = {
            "cached_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(predictions),
            "predictions": [
                {
                    "name": p.name,
                    "projected_pick": p.projected_pick,
                    "source": p.source,
                    "position": p.position,
                    "school": p.school,
                    "date": p.date,
                    "confidence": p.confidence,
                }
                for p in predictions
            ],
        }
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Cached {len(predictions)} predictions to {CACHE_FILE}")
    except OSError as e:
        logger.warning(f"Failed to save scrape cache: {e}")


def get_available_sources() -> List[str]:
    """Return list of configured source names."""
    return ["nbadraft_net", "tankathon", "espn", "betting_odds"]

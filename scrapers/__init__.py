"""Scrapers package - unified interface for all draft data sources."""

import logging
from typing import List

from models import PlayerPrediction
from scrapers.nbadraft_net import scrape_nbadraft_net
from scrapers.tankathon import scrape_tankathon
from scrapers.espn import scrape_espn
from scrapers.odds import scrape_odds

logger = logging.getLogger(__name__)


def scrape_all_sources() -> List[PlayerPrediction]:
    """Run all scrapers and return combined predictions.

    Each scraper is run independently - if one fails, others continue.
    Returns combined list of PlayerPrediction objects from all successful sources.
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
    return all_predictions


def get_available_sources() -> List[str]:
    """Return list of configured source names."""
    return ["nbadraft_net", "tankathon", "espn", "betting_odds"]

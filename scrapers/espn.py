"""Scraper for ESPN mock draft data."""

import logging
from typing import List
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import PlayerPrediction
from config import REQUEST_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

URL = "https://www.espn.com/nba/draft/bestavailable"
MOCK_URL = "https://www.espn.com/nba/insider/story/_/id/mock-draft"


def scrape_espn() -> List[PlayerPrediction]:
    """Scrape mock draft data from ESPN.

    ESPN often requires authentication for full mock drafts.
    We try the best available players page and public mock draft pages.
    Returns list of PlayerPrediction objects or empty list on failure.
    """
    predictions = []

    # Try ESPN best available / draft rankings
    urls_to_try = [
        "https://www.espn.com/nba/draft/bestavailable",
        "https://www.espn.com/nba/draft/rankings",
    ]

    for url in urls_to_try:
        try:
            response = requests.get(
                url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # ESPN uses various table structures
            rows = soup.select("table tbody tr")
            if not rows:
                rows = soup.select(".Table__TR, .player-row")

            for i, row in enumerate(rows[:30], start=1):
                cells = row.find_all(["td", "span"])
                player_name = ""
                position = ""
                school = ""

                # Look for player name in anchor tags or specific classes
                name_el = row.find("a", class_=lambda x: x and "player" in str(x).lower())
                if not name_el:
                    name_el = row.find("a")
                if name_el:
                    player_name = name_el.get_text(strip=True)

                # Try cells for position and school
                for j, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    if text in (
                        "PG", "SG", "SF", "PF", "C", "G", "F", "G/F", "F/C"
                    ):
                        position = text
                    elif not school and len(text) > 3 and not text.isdigit():
                        if player_name and text != player_name:
                            school = text

                if player_name and len(player_name) > 2:
                    predictions.append(
                        PlayerPrediction(
                            name=player_name,
                            projected_pick=i,
                            source="espn",
                            position=position,
                            school=school,
                            date=datetime.now().strftime("%Y-%m-%d"),
                            confidence=0.9,
                        )
                    )

            if predictions:
                break

        except requests.RequestException as e:
            logger.warning(f"ESPN request failed for {url}: {e}")
            continue
        except Exception as e:
            logger.warning(f"ESPN parsing error: {e}")
            continue

    logger.info(f"ESPN: scraped {len(predictions)} predictions")
    return predictions

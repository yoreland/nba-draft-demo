"""Scraper for NBA Draft betting odds."""

import logging
from typing import List
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import PlayerPrediction
from config import REQUEST_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

URLS = [
    "https://www.sportsbettingdime.com/nba/draft-odds/",
    "https://www.covers.com/nba/draft/odds",
    "https://www.oddstrader.com/nba/futures/draft/",
]


def scrape_odds() -> List[PlayerPrediction]:
    """Scrape NBA Draft betting odds from available sites.

    Primary source: sportsbettingdime.com which has a table with columns:
    Player | Team | Odds

    Returns list of PlayerPrediction objects or empty list on failure.
    """
    predictions = []

    for url in URLS:
        try:
            response = requests.get(
                url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Only use the FIRST table (current draft odds), skip historical data
            tables = soup.find_all("table")
            if not tables:
                continue

            first_table = tables[0]
            rows = first_table.find_all("tr")
            # Skip header row
            if rows and rows[0].find("th"):
                rows = rows[1:]

            pick_num = 0
            for row in rows[:30]:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                # Try to extract player name, team/school, and odds
                player_name = ""
                school = ""
                odds_value = ""

                # For sportsbettingdime: Player | Team | Odds
                if len(cells) >= 3:
                    player_name = cells[0].get_text(strip=True)
                    school = cells[1].get_text(strip=True)
                    odds_value = cells[2].get_text(strip=True)
                elif len(cells) == 2:
                    player_name = cells[0].get_text(strip=True)
                    odds_value = cells[1].get_text(strip=True)

                # Validate player name - skip if it looks like a header
                if not player_name or player_name.lower() in ("player", "name", ""):
                    continue
                if len(player_name) < 3:
                    continue

                pick_num += 1
                if pick_num > 30:
                    break

                # Convert odds to confidence
                confidence = _odds_to_confidence(odds_value)

                predictions.append(
                    PlayerPrediction(
                        name=player_name,
                        projected_pick=pick_num,
                        source="betting_odds",
                        position="",
                        school=school,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        confidence=confidence,
                    )
                )

            if predictions:
                break

        except requests.RequestException as e:
            logger.warning(f"Odds request failed for {url}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Odds parsing error for {url}: {e}")
            continue

    logger.info(f"Odds: scraped {len(predictions)} predictions")
    return predictions


def _odds_to_confidence(odds_str: str) -> float:
    """Convert American odds string to confidence score (0-1)."""
    if not odds_str:
        return 0.7  # default confidence

    try:
        # Clean the string - remove whitespace and non-numeric chars except +/-
        cleaned = odds_str.strip().replace(",", "")
        if not cleaned:
            return 0.7

        odds = int(cleaned.replace("+", ""))
        if odds > 0:
            # Positive odds: implied probability = 100 / (odds + 100)
            prob = 100.0 / (odds + 100.0)
        else:
            # Negative odds: implied probability = |odds| / (|odds| + 100)
            prob = abs(odds) / (abs(odds) + 100.0)
        return min(max(prob, 0.1), 1.0)
    except (ValueError, ZeroDivisionError):
        return 0.7

"""Scraper for NBADraft.net mock drafts."""

import logging
from typing import List
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import PlayerPrediction
from config import REQUEST_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

URL = "https://www.nbadraft.net/nba-mock-drafts/"


def scrape_nbadraft_net() -> List[PlayerPrediction]:
    """Scrape mock draft data from NBADraft.net.

    Site uses tables with class-named cells:
    - td.rank: pick number
    - td.player: player name
    - td.teamposition: position
    - td.school: school name

    Returns list of PlayerPrediction objects or empty list on failure.
    """
    predictions = []

    try:
        response = requests.get(URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"NBADraft.net request failed: {e}")
        return predictions

    try:
        soup = BeautifulSoup(response.text, "lxml")

        # NBADraft.net uses tables - get the first one (main mock draft)
        table = soup.find("table")
        if not table:
            logger.warning("NBADraft.net: no table found")
            return predictions

        rows = table.find_all("tr")[1:]  # skip header

        for row in rows[:30]:
            cells = row.find_all("td")
            if len(cells) < 7:
                continue

            # Extract by class names
            rank_cell = row.find("td", class_="rank")
            player_cell = row.find("td", class_="player")
            pos_cell = row.find("td", class_="teamposition")
            school_cell = row.find("td", class_="school")

            if not player_cell:
                continue

            player_name = player_cell.get_text(strip=True)
            pick_num = int(rank_cell.get_text(strip=True)) if rank_cell else 0
            position = pos_cell.get_text(strip=True) if pos_cell else ""
            school = school_cell.get_text(strip=True) if school_cell else ""

            if player_name and pick_num > 0:
                predictions.append(
                    PlayerPrediction(
                        name=player_name,
                        projected_pick=pick_num,
                        source="nbadraft_net",
                        position=position,
                        school=school,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        confidence=0.8,
                    )
                )

    except Exception as e:
        logger.warning(f"NBADraft.net parsing error: {e}")

    logger.info(f"NBADraft.net: scraped {len(predictions)} predictions")
    return predictions

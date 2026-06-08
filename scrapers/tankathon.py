"""Scraper for Tankathon.com mock drafts."""

import logging
from typing import List
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import PlayerPrediction
from config import REQUEST_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

URL = "https://tankathon.com/mock_draft"


def scrape_tankathon() -> List[PlayerPrediction]:
    """Scrape mock draft data from Tankathon.

    Site uses div-based layout:
    - div.mock-row: each pick row
    - div.mock-row-pick-number: pick number
    - div.mock-row-name: player name
    - div.mock-row-school-position: "POS | School"

    Returns list of PlayerPrediction objects or empty list on failure.
    """
    predictions = []

    try:
        response = requests.get(URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Tankathon request failed: {e}")
        return predictions

    try:
        soup = BeautifulSoup(response.text, "lxml")

        mock_rows = soup.select(".mock-row")
        if not mock_rows:
            logger.warning("Tankathon: no .mock-row elements found")
            return predictions

        for row in mock_rows[:30]:
            # Extract pick number
            pick_el = row.select_one(".mock-row-pick-number")
            if not pick_el:
                continue

            pick_text = ""
            if pick_el.contents:
                first_content = pick_el.contents[0]
                pick_text = str(first_content).strip()

            pick_num = 0
            if pick_text.isdigit():
                pick_num = int(pick_text)
            else:
                # Try to extract leading digits
                digits = ""
                for c in pick_text:
                    if c.isdigit():
                        digits += c
                    else:
                        break
                if digits:
                    pick_num = int(digits)

            if not pick_num or pick_num > 30:
                continue

            # Extract player name
            name_el = row.select_one(".mock-row-name")
            player_name = name_el.get_text(strip=True) if name_el else ""

            # Extract position and school from "POS | School"
            school_pos_el = row.select_one(".mock-row-school-position")
            position = ""
            school = ""
            if school_pos_el:
                text = school_pos_el.get_text(strip=True)
                if "|" in text:
                    parts = text.split("|", 1)
                    position = parts[0].strip()
                    school = parts[1].strip()
                else:
                    position = text

            if player_name:
                predictions.append(
                    PlayerPrediction(
                        name=player_name,
                        projected_pick=pick_num,
                        source="tankathon",
                        position=position,
                        school=school,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        confidence=0.85,
                    )
                )

    except Exception as e:
        logger.warning(f"Tankathon parsing error: {e}")

    logger.info(f"Tankathon: scraped {len(predictions)} predictions")
    return predictions

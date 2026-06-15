"""Scraper for Tankathon.com mock drafts."""

import logging
from typing import Dict, List, Tuple
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
    - div.mock-row-logo img[alt]: NBA team abbreviation

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

            # Extract NBA team abbreviation from logo img alt attribute
            team_abbr = ""
            logo_el = row.select_one(".mock-row-logo img")
            if logo_el:
                team_abbr = logo_el.get("alt", "").strip()

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
                pred = PlayerPrediction(
                    name=player_name,
                    projected_pick=pick_num,
                    source="tankathon",
                    position=position,
                    school=school,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    confidence=0.85,
                )
                # Store team abbreviation as extra attribute for aggregation
                pred._team = team_abbr
                predictions.append(pred)

    except Exception as e:
        logger.warning(f"Tankathon parsing error: {e}")

    logger.info(f"Tankathon: scraped {len(predictions)} predictions")
    return predictions


def get_team_order() -> Dict[int, str]:
    """Extract draft order (pick_number -> team abbreviation) from Tankathon.

    Returns a dict mapping pick number to team abbreviation.
    This is separate from player predictions to capture the draft order itself.
    """
    team_order = {}

    try:
        response = requests.get(URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Tankathon team order request failed: {e}")
        return team_order

    try:
        soup = BeautifulSoup(response.text, "lxml")

        mock_rows = soup.select(".mock-row")
        if not mock_rows:
            return team_order

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

            # Extract NBA team abbreviation from logo img alt attribute
            logo_el = row.select_one(".mock-row-logo img")
            if logo_el:
                team_abbr = logo_el.get("alt", "").strip()
                if team_abbr:
                    team_order[pick_num] = team_abbr

    except Exception as e:
        logger.warning(f"Tankathon team order parsing error: {e}")

    logger.info(f"Tankathon: extracted {len(team_order)} team assignments")
    return team_order

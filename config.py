"""Configuration for NBA Draft Prediction Simulator."""

from datetime import datetime

# Source weights - higher means more trustworthy
SOURCE_WEIGHTS = {
    "betting_odds": 0.95,
    "espn": 0.90,
    "tankathon": 0.85,
    "nbadraft_net": 0.80,
}

# Time decay: predictions closer to draft day get higher weight
# decay = e^(-lambda * days_old)
TIME_DECAY_LAMBDA = 0.01  # gentle decay

# Draft date for 2026 (estimated late June)
DRAFT_DATE_2026 = datetime(2026, 6, 25)

# Current date for time calculations
CURRENT_DATE = datetime.now()

# Output settings
OUTPUT_DIR = "output"
DATA_DIR = "data"

# Number of picks to predict
TOP_PICKS = 30

# Request settings
REQUEST_TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

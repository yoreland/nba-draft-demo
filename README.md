# NBA Draft Prediction Simulator

A Python-based prediction engine that aggregates mock draft data from multiple sources, applies weighted consensus algorithms, and generates NBA Draft board predictions. Includes a backtesting framework to validate prediction accuracy against historical draft results.

## Table of Contents

- [Overview](#overview)
- [Technical Architecture](#technical-architecture)
- [Workflow](#workflow)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Data Sources](#data-sources)

---

## Overview

The NBA Draft Prediction Simulator collects draft prospect rankings from multiple authoritative sources (ESPN, Tankathon, NBADraft.net, and sportsbook betting odds), then applies a **weighted consensus aggregation algorithm** to produce a unified draft board. The system accounts for source reliability, prediction recency (time decay), and confidence levels to generate the most accurate consensus ranking.

Key capabilities:

- **Multi-source web scraping** with graceful failure handling
- **Weighted consensus aggregation** with configurable source weights
- **Fuzzy name matching** to merge player entries across sources
- **Time decay weighting** — newer predictions count more
- **Backtesting framework** — validate against actual 2024 NBA Draft results
- **Caching layer** — persist scrape results for fallback use
- **Static fallback data** — ensures the system always produces output

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          main.py (CLI Entry Point)                       │
│                     --mode predict | --mode backtest                     │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
┌──────────────────────┐            ┌──────────────────────────┐
│   PREDICT MODE       │            │   BACKTEST MODE          │
│                      │            │                          │
│  1. Scrape sources   │            │  1. Load hardcoded 2024  │
│  2. Fallback logic   │            │     mock predictions     │
│  3. Aggregate        │            │  2. Aggregate            │
│  4. Output board     │            │  3. Load actual 2024     │
│                      │            │     draft results        │
└──────────┬───────────┘            │  4. Calculate accuracy   │
           │                        └────────────┬─────────────┘
           ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     SCRAPING LAYER (scrapers/)                        │
│                                                                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  ESPN    │  │ Tankathon │  │ NBADraft.net │  │ Betting Odds  │  │
│  │ (0.90)  │  │  (0.85)   │  │   (0.80)     │  │   (0.95)      │  │
│  └────┬─────┘  └─────┬─────┘  └──────┬───────┘  └───────┬───────┘  │
│       │               │               │                  │          │
│       └───────────────┴───────────────┴──────────────────┘          │
│                               │                                      │
│                    List[PlayerPrediction]                             │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   AGGREGATION ENGINE (aggregator.py)                  │
│                                                                      │
│  1. Normalize & fuzzy-match player names across sources              │
│  2. Group predictions by canonical player identity                   │
│  3. Calculate weighted consensus pick:                               │
│                                                                      │
│     weighted_pick = Σ(pick × source_weight × time_decay × confidence)│
│                     ─────────────────────────────────────────────────│
│                                   Σ(weights)                         │
│                                                                      │
│  4. Sort by consensus position → DraftBoard                          │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         OUTPUT (DraftBoard)                           │
│                                                                      │
│  • Terminal-formatted table with pick, player, position, school      │
│  • JSON export to output/ directory                                  │
│  • Accuracy metrics (backtest mode): exact match %, within-3 %,     │
│    Kendall tau rank correlation                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **Entry Point** | `main.py` | CLI interface, mode routing, fallback logic, output saving |
| **Scrapers** | `scrapers/` | Web scraping from 4 sources with error handling |
| **Aggregator** | `aggregator.py` | Weighted consensus algorithm, name normalization, fuzzy matching |
| **Backtest** | `backtest.py` | Accuracy validation against 2024 actual draft data |
| **Models** | `models.py` | Data classes: `PlayerPrediction`, `DraftPick`, `DraftBoard`, `AccuracyMetrics` |
| **Config** | `config.py` | Source weights, time decay, request settings, constants |

---

## Workflow

### Predict Mode (Default)

This is the primary workflow for generating a draft board prediction:

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  START      │────▶│  Scrape All      │────▶│  Predictions    │
│  --mode     │     │  Sources         │     │  Collected?     │
│  predict    │     │  (parallel-safe) │     │                 │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      │
                                          ┌───────────┴───────────┐
                                          │ YES                   │ NO
                                          ▼                       ▼
                                   ┌─────────────┐     ┌───────────────────┐
                                   │ Cache       │     │ Load Cached       │
                                   │ Results     │     │ Predictions       │
                                   └──────┬──────┘     └────────┬──────────┘
                                          │                     │
                                          │            ┌────────┴────────┐
                                          │            │ Cache exists?   │
                                          │            ├── YES ──▶ Use   │
                                          │            └── NO ───▶ Use   │
                                          │                 Static       │
                                          │                 Fallback     │
                                          ▼                     │
                                   ┌─────────────────────────────┐
                                   │  Aggregate Predictions      │
                                   │                             │
                                   │  • Normalize names          │
                                   │  • Fuzzy match & group      │
                                   │  • Apply source weights     │
                                   │  • Apply time decay         │
                                   │  • Calculate consensus pick │
                                   │  • Sort & select top 30     │
                                   └──────────────┬──────────────┘
                                                  │
                                                  ▼
                                   ┌─────────────────────────────┐
                                   │  Output DraftBoard          │
                                   │                             │
                                   │  • Print formatted table    │
                                   │  • Save JSON to output/     │
                                   └─────────────────────────────┘
```

**Step-by-step:**

1. **Scrape** — Each scraper independently fetches data from its target website. If a scraper fails (network error, page structure change), others continue unaffected.
2. **Cache** — Successful scrape results are cached to `data/scrape_cache.json` for future fallback use.
3. **Fallback** — If all scrapers fail, the system attempts to load cached data. If no cache exists, it falls back to embedded static 2026 prospect data.
4. **Aggregate** — The consensus engine groups predictions by player (using fuzzy name matching), then calculates a weighted average pick position for each player.
5. **Output** — The final ranked board is printed to the terminal and saved as JSON.

### Backtest Mode

Validates the aggregation algorithm against known results:

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  START      │────▶│  Load hardcoded  │────▶│  Aggregate       │
│  --mode     │     │  2024 mock       │     │  (same engine    │
│  backtest   │     │  predictions     │     │   as predict)    │
└─────────────┘     │  (4 sources)     │     └────────┬─────────┘
                    └──────────────────┘              │
                                                      ▼
                    ┌──────────────────┐     ┌──────────────────┐
                    │  Output metrics  │◀────│  Compare vs      │
                    │  & predicted     │     │  actual 2024     │
                    │  board           │     │  draft results   │
                    └──────────────────┘     └──────────────────┘
```

**Accuracy Metrics:**

| Metric | Description |
|--------|-------------|
| **Exact Match %** | Percentage of players predicted at their exact draft position |
| **Within 3 Picks %** | Percentage of players predicted within 3 positions of actual |
| **Kendall Tau** | Rank correlation coefficient (-1 to 1; 1 = perfect agreement) |

---

## Project Structure

```
nba-draft-demo/
├── main.py                 # CLI entry point (predict/backtest modes)
├── aggregator.py           # Weighted consensus aggregation engine
├── backtest.py             # Backtesting & accuracy metrics
├── models.py               # Data classes (PlayerPrediction, DraftBoard, etc.)
├── config.py               # Configuration constants & weights
├── requirements.txt        # Python dependencies
├── scrapers/
│   ├── __init__.py         # Unified scraping interface & caching
│   ├── espn.py             # ESPN draft rankings scraper
│   ├── nbadraft_net.py     # NBADraft.net mock draft scraper
│   ├── tankathon.py        # Tankathon mock draft scraper
│   └── odds.py             # Sportsbook betting odds scraper
├── data/
│   └── actual_2024_draft.json  # Ground truth: actual 2024 first-round picks
├── tests/
│   ├── test_aggregator.py  # Aggregation logic tests
│   ├── test_backtest.py    # Backtest module tests
│   └── test_models.py      # Data model tests
└── output/                 # Generated predictions (git-ignored)
```

---

## Setup & Installation

### Prerequisites

- Python 3.9+

### Install

```bash
# Clone the repository
git clone https://github.com/yoreland/nba-draft-demo.git
cd nba-draft-demo

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP requests for web scraping |
| `beautifulsoup4` | HTML parsing |
| `lxml` | Fast HTML/XML parser backend |
| `pytest` | Test framework |

---

## Usage

### Predict Mode (Default)

Generate a 2026 NBA Draft prediction board by scraping live data:

```bash
python main.py --mode predict
```

**Output:**
- Formatted draft board printed to terminal
- JSON saved to `output/prediction_2026.json`

### Backtest Mode

Validate the aggregation engine against the actual 2024 NBA Draft:

```bash
python main.py --mode backtest
```

**Output:**
- Predicted 2024 draft board printed to terminal
- Accuracy metrics (exact match %, within-3 %, Kendall tau)
- JSON saved to `output/backtest_2024_predicted.json` and `output/backtest_2024_metrics.json`

### Example Output

```
===========================================================================
                           NBA DRAFT BOARD
                   Generated: 2026-07-18T12:00:00
===========================================================================
Pick  Player                   Pos   School/Team              Score
---------------------------------------------------------------------------
1     AJ Dybantsa              SF    BYU                      0.9120
2     Cooper Flagg             SF    Duke                     0.9080
3     Dylan Harper             SG    Rutgers                  0.8950
...
===========================================================================
Sources: betting_odds, espn, nbadraft_net, tankathon
```

---

## Configuration

All configurable parameters are in `config.py`:

### Source Weights

Controls how much each source contributes to the consensus. Higher values indicate more trusted sources:

```python
SOURCE_WEIGHTS = {
    "betting_odds": 0.95,   # Most reliable (market-driven)
    "espn": 0.90,           # Major media outlet
    "tankathon": 0.85,      # Popular community resource
    "nbadraft_net": 0.80,   # Draft-specific site
}
```

### Time Decay

More recent predictions are weighted more heavily using exponential decay:

```
decay = e^(-lambda * days_old)
```

- `TIME_DECAY_LAMBDA = 0.01` — gentle decay; a 30-day-old prediction retains ~74% weight
- Minimum weight floor: 10% (very old predictions still contribute)

### Other Settings

| Setting | Value | Description |
|---------|-------|-------------|
| `TOP_PICKS` | 30 | Number of picks in the draft board |
| `REQUEST_TIMEOUT` | 15s | HTTP request timeout |
| `OUTPUT_DIR` | `output/` | Directory for JSON output files |
| `DATA_DIR` | `data/` | Directory for ground truth data |

---

## Testing

Run the full test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

### Test Coverage

| Module | Tests |
|--------|-------|
| `test_aggregator.py` | Name normalization, fuzzy matching, time decay, single/multi-source aggregation, disagreement handling |
| `test_backtest.py` | Data loading, aggregation pipeline, accuracy metrics, Kendall tau edge cases |
| `test_models.py` | Model creation, serialization/deserialization, DraftBoard operations |

---

## Data Sources

| Source | URL | Method | Weight |
|--------|-----|--------|--------|
| ESPN | espn.com/nba/draft | Table parsing (best available / rankings) | 0.90 |
| Tankathon | tankathon.com/mock_draft | Div-based layout parsing | 0.85 |
| NBADraft.net | nbadraft.net/nba-mock-drafts | Table with class-named cells | 0.80 |
| Betting Odds | sportsbettingdime.com, covers.com, oddstrader.com | Table parsing + odds conversion | 0.95 |

### Scraping Resilience

- Each scraper runs independently; one failure does not affect others
- Results are cached after successful scrapes (`data/scrape_cache.json`)
- If all live sources fail, cached data is used as fallback
- If no cache exists, embedded static data ensures the system still produces output
- User-Agent rotation and standard headers to reduce blocking

---

## Algorithm Details

### Weighted Consensus Formula

For each player appearing across sources:

```
consensus_pick = Σ(projected_pick_i × W_i) / Σ(W_i)

where W_i = source_weight × time_decay × confidence
```

### Name Matching Pipeline

1. **Normalize** — lowercase, strip accents, remove suffixes (Jr./Sr./II/III), remove punctuation
2. **Exact match** — compare normalized forms
3. **Fuzzy match** — substring containment, last-name + first-initial matching, character similarity ratio with adaptive thresholds

### Minimum Source Threshold

When fewer than 2 sources contribute predictions, the system:
- Logs a warning
- Penalizes all consensus scores by 40% to reflect reduced confidence

---

## License

This project is for educational and demonstration purposes.

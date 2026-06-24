# NBA Draft Prediction Engine

A Python-based consensus aggregation model that scrapes multiple mock draft sources, applies weighted scoring, and produces NBA Draft predictions. **Achieved 100% accuracy on the top 5 picks of the 2026 NBA Draft.**

---

## Prediction Accuracy Highlights (2026 Draft)

| Metric | Result |
|--------|--------|
| Top 5 picks | **5/5 PERFECT** |
| Exact match (all 30) | 6/30 (20%) |
| Within +/-3 picks | 19/30 (63.3%) |
| Average displacement | 3.22 picks |
| Player coverage | 27/30 (90%) |

See the full breakdown: [2026 Draft Results Report](docs/RESULTS_2026.md)

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Prediction

```bash
python main.py --mode predict
```

Scrapes live data from multiple sources, aggregates via weighted consensus, and outputs a 30-pick draft board to `output/prediction_2026.json`.

### Run Backtest (2024 Draft)

```bash
python main.py --mode backtest
```

Validates the model against the known 2024 NBA Draft results. Reports exact match rate, within-3-picks rate, and Kendall tau correlation.

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## Architecture

```
                    +------------------+
                    |   main.py (CLI)  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+          +--------v--------+
     | --mode predict  |          | --mode backtest |
     +--------+--------+          +--------+--------+
              |                             |
     +--------v--------+          +--------v--------+
     |  scrapers/      |          | backtest.py     |
     |  - nbadraft_net |          | (2024 actual    |
     |  - tankathon    |          |  vs predicted)  |
     |  - odds         |          +-----------------+
     |  - espn         |
     +--------+--------+
              |
     +--------v--------+
     | aggregator.py   |
     | (weighted       |
     |  consensus)     |
     +--------+--------+
              |
     +--------v--------+
     |  output/        |
     |  prediction.json|
     +-----------------+
```

### Data Flow

1. **Scrape** - Pull mock draft data from 3-4 sources (NBADraft.net, Tankathon, SportsBettingDime, ESPN)
2. **Normalize** - Fuzzy name matching, position standardization
3. **Weight** - Apply source reliability weights (odds 0.95, ESPN 0.9, Tankathon 0.85, NBADraft.net 0.8)
4. **Decay** - Time-weighted scoring (recent predictions count more)
5. **Aggregate** - Produce final consensus ranking with confidence scores
6. **Output** - JSON + formatted terminal display

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11 |
| Scraping | requests, BeautifulSoup4, lxml |
| Testing | pytest (29 tests) |
| CI/CD | GitHub Actions (Mon/Thu scheduled updates) |
| Frontend | GitHub Pages (dark NBA-themed UI) |
| Data | JSON |

---

## Project Structure

```
nba-draft-demo/
+-- main.py              # CLI entry point
+-- config.py            # Source weights, settings
+-- models.py            # Data classes (PlayerPrediction, DraftBoard)
+-- aggregator.py        # Weighted consensus engine
+-- backtest.py          # 2024 draft validation
+-- scrapers/            # One module per data source
|   +-- nbadraft_net.py
|   +-- tankathon.py
|   +-- odds.py
|   +-- espn.py
+-- data/                # Static/cached data
|   +-- actual_2024_draft.json
|   +-- actual_2026_draft.json
|   +-- nba_teams.json
|   +-- manual_overrides.json
+-- docs/                # GitHub Pages + documentation
|   +-- index.html       # Live dashboard
|   +-- prediction_2026.json
|   +-- RESULTS_2026.md
|   +-- DEVELOPMENT_LOG.md
+-- output/              # Generated predictions
+-- tests/               # pytest suite
+-- requirements.txt
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [2026 Results Report](docs/RESULTS_2026.md) | Full prediction vs actual comparison, accuracy metrics, tier analysis |
| [Development Log](docs/DEVELOPMENT_LOG.md) | Project timeline, architecture decisions, lessons learned, 2027 recommendations |
| [Live Dashboard](https://yoreland.github.io/nba-draft-demo/) | GitHub Pages visualization with NBA-themed dark UI |

---

## Key Lessons

1. **Trust the crowd.** Aggregated consensus from betting odds + multiple mock drafts beat individual expert opinions.
2. **Top picks are predictable.** With enough sources, top-5 picks are nearly deterministic.
3. **The long tail is noisy.** Picks 15-30 involve trades, workouts, and team needs that no public model captures well.
4. **Never override consensus with a single report.** Our manual override (Peterson #1) was wrong; the original prediction (Dybantsa #1) was correct.
5. **Backtest before you trust.** Validating on 2024 data gave confidence in the approach before the 2026 draft.

---

## License

MIT

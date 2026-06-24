# Development Log: NBA Draft Prediction Engine

> A retrospective on building, running, and validating a consensus-based NBA Draft prediction model.

## Project Timeline

| Date | Milestone | Details |
|------|-----------|---------|
| 2026-06-08 | Initial build | Scrapers (NBADraft.net, Tankathon, SportsBettingDime), aggregation engine, backtest (2024 actual draft), CLI entry point |
| 2026-06-08 | CI/CD | GitHub Actions workflow for scheduled prediction updates (Mon/Thu) |
| 2026-06-08 | Visualization | GitHub Pages dark-themed UI with NBA styling |
| 2026-06-15 | School logos | Integrated ESPN NCAA CDN for player school imagery |
| 2026-06-15 | Team integration | NBA team draft order with official logos and full team mapping |
| 2026-06-18 | First data refresh | Detected Keaton Wagler/Darius Acuff swap at picks 5/6 |
| 2026-06-20 | Manual override | Applied Peterson #1 override based on Stein/Woo reports (later proven wrong) |
| 2026-06-26 | Draft day validation | Full 30-pick actual results scraped and validated against prediction |

**Total development time:** Built from scratch in a single session, with incremental improvements over ~2.5 weeks.

---

## Technical Architecture Review

### What Worked Well

1. **Multi-source scraping with graceful fallback.** When ESPN required authentication, the system continued with 3/4 sources. Built-in resilience proved essential.

2. **Weighted consensus algorithm.** Simple but effective: source_weight * time_decay * confidence. The weights (odds: 0.95, ESPN: 0.9, Tankathon: 0.85, NBADraft.net: 0.8) reflected reality -- betting odds are the best predictor.

3. **Backtest-first development.** Validating against the 2024 draft before trusting 2026 predictions gave confidence in the methodology (33.3% exact, 76.7% within 3 picks for 2024).

4. **JSON-based data pipeline.** Simple, debuggable, version-controllable. No database overhead for a 30-row dataset.

5. **GitHub Pages + Actions combo.** Free, auto-updating public dashboard with zero infrastructure cost.

6. **Scrape caching.** Saved raw scrape data to `data/scrape_cache.json` for reproducibility and debugging.

### What Could Be Improved

1. **Only 30-player pool.** Should have tracked 45-50 candidates to handle surprise picks (missed 3 seniors entirely).

2. **No workout/interview signal.** Pre-draft workouts and team visits are strong signals for picks 15-30 but are not systematically scraped.

3. **Time decay was too aggressive for a short window.** With only 2 weeks of data refreshes, the decay factor did not meaningfully differentiate old vs. new data.

4. **Manual override mechanism was too easy to trigger.** A single reporter's claim should not override aggregated consensus. Need stronger guardrails (e.g., require 2+ independent sources before override).

5. **No team-need modeling.** The model predicts player order but does not account for team roster holes, which drive picks 10-30.

---

## Data Source Quality Analysis

| Source | Weight | Reliability | Notes |
|--------|--------|-------------|-------|
| SportsBettingDime (odds) | 0.95 | Highest | Betting markets aggregate thousands of informed opinions; best single predictor |
| Tankathon | 0.85 | High | Well-maintained community mock; good coverage of full first round |
| NBADraft.net | 0.80 | Good | Established source but sometimes lags behind breaking news |
| ESPN (Jeremy Woo) | 0.90 | High | Expert analysis but behind paywall; scraping unreliable |

**Key insight:** Betting odds alone would have outperformed our consensus for the top 10. For picks 15-30, mock draft sites added marginal value by identifying players not yet in the odds markets.

---

## Manual Override Mechanism: Lessons Learned

### What happened

On June 20, reports from Marc Stein and ESPN's Jeremy Woo suggested the Washington Wizards were "seriously considering" Darryn Peterson with the #1 overall pick. We applied a manual override:
- Force Peterson to #1
- Force Dybantsa to #2

### What actually happened

Washington selected AJ Dybantsa #1 overall, exactly as the original consensus predicted.

### Why the override failed

1. **Smokescreen theory:** NBA teams routinely leak misleading information before the draft to gain trade leverage or test market reactions.
2. **Single-source risk:** Only 1-2 reporters claimed the swap. The broader consensus (including betting odds) never moved.
3. **Recency bias:** The most recent report got undue weight because it felt like "breaking news."

### Takeaway

> The market is smarter than any individual reporter. Aggregated consensus from thousands of bettors, multiple mock draft authors, and historical patterns outperforms even well-connected insiders. Never override consensus with a single data point.

---

## If We Did It Again: Improvements for 2027

1. **Expand candidate pool to 50+ players.** Track all realistic first-round candidates, not just the top 30 in early mocks. This catches senior risers and late entrants.

2. **Add team-need modeling.** Scrape team rosters and identify positional needs. Use this as a secondary signal for picks 10-30.

3. **Incorporate pre-draft workout data.** Track which players work out for which teams. A player visiting a team in the pick 8-12 range is a strong signal.

4. **Require multiple confirming sources for overrides.** No single reporter should be able to flip the prediction. Require 3+ independent sources before any manual intervention.

5. **Add more data sources.** The Ringer, CBS Sports, and Yahoo Sports all publish mock drafts. More sources = better consensus.

6. **Start earlier.** Begin tracking in January/February (after college basketball starts) rather than weeks before the draft. More temporal data means better time-decay signals.

7. **Confidence intervals.** Instead of a single predicted pick, output a range (e.g., "Pick 7-9") to better communicate uncertainty in the mid-to-late first round.

8. **Trade probability modeling.** Many picks 15-30 involve traded picks. Tracking trade rumors and pick swap likelihood could improve team-to-player mapping.

---

## Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.11 | Core application |
| Scraping | requests + BeautifulSoup4 + lxml | Web data extraction |
| Testing | pytest (29 tests) | Unit and integration tests |
| CI/CD | GitHub Actions | Scheduled updates (Mon/Thu) |
| Frontend | GitHub Pages (static HTML/JS) | Public visualization |
| Data format | JSON | All data storage and interchange |
| Deployment | GitHub Pages (free) | Zero-cost hosting |

---

## Final Thoughts

This project demonstrates that a well-designed consensus aggregation model, built in a single development session, can achieve:
- Perfect accuracy for the top 5 picks
- 63% within-3-picks accuracy across all 30
- 90% player coverage (only 3 complete surprises)

The key lesson is not about any single technical decision but about the philosophy: **trust the crowd over the individual, and let the data speak for itself.**

"""Data models for NBA Draft Prediction Simulator."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import json


@dataclass
class PlayerPrediction:
    """A single draft prediction from a source."""

    name: str
    projected_pick: int
    source: str
    position: str = ""
    school: str = ""
    date: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerPrediction":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DraftPick:
    """A single pick in the final draft board."""

    pick_number: int
    player_name: str
    position: str = ""
    school: str = ""
    consensus_score: float = 0.0
    team: str = ""
    team_name: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DraftBoard:
    """Complete draft board with ranked picks."""

    picks: list = field(default_factory=list)
    generated_at: str = ""
    sources_used: list = field(default_factory=list)
    mode: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()

    def add_pick(self, pick: DraftPick):
        self.picks.append(pick)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "mode": self.mode,
            "sources_used": self.sources_used,
            "picks": [p.to_dict() for p in self.picks],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def print_board(self):
        """Print a formatted draft board to terminal."""
        print("\n" + "=" * 90)
        print(f"{'NBA DRAFT BOARD':^90}")
        print(f"{'Generated: ' + self.generated_at:^90}")
        print("=" * 90)
        print(
            f"{'Pick':<6}{'Team':<5}{'TeamName':<14}{'Player':<22}{'Pos':<6}{'School/Team':<22}{'Score':<10}"
        )
        print("-" * 90)
        for pick in self.picks:
            team = pick.team if pick.team else "--"
            # Extract short team name (e.g. "Wizards" from "Washington Wizards")
            team_short = pick.team_name.split()[-1] if pick.team_name else "--"
            print(
                f"{pick.pick_number:<6}"
                f"{team:<5}"
                f"{team_short:<14}"
                f"{pick.player_name:<22}"
                f"{pick.position:<6}"
                f"{pick.school:<22}"
                f"{pick.consensus_score:<10.3f}"
            )
        print("=" * 90)
        print(f"Sources: {', '.join(self.sources_used)}")
        print()


@dataclass
class AccuracyMetrics:
    """Accuracy metrics from backtesting."""

    exact_match_pct: float = 0.0
    within_3_pct: float = 0.0
    kendall_tau: float = 0.0
    total_picks_compared: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    def print_metrics(self):
        """Print formatted accuracy metrics."""
        print("\n" + "=" * 50)
        print(f"{'BACKTEST ACCURACY METRICS':^50}")
        print("=" * 50)
        print(f"  Total picks compared:  {self.total_picks_compared}")
        print(f"  Exact match:           {self.exact_match_pct:.1f}%")
        print(f"  Within 3 picks:        {self.within_3_pct:.1f}%")
        print(f"  Kendall tau:           {self.kendall_tau:.4f}")
        print("=" * 50)
        print()

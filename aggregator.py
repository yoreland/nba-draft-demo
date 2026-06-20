"""Weighted Consensus Aggregation Engine for NBA Draft predictions."""

import json
import math
import logging
import os
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict

from models import PlayerPrediction, DraftBoard, DraftPick
from config import SOURCE_WEIGHTS, TIME_DECAY_LAMBDA, CURRENT_DATE, TOP_PICKS

logger = logging.getLogger(__name__)

# Path to NBA teams data file
NBA_TEAMS_FILE = os.path.join(os.path.dirname(__file__), "data", "nba_teams.json")

# Path to manual news overrides file
MANUAL_OVERRIDES_FILE = os.path.join(
    os.path.dirname(__file__), "data", "manual_overrides.json"
)


def load_nba_teams() -> Dict[str, Dict]:
    """Load NBA teams mapping from data file.

    Returns dict mapping team abbreviation to {name, espn_slug}.
    """
    try:
        with open(NBA_TEAMS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load NBA teams data: {e}")
        return {}


def load_manual_overrides(path: str = MANUAL_OVERRIDES_FILE) -> List[Dict]:
    """Load the persistent manual news overrides.

    Returns the list of override entries. Each entry has at minimum
    ``player_name`` and ``force_pick``; ``reason`` and ``date`` are optional.
    Missing or malformed files yield an empty list (overrides are optional).
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("overrides", [])
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Could not load manual overrides: {e}")
        return []


def apply_manual_overrides(
    board: DraftBoard,
    team_order: Dict[int, str] = None,
    overrides: List[Dict] = None,
) -> List[Dict]:
    """Apply manual news overrides to a consensus draft board, in place.

    For each override the named player is forced to the ``force_pick`` slot
    (matched fuzzily against the board). All other players keep their relative
    consensus order and fill the remaining slots. After reordering, pick numbers
    are re-sequenced and team assignments are re-mapped to follow the new slots
    (team allocation follows the pick position, not the player).

    Returns the list of overrides that were actually applied, in pick order, so
    callers can report what changed.
    """
    if overrides is None:
        overrides = load_manual_overrides()
    if not overrides or not board.picks:
        return []

    picks = list(board.picks)
    n = len(picks)

    # Resolve each override to a concrete pick via fuzzy name matching.
    forced: Dict[int, Tuple[DraftPick, Dict]] = {}  # force_pick (1-based) -> (pick, override)
    used_ids = set()
    for ov in overrides:
        name = ov.get("player_name")
        force_pick = ov.get("force_pick")
        if not name or not force_pick:
            continue
        if not (1 <= force_pick <= n):
            logger.warning(
                f"Manual override for '{name}' has out-of-range force_pick "
                f"{force_pick} (board has {n} picks); skipping."
            )
            continue
        if force_pick in forced:
            logger.warning(
                f"Manual override force_pick {force_pick} already assigned; "
                f"skipping duplicate for '{name}'."
            )
            continue

        match = None
        for p in picks:
            if id(p) in used_ids:
                continue
            if fuzzy_match(p.player_name, name):
                match = p
                break
        if match is None:
            logger.warning(
                f"Manual override player '{name}' not found on the board; skipping."
            )
            continue

        forced[force_pick] = (match, ov)
        used_ids.add(id(match))

    if not forced:
        return []

    # Players not pinned by an override keep their original consensus order.
    remaining = [p for p in picks if id(p) not in used_ids]

    new_order: List[DraftPick] = [None] * n
    for force_pick, (pick, _ov) in forced.items():
        new_order[force_pick - 1] = pick
    fill = iter(remaining)
    for i in range(n):
        if new_order[i] is None:
            new_order[i] = next(fill)

    # Re-sequence pick numbers and re-map teams to follow the new slots.
    nba_teams = load_nba_teams()
    for idx, pick in enumerate(new_order, start=1):
        pick.pick_number = idx
        team_abbr = ""
        team_name = ""
        if team_order and idx in team_order:
            team_abbr = team_order[idx]
            team_name = nba_teams.get(team_abbr, {}).get("name", "")
        pick.team = team_abbr
        pick.team_name = team_name

    board.picks = new_order

    # Report applied overrides in final pick order.
    applied = [ov for _fp, (_pick, ov) in sorted(forced.items())]
    return applied


def normalize_name(name: str) -> str:
    """Normalize a player name for matching across sources.

    Handles common variations:
    - Case differences
    - Jr./Sr./III suffixes
    - Extra whitespace
    - Unicode accents
    - Common nickname variations
    """
    if not name:
        return ""

    # Lowercase and strip
    n = name.lower().strip()

    # Remove/normalize unicode accents
    import unicodedata
    n = unicodedata.normalize("NFKD", n)
    n = "".join(c for c in n if not unicodedata.combining(c))

    # Remove common suffixes
    for suffix in [" jr.", " jr", " sr.", " sr", " iii", " ii", " iv"]:
        if n.endswith(suffix):
            n = n[: -len(suffix)]

    # Remove punctuation
    n = n.replace(".", "").replace("'", "").replace("-", " ")

    # Collapse whitespace
    n = " ".join(n.split())

    return n


def fuzzy_match(name1: str, name2: str) -> bool:
    """Check if two player names likely refer to the same person.

    Uses normalized names and simple character-level similarity.
    """
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    # Exact match after normalization
    if n1 == n2:
        return True

    # Must have at least 2 parts to do substring/initial matching
    parts1 = n1.split()
    parts2 = n2.split()

    # One contains the other (but only if the contained string is substantial)
    if len(n1) > 5 and len(n2) > 5:
        if n1 in n2 or n2 in n1:
            return True

    # Check last name match + first name match or initial
    if len(parts1) >= 2 and len(parts2) >= 2:
        # Same last name and same first name or first initial
        if parts1[-1] == parts2[-1] and parts1[0][0] == parts2[0][0]:
            # Additional check: first names must be similar, not just same initial
            if parts1[0] == parts2[0] or _similarity_ratio(parts1[0], parts2[0]) > 0.7:
                return True

    # Simple edit distance ratio - must be very high for short names.
    # NOTE: The custom _similarity_ratio uses character-set overlap, not edit distance.
    # This can produce false positives on names with high character overlap but different
    # meaning (e.g., "Cameron Carr" vs "Cameron Carter"). For the 30-player scale of a
    # single draft class this is acceptable, but would need a stricter metric at scale.
    ratio = _similarity_ratio(n1, n2)
    min_len = min(len(n1), len(n2))
    threshold = 0.92 if min_len < 12 else 0.87
    return ratio > threshold


def _similarity_ratio(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings (0-1)."""
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    # Use length of matching characters / average length
    len1, len2 = len(s1), len(s2)
    max_len = max(len1, len2)

    # Count matching characters at same positions
    matches = sum(1 for a, b in zip(s1, s2) if a == b)

    # Also count characters present in both strings
    set1, set2 = set(s1), set(s2)
    common_chars = len(set1 & set2)

    score = (matches / max_len * 0.6) + (common_chars / len(set1 | set2) * 0.4)
    return score


def calculate_time_decay(date_str: str) -> float:
    """Calculate time decay factor for a prediction date.

    More recent predictions get higher weight.
    """
    if not date_str:
        return 0.5  # default for unknown dates

    try:
        pred_date = datetime.strptime(date_str, "%Y-%m-%d")
        days_old = (CURRENT_DATE - pred_date).days
        if days_old < 0:
            days_old = 0
        decay = math.exp(-TIME_DECAY_LAMBDA * days_old)
        return max(decay, 0.1)  # minimum 10% weight
    except ValueError:
        return 0.5


def aggregate_predictions(
    predictions: List[PlayerPrediction],
    team_order: Dict[int, str] = None,
) -> DraftBoard:
    """Aggregate predictions from multiple sources into a consensus draft board.

    Algorithm:
    1. Group predictions by normalized player name
    2. For each player, calculate weighted consensus pick position:
       weighted_pick = sum(pick * source_weight * time_decay * confidence) / sum(weights)
    3. Sort by consensus pick position
    4. Assign NBA teams based on team_order (pick_number -> team abbreviation)
    5. Return top N picks as DraftBoard
    """
    if not predictions:
        logger.warning("No predictions to aggregate")
        return DraftBoard(mode="predict")

    # Load NBA team metadata
    nba_teams = load_nba_teams()

    # Group predictions by normalized player name
    player_groups: Dict[str, List[PlayerPrediction]] = defaultdict(list)
    canonical_names: Dict[str, str] = {}  # normalized -> best display name
    player_info: Dict[str, Dict] = {}  # normalized -> {position, school}

    for pred in predictions:
        norm = normalize_name(pred.name)

        # Check if this matches an existing group
        matched_key = None
        for existing_key in list(player_groups.keys()):
            if fuzzy_match(norm, existing_key):
                matched_key = existing_key
                break

        key = matched_key if matched_key else norm
        player_groups[key].append(pred)

        # Keep the most complete name as canonical
        if key not in canonical_names or len(pred.name) > len(canonical_names[key]):
            canonical_names[key] = pred.name

        # Keep position/school info
        if key not in player_info:
            player_info[key] = {"position": "", "school": ""}
        if pred.position:
            player_info[key]["position"] = pred.position
        if pred.school:
            player_info[key]["school"] = pred.school

    # Calculate weighted consensus for each player
    consensus: List[Tuple[str, float, float]] = []  # (key, weighted_pick, score)
    sources_used = set()

    for key, preds in player_groups.items():
        total_weight = 0.0
        weighted_pick_sum = 0.0

        for pred in preds:
            source_weight = SOURCE_WEIGHTS.get(pred.source, 0.5)
            time_decay = calculate_time_decay(pred.date)
            weight = source_weight * time_decay * pred.confidence
            weighted_pick_sum += pred.projected_pick * weight
            total_weight += weight
            sources_used.add(pred.source)

        if total_weight > 0:
            consensus_pick = weighted_pick_sum / total_weight
            # Score reflects how strong the consensus is (higher = better agreement)
            score = total_weight / len(preds)
            consensus.append((key, consensus_pick, score))

    # Minimum-source warning: if fewer than 2 sources contributed, confidence is degraded
    MIN_SOURCES = 2
    if len(sources_used) < MIN_SOURCES:
        logger.warning(
            f"Only {len(sources_used)} source(s) contributed predictions. "
            f"Consensus confidence is degraded (minimum {MIN_SOURCES} recommended)."
        )
        print(
            f"\n⚠ WARNING: Only {len(sources_used)} source(s) contributed. "
            f"Consensus confidence is degraded."
        )
        # Penalize consensus scores when source diversity is low
        consensus = [
            (key, pick, score * 0.6) for key, pick, score in consensus
        ]

    # Sort by consensus pick position
    consensus.sort(key=lambda x: x[1])

    # Build draft board
    board = DraftBoard(mode="predict", sources_used=sorted(sources_used))

    for i, (key, consensus_pick, score) in enumerate(consensus[:TOP_PICKS], start=1):
        info = player_info.get(key, {})

        # Determine team for this pick position
        team_abbr = ""
        team_name = ""
        if team_order and i in team_order:
            team_abbr = team_order[i]
            team_data = nba_teams.get(team_abbr, {})
            team_name = team_data.get("name", "")

        board.add_pick(
            DraftPick(
                pick_number=i,
                player_name=canonical_names.get(key, key),
                position=info.get("position", ""),
                school=info.get("school", ""),
                consensus_score=round(score, 4),
                team=team_abbr,
                team_name=team_name,
            )
        )

    return board

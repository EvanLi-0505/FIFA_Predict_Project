"""Leakage-free historical feature engineering.

Ported verbatim from the source notebook, PHASE 5.2 (`calculate_team_features`)
and PHASE 5.3 (`generate_historical_features`). The two-step per-date
processing (compute features for every match on a date, THEN update team
history with that date's results) is the core leakage-prevention mechanism
and must not be altered: it guarantees that same-day results never leak into
same-day feature values.
"""

from __future__ import annotations

from collections import defaultdict, deque

import numpy as np
import pandas as pd

from core.config import RECENT_MATCH_WINDOW


def calculate_team_features(history, window_size: int = RECENT_MATCH_WINDOW) -> dict:
    """Calculate a team's pre-match performance features.

    Uses only the team's most recent `window_size` historical matches
    (already-completed matches strictly before the match being featurised).
    """

    recent_matches = list(history)[-window_size:]
    matches_available = len(recent_matches)

    if matches_available == 0:
        return {
            "recent_win_rate": np.nan,
            "recent_draw_rate": np.nan,
            "avg_goals_scored": np.nan,
            "avg_goals_conceded": np.nan,
            "recent_goal_difference": np.nan,
            "matches_available": 0,
        }

    wins = sum(match["result"] == "Win" for match in recent_matches)
    draws = sum(match["result"] == "Draw" for match in recent_matches)

    goals_scored = [match["goals_scored"] for match in recent_matches]
    goals_conceded = [match["goals_conceded"] for match in recent_matches]

    return {
        "recent_win_rate": wins / matches_available,
        "recent_draw_rate": draws / matches_available,
        "avg_goals_scored": np.mean(goals_scored),
        "avg_goals_conceded": np.mean(goals_conceded),
        "recent_goal_difference": np.mean(goals_scored) - np.mean(goals_conceded),
        "matches_available": matches_available,
    }


def generate_historical_features(
    match_data: pd.DataFrame, window_size: int = RECENT_MATCH_WINDOW
) -> pd.DataFrame:
    """Generate leakage-free pre-match historical features for every match.

    Features for all matches on the same calendar date are calculated
    BEFORE any result from that date is added to team history. This
    prevents current-match, future-match, and same-day result leakage.

    Also returns, as a side effect available via `build_team_history_index`,
    the final `team_history` state — but to keep this function's behaviour
    identical to the notebook, that state is not returned here. Use
    `core.prediction.team_state.build_team_latest_state_index` if you need
    the "most recent state per team" for dynamic prediction.
    """

    data = match_data.sort_values("date").reset_index(drop=True).copy()

    team_history = defaultdict(lambda: deque(maxlen=window_size))
    feature_rows = []

    for current_date, daily_matches in data.groupby("date", sort=True):
        daily_updates = []

        # STEP 1: calculate features before adding today's results
        for index, row in daily_matches.iterrows():
            home_team = row["home_team"]
            away_team = row["away_team"]

            home_features = calculate_team_features(
                team_history[home_team], window_size
            )
            away_features = calculate_team_features(
                team_history[away_team], window_size
            )

            feature_rows.append(
                {
                    "index": index,
                    "home_recent_win_rate": home_features["recent_win_rate"],
                    "away_recent_win_rate": away_features["recent_win_rate"],
                    "home_recent_draw_rate": home_features["recent_draw_rate"],
                    "away_recent_draw_rate": away_features["recent_draw_rate"],
                    "home_avg_goals_scored": home_features["avg_goals_scored"],
                    "away_avg_goals_scored": away_features["avg_goals_scored"],
                    "home_avg_goals_conceded": home_features["avg_goals_conceded"],
                    "away_avg_goals_conceded": away_features["avg_goals_conceded"],
                    "home_recent_goal_difference": home_features[
                        "recent_goal_difference"
                    ],
                    "away_recent_goal_difference": away_features[
                        "recent_goal_difference"
                    ],
                    "home_matches_available": home_features["matches_available"],
                    "away_matches_available": away_features["matches_available"],
                }
            )

            if pd.notna(row["home_score"]) and pd.notna(row["away_score"]):
                daily_updates.append(row)

        # STEP 2: add today's completed results only after all of today's
        # features have been calculated
        for row in daily_updates:
            home_team = row["home_team"]
            away_team = row["away_team"]
            home_score = row["home_score"]
            away_score = row["away_score"]

            if home_score > away_score:
                home_result, away_result = "Win", "Loss"
            elif home_score < away_score:
                home_result, away_result = "Loss", "Win"
            else:
                home_result, away_result = "Draw", "Draw"

            team_history[home_team].append(
                {
                    "result": home_result,
                    "goals_scored": home_score,
                    "goals_conceded": away_score,
                }
            )
            team_history[away_team].append(
                {
                    "result": away_result,
                    "goals_scored": away_score,
                    "goals_conceded": home_score,
                }
            )

    feature_df = pd.DataFrame(feature_rows).set_index("index").sort_index()

    result_df = pd.concat([data, feature_df], axis=1)

    return result_df

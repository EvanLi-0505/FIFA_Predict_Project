"""Global constants preserved exactly from the source Colab notebook.

Every value here was taken verbatim from
`IPYNB_colab_code/fifa_world_cup_match_prediction.py`. Do not change any of
these values without explicit approval — they are part of the validated ML
methodology (see Development Prompt.md, Section 2).
"""

# Reproducibility (Phase 1.1 in the source notebook)
RANDOM_STATE = 42

# Historical feature window size (Phase 5.4 / RECENT_MATCH_WINDOW)
RECENT_MATCH_WINDOW = 5

# Chronological train/test split ratio (Phase 7.1)
TRAIN_RATIO = 0.80

# Target classes, in the exact form produced by create_match_result()
CLASS_LABELS = ["Draw", "Home Loss", "Home Win"]

# Required raw dataset columns (results.csv schema)
REQUIRED_RAW_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "tournament",
    "city",
    "country",
    "neutral",
]

# Tournament category labels produced by categorize_tournament()
TOURNAMENT_CATEGORIES = [
    "Friendly",
    "Other Competitive",
    "World Cup",
    "World Cup Qualification",
]

# Feature schema versions, stamped into every trained model's metadata.
# feature_v1: the notebook's 23 predictors, unchanged (notebook parity).
# feature_v2: feature_v1 + pre-match Elo ratings (core/feature_engineering/elo.py),
#             added in v2.1.0 — not part of the original notebook methodology.
ORIGINAL_FEATURE_VERSION = "feature_v1"
ELO_FEATURE_VERSION = "feature_v2"
SUPPORTED_FEATURE_VERSIONS = (ORIGINAL_FEATURE_VERSION, ELO_FEATURE_VERSION)
DEFAULT_FEATURE_VERSION = ELO_FEATURE_VERSION

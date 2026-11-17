"""RR EDGE Supervised Machine Learning Intelligence Package."""

from .config import (
    BATTER_FEATURE_COLS,
    BOWLER_FEATURE_COLS,
    TRAIN_SEASONS,
    VAL_SEASONS,
    TEST_SEASONS,
    RANDOM_SEED,
)
def run_ml_pipeline(*args, **kwargs):
    """Lazy-load pipeline to avoid importing heavy training libraries (xgboost) during web serving."""
    from .pipeline import run_ml_pipeline as _run
    return _run(*args, **kwargs)

__all__ = [
    "BATTER_FEATURE_COLS",
    "BOWLER_FEATURE_COLS",
    "TRAIN_SEASONS",
    "VAL_SEASONS",
    "TEST_SEASONS",
    "RANDOM_SEED",
    "run_ml_pipeline",
]


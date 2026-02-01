"""Analytics module for workout data analysis."""

from gymup_tracker.analytics.metrics import (
    calculate_1rm,
    calculate_tonnage,
    calculate_volume,
)
from gymup_tracker.analytics.progression import (
    analyze_progression,
    detect_plateau,
    calculate_trend,
)

__all__ = [
    "calculate_1rm",
    "calculate_tonnage",
    "calculate_volume",
    "analyze_progression",
    "detect_plateau",
    "calculate_trend",
]

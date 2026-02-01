"""Progression analysis for workout data."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from gymup_tracker.analytics.metrics import calculate_1rm, estimate_best_1rm_from_history


@dataclass
class ProgressionAnalysis:
    """Results of progression analysis."""

    trend: str  # "improving", "plateau", "declining"
    slope: float  # Weight change per week
    r_squared: float  # How well the trend fits
    weeks_analyzed: int
    start_weight: float
    current_weight: float
    weight_change: float
    weight_change_percent: float
    plateau_weeks: int  # Number of weeks without progress
    pr_count: int  # Personal records in the period
    estimated_1rm: float
    recommendation: str


def calculate_trend(
    dates: list[datetime], weights: list[float]
) -> tuple[float, float, float]:
    """
    Calculate linear trend from weight data.

    Args:
        dates: List of workout dates
        weights: List of weights corresponding to dates

    Returns:
        Tuple of (slope per week, intercept, r_squared)
    """
    if len(dates) < 2 or len(weights) < 2:
        return 0.0, weights[0] if weights else 0.0, 0.0

    # Convert dates to weeks from start
    start_date = min(dates)
    x = np.array([(d - start_date).days / 7 for d in dates])
    y = np.array(weights)

    # Linear regression
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x * x)

    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return 0.0, np.mean(y), 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    # Calculate R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return float(slope), float(intercept), float(max(0, r_squared))


def detect_plateau(
    history: list[dict], threshold_weeks: int = 2, tolerance_percent: float = 2.5
) -> tuple[bool, int]:
    """
    Detect if exercise is in a plateau.

    Args:
        history: Workout history with dates and sets
        threshold_weeks: Minimum weeks without progress to consider plateau
        tolerance_percent: Percentage variance allowed within plateau

    Returns:
        Tuple of (is_plateau, weeks_in_plateau)
    """
    if len(history) < 2:
        return False, 0

    # Get max weight from each workout
    workout_maxes = []
    for workout in history:
        max_weight = max(
            (s.get("weight", 0) or 0 for s in workout.get("sets", [])),
            default=0,
        )
        if max_weight > 0 and workout.get("date"):
            workout_maxes.append((workout["date"], max_weight))

    if len(workout_maxes) < 2:
        return False, 0

    # Sort by date
    workout_maxes.sort(key=lambda x: x[0])

    # Check recent workouts for plateau
    recent_weights = [w for _, w in workout_maxes[-8:]]  # Last 8 workouts
    if not recent_weights:
        return False, 0

    max_recent = max(recent_weights)
    min_recent = min(recent_weights)

    # Calculate percentage variance
    if max_recent > 0:
        variance_percent = ((max_recent - min_recent) / max_recent) * 100
    else:
        variance_percent = 0

    # Check if weights are within tolerance
    is_plateau = variance_percent <= tolerance_percent and len(recent_weights) >= 3

    # Count weeks in plateau
    if is_plateau:
        # Calculate weeks from oldest to newest plateau workout
        first_plateau = workout_maxes[-len(recent_weights)][0]
        last_workout = workout_maxes[-1][0]
        weeks_in_plateau = max(1, (last_workout - first_plateau).days // 7)
    else:
        weeks_in_plateau = 0

    return is_plateau and weeks_in_plateau >= threshold_weeks, weeks_in_plateau


def analyze_progression(history: list[dict], weeks: int = 12) -> ProgressionAnalysis:
    """
    Analyze exercise progression over time.

    Args:
        history: Workout history from QueryService.get_exercise_history()
        weeks: Number of weeks to analyze

    Returns:
        ProgressionAnalysis with trend information
    """
    if not history:
        return ProgressionAnalysis(
            trend="insufficient_data",
            slope=0,
            r_squared=0,
            weeks_analyzed=0,
            start_weight=0,
            current_weight=0,
            weight_change=0,
            weight_change_percent=0,
            plateau_weeks=0,
            pr_count=0,
            estimated_1rm=0,
            recommendation="Need more workout data for analysis.",
        )

    # Extract dates and max weights
    dates = []
    max_weights = []
    all_time_max = 0
    pr_count = 0

    for workout in history:
        if not workout.get("date"):
            continue

        sets = workout.get("sets", [])
        max_weight = max((s.get("weight", 0) or 0 for s in sets), default=0)

        if max_weight > 0:
            dates.append(workout["date"])
            max_weights.append(max_weight)

            # Count PRs
            if max_weight > all_time_max:
                all_time_max = max_weight
                pr_count += 1

    if len(dates) < 2:
        return ProgressionAnalysis(
            trend="insufficient_data",
            slope=0,
            r_squared=0,
            weeks_analyzed=0,
            start_weight=max_weights[0] if max_weights else 0,
            current_weight=max_weights[0] if max_weights else 0,
            weight_change=0,
            weight_change_percent=0,
            plateau_weeks=0,
            pr_count=pr_count,
            estimated_1rm=estimate_best_1rm_from_history(history),
            recommendation="Need more workouts for trend analysis.",
        )

    # Calculate trend
    slope, intercept, r_squared = calculate_trend(dates, max_weights)

    # Calculate metrics
    start_weight = max_weights[0]
    current_weight = max_weights[-1]
    weight_change = current_weight - start_weight
    weight_change_percent = (weight_change / start_weight * 100) if start_weight > 0 else 0

    weeks_analyzed = max(1, (dates[-1] - dates[0]).days // 7)

    # Detect plateau
    is_plateau, plateau_weeks = detect_plateau(history)

    # Determine trend
    if is_plateau:
        trend = "plateau"
    elif slope > 0.5:  # More than 0.5kg/week improvement
        trend = "improving"
    elif slope < -0.5:  # More than 0.5kg/week decline
        trend = "declining"
    else:
        trend = "stable"

    # Generate recommendation
    estimated_1rm = estimate_best_1rm_from_history(history)

    if trend == "improving":
        recommendation = f"Strong progress! Continue current approach. Consider a small weight increase."
    elif trend == "plateau":
        recommendation = f"Plateau detected ({plateau_weeks} weeks). Consider: varying rep ranges, increasing volume, or taking a deload week."
    elif trend == "declining":
        recommendation = "Performance declining. Check recovery, sleep, and nutrition. Consider a deload."
    else:
        recommendation = "Stable performance. Ready for progressive overload when you feel prepared."

    return ProgressionAnalysis(
        trend=trend,
        slope=round(slope, 2),
        r_squared=round(r_squared, 3),
        weeks_analyzed=weeks_analyzed,
        start_weight=start_weight,
        current_weight=current_weight,
        weight_change=round(weight_change, 1),
        weight_change_percent=round(weight_change_percent, 1),
        plateau_weeks=plateau_weeks,
        pr_count=pr_count,
        estimated_1rm=round(estimated_1rm, 1),
        recommendation=recommendation,
    )


def suggest_next_weight(
    history: list[dict],
    progression_rate: float = 0.025,  # 2.5% default
    conservative: bool = True,
) -> dict:
    """
    Suggest weight for next workout based on history.

    Args:
        history: Workout history
        progression_rate: Target weekly progression rate
        conservative: Use conservative progression

    Returns:
        Dict with suggested weight and reasoning
    """
    if not history:
        return {
            "suggested_weight": None,
            "confidence": "low",
            "reasoning": "No workout history available.",
        }

    # Get recent performance
    recent = history[-3:] if len(history) >= 3 else history
    analysis = analyze_progression(history)

    # Get the most recent successful sets
    last_workout = history[-1]
    last_sets = last_workout.get("sets", [])

    if not last_sets:
        return {
            "suggested_weight": None,
            "confidence": "low",
            "reasoning": "No set data in recent workout.",
        }

    last_weight = max(s.get("weight", 0) or 0 for s in last_sets)
    last_reps = [s.get("reps", 0) or 0 for s in last_sets if s.get("weight") == last_weight]
    avg_reps = sum(last_reps) / len(last_reps) if last_reps else 0

    # Decision logic
    if analysis.trend == "plateau":
        # Try to break plateau with small increase
        suggested = last_weight + 2.5
        confidence = "medium"
        reasoning = f"Plateau detected. Small 2.5kg increase to test new weight. Target same reps ({int(avg_reps)})."
    elif analysis.trend == "declining":
        # Maintain or slightly reduce
        suggested = last_weight
        confidence = "high"
        reasoning = "Performance declining. Maintain current weight and focus on form and recovery."
    elif avg_reps >= 10:
        # High reps = ready for increase
        increase = 5 if not conservative else 2.5
        suggested = last_weight + increase
        confidence = "high"
        reasoning = f"Excellent rep performance ({int(avg_reps)} reps). Ready for {increase}kg increase."
    elif avg_reps >= 8:
        # Good reps = small increase
        suggested = last_weight + 2.5
        confidence = "high"
        reasoning = f"Solid performance ({int(avg_reps)} reps). Suggest 2.5kg increase."
    elif avg_reps >= 6:
        # Moderate reps = maintain
        suggested = last_weight
        confidence = "high"
        reasoning = f"Building strength at current weight ({int(avg_reps)} reps). Maintain and aim for more reps."
    else:
        # Low reps = consider reducing
        suggested = last_weight - 2.5 if last_weight > 20 else last_weight
        confidence = "medium"
        reasoning = f"Low rep performance ({int(avg_reps)} reps). Consider maintaining or small reduction for better form."

    return {
        "suggested_weight": round(suggested, 1),
        "last_weight": last_weight,
        "last_avg_reps": round(avg_reps, 1),
        "confidence": confidence,
        "reasoning": reasoning,
        "estimated_1rm": analysis.estimated_1rm,
        "trend": analysis.trend,
    }

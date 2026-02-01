"""Metrics calculations for workout analysis."""

from typing import Optional


def calculate_1rm(weight: float, reps: int, formula: str = "epley") -> float:
    """
    Calculate estimated 1 rep max.

    Args:
        weight: Weight used
        reps: Number of reps performed
        formula: Formula to use ("epley", "brzycki", "lander")

    Returns:
        Estimated 1RM
    """
    if reps <= 0 or weight <= 0:
        return 0.0

    if reps == 1:
        return weight

    if formula == "epley":
        # Epley formula: weight * (1 + reps/30)
        return weight * (1 + reps / 30)
    elif formula == "brzycki":
        # Brzycki formula: weight * (36 / (37 - reps))
        if reps >= 37:
            return weight * 2  # Cap at very high reps
        return weight * (36 / (37 - reps))
    elif formula == "lander":
        # Lander formula: (100 * weight) / (101.3 - 2.67123 * reps)
        denominator = 101.3 - 2.67123 * reps
        if denominator <= 0:
            return weight * 2
        return (100 * weight) / denominator
    else:
        # Default to Epley
        return weight * (1 + reps / 30)


def calculate_tonnage(sets: list[dict]) -> float:
    """
    Calculate total tonnage (volume load) from sets.

    Args:
        sets: List of sets with 'weight' and 'reps' keys

    Returns:
        Total tonnage (weight * reps for all sets)
    """
    total = 0.0
    for s in sets:
        weight = s.get("weight", 0) or 0
        reps = s.get("reps", 0) or 0
        total += weight * reps
    return total


def calculate_volume(sets: list[dict]) -> dict:
    """
    Calculate volume metrics from sets.

    Args:
        sets: List of sets with 'weight' and 'reps' keys

    Returns:
        Dict with total_sets, total_reps, tonnage, avg_weight, avg_reps
    """
    if not sets:
        return {
            "total_sets": 0,
            "total_reps": 0,
            "tonnage": 0,
            "avg_weight": 0,
            "avg_reps": 0,
        }

    total_reps = sum(s.get("reps", 0) or 0 for s in sets)
    weights = [s.get("weight", 0) or 0 for s in sets if s.get("weight")]
    reps_list = [s.get("reps", 0) or 0 for s in sets if s.get("reps")]

    return {
        "total_sets": len(sets),
        "total_reps": total_reps,
        "tonnage": calculate_tonnage(sets),
        "avg_weight": sum(weights) / len(weights) if weights else 0,
        "avg_reps": sum(reps_list) / len(reps_list) if reps_list else 0,
    }


def calculate_intensity(weight: float, one_rm: float) -> float:
    """
    Calculate intensity as percentage of 1RM.

    Args:
        weight: Weight used
        one_rm: Estimated or known 1RM

    Returns:
        Intensity as percentage (0-100)
    """
    if one_rm <= 0:
        return 0.0
    return min(100.0, (weight / one_rm) * 100)


def estimate_best_1rm_from_history(history: list[dict]) -> float:
    """
    Estimate best 1RM from workout history.

    Args:
        history: List of workout dicts with 'sets' containing weight/reps

    Returns:
        Best estimated 1RM across all sets
    """
    best = 0.0
    for workout in history:
        for s in workout.get("sets", []):
            weight = s.get("weight", 0) or 0
            reps = s.get("reps", 0) or 0
            if weight > 0 and reps > 0:
                estimated = calculate_1rm(weight, reps)
                best = max(best, estimated)
    return best


def calculate_avg_rpe(sets: list[dict]) -> Optional[float]:
    """
    Calculate average RPE from sets.

    Args:
        sets: List of sets with optional 'rpe' key

    Returns:
        Average RPE or None if no RPE data
    """
    rpe_values = [s.get("rpe") for s in sets if s.get("rpe") is not None]
    if not rpe_values:
        return None
    return sum(rpe_values) / len(rpe_values)

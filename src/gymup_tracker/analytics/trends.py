"""Trend analysis and pattern detection."""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from gymup_tracker.analytics.metrics import calculate_1rm


def calculate_weekly_volume(history: list[dict]) -> list[dict]:
    """
    Calculate weekly volume from workout history.

    Args:
        history: Workout history with dates and sets

    Returns:
        List of weekly volume summaries
    """
    if not history:
        return []

    # Group by week
    weeks = {}
    for workout in history:
        date = workout.get("date")
        if not date:
            continue

        # Get week start (Monday)
        week_start = date - timedelta(days=date.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        if week_key not in weeks:
            weeks[week_key] = {
                "week_start": week_start,
                "workouts": 0,
                "tonnage": 0,
                "sets": 0,
                "reps": 0,
            }

        weeks[week_key]["workouts"] += 1
        weeks[week_key]["tonnage"] += workout.get("tonnage", 0) or 0

        for s in workout.get("sets", []):
            weeks[week_key]["sets"] += 1
            weeks[week_key]["reps"] += s.get("reps", 0) or 0

    return sorted(weeks.values(), key=lambda x: x["week_start"])


def detect_overreaching(history: list[dict], rpe_threshold: float = 8.5) -> dict:
    """
    Detect signs of overreaching from workout history.

    Args:
        history: Workout history with RPE data
        rpe_threshold: Average RPE threshold for concern

    Returns:
        Dict with overreaching assessment
    """
    if len(history) < 3:
        return {
            "is_overreaching": False,
            "confidence": "low",
            "factors": [],
            "recommendation": "Need more data for overreaching assessment.",
        }

    recent = history[-5:]  # Last 5 workouts
    factors = []

    # Check RPE trend
    rpe_values = []
    for workout in recent:
        rpe = workout.get("rpe_avg")
        if rpe:
            rpe_values.append(rpe)

    if rpe_values:
        avg_rpe = sum(rpe_values) / len(rpe_values)
        if avg_rpe >= rpe_threshold:
            factors.append(f"High average RPE ({avg_rpe:.1f})")

        # Check if RPE is increasing
        if len(rpe_values) >= 3:
            if rpe_values[-1] > rpe_values[0] + 1:
                factors.append("RPE trending upward")

    # Check performance decline
    if len(history) >= 4:
        first_half = history[: len(history) // 2]
        second_half = history[len(history) // 2:]

        first_avg = np.mean([
            max((s.get("weight", 0) or 0 for s in w.get("sets", [])), default=0)
            for w in first_half
        ])
        second_avg = np.mean([
            max((s.get("weight", 0) or 0 for s in w.get("sets", [])), default=0)
            for w in second_half
        ])

        if second_avg < first_avg * 0.95:  # 5% decline
            factors.append("Performance declining despite consistent training")

    is_overreaching = len(factors) >= 2

    if is_overreaching:
        recommendation = "Consider a deload week: reduce volume by 40-50% and intensity by 10%."
    elif len(factors) == 1:
        recommendation = "Monitor fatigue levels. One warning sign present."
    else:
        recommendation = "No signs of overreaching. Continue current program."

    return {
        "is_overreaching": is_overreaching,
        "confidence": "high" if len(rpe_values) >= 3 else "medium",
        "factors": factors,
        "recommendation": recommendation,
    }


def calculate_1rm_trajectory(
    history: list[dict], weeks_forward: int = 4
) -> dict:
    """
    Calculate 1RM trajectory and project future values.

    Args:
        history: Workout history
        weeks_forward: Weeks to project forward

    Returns:
        Dict with historical and projected 1RM data
    """
    if len(history) < 2:
        return {
            "historical": [],
            "projected": [],
            "current_1rm": 0,
            "projected_1rm": 0,
            "confidence": "low",
        }

    # Calculate 1RM for each workout
    data_points = []
    for workout in history:
        date = workout.get("date")
        if not date:
            continue

        best_1rm = 0
        for s in workout.get("sets", []):
            weight = s.get("weight", 0) or 0
            reps = s.get("reps", 0) or 0
            if weight > 0 and reps > 0:
                estimated = calculate_1rm(weight, reps)
                best_1rm = max(best_1rm, estimated)

        if best_1rm > 0:
            data_points.append({"date": date, "one_rm": best_1rm})

    if len(data_points) < 2:
        return {
            "historical": data_points,
            "projected": [],
            "current_1rm": data_points[-1]["one_rm"] if data_points else 0,
            "projected_1rm": 0,
            "confidence": "low",
        }

    # Linear regression for projection
    dates = [dp["date"] for dp in data_points]
    one_rms = [dp["one_rm"] for dp in data_points]

    start_date = min(dates)
    x = np.array([(d - start_date).days for d in dates])
    y = np.array(one_rms)

    # Calculate slope
    n = len(x)
    slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x * x) - np.sum(x) ** 2)
    intercept = (np.sum(y) - slope * np.sum(x)) / n

    # R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Project forward
    last_date = max(dates)
    projected = []
    for week in range(1, weeks_forward + 1):
        proj_date = last_date + timedelta(weeks=week)
        days_from_start = (proj_date - start_date).days
        proj_1rm = slope * days_from_start + intercept
        projected.append({
            "date": proj_date,
            "one_rm": round(max(0, proj_1rm), 1),
        })

    return {
        "historical": [{"date": dp["date"], "one_rm": round(dp["one_rm"], 1)} for dp in data_points],
        "projected": projected,
        "current_1rm": round(data_points[-1]["one_rm"], 1),
        "projected_1rm": round(projected[-1]["one_rm"], 1) if projected else 0,
        "weekly_gain": round(slope * 7, 2),  # Convert daily to weekly
        "r_squared": round(max(0, r_squared), 3),
        "confidence": "high" if r_squared > 0.7 else "medium" if r_squared > 0.4 else "low",
    }


def find_personal_records(history: list[dict]) -> list[dict]:
    """
    Find personal records from workout history.

    Args:
        history: Workout history

    Returns:
        List of PR achievements with dates
    """
    prs = []
    max_weight_seen = 0
    max_1rm_seen = 0

    for workout in sorted(history, key=lambda x: x.get("date") or datetime.min):
        date = workout.get("date")
        if not date:
            continue

        for s in workout.get("sets", []):
            weight = s.get("weight", 0) or 0
            reps = s.get("reps", 0) or 0

            # Weight PR
            if weight > max_weight_seen and weight > 0:
                prs.append({
                    "type": "weight",
                    "date": date,
                    "weight": weight,
                    "reps": reps,
                    "previous": max_weight_seen,
                })
                max_weight_seen = weight

            # 1RM PR
            if weight > 0 and reps > 0:
                estimated_1rm = calculate_1rm(weight, reps)
                if estimated_1rm > max_1rm_seen:
                    prs.append({
                        "type": "estimated_1rm",
                        "date": date,
                        "weight": weight,
                        "reps": reps,
                        "estimated_1rm": round(estimated_1rm, 1),
                        "previous": round(max_1rm_seen, 1),
                    })
                    max_1rm_seen = estimated_1rm

    return prs

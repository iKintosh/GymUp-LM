"""LLM analysis functions."""

from typing import Optional
from datetime import datetime, timedelta

from gymup_tracker.analytics.progression import analyze_progression, suggest_next_weight
from gymup_tracker.db.constants import get_muscle_name, get_equipment_name
from gymup_tracker.db.queries import datetime_to_ms
from gymup_tracker.llm.client import OllamaClient, get_ollama_status
from gymup_tracker.llm.prompts import (
    SYSTEM_PROMPT,
    ANALYZE_PROGRESSION_TEMPLATE,
    SUGGEST_WEIGHTS_TEMPLATE,
    GENERATE_WORKOUT_PLAN_TEMPLATE,
    TRAINING_SUMMARY_TEMPLATE,
    RECOVERY_ANALYSIS_TEMPLATE,
    format_workout_history,
    format_recent_workouts,
    format_exercises_for_plan,
    add_user_context,
    parse_ai_recommendation,
    get_exercise_type,
    get_rep_range_hint,
)


def analyze_exercise_progression(
    exercise_name: str,
    muscle_group: str,
    equipment: str,
    history: list[dict],
    weeks: int = 8,
    user_context: str = None,
    use_llm: bool = True,
    exercise_stats: dict = None,  # New: comprehensive stats from get_day_exercise_data
) -> dict:
    """
    Analyze exercise progression using rule-based analysis and optionally LLM.

    Args:
        exercise_name: Name of the exercise
        muscle_group: Primary muscle group
        equipment: Equipment used
        history: Workout history from QueryService
        weeks: Number of weeks to analyze
        user_context: Optional user notes
        use_llm: Whether to use LLM for enhanced analysis
        exercise_stats: Comprehensive stats dict (from get_day_exercise_data)

    Returns:
        Dict with analysis results
    """
    # Always run rule-based analysis
    analysis = analyze_progression(history, weeks)

    # Use exercise_stats if provided for more accurate data
    if exercise_stats:
        sessions_count = exercise_stats.get("sessions_count_8w", len(history))
        total_sets = exercise_stats.get("total_sets_8w", 0)
        avg_sets_per_week = exercise_stats.get("avg_sets_per_week", 0)
        pr_weight_8w = exercise_stats.get("pr_weight_8w")
        all_time_pr = exercise_stats.get("all_time_pr")
        weight_change = exercise_stats.get("weight_change", analysis.weight_change)
        weight_change_pct = exercise_stats.get("weight_change_pct", analysis.weight_change_percent)
    else:
        sessions_count = len(history)
        total_sets = sum(len(w.get("sets", [])) for w in history)
        avg_sets_per_week = total_sets / max(weeks, 1) if weeks else 0
        pr_weight_8w = None
        all_time_pr = None
        weight_change = analysis.weight_change
        weight_change_pct = analysis.weight_change_percent

    result = {
        "exercise_name": exercise_name,
        "muscle_group": muscle_group,
        "equipment": equipment,
        "weeks_analyzed": analysis.weeks_analyzed,
        "trend": analysis.trend,
        "slope": analysis.slope,
        "weight_change": weight_change,
        "weight_change_percent": weight_change_pct,
        "plateau_weeks": analysis.plateau_weeks,
        "pr_count": analysis.pr_count,
        "estimated_1rm": analysis.estimated_1rm,
        "sessions_count": sessions_count,
        "total_sets": total_sets,
        "avg_sets_per_week": avg_sets_per_week,
        "pr_weight_8w": pr_weight_8w,
        "all_time_pr": all_time_pr,
        "rule_based_recommendation": analysis.recommendation,
        "llm_analysis": None,
        "llm_available": False,
    }

    if not use_llm:
        return result

    # Check LLM availability
    status = get_ollama_status()
    result["llm_available"] = status["model_ready"]

    if not status["model_ready"]:
        return result

    # Generate LLM analysis
    client = OllamaClient()

    # Calculate min/max weights from history
    all_weights = []
    for w in history:
        for s in w.get("sets", []):
            if s.get("weight"):
                all_weights.append(s["weight"])
    min_weight = min(all_weights) if all_weights else 0
    max_weight = max(all_weights) if all_weights else 0

    # Determine exercise type
    exercise_type = get_exercise_type(muscle_group, equipment)

    prompt = ANALYZE_PROGRESSION_TEMPLATE.format(
        exercise_name=exercise_name,
        exercise_type=exercise_type,
        muscle_group=muscle_group,
        weeks=weeks,
        sessions_count=sessions_count,
        total_sets=total_sets,
        min_weight=min_weight,
        max_weight=max_weight,
        avg_sets_per_week=round(avg_sets_per_week, 1),
        workout_history=format_workout_history(history),
        estimated_1rm=analysis.estimated_1rm or "N/A",
        pr_weight_8w=pr_weight_8w or "N/A",
        all_time_pr=all_time_pr or "N/A",
        trend=analysis.trend,
        weight_change=round(weight_change, 1) if weight_change else 0,
        weight_change_pct=round(weight_change_pct, 1) if weight_change_pct else 0,
        user_context=add_user_context(user_context),
    )

    response = client.generate(prompt, system=SYSTEM_PROMPT)
    result["llm_analysis"] = response.content

    return result


def suggest_next_weights(
    exercise_name: str,
    muscle_group: str,
    history: list[dict],
    user_context: str = None,
    use_llm: bool = True,
    exercise_stats: dict = None,  # New: comprehensive stats from get_day_exercise_data
) -> dict:
    """
    Suggest weights for next workout.

    Args:
        exercise_name: Name of the exercise
        muscle_group: Primary muscle group
        history: Workout history
        user_context: Optional user notes
        use_llm: Whether to use LLM for enhanced suggestion
        exercise_stats: Comprehensive stats dict (from get_day_exercise_data)

    Returns:
        Dict with weight suggestion and reasoning
    """
    # Rule-based suggestion
    suggestion = suggest_next_weight(history)
    analysis = analyze_progression(history)

    # Use exercise_stats if provided for more accurate data
    equipment = exercise_stats.get("equipment", "") if exercise_stats else ""
    exercise_type = get_exercise_type(muscle_group, equipment)

    if exercise_stats:
        weight_change = exercise_stats.get("weight_change", 0)
        weight_change_pct = exercise_stats.get("weight_change_pct", 0)
        sessions_count = exercise_stats.get("sessions_count_8w", len(history))
    else:
        weight_change = analysis.weight_change
        weight_change_pct = analysis.weight_change_percent
        sessions_count = len(history)

    result = {
        "exercise_name": exercise_name,
        "muscle_group": muscle_group,
        "exercise_type": exercise_type,
        "suggested_weight": suggestion["suggested_weight"],
        "last_weight": suggestion.get("last_weight"),
        "last_avg_reps": suggestion.get("last_avg_reps"),
        "confidence": suggestion["confidence"],
        "trend": suggestion.get("trend"),
        "estimated_1rm": suggestion.get("estimated_1rm"),
        "weight_change": weight_change,
        "weight_change_pct": weight_change_pct,
        "sessions_count": sessions_count,
        "rule_based_reasoning": suggestion["reasoning"],
        "llm_suggestion": None,
        "llm_available": False,
    }

    if not use_llm:
        return result

    # Check LLM availability
    status = get_ollama_status()
    result["llm_available"] = status["model_ready"]

    if not status["model_ready"]:
        return result

    # Generate LLM suggestion
    client = OllamaClient()

    # Calculate min/max weights from history
    all_weights = []
    for w in history:
        for s in w.get("sets", []):
            if s.get("weight"):
                all_weights.append(s["weight"])
    min_weight = min(all_weights) if all_weights else 0
    max_weight = max(all_weights) if all_weights else 0

    # Get rep range hint for exercise type
    rep_range_hint = get_rep_range_hint(exercise_type)

    prompt = SUGGEST_WEIGHTS_TEMPLATE.format(
        exercise_name=exercise_name,
        muscle_group=muscle_group,
        exercise_type=exercise_type,
        rep_range_hint=rep_range_hint,
        min_weight=min_weight,
        max_weight=max_weight,
        recent_workouts=format_recent_workouts(history, limit=3),
        last_weight=suggestion.get("last_weight") or "N/A",
        last_avg_reps=suggestion.get("last_avg_reps") or "N/A",
        estimated_1rm=analysis.estimated_1rm or "N/A",
        trend=analysis.trend,
        weight_change=round(weight_change, 1) if weight_change else 0,
        weight_change_pct=round(weight_change_pct, 1) if weight_change_pct else 0,
        sessions_count=sessions_count,
        user_context=add_user_context(user_context),
    )

    response = client.generate(prompt, system=SYSTEM_PROMPT)

    # Parse AI recommendation into structured format
    parsed = parse_ai_recommendation(response.content)

    result["llm_suggestion_raw"] = response.content
    result["ai_weight"] = parsed.get("weight")
    result["ai_reps"] = parsed.get("reps")
    result["ai_sets"] = parsed.get("sets")
    result["ai_short_answer"] = parsed.get("short_answer")
    result["ai_reasoning"] = parsed.get("reasoning")
    result["parsing_failed"] = parsed.get("parsing_failed", False)

    return result


def generate_training_summary(
    db_path: str,
    weeks: int = 4,
    use_llm: bool = True,
) -> dict:
    """
    Generate AI summary of training over the past N weeks with detailed exercise data.

    Args:
        db_path: Path to database
        weeks: Number of weeks to summarize (default 4)
        use_llm: Whether to use LLM

    Returns:
        Dict with training summary
    """
    from gymup_tracker.db import QueryService

    query = QueryService(db_path)

    # Get training stats
    stats = query.get_overview_stats()

    result = {
        "summary": None,
        "llm_available": False,
    }

    if not use_llm:
        return result

    # Check LLM availability
    status = get_ollama_status()
    result["llm_available"] = status["model_ready"]

    if not status["model_ready"]:
        return result

    # Get detailed exercise performance data (last 4 weeks only)
    cutoff = datetime.now() - timedelta(weeks=weeks)
    cutoff_ms = datetime_to_ms(cutoff)

    used_exercises = query.get_used_exercises()
    exercise_data = []

    for exercise_template in used_exercises[:20]:  # Check top 20 exercises
        history = query.get_exercise_history(exercise_template.id, weeks=weeks)
        if not history:
            continue  # Skip if no history in this period

        # Get proper display name
        if exercise_template.name:
            exercise_name = exercise_template.name.strip()
        else:
            muscle = get_muscle_name(exercise_template.mainMuscleWorked)
            equipment = get_equipment_name(exercise_template.equipment)
            exercise_name = f"{muscle} ({equipment})"

        # Calculate stats for this exercise
        max_weight = 0
        first_weight = 0
        last_weight = 0
        weights = []
        workouts_count = len(history)
        total_reps = 0
        total_sets = 0

        for i, workout in enumerate(history):
            sets = workout.get("sets", [])
            for s in sets:
                # Skip warm-up sets (rpe/hard_sense <= 1)
                rpe = s.get("rpe")
                if rpe is not None and rpe == 1:
                    continue

                w = s.get("weight", 0)
                r = s.get("reps", 0)
                if w:
                    w = round(w, 1)  # Round to avoid floating point issues
                    weights.append(w)
                    max_weight = max(max_weight, w)
                    total_reps += r
                    total_sets += 1
                    if first_weight == 0:
                        first_weight = w
                    last_weight = w

        if not weights:
            continue

        avg_weight = sum(weights) / len(weights)
        avg_reps = total_reps / len(weights) if weights else 0
        avg_sets_per_session = total_sets / workouts_count if workouts_count > 0 else 0

        # Calculate trend
        weight_change = last_weight - first_weight
        weight_change_pct = (weight_change / first_weight * 100) if first_weight > 0 else 0

        # Determine status
        if weight_change_pct > 5:
            ex_status = "improving"
        elif weight_change_pct < -5:
            ex_status = "declining"
        elif abs(weight_change_pct) <= 2.5:
            ex_status = "plateau"
        else:
            ex_status = "stable"

        exercise_data.append({
            "name": exercise_name,
            "muscle_group": get_muscle_name(exercise_template.mainMuscleWorked),
            "workouts": workouts_count,
            "total_sets": total_sets,
            "avg_sets_per_session": round(avg_sets_per_session, 1),
            "pr_weight": max_weight,
            "first_weight": first_weight,
            "last_weight": last_weight,
            "weight_change": round(weight_change, 1),
            "weight_change_pct": round(weight_change_pct, 1),
            "avg_weight": round(avg_weight, 1),
            "avg_reps": round(avg_reps, 1),
            "status": ex_status,
        })

    # Format training stats
    avg_workouts_per_week = round(stats['month_trainings'] / 4, 1) if stats['month_trainings'] > 0 else 0

    training_stats_str = f"""
**Overall Stats (Last 30 Days):**
- Total workouts this month: {stats['month_trainings']}
- Total volume this month: {stats['month_tonnage']:,.0f} kg
- Average workouts per week: {avg_workouts_per_week} sessions/week

**This Week:**
- Workouts: {stats['week_trainings']}
- Volume: {stats['week_tonnage']:,.0f} kg

**All-time Stats:**
- Total workouts: {stats['total_trainings']}
- Total volume: {stats['total_tonnage']:,.0f} kg
"""

    # Format exercise performance with trends
    improving = [ex for ex in exercise_data if ex['status'] == 'improving']
    declining = [ex for ex in exercise_data if ex['status'] == 'declining']
    plateau = [ex for ex in exercise_data if ex['status'] == 'plateau']

    exercise_str = ""

    if improving:
        exercise_str += "\n**Improving Exercises:**\n" + "\n".join([
            f"- **{ex['name']}**: {ex['first_weight']}kg → {ex['last_weight']}kg ({ex['weight_change_pct']:+.1f}%) | PR: {ex['pr_weight']}kg | {ex['workouts']} sessions"
            for ex in improving
        ])

    if plateau:
        exercise_str += "\n\n**Plateau/Stable:**\n" + "\n".join([
            f"- **{ex['name']}**: {ex['last_weight']}kg | PR: {ex['pr_weight']}kg | {ex['workouts']} sessions"
            for ex in plateau
        ])

    if declining:
        exercise_str += "\n\n**Declining:**\n" + "\n".join([
            f"- **{ex['name']}**: {ex['first_weight']}kg → {ex['last_weight']}kg ({ex['weight_change_pct']:+.1f}%) | {ex['workouts']} sessions"
            for ex in declining
        ])

    client = OllamaClient()
    prompt = TRAINING_SUMMARY_TEMPLATE.format(
        weeks=weeks,
        training_stats=training_stats_str,
        recent_workouts=exercise_str,
    )

    response = client.generate(prompt, system=SYSTEM_PROMPT)
    result["summary"] = response.content

    return result


def analyze_recovery_status(
    db_path: str,
    weeks: int = 4,
    use_llm: bool = True,
) -> dict:
    """
    Analyze recovery and fatigue status from recent training data.

    Args:
        db_path: Path to database
        weeks: Number of weeks to analyze
        use_llm: Whether to use LLM

    Returns:
        Dict with recovery analysis
    """
    from gymup_tracker.db import QueryService

    query = QueryService(db_path)

    # Get recent trainings
    trainings = query.get_all_trainings(limit=20)

    result = {
        "status": None,
        "recommendations": None,
        "llm_available": False,
    }

    if not use_llm:
        return result

    # Check LLM availability
    status = get_ollama_status()
    result["llm_available"] = status["model_ready"]

    if not status["model_ready"]:
        return result

    if not trainings:
        result["status"] = "No training data available"
        return result

    # Format training data for analysis
    training_data_str = "\n".join([
        f"- {t.day.name if t.day else 'Unknown'}: {t.start_datetime.strftime('%b %d')} - "
        f"Volume: {t.tonnage or 0:,.0f}kg, Sets: {t.setsAmount or 'N/A'}, RPE: {t.hard_sense or 'N/A'}"
        for t in trainings[:10]
    ])

    # Calculate RPE trend (comparing first half vs second half of last 6 sessions)
    rpe_values = [t.hard_sense for t in trainings[:6] if t.hard_sense]
    if len(rpe_values) >= 4:
        first_half_rpe = sum(rpe_values[:len(rpe_values)//2]) / (len(rpe_values)//2)
        second_half_rpe = sum(rpe_values[len(rpe_values)//2:]) / (len(rpe_values) - len(rpe_values)//2)
        if second_half_rpe > first_half_rpe + 0.5:
            rpe_trend = f"Increasing ({first_half_rpe:.1f} → {second_half_rpe:.1f})"
        elif second_half_rpe < first_half_rpe - 0.5:
            rpe_trend = f"Decreasing ({first_half_rpe:.1f} → {second_half_rpe:.1f})"
        else:
            rpe_trend = f"Stable (~{sum(rpe_values)/len(rpe_values):.1f})"
    else:
        rpe_trend = "Insufficient data"

    # Calculate volume trend
    volume_values = [t.tonnage or 0 for t in trainings[:6] if t.tonnage]
    if len(volume_values) >= 4:
        first_half_vol = sum(volume_values[:len(volume_values)//2]) / (len(volume_values)//2)
        second_half_vol = sum(volume_values[len(volume_values)//2:]) / (len(volume_values) - len(volume_values)//2)
        vol_change = ((second_half_vol - first_half_vol) / first_half_vol * 100) if first_half_vol > 0 else 0
        if vol_change > 10:
            volume_trend = f"Increasing (+{vol_change:.0f}%)"
        elif vol_change < -10:
            volume_trend = f"Decreasing ({vol_change:.0f}%)"
        else:
            volume_trend = "Stable"
    else:
        volume_trend = "Insufficient data"

    # Calculate weight progression trend
    weight_trend = "See individual exercises"

    # Performance indicators
    performance_str = f"""
- Sessions analyzed: {len(trainings[:10])}
- Avg session volume: {sum(t.tonnage or 0 for t in trainings[:10]) / len(trainings[:10]):,.0f}kg
- Sessions with RPE data: {len(rpe_values)} of {len(trainings[:6])}
"""

    client = OllamaClient()
    prompt = RECOVERY_ANALYSIS_TEMPLATE.format(
        training_data=training_data_str,
        performance_indicators=performance_str,
        rpe_trends=rpe_trend,
        volume_trends=volume_trend,
        weight_trends=weight_trend,
    )

    response = client.generate(prompt, system=SYSTEM_PROMPT)
    result["status"] = response.content

    return result


def generate_workout_plan(
    day_name: str,
    program_name: str,
    exercises: list[dict],
    last_session: dict = None,
    training_context: dict = None,
    user_context: str = None,
    use_llm: bool = True,
) -> dict:
    """
    Generate a workout plan for a training day.

    Args:
        day_name: Name of the training day
        program_name: Name of the program
        exercises: List of exercises with comprehensive performance data
            (from get_day_exercise_data - includes last_3_sessions, trend, etc.)
        last_session: Last training session data
        training_context: Overall training stats (workouts/week, volume, etc.)
        user_context: Optional user notes
        use_llm: Whether to use LLM

    Returns:
        Dict with workout plan
    """
    result = {
        "day_name": day_name,
        "program_name": program_name,
        "exercises": exercises,
        "plan": None,
        "llm_available": False,
    }

    if not use_llm:
        result["plan"] = "LLM disabled. Enable AI features for workout plan generation."
        return result

    # Check LLM availability
    status = get_ollama_status()
    result["llm_available"] = status["model_ready"]

    if not status["model_ready"]:
        result["plan"] = "Ollama not available. Install Ollama and pull a model to generate workout plans."
        return result

    # Format exercises with comprehensive performance data
    # Use the new format_exercises_for_plan which handles all the new fields
    exercises_detailed = format_exercises_for_plan(exercises)

    # Format last session
    last_session_str = "No previous session data available."
    if last_session:
        lines = []
        for workout in last_session.get("workouts", []):
            name = workout.get("name", "Unknown")
            sets = workout.get("sets", [])
            if sets:
                sets_str = " | ".join(f"{s.get('weight')}kg×{s.get('reps')}" for s in sets)
                volume = sum((s.get('weight', 0) or 0) * (s.get('reps', 0) or 0) for s in sets)
                lines.append(f"- {name}: {sets_str} (vol: {volume:.0f}kg)")
        if lines:
            last_session_str = "\n".join(lines)

    # Generate plan
    client = OllamaClient()

    prompt = GENERATE_WORKOUT_PLAN_TEMPLATE.format(
        day_name=day_name,
        program_name=program_name,
        exercises_detailed=exercises_detailed,
        last_session_summary=last_session_str,
        user_context=add_user_context(user_context),
    )

    response = client.generate(prompt, system=SYSTEM_PROMPT, max_tokens=1500)
    result["plan"] = response.content

    return result

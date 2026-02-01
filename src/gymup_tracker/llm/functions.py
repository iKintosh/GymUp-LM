"""LLM analysis functions."""

from typing import Optional

from gymup_tracker.analytics.progression import analyze_progression, suggest_next_weight
from gymup_tracker.db.constants import get_muscle_name, get_equipment_name
from gymup_tracker.llm.client import OllamaClient, get_ollama_status
from gymup_tracker.llm.prompts import (
    SYSTEM_PROMPT,
    ANALYZE_PROGRESSION_TEMPLATE,
    SUGGEST_WEIGHTS_TEMPLATE,
    GENERATE_WORKOUT_PLAN_TEMPLATE,
    format_workout_history,
    format_recent_workouts,
    format_exercises_for_plan,
    add_user_context,
)


def analyze_exercise_progression(
    exercise_name: str,
    muscle_group: str,
    equipment: str,
    history: list[dict],
    weeks: int = 8,
    user_context: str = None,
    use_llm: bool = True,
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

    Returns:
        Dict with analysis results
    """
    # Always run rule-based analysis
    analysis = analyze_progression(history, weeks)

    result = {
        "exercise_name": exercise_name,
        "muscle_group": muscle_group,
        "equipment": equipment,
        "weeks_analyzed": analysis.weeks_analyzed,
        "trend": analysis.trend,
        "slope": analysis.slope,
        "weight_change": analysis.weight_change,
        "weight_change_percent": analysis.weight_change_percent,
        "plateau_weeks": analysis.plateau_weeks,
        "pr_count": analysis.pr_count,
        "estimated_1rm": analysis.estimated_1rm,
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

    prompt = ANALYZE_PROGRESSION_TEMPLATE.format(
        exercise_name=exercise_name,
        muscle_group=muscle_group,
        equipment=equipment,
        weeks=weeks,
        workout_history=format_workout_history(history),
        estimated_1rm=analysis.estimated_1rm,
        trend=analysis.trend,
        weight_change=analysis.weight_change,
        weight_change_percent=analysis.weight_change_percent,
        plateau_weeks=analysis.plateau_weeks,
        pr_count=analysis.pr_count,
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
) -> dict:
    """
    Suggest weights for next workout.

    Args:
        exercise_name: Name of the exercise
        muscle_group: Primary muscle group
        history: Workout history
        user_context: Optional user notes
        use_llm: Whether to use LLM for enhanced suggestion

    Returns:
        Dict with weight suggestion and reasoning
    """
    # Rule-based suggestion
    suggestion = suggest_next_weight(history)
    analysis = analyze_progression(history)

    result = {
        "exercise_name": exercise_name,
        "muscle_group": muscle_group,
        "suggested_weight": suggestion["suggested_weight"],
        "last_weight": suggestion.get("last_weight"),
        "last_avg_reps": suggestion.get("last_avg_reps"),
        "confidence": suggestion["confidence"],
        "trend": suggestion.get("trend"),
        "estimated_1rm": suggestion.get("estimated_1rm"),
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

    prompt = SUGGEST_WEIGHTS_TEMPLATE.format(
        exercise_name=exercise_name,
        muscle_group=muscle_group,
        recent_workouts=format_recent_workouts(history, limit=3),
        last_weight=suggestion.get("last_weight", "N/A"),
        last_avg_reps=suggestion.get("last_avg_reps", "N/A"),
        estimated_1rm=analysis.estimated_1rm,
        trend=analysis.trend,
        user_context=add_user_context(user_context),
    )

    response = client.generate(prompt, system=SYSTEM_PROMPT)
    result["llm_suggestion"] = response.content

    return result


def generate_workout_plan(
    day_name: str,
    program_name: str,
    exercises: list[dict],
    last_session: dict = None,
    user_context: str = None,
    use_llm: bool = True,
) -> dict:
    """
    Generate a workout plan for a training day.

    Args:
        day_name: Name of the training day
        program_name: Name of the program
        exercises: List of exercises with names and rest times
        last_session: Last training session data
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

    # Format last session
    last_session_str = "No previous session data."
    if last_session:
        lines = []
        for workout in last_session.get("workouts", []):
            name = workout.get("name", "Unknown")
            sets = workout.get("sets", [])
            sets_str = ", ".join(f"{s.get('weight')}kg x {s.get('reps')}" for s in sets)
            lines.append(f"- {name}: {sets_str}")
        if lines:
            last_session_str = "\n".join(lines)

    # Generate plan
    client = OllamaClient()

    prompt = GENERATE_WORKOUT_PLAN_TEMPLATE.format(
        day_name=day_name,
        program_name=program_name,
        exercises=format_exercises_for_plan(exercises),
        last_session=last_session_str,
        user_context=add_user_context(user_context),
    )

    response = client.generate(prompt, system=SYSTEM_PROMPT, max_tokens=1000)
    result["plan"] = response.content

    return result

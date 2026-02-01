"""Prompt templates for LLM analysis."""

SYSTEM_PROMPT = """You are an expert strength & conditioning coach analyzing workout data.
Your role is to provide evidence-based weight progression recommendations.

Key principles:
- Progressive overload: 2.5-5% weight increases when performance is consistent
- Deload consideration: Suggest lighter weights if detecting fatigue patterns
- Exercise specificity: Different progressions for compound vs isolation movements
- Safety first: Conservative recommendations for complex movements
- Individual variability: Account for recent performance trends

Always provide:
1. Clear, actionable recommendations
2. Reasoning based on the data provided
3. Alternative approaches when appropriate
4. Warning signs to watch for

Be concise but thorough. Use bullet points for clarity."""


ANALYZE_PROGRESSION_TEMPLATE = """Analyze the following exercise progression data:

**Exercise**: {exercise_name}
**Muscle Group**: {muscle_group}
**Equipment**: {equipment}
**Analysis Period**: {weeks} weeks

**Recent Workout History**:
{workout_history}

**Current Stats**:
- Estimated 1RM: {estimated_1rm} kg
- Trend: {trend}
- Weight change: {weight_change} kg ({weight_change_percent}%)
- Plateau weeks: {plateau_weeks}
- Personal records in period: {pr_count}

{user_context}

Provide a comprehensive analysis including:
1. Overall assessment of progression
2. Key strengths identified
3. Areas to monitor or improve
4. Specific recommendations for next steps"""


SUGGEST_WEIGHTS_TEMPLATE = """Based on the workout data, suggest the optimal weight for the next session:

**Exercise**: {exercise_name}
**Muscle Group**: {muscle_group}

**Last 3 Workouts**:
{recent_workouts}

**Performance Summary**:
- Last weight used: {last_weight} kg
- Last session average reps: {last_avg_reps}
- Estimated 1RM: {estimated_1rm} kg
- Current trend: {trend}

{user_context}

Provide:
1. Recommended weight for next session
2. Target rep range
3. Detailed reasoning
4. Alternative approach if fatigued
5. Warning signs to watch during the workout"""


GENERATE_WORKOUT_PLAN_TEMPLATE = """Generate a workout plan for the following training day:

**Day Name**: {day_name}
**Program**: {program_name}

**Exercises**:
{exercises}

**Recent Performance** (last session):
{last_session}

{user_context}

Create a detailed workout plan including:
1. Warm-up recommendations
2. Working sets with weights, reps, and rest times for each exercise
3. Notes on exercise execution
4. Total estimated duration
5. Recovery recommendations for after the session"""


def format_workout_history(history: list[dict], limit: int = 5) -> str:
    """Format workout history for prompt injection."""
    if not history:
        return "No workout history available."

    lines = []
    for workout in history[-limit:]:
        date = workout.get("date")
        date_str = date.strftime("%Y-%m-%d") if date else "Unknown date"

        sets = workout.get("sets", [])
        sets_str = ", ".join(
            f"{s.get('weight', 0)}kg x {s.get('reps', 0)}"
            + (f" (RPE {s.get('rpe')})" if s.get('rpe') else "")
            for s in sets
        )

        lines.append(f"- {date_str}: {sets_str}")

    return "\n".join(lines)


def format_recent_workouts(history: list[dict], limit: int = 3) -> str:
    """Format recent workouts with more detail."""
    if not history:
        return "No recent workouts."

    lines = []
    for workout in history[-limit:]:
        date = workout.get("date")
        date_str = date.strftime("%B %d, %Y") if date else "Unknown date"
        lines.append(f"\n**{date_str}**:")

        for i, s in enumerate(workout.get("sets", []), 1):
            weight = s.get("weight", 0)
            reps = s.get("reps", 0)
            rpe = s.get("rpe")
            rpe_str = f", RPE {rpe}" if rpe else ""
            lines.append(f"  Set {i}: {weight}kg x {reps} reps{rpe_str}")

        tonnage = workout.get("tonnage", 0)
        if tonnage:
            lines.append(f"  Total volume: {tonnage}kg")

    return "\n".join(lines)


def format_exercises_for_plan(exercises: list[dict]) -> str:
    """Format exercises for workout plan generation."""
    if not exercises:
        return "No exercises defined."

    lines = []
    for i, ex in enumerate(exercises, 1):
        name = ex.get("name", "Unknown")
        rest = ex.get("rest_time", 0)
        rest_str = f" (Rest: {rest}s)" if rest else ""
        lines.append(f"{i}. {name}{rest_str}")

    return "\n".join(lines)


def add_user_context(context: str = None) -> str:
    """Format optional user context."""
    if not context or not context.strip():
        return ""
    return f"\n**User Notes**: {context.strip()}\n"

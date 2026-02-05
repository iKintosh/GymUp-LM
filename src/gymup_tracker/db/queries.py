"""Data access layer for GymUp database."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload

from gymup_tracker.db.models import (
    Program,
    Day,
    ThExercise,
    Exercise,
    Training,
    Workout,
    Set,
    get_session,
)
from gymup_tracker.db.constants import get_muscle_name, get_equipment_name


def datetime_to_ms(dt: datetime) -> int:
    """Convert datetime to milliseconds timestamp."""
    return int(dt.timestamp() * 1000)


class QueryService:
    """Service for querying workout data."""

    def __init__(self, db_path: Path | str):
        self.db_path = db_path

    def _get_session(self) -> Session:
        return get_session(self.db_path)

    # Program queries
    def get_all_programs(self) -> list[Program]:
        """Get all training programs."""
        with self._get_session() as session:
            return session.query(Program).all()

    def get_program(self, program_id: int) -> Optional[Program]:
        """Get a single program by ID."""
        with self._get_session() as session:
            return session.query(Program).filter(Program.id == program_id).first()

    def get_active_program(self) -> Optional[Program]:
        """Get the currently active program (most recently used)."""
        with self._get_session() as session:
            # Get the program with most recent training
            latest_training = (
                session.query(Training)
                .order_by(desc(Training.startDateTime))
                .first()
            )
            if latest_training and latest_training.day:
                return latest_training.day.program
            # Fallback to first program
            return session.query(Program).first()

    # Day queries
    def get_days_for_program(self, program_id: int) -> list[Day]:
        """Get all days for a program."""
        with self._get_session() as session:
            return (
                session.query(Day)
                .filter(Day.program_id == program_id)
                .order_by(Day.order_num)
                .all()
            )

    def get_day(self, day_id: int) -> Optional[Day]:
        """Get a single day by ID."""
        with self._get_session() as session:
            return session.query(Day).filter(Day.id == day_id).first()

    # Exercise template queries
    def get_all_exercise_templates(self) -> list[ThExercise]:
        """Get all exercise templates."""
        with self._get_session() as session:
            return (
                session.query(ThExercise)
                .filter(ThExercise.archTime == None)  # Not archived
                .order_by(ThExercise.name)
                .all()
            )

    def get_exercise_template(self, th_exercise_id: int) -> Optional[ThExercise]:
        """Get exercise template by ID."""
        with self._get_session() as session:
            return (
                session.query(ThExercise)
                .filter(ThExercise.id == th_exercise_id)
                .first()
            )

    def get_exercises_for_day(self, day_id: int) -> list[dict]:
        """Get all exercises for a day with template data."""
        with self._get_session() as session:
            exercises = (
                session.query(Exercise)
                .options(joinedload(Exercise.template))
                .filter(Exercise.day_id == day_id)
                .order_by(Exercise.order_num)
                .all()
            )

            # Convert to dicts to avoid session detachment issues
            result = []
            for ex in exercises:
                template = ex.template
                if template:
                    # Get display name with fallback for unnamed exercises
                    if template.name:
                        display_name = template.name.strip()
                    else:
                        muscle = get_muscle_name(template.mainMuscleWorked)
                        equipment = get_equipment_name(template.equipment)
                        display_name = f"{muscle} ({equipment})"
                else:
                    display_name = "Unknown Exercise"

                result.append({
                    "id": ex.id,
                    "template_id": ex.th_exercise_id,
                    "template_name": display_name,
                    "rest_time": ex.restTime,
                    "rest_time_after": ex.restTimeAfterExercise,
                    "order": ex.order_num,
                    "is_measure_weight": ex.isMeasureWeight,
                    "is_measure_reps": ex.isMeasureReps,
                })
            return result

    # Training queries
    def get_all_trainings(self, limit: int = 100, performed_only: bool = True) -> list[Training]:
        """Get recent training sessions."""
        with self._get_session() as session:
            query = (
                session.query(Training)
                .options(joinedload(Training.day))
            )
            if performed_only:
                query = query.filter(Training.finishDateTime > 0)
            return (
                query
                .order_by(desc(Training.startDateTime))
                .limit(limit)
                .all()
            )

    def get_trainings_for_day(self, day_id: int, limit: int = 20, performed_only: bool = True) -> list[Training]:
        """Get training sessions for a specific day."""
        with self._get_session() as session:
            query = session.query(Training).filter(Training.day_id == day_id)
            if performed_only:
                query = query.filter(Training.finishDateTime > 0)
            return (
                query
                .order_by(desc(Training.startDateTime))
                .limit(limit)
                .all()
            )

    def get_training(self, training_id: int) -> Optional[Training]:
        """Get a single training session by ID."""
        with self._get_session() as session:
            return (
                session.query(Training)
                .options(
                    joinedload(Training.day),
                    joinedload(Training.workouts).joinedload(Workout.template),
                    joinedload(Training.workouts).joinedload(Workout.sets),
                )
                .filter(Training.id == training_id)
                .first()
            )

    def get_trainings_in_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[Training]:
        """Get trainings within a date range."""
        with self._get_session() as session:
            start_ms = datetime_to_ms(start_date)
            end_ms = datetime_to_ms(end_date)
            return (
                session.query(Training)
                .filter(
                    Training.startDateTime >= start_ms,
                    Training.startDateTime <= end_ms,
                )
                .order_by(desc(Training.startDateTime))
                .all()
            )

    # Workout queries
    def get_workouts_for_training(self, training_id: int) -> list[Workout]:
        """Get all workouts for a training session."""
        with self._get_session() as session:
            return (
                session.query(Workout)
                .options(joinedload(Workout.template))
                .filter(Workout.training_id == training_id)
                .order_by(Workout.order_num)
                .all()
            )

    def get_exercise_history(
        self, th_exercise_id: int, weeks: int = 12, performed_only: bool = True
    ) -> list[dict]:
        """Get workout history for an exercise over the past N weeks."""
        with self._get_session() as session:
            cutoff = datetime.now() - timedelta(weeks=weeks)
            cutoff_ms = datetime_to_ms(cutoff)

            query = (
                session.query(Workout)
                .join(Training)
                .options(joinedload(Workout.training))
                .filter(
                    Workout.th_exercise_id == th_exercise_id,
                    Training.startDateTime >= cutoff_ms,
                )
            )
            if performed_only:
                query = query.filter(Training.finishDateTime > 0)

            workouts = query.order_by(Training.startDateTime).all()

            history = []
            for workout in workouts:
                # Fetch sets separately to avoid eager loading issues
                # Skip warm-up sets (hard_sense <= 1) and round weights
                sets_data = [
                    {
                        "weight": round(s.weight, 1) if s.weight else 0,
                        "reps": int(s.reps) if s.reps else 0,
                        "rpe": s.hard_sense,
                        "order": s.id,
                    }
                    for s in list(workout.sets)
                    if not (s.hard_sense is not None and s.hard_sense == 1)  # Skip warm-ups
                ]

                history.append({
                    "date": workout.training.start_datetime,
                    "sets": sets_data,
                    "tonnage": workout.tonnage,
                    "rpe_avg": workout.hard_sense,
                    "training_id": workout.training_id,
                })

            return history

    # Set queries
    def get_sets_for_workout(self, workout_id: int) -> list[Set]:
        """Get all sets for a workout."""
        with self._get_session() as session:
            return (
                session.query(Set)
                .filter(Set.workout_id == workout_id)
                .all()
            )

    # Aggregate queries
    def get_overview_stats(self) -> dict:
        """Get overall statistics for the dashboard (performed workouts only)."""
        with self._get_session() as session:
            # Only count performed workouts (finishDateTime > 0)
            performed_filter = Training.finishDateTime > 0

            total_trainings = (
                session.query(func.count(Training.id))
                .filter(performed_filter)
                .scalar() or 0
            )
            total_tonnage = (
                session.query(func.sum(Training.tonnage))
                .filter(performed_filter)
                .scalar() or 0
            )
            total_sets = (
                session.query(func.sum(Training.setsAmount))
                .filter(performed_filter)
                .scalar() or 0
            )
            total_reps = (
                session.query(func.sum(Training.repsAmount))
                .filter(performed_filter)
                .scalar() or 0
            )

            # This week stats
            week_ago = datetime.now() - timedelta(days=7)
            week_ago_ms = datetime_to_ms(week_ago)
            week_trainings = (
                session.query(func.count(Training.id))
                .filter(performed_filter, Training.startDateTime >= week_ago_ms)
                .scalar() or 0
            )
            week_tonnage = (
                session.query(func.sum(Training.tonnage))
                .filter(performed_filter, Training.startDateTime >= week_ago_ms)
                .scalar() or 0
            )

            # This month stats
            month_ago = datetime.now() - timedelta(days=30)
            month_ago_ms = datetime_to_ms(month_ago)
            month_trainings = (
                session.query(func.count(Training.id))
                .filter(performed_filter, Training.startDateTime >= month_ago_ms)
                .scalar() or 0
            )
            month_tonnage = (
                session.query(func.sum(Training.tonnage))
                .filter(performed_filter, Training.startDateTime >= month_ago_ms)
                .scalar() or 0
            )

            return {
                "total_trainings": total_trainings,
                "total_tonnage": total_tonnage,
                "total_sets": total_sets,
                "total_reps": int(total_reps) if total_reps else 0,
                "week_trainings": week_trainings,
                "week_tonnage": week_tonnage or 0,
                "month_trainings": month_trainings,
                "month_tonnage": month_tonnage or 0,
            }

    def get_exercise_stats(self, th_exercise_id: int) -> dict:
        """Get statistics for a specific exercise (performed workouts only)."""
        with self._get_session() as session:
            template = (
                session.query(ThExercise)
                .filter(ThExercise.id == th_exercise_id)
                .first()
            )

            if not template:
                return {}

            # Get all performed workouts for this exercise
            workouts = (
                session.query(Workout)
                .join(Training)
                .options(joinedload(Workout.training))
                .filter(
                    Workout.th_exercise_id == th_exercise_id,
                    Training.finishDateTime > 0,
                )
                .all()
            )

            if not workouts:
                return {
                    "name": template.name,
                    "muscle_group": get_muscle_name(template.mainMuscleWorked),
                    "equipment": get_equipment_name(template.equipment),
                    "total_sessions": 0,
                }

            # Calculate stats - fetch sets for each workout
            all_sets = []
            for w in workouts:
                all_sets.extend(list(w.sets))
            max_weight = max((s.weight or 0 for s in all_sets), default=0)
            total_volume = sum(w.tonnage or 0 for w in workouts)

            # Most recent workout
            sorted_workouts = sorted(
                workouts,
                key=lambda w: w.training.startDateTime if w.training and w.training.startDateTime else 0,
                reverse=True,
            )
            last_workout = sorted_workouts[0] if sorted_workouts else None

            last_sets = []
            if last_workout:
                last_sets = [
                    {"weight": s.weight, "reps": int(s.reps) if s.reps else 0}
                    for s in last_workout.sets
                ]

            # Estimate 1RM from best set
            best_1rm = 0
            for s in all_sets:
                if s.weight and s.reps and s.reps > 0:
                    # Epley formula
                    estimated = s.weight * (1 + s.reps / 30)
                    best_1rm = max(best_1rm, estimated)

            return {
                "name": template.name,
                "muscle_group": get_muscle_name(template.mainMuscleWorked),
                "equipment": get_equipment_name(template.equipment),
                "total_sessions": len(workouts),
                "max_weight": max_weight,
                "total_volume": total_volume,
                "estimated_1rm": round(best_1rm, 1),
                "last_workout_date": last_workout.training.start_datetime if last_workout and last_workout.training else None,
                "last_sets": last_sets,
            }

    def get_used_exercises(self) -> list[ThExercise]:
        """Get exercises that have been used in workouts, sorted by frequency (most used first)."""
        with self._get_session() as session:
            # Get exercises with their usage count, sorted by frequency
            exercise_counts = (
                session.query(
                    ThExercise,
                    func.count(Workout.id).label('usage_count')
                )
                .join(Workout, ThExercise.id == Workout.th_exercise_id)
                .group_by(ThExercise.id)
                .order_by(desc(func.count(Workout.id)), ThExercise.name)
                .all()
            )

            # Extract just the exercises (they're tuples of (exercise, count))
            return [ex[0] for ex in exercise_counts]

    def get_muscle_volume_distribution(self, weeks: int = 4) -> dict[str, float]:
        """Get volume distribution by muscle group over past N weeks (performed only)."""
        with self._get_session() as session:
            cutoff = datetime.now() - timedelta(weeks=weeks)
            cutoff_ms = datetime_to_ms(cutoff)

            workouts = (
                session.query(Workout)
                .join(Training)
                .options(joinedload(Workout.template))
                .filter(
                    Training.startDateTime >= cutoff_ms,
                    Training.finishDateTime > 0,
                )
                .all()
            )

            volume_by_muscle = {}
            for workout in workouts:
                if workout.template and workout.template.mainMuscleWorked:
                    muscle = get_muscle_name(workout.template.mainMuscleWorked)
                    volume_by_muscle[muscle] = volume_by_muscle.get(muscle, 0) + (workout.tonnage or 0)

            return volume_by_muscle

    def get_top_exercises_by_volume(self, weeks: int = 4, limit: int = 10) -> list[dict]:
        """Get top exercises by total volume in past N weeks (performed only)."""
        with self._get_session() as session:
            cutoff = datetime.now() - timedelta(weeks=weeks)
            cutoff_ms = datetime_to_ms(cutoff)

            # Query workouts with exercise info and volume, group by exercise
            results = (
                session.query(
                    ThExercise,
                    func.sum(Workout.tonnage).label('total_volume'),
                    func.count(Workout.id).label('session_count')
                )
                .join(Workout, ThExercise.id == Workout.th_exercise_id)
                .join(Training, Workout.training_id == Training.id)
                .filter(
                    Training.startDateTime >= cutoff_ms,
                    Training.finishDateTime > 0,
                )
                .group_by(ThExercise.id)
                .order_by(desc(func.sum(Workout.tonnage)))
                .limit(limit)
                .all()
            )

            return [
                {
                    "name": ex.name,
                    "muscle_group": get_muscle_name(ex.mainMuscleWorked) if ex.mainMuscleWorked else "Unknown",
                    "total_volume": vol or 0,
                    "session_count": count or 0,
                }
                for ex, vol, count in results
            ]

    def get_program_stats(self, program_id: int, weeks: int = 4) -> dict:
        """Get statistics for a specific program (performed workouts only)."""
        with self._get_session() as session:
            # Total stats (all time)
            all_trainings = (
                session.query(Training)
                .join(Day, Training.day_id == Day.id)
                .filter(Day.program_id == program_id, Training.finishDateTime > 0)
                .all()
            )

            total_volume = sum(t.tonnage or 0 for t in all_trainings)
            total_workouts = len(all_trainings)

            # This week/month stats
            cutoff_week = datetime.now() - timedelta(weeks=1)
            cutoff_month = datetime.now() - timedelta(weeks=4)
            cutoff_week_ms = datetime_to_ms(cutoff_week)
            cutoff_month_ms = datetime_to_ms(cutoff_month)

            week_trainings = [
                t for t in all_trainings
                if t.startDateTime and t.startDateTime >= cutoff_week_ms
            ]
            week_volume = sum(t.tonnage or 0 for t in week_trainings)

            month_trainings = [
                t for t in all_trainings
                if t.startDateTime and t.startDateTime >= cutoff_month_ms
            ]
            month_volume = sum(t.tonnage or 0 for t in month_trainings)

            # Get all days in program
            days = session.query(Day).filter(Day.program_id == program_id).order_by(Day.order_num).all()
            day_count = len(days)

            # Get last training date
            last_training = max(
                (t for t in all_trainings if t.start_datetime),
                key=lambda t: t.start_datetime,
                default=None
            )

            return {
                "program_id": program_id,
                "total_workouts": total_workouts,
                "total_volume": total_volume,
                "week_workouts": len(week_trainings),
                "week_volume": week_volume,
                "month_workouts": len(month_trainings),
                "month_volume": month_volume,
                "days_in_program": day_count,
                "last_workout_date": last_training.start_datetime if last_training else None,
                "avg_workouts_per_week": round(total_workouts / max(1, weeks), 1) if total_workouts > 0 else 0,
            }

    def get_day_exercise_data(self, day_id: int) -> dict:
        """
        Get exercises for a day with comprehensive performance data.

        Includes ALL historical data for each exercise template (th_exercise_id),
        regardless of which program/day it was performed in.
        """
        from datetime import datetime, timedelta

        with self._get_session() as session:
            day = session.query(Day).filter(Day.id == day_id).first()
            if not day:
                return {}

            # Get exercises for this day
            exercises_list = (
                session.query(Exercise)
                .filter(Exercise.day_id == day_id)
                .order_by(Exercise.order_num)
                .all()
            )

            exercises = []
            for ex in exercises_list:
                template = ex.template
                if not template:
                    continue

                # Get proper display name
                if template.name:
                    display_name = template.name.strip()
                else:
                    muscle = get_muscle_name(template.mainMuscleWorked)
                    equipment = get_equipment_name(template.equipment)
                    display_name = f"{muscle} ({equipment})"

                # Get last 8 weeks of workouts for trend analysis
                # This includes ALL sessions for this exercise, not just this program
                cutoff_8w = datetime.now() - timedelta(weeks=8)
                cutoff_8w_ms = datetime_to_ms(cutoff_8w)

                recent_workouts = (
                    session.query(Workout)
                    .join(Training)
                    .filter(
                        Workout.th_exercise_id == template.id,
                        Training.finishDateTime > 0,
                        Training.startDateTime >= cutoff_8w_ms
                    )
                    .order_by(Training.startDateTime)
                    .all()
                )

                # Get ALL-TIME PR (not just recent)
                all_time_pr = (
                    session.query(Set.weight)
                    .join(Workout)
                    .join(Training)
                    .filter(
                        Workout.th_exercise_id == template.id,
                        Training.finishDateTime > 0,
                        Set.weight.isnot(None)
                    )
                    .order_by(Set.weight.desc())
                    .first()
                )
                all_time_pr_weight = all_time_pr[0] if all_time_pr else None

                # Collect detailed stats from recent workouts
                session_data = []  # Per-session data for trend analysis
                all_weights = []
                all_reps = []
                total_sets_8w = 0

                for w in recent_workouts:
                    session_weights = []
                    session_reps = []
                    session_volume = 0

                    for s in w.sets:
                        # Skip warm-up sets (hard_sense <= 1 means very easy / warm-up)
                        if s.hard_sense is not None and s.hard_sense == 1:
                            continue

                        if s.weight:
                            # Round to avoid floating point precision issues
                            weight_rounded = round(s.weight, 1)
                            session_weights.append(weight_rounded)
                            all_weights.append(weight_rounded)
                        if s.reps:
                            session_reps.append(int(s.reps))
                            all_reps.append(int(s.reps))
                        if s.weight and s.reps:
                            session_volume += s.weight * s.reps
                        total_sets_8w += 1

                    if session_weights:
                        max_weight = max(session_weights)
                        avg_reps = sum(session_reps) / len(session_reps) if session_reps else 0
                        # Epley formula for estimated 1RM
                        e1rm = max_weight * (1 + avg_reps / 30) if avg_reps > 0 else max_weight

                        session_data.append({
                            "date": w.training.start_datetime,
                            "max_weight": max_weight,
                            "avg_reps": avg_reps,
                            "volume": session_volume,
                            "sets_count": len(session_weights),
                            "estimated_1rm": round(e1rm, 1),
                        })

                # Calculate trend using session max weights (more accurate)
                trend = "no_data"
                weight_change = 0
                weight_change_pct = 0

                if len(session_data) >= 3:
                    # Compare first 3 sessions vs last 3 sessions
                    first_weights = [s["max_weight"] for s in session_data[:3]]
                    last_weights = [s["max_weight"] for s in session_data[-3:]]
                    first_avg = sum(first_weights) / len(first_weights)
                    last_avg = sum(last_weights) / len(last_weights)

                    weight_change = last_avg - first_avg
                    weight_change_pct = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0

                    if weight_change_pct > 5:
                        trend = "improving"
                    elif weight_change_pct < -5:
                        trend = "declining"
                    elif abs(weight_change_pct) <= 2:
                        trend = "plateau"
                    else:
                        trend = "stable"
                elif len(session_data) >= 1:
                    trend = "insufficient_data"

                # Get last 3 sessions for detailed history
                last_3_sessions = []
                for s in session_data[-3:]:
                    last_3_sessions.append({
                        "date": s["date"],
                        "weight": s["max_weight"],
                        "avg_reps": round(s["avg_reps"], 1),
                        "volume": round(s["volume"], 0),
                        "estimated_1rm": s["estimated_1rm"],
                    })

                # Get the most recent workout sets (excluding warm-ups)
                last_sets = []
                if recent_workouts:
                    last_workout = recent_workouts[-1]
                    last_sets = [
                        {
                            "weight": round(s.weight, 1) if s.weight else 0,
                            "reps": int(s.reps) if s.reps else 0,
                            "rpe": s.hard_sense
                        }
                        for s in last_workout.sets
                        # Skip warm-up sets (hard_sense <= 1)
                        if not (s.hard_sense is not None and s.hard_sense == 1)
                    ]

                last_weight = max((s["weight"] for s in last_sets if s["weight"]), default=None) if last_sets else None
                if last_weight:
                    last_weight = round(last_weight, 1)
                last_avg_reps = sum(s["reps"] for s in last_sets) / len(last_sets) if last_sets else 0

                # Calculate current estimated 1RM
                estimated_1rm = None
                if last_weight and last_avg_reps > 0:
                    estimated_1rm = round(last_weight * (1 + last_avg_reps / 30), 1)

                # Weekly volume (sets per week over 8 weeks)
                weeks_with_data = len(set(s["date"].isocalendar()[1] for s in session_data)) if session_data else 0
                avg_sets_per_week = round(total_sets_8w / max(weeks_with_data, 1), 1)

                exercises.append({
                    "id": template.id,
                    "name": display_name,
                    "muscle_group": get_muscle_name(template.mainMuscleWorked),
                    "equipment": get_equipment_name(template.equipment),
                    "rest_time": ex.restTime or 180,
                    # Current performance
                    "last_weight": last_weight,
                    "last_avg_reps": round(last_avg_reps, 1),
                    "last_sets": last_sets,
                    "estimated_1rm": estimated_1rm,
                    # Historical data
                    "last_3_sessions": last_3_sessions,
                    "sessions_count_8w": len(recent_workouts),
                    "total_sets_8w": total_sets_8w,
                    "avg_sets_per_week": avg_sets_per_week,
                    # Trend analysis
                    "trend": trend,
                    "weight_change": round(weight_change, 1),
                    "weight_change_pct": round(weight_change_pct, 1),
                    # PRs
                    "pr_weight_8w": max(all_weights) if all_weights else None,
                    "all_time_pr": all_time_pr_weight,
                })

            return {
                "day_id": day_id,
                "day_name": day.name,
                "program_id": day.program_id,
                "exercises": exercises,
            }

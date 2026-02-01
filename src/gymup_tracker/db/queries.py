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

    def get_exercises_for_day(self, day_id: int) -> list[Exercise]:
        """Get all exercises for a day."""
        with self._get_session() as session:
            return (
                session.query(Exercise)
                .options(joinedload(Exercise.template))
                .filter(Exercise.day_id == day_id)
                .order_by(Exercise.order_num)
                .all()
            )

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
                sets_data = [
                    {
                        "weight": s.weight,
                        "reps": int(s.reps) if s.reps else 0,
                        "rpe": s.hard_sense,
                        "order": s.id,
                    }
                    for s in list(workout.sets)
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
        """Get exercises that have been used in workouts."""
        with self._get_session() as session:
            used_ids = (
                session.query(Workout.th_exercise_id)
                .distinct()
                .all()
            )
            used_ids = [id[0] for id in used_ids if id[0]]

            exercises = (
                session.query(ThExercise)
                .filter(ThExercise.id.in_(used_ids))
                .all()
            )

            # Sort by name, putting named exercises first
            return sorted(
                exercises,
                key=lambda e: (0 if e.name else 1, e.name or f"Exercise #{e.id}")
            )

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

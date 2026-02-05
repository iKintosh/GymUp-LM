"""Programs page for GymUp Tracker."""

import streamlit as st

from gymup_tracker.db import QueryService
from gymup_tracker.db.constants import get_muscle_name, get_equipment_name
from gymup_tracker.llm.functions import generate_workout_plan
from gymup_tracker.llm.client import get_ollama_status


def render_programs(db_path: str):
    """Render the programs page."""
    st.title("Programs")

    query = QueryService(db_path)

    # List all programs
    programs = query.get_all_programs()

    if not programs:
        st.info("No programs found in the database.")
        return

    # Program selector
    program_names = [p.name for p in programs]
    selected_idx = st.selectbox(
        "Select Program",
        range(len(programs)),
        format_func=lambda i: program_names[i],
    )

    selected_program = programs[selected_idx]

    st.divider()

    # Program details
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header(selected_program.name)
        if selected_program.comment:
            st.markdown(selected_program.comment)
        if selected_program.userComment:
            st.caption(f"Notes: {selected_program.userComment}")

    with col2:
        # Program stats
        stats = query.get_program_stats(selected_program.id)

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Total Workouts", stats["total_workouts"])
            st.metric("This Week", stats["week_workouts"])
        with col_b:
            st.metric("Total Volume", f"{stats['total_volume']:,.0f} kg")
            st.metric("This Week", f"{stats['week_volume']:,.0f} kg")

        if stats["last_workout_date"]:
            st.caption(f"Last workout: {stats['last_workout_date'].strftime('%b %d')}")

    # Program days
    st.subheader("Training Days")

    days = query.get_days_for_program(selected_program.id)

    if not days:
        st.info("No days defined for this program.")
        return

    # Create tabs for each day
    tabs = st.tabs([day.name for day in days])

    for tab, day in zip(tabs, days):
        with tab:
            if day.comment:
                st.caption(day.comment)

            # AI Workout Planner
            llm_status = get_ollama_status()
            col1, col2 = st.columns([3, 1])
            with col2:
                plan_btn = st.button(
                    "🤖 Plan Workout",
                    key=f"plan_{day.id}",
                    disabled=not llm_status["model_ready"],
                    help="Generate AI-powered workout plan for this day"
                )

            if plan_btn:
                with st.spinner("Generating workout plan..."):
                    day_data = query.get_day_exercise_data(day.id)
                    program = query.get_program(day.program_id)

                    # Use full exercise data with performance metrics
                    exercises_for_plan = [
                        {
                            "name": ex["name"],
                            "rest_time": ex["rest_time"],
                            "last_weight": ex.get("last_weight"),
                            "last_reps": ex.get("last_reps", []),
                            "pr_weight": ex.get("pr_weight"),
                            "trend": ex.get("trend", "unknown"),
                        }
                        for ex in day_data.get("exercises", [])
                    ]

                    # Get last session for reference
                    trainings = query.get_trainings_for_day(day.id, limit=1)
                    last_session = None
                    if trainings:
                        t = trainings[0]
                        workouts = query.get_workouts_for_training(t.id)
                        last_session = {
                            "workouts": [
                                {
                                    "name": w.template.name.strip() if w.template and w.template.name else "Unknown",
                                    "sets": [{"weight": s.weight, "reps": s.reps} for s in w.sets],
                                }
                                for w in workouts
                            ]
                        }

                    # Build training context with overall stats
                    program_stats = query.get_program_stats(selected_program.id)
                    overview_stats = query.get_overview_stats()

                    training_context = {
                        "week_workouts": program_stats.get("week_workouts", 0),
                        "week_volume": program_stats.get("week_volume", 0),
                        "avg_workouts_per_week": round(program_stats.get("total_workouts", 0) / max(1, 4), 1),
                        "last_workout": program_stats.get("last_workout_date").strftime("%b %d") if program_stats.get("last_workout_date") else "N/A",
                        "total_program_workouts": program_stats.get("total_workouts", 0),
                        "total_program_volume": program_stats.get("total_volume", 0),
                    }

                    # Generate plan
                    plan_result = generate_workout_plan(
                        day_name=day.name,
                        program_name=program.name if program else "Unknown",
                        exercises=exercises_for_plan,
                        last_session=last_session,
                        training_context=training_context,
                        use_llm=True,
                    )

                    if plan_result.get("plan"):
                        with st.expander("📝 AI Workout Plan", expanded=True):
                            st.markdown(plan_result["plan"])

            exercises_list = query.get_exercises_for_day(day.id)

            if not exercises_list:
                st.info("No exercises defined for this day.")
                continue

            # Exercise table
            st.markdown("#### Exercises")
            for i, exercise in enumerate(exercises_list, 1):
                exercise_name = exercise.get('template_name', 'Unknown Exercise')

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{i}. {exercise_name}**")

                    with col2:
                        rest_time = exercise.get('rest_time')
                        if rest_time:
                            st.caption(f"⏱️ Rest: {rest_time}s")

                    with col3:
                        # Get exercise stats
                        template_id = exercise.get('template_id')
                        if template_id:
                            stats = query.get_exercise_stats(template_id)
                            sessions = stats.get("total_sessions", 0)
                            if sessions > 0:
                                st.caption(f"📊 {sessions} sessions")

                st.divider()

            # Day training history - show last 3 sessions inline
            st.markdown("#### Recent Sessions")

            trainings = query.get_trainings_for_day(day.id, limit=3)

            if trainings:
                for idx, training in enumerate(trainings):
                    date = training.start_datetime
                    date_str = date.strftime("%b %d, %Y") if date else "Unknown"

                    # Calculate session metrics
                    volume = training.tonnage or 0
                    duration = training.duration_minutes

                    # Session header
                    st.markdown(f"**{date_str}** — {volume:,.0f}kg" + (f" • {duration}min" if duration else ""))

                    workouts = query.get_workouts_for_training(training.id)

                    if workouts:
                        for workout in workouts:
                            template = workout.template
                            if template:
                                if template.name:
                                    name = template.name.strip()
                                else:
                                    muscle = get_muscle_name(template.mainMuscleWorked)
                                    equipment = get_equipment_name(template.equipment)
                                    name = f"{muscle} ({equipment})"
                            else:
                                name = "Unknown"

                            sets = list(workout.sets)
                            if sets:
                                sets_str = " | ".join(
                                    f"{s.weight}kg×{int(s.reps)}"
                                    for s in sorted(sets, key=lambda x: x.order_num or 0)
                                )
                                st.caption(f"• {name}: {sets_str}")

                    st.divider()
            else:
                st.info("No training history for this day yet.")

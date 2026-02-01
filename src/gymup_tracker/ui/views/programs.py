"""Programs page for GymUp Tracker."""

import streamlit as st

from gymup_tracker.db import QueryService


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
        # Show number of trainings for this program
        trainings_count = 0
        for day in query.get_days_for_program(selected_program.id):
            trainings_count += len(list(query.get_trainings_for_day(day.id, limit=100)))
        if trainings_count > 0:
            st.metric("Trainings", trainings_count)

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

            exercises = query.get_exercises_for_day(day.id)
            exercises_list = list(exercises)

            if not exercises_list:
                st.info("No exercises defined for this day.")
                continue

            # Exercise table
            for i, exercise in enumerate(exercises_list, 1):
                template = exercise.template
                if not template:
                    continue

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{i}. {template.name}**")

                    with col2:
                        if exercise.restTime:
                            st.caption(f"Rest: {exercise.restTime}s")

                    with col3:
                        # Get exercise stats
                        stats = query.get_exercise_stats(template.id)
                        if stats.get("total_sessions", 0) > 0:
                            st.caption(f"{stats['total_sessions']} sessions")

                st.divider()

            # Day training history
            st.markdown("#### Recent Sessions")

            trainings = query.get_trainings_for_day(day.id, limit=5)

            if trainings:
                for training in trainings:
                    date = training.start_datetime
                    date_str = date.strftime("%B %d, %Y") if date else "Unknown"

                    with st.expander(f"{date_str} - {training.tonnage or 0:,.0f}kg"):
                        workouts = query.get_workouts_for_training(training.id)

                        for workout in workouts:
                            template = workout.template
                            name = template.name if template else "Unknown"

                            sets = list(workout.sets)
                            if sets:
                                sets_str = " | ".join(
                                    f"{s.weight}kg x {s.reps}"
                                    for s in sorted(sets, key=lambda x: x.order_num or 0)
                                )
                                st.markdown(f"**{name}**: {sets_str}")

                        if training.duration_minutes:
                            st.caption(f"Duration: {training.duration_minutes} min")
            else:
                st.info("No training history for this day yet.")

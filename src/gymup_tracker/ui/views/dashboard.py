"""Dashboard page for GymUp Tracker."""

import streamlit as st

from gymup_tracker.db import QueryService
from gymup_tracker.analytics.trends import calculate_weekly_volume
from gymup_tracker.ui.components.charts import (
    create_volume_chart,
    create_muscle_distribution_chart,
)


def render_dashboard(db_path: str):
    """Render the main dashboard page."""
    st.title("Dashboard")

    query = QueryService(db_path)

    # Overview stats
    stats = query.get_overview_stats()

    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Workouts",
            stats["total_trainings"],
            help="All-time training sessions",
        )

    with col2:
        st.metric(
            "This Week",
            stats["week_trainings"],
            f"{stats['week_tonnage']:,.0f} kg",
        )

    with col3:
        st.metric(
            "This Month",
            stats["month_trainings"],
            f"{stats['month_tonnage']:,.0f} kg",
        )

    with col4:
        st.metric(
            "Total Volume",
            f"{stats['total_tonnage']:,.0f} kg",
            help="All-time tonnage",
        )

    st.divider()

    # Recent trainings
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recent Workouts")

        trainings = query.get_all_trainings(limit=5)

        if trainings:
            for training in trainings:
                date = training.start_datetime
                date_str = date.strftime("%b %d, %Y") if date else "Unknown"
                day_name = training.day.name if training.day else "Unknown"

                with st.container():
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.markdown(f"**{day_name}**")
                        st.caption(date_str)
                    with c2:
                        st.metric("Volume", f"{training.tonnage or 0:,.0f} kg", label_visibility="collapsed")
                    with c3:
                        duration = training.duration_minutes
                        if duration:
                            st.metric("Duration", f"{duration} min", label_visibility="collapsed")

                    st.divider()
        else:
            st.info("No workout history yet.")

    with col2:
        st.subheader("Muscle Distribution")

        volume_by_muscle = query.get_muscle_volume_distribution(weeks=4)

        if volume_by_muscle:
            fig = create_muscle_distribution_chart(
                volume_by_muscle,
                title="Volume by Muscle (Last 4 Weeks)",
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No volume data available.")

    # Weekly volume chart
    st.subheader("Weekly Training Volume")

    all_trainings = query.get_all_trainings(limit=100)
    if all_trainings:
        # Build history for volume calculation
        history = []
        for t in all_trainings:
            if t.start_datetime:
                history.append({
                    "date": t.start_datetime,
                    "tonnage": t.tonnage or 0,
                    "sets": [],
                })

        weekly = calculate_weekly_volume(history)

        if weekly:
            fig = create_volume_chart(weekly[-8:], title="Weekly Volume (Last 8 Weeks)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data for weekly volume chart.")
    else:
        st.info("No training data available.")

    # Active program
    st.subheader("Active Program")

    active = query.get_active_program()
    if active:
        st.markdown(f"### {active.name}")
        if active.comment:
            st.caption(active.comment)

        days = query.get_days_for_program(active.id)
        if days:
            cols = st.columns(min(len(days), 4))
            for i, day in enumerate(days[:4]):
                with cols[i]:
                    st.markdown(f"**{day.name}**")
                    exercises = query.get_exercises_for_day(day.id)
                    st.caption(f"{len(list(exercises))} exercises")
    else:
        programs = query.get_all_programs()
        if programs:
            st.info("No active program. Select one from the Programs page.")
        else:
            st.info("No programs found in database.")

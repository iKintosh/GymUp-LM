"""Dashboard page for GymUp Tracker."""

import streamlit as st

from gymup_tracker.db import QueryService
from gymup_tracker.analytics.trends import calculate_weekly_volume
from gymup_tracker.llm.functions import generate_training_summary, analyze_recovery_status
from gymup_tracker.llm.client import get_ollama_status
from gymup_tracker.ui.components.charts import (
    create_volume_chart,
    create_muscle_distribution_chart,
    create_exercise_volume_chart,
)


def render_dashboard(db_path: str):
    """Render the main dashboard page."""
    st.title("Dashboard")

    query = QueryService(db_path)

    # AI Training Summary & Recovery Analysis (with caching)
    llm_status = get_ollama_status()
    if llm_status["model_ready"]:
        # Use Streamlit's cache to avoid regenerating AI responses on every render
        @st.cache_data(ttl=3600)  # Cache for 1 hour
        def get_ai_training_summary():
            return generate_training_summary(db_path, weeks=4, use_llm=True)

        @st.cache_data(ttl=3600)
        def get_ai_recovery_analysis():
            return analyze_recovery_status(db_path, weeks=4, use_llm=True)

        col1, col2 = st.columns(2)

        with col1:
            with st.spinner("🤖 Generating AI summary..."):
                summary_result = get_ai_training_summary()
                if summary_result.get("summary"):
                    # Store in session state for use by other LLM calls
                    st.session_state.cached_training_summary = summary_result["summary"]
                    with st.expander("🤖 **AI Training Summary (Last 4 Weeks)**", expanded=True):
                        st.markdown(summary_result["summary"])

        with col2:
            with st.spinner("💪 Analyzing recovery status..."):
                recovery_result = get_ai_recovery_analysis()
                if recovery_result.get("status"):
                    with st.expander("💪 **Recovery & Fatigue Analysis**", expanded=True):
                        st.markdown(recovery_result["status"])

        st.divider()

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
                    c1, c2, c3 = st.columns([2.5, 1.5, 1.5])
                    with c1:
                        st.markdown(f"**{day_name}**")
                        st.caption(date_str)
                    with c2:
                        volume = training.tonnage or 0
                        st.caption(f"📊 {volume:,.0f} kg")
                    with c3:
                        duration = training.duration_minutes
                        if duration:
                            st.caption(f"⏱️ {duration:.0f} min")
                        else:
                            st.caption("⏱️ N/A")

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

    # Top exercises by volume
    st.subheader("Top Exercises by Volume (Last 4 Weeks)")

    top_exercises = query.get_top_exercises_by_volume(weeks=4, limit=10)

    if top_exercises:
        fig = create_exercise_volume_chart(top_exercises)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No exercise volume data available.")

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

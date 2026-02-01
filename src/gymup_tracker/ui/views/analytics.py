"""Analytics page for GymUp Tracker."""

import streamlit as st
from datetime import datetime, timedelta

from gymup_tracker.db import QueryService
from gymup_tracker.analytics.trends import (
    calculate_weekly_volume,
    detect_overreaching,
)
from gymup_tracker.ui.components.charts import (
    create_volume_chart,
    create_muscle_distribution_chart,
)


def render_analytics(db_path: str):
    """Render the analytics page."""
    st.title("Analytics")

    query = QueryService(db_path)

    # Time range selector
    time_range = st.selectbox(
        "Time Range",
        ["Last 4 Weeks", "Last 8 Weeks", "Last 12 Weeks", "All Time"],
    )

    weeks_map = {
        "Last 4 Weeks": 4,
        "Last 8 Weeks": 8,
        "Last 12 Weeks": 12,
        "All Time": 52,
    }
    weeks = weeks_map[time_range]

    st.divider()

    # Volume trends
    st.subheader("Volume Trends")

    trainings = query.get_all_trainings(limit=500)

    if trainings:
        # Build history
        history = []
        for t in trainings:
            if t.start_datetime:
                cutoff = datetime.now() - timedelta(weeks=weeks)
                if t.start_datetime >= cutoff:
                    history.append({
                        "date": t.start_datetime,
                        "tonnage": t.tonnage or 0,
                        "sets": [],
                        "rpe_avg": t.hard_sense,
                    })

        weekly = calculate_weekly_volume(history)

        if weekly:
            fig = create_volume_chart(weekly, title="Weekly Training Volume")
            st.plotly_chart(fig, use_container_width=True)

            # Weekly stats
            col1, col2, col3, col4 = st.columns(4)

            avg_tonnage = sum(w["tonnage"] for w in weekly) / len(weekly) if weekly else 0
            avg_workouts = sum(w["workouts"] for w in weekly) / len(weekly) if weekly else 0
            max_tonnage = max(w["tonnage"] for w in weekly) if weekly else 0
            total_workouts = sum(w["workouts"] for w in weekly) if weekly else 0

            with col1:
                st.metric("Avg Weekly Volume", f"{avg_tonnage:,.0f} kg")

            with col2:
                st.metric("Avg Workouts/Week", f"{avg_workouts:.1f}")

            with col3:
                st.metric("Peak Week Volume", f"{max_tonnage:,.0f} kg")

            with col4:
                st.metric("Total Workouts", total_workouts)
        else:
            st.info("Not enough data for volume analysis.")
    else:
        st.info("No training data available.")

    st.divider()

    # Muscle volume distribution
    st.subheader("Muscle Group Distribution")

    col1, col2 = st.columns(2)

    with col1:
        volume_by_muscle = query.get_muscle_volume_distribution(weeks=weeks)

        if volume_by_muscle:
            fig = create_muscle_distribution_chart(
                volume_by_muscle,
                title=f"Volume by Muscle ({time_range})",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No muscle volume data.")

    with col2:
        # Volume breakdown
        if volume_by_muscle:
            st.markdown("#### Volume Breakdown")

            total = sum(volume_by_muscle.values())
            sorted_muscles = sorted(volume_by_muscle.items(), key=lambda x: x[1], reverse=True)

            for muscle, volume in sorted_muscles[:10]:
                pct = (volume / total * 100) if total > 0 else 0
                st.markdown(f"**{muscle}**: {volume:,.0f} kg ({pct:.1f}%)")

    st.divider()

    # Fatigue analysis
    st.subheader("Recovery & Fatigue Analysis")

    if history and len(history) >= 3:
        fatigue = detect_overreaching(history)

        col1, col2 = st.columns(2)

        with col1:
            if fatigue["is_overreaching"]:
                st.error("Overreaching Detected")
            else:
                st.success("Recovery Looks Good")

            st.markdown(f"**Confidence**: {fatigue['confidence'].title()}")

        with col2:
            if fatigue["factors"]:
                st.markdown("**Warning Signs:**")
                for factor in fatigue["factors"]:
                    st.markdown(f"- {factor}")

        st.info(fatigue["recommendation"])
    else:
        st.info("Need more training data for fatigue analysis (minimum 3 workouts).")

    st.divider()

    # Training frequency
    st.subheader("Training Frequency")

    if trainings:
        # Group by day of week
        day_counts = {i: 0 for i in range(7)}
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        cutoff = datetime.now() - timedelta(weeks=weeks)
        for t in trainings:
            if t.start_datetime and t.start_datetime >= cutoff:
                day_counts[t.start_datetime.weekday()] += 1

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Workouts by Day")
            for i, name in enumerate(day_names):
                count = day_counts[i]
                bar = "█" * min(count, 20)
                st.markdown(f"**{name}**: {bar} {count}")

        with col2:
            # Time of day analysis
            st.markdown("#### Workout Times")

            morning = 0  # Before 12:00
            afternoon = 0  # 12:00 - 18:00
            evening = 0  # After 18:00

            for t in trainings:
                if t.start_datetime and t.start_datetime >= cutoff:
                    hour = t.start_datetime.hour
                    if hour < 12:
                        morning += 1
                    elif hour < 18:
                        afternoon += 1
                    else:
                        evening += 1

            total = morning + afternoon + evening
            if total > 0:
                st.markdown(f"**Morning** (before 12:00): {morning} ({morning/total*100:.0f}%)")
                st.markdown(f"**Afternoon** (12:00-18:00): {afternoon} ({afternoon/total*100:.0f}%)")
                st.markdown(f"**Evening** (after 18:00): {evening} ({evening/total*100:.0f}%)")
    else:
        st.info("No training data for frequency analysis.")

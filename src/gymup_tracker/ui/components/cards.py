"""Card components for displaying workout data."""

import streamlit as st
from datetime import datetime
from typing import Optional


def metric_card(
    label: str,
    value: str | int | float,
    delta: Optional[str | int | float] = None,
    delta_color: str = "normal",
    help_text: str = None,
):
    """
    Display a metric card.

    Args:
        label: Metric label
        value: Metric value
        delta: Optional change value
        delta_color: Color for delta ("normal", "inverse", "off")
        help_text: Optional help tooltip
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text,
    )


def exercise_card(
    name: str,
    muscle_group: str,
    equipment: str,
    last_weight: float = None,
    last_reps: int = None,
    estimated_1rm: float = None,
    total_sessions: int = None,
    on_click: callable = None,
):
    """
    Display an exercise card with key stats.

    Args:
        name: Exercise name
        muscle_group: Primary muscle group
        equipment: Equipment used
        last_weight: Most recent weight used
        last_reps: Most recent reps
        estimated_1rm: Estimated 1RM
        total_sessions: Number of training sessions
        on_click: Callback when card is clicked
    """
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(name)
            st.caption(f"{muscle_group} | {equipment}")

        with col2:
            if total_sessions:
                st.metric("Sessions", total_sessions)

        if last_weight is not None or estimated_1rm is not None:
            col1, col2, col3 = st.columns(3)

            with col1:
                if last_weight is not None:
                    last_str = f"{last_weight}kg"
                    if last_reps:
                        last_str += f" x {last_reps}"
                    st.metric("Last", last_str)

            with col2:
                if estimated_1rm is not None:
                    st.metric("Est. 1RM", f"{estimated_1rm:.1f}kg")


def training_card(
    training_id: int,
    date: datetime,
    day_name: str,
    duration_minutes: int = None,
    tonnage: float = None,
    sets_amount: int = None,
    reps_amount: int = None,
    rpe: int = None,
):
    """
    Display a training session card.

    Args:
        training_id: Training session ID
        date: Session date
        day_name: Name of the training day
        duration_minutes: Session duration
        tonnage: Total tonnage
        sets_amount: Total sets
        reps_amount: Total reps
        rpe: Session RPE
    """
    with st.container():
        # Header
        date_str = date.strftime("%B %d, %Y at %H:%M") if date else "Unknown date"
        st.markdown(f"**{day_name}** - {date_str}")

        # Stats row
        cols = st.columns(5)

        with cols[0]:
            if duration_minutes:
                st.metric("Duration", f"{duration_minutes} min")

        with cols[1]:
            if tonnage:
                st.metric("Volume", f"{tonnage:,.0f} kg")

        with cols[2]:
            if sets_amount:
                st.metric("Sets", sets_amount)

        with cols[3]:
            if reps_amount:
                st.metric("Reps", reps_amount)

        with cols[4]:
            if rpe:
                st.metric("RPE", rpe)

        st.divider()


def llm_status_indicator(is_available: bool, model_name: str = None):
    """
    Display LLM status indicator.

    Args:
        is_available: Whether LLM is available
        model_name: Name of the active model
    """
    if is_available:
        st.success(f"AI: {model_name or 'Connected'}", icon="🤖")
    else:
        st.warning("AI: Offline", icon="⚠️")


def analysis_result_card(
    title: str,
    trend: str,
    key_metrics: dict,
    recommendations: list[str],
    llm_analysis: str = None,
):
    """
    Display analysis results.

    Args:
        title: Analysis title
        trend: Current trend (improving, plateau, declining)
        key_metrics: Dict of metric name -> value
        recommendations: List of recommendations
        llm_analysis: Optional LLM-generated analysis
    """
    # Trend indicator
    trend_icons = {
        "improving": "📈",
        "plateau": "➡️",
        "declining": "📉",
        "stable": "➡️",
        "insufficient_data": "❓",
    }

    trend_colors = {
        "improving": "green",
        "plateau": "orange",
        "declining": "red",
        "stable": "blue",
        "insufficient_data": "gray",
    }

    icon = trend_icons.get(trend, "❓")
    color = trend_colors.get(trend, "gray")

    st.markdown(f"### {icon} {title}")
    st.markdown(f"**Trend:** :{color}[{trend.replace('_', ' ').title()}]")

    # Metrics
    cols = st.columns(len(key_metrics))
    for col, (name, value) in zip(cols, key_metrics.items()):
        with col:
            st.metric(name, value)

    # Recommendations
    st.markdown("#### Recommendations")
    for rec in recommendations:
        st.markdown(f"- {rec}")

    # LLM Analysis
    if llm_analysis:
        with st.expander("AI Analysis", expanded=True):
            st.markdown(llm_analysis)

"""Exercises page for GymUp Tracker."""

import streamlit as st

from gymup_tracker.db import QueryService
from gymup_tracker.db.constants import get_muscle_name, get_equipment_name, get_exercise_display_name
from gymup_tracker.analytics.progression import analyze_progression
from gymup_tracker.analytics.trends import calculate_1rm_trajectory, find_personal_records
from gymup_tracker.llm.client import get_ollama_status
from gymup_tracker.llm.functions import analyze_exercise_progression, suggest_next_weights
from gymup_tracker.ui.components.charts import (
    create_progression_chart,
    create_1rm_trajectory_chart,
)


def render_exercises(db_path: str):
    """Render the exercises page."""
    st.title("Exercises")

    query = QueryService(db_path)

    # Get exercises that have been used
    used_exercises = query.get_used_exercises()

    if not used_exercises:
        st.info("No exercises with training history found.")
        return

    # Exercise selector
    exercise_names = [get_exercise_display_name(ex) for ex in used_exercises]
    selected_idx = st.selectbox(
        "Select Exercise",
        range(len(used_exercises)),
        format_func=lambda i: exercise_names[i],
    )

    selected_exercise = used_exercises[selected_idx]
    exercise_name = get_exercise_display_name(selected_exercise)

    st.divider()

    # Exercise details
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header(exercise_name)
        muscle = get_muscle_name(selected_exercise.mainMuscleWorked)
        equipment = get_equipment_name(selected_exercise.equipment)
        st.caption(f"{muscle} | {equipment}")

    with col2:
        # LLM status
        llm_status = get_ollama_status()
        if llm_status["model_ready"]:
            st.success("AI Ready", icon="🤖")
        else:
            st.warning("AI Offline", icon="⚠️")

    # Exercise stats
    stats = query.get_exercise_stats(selected_exercise.id)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Sessions", stats.get("total_sessions", 0))

    with col2:
        st.metric("Max Weight", f"{stats.get('max_weight', 0):.1f} kg")

    with col3:
        st.metric("Est. 1RM", f"{stats.get('estimated_1rm', 0):.1f} kg")

    with col4:
        st.metric("Total Volume", f"{stats.get('total_volume', 0):,.0f} kg")

    # Last workout info
    if stats.get("last_sets"):
        last_date = stats.get("last_workout_date")
        date_str = last_date.strftime("%B %d") if last_date else ""
        sets_str = " | ".join(f"{s['weight']}kg x {s['reps']}" for s in stats["last_sets"])
        st.info(f"Last workout ({date_str}): {sets_str}")

    st.divider()

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Progression", "AI Analysis", "History"])

    # Get workout history (12 weeks for full view, but trend uses last 4)
    history = query.get_exercise_history(selected_exercise.id, weeks=12)

    with tab1:
        st.subheader("Weight Progression")

        if not history:
            st.info("No workout history available.")
        else:
            # Progression chart
            fig = create_progression_chart(
                history,
                title=f"{exercise_name} - Progress",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 1RM trajectory
            trajectory = calculate_1rm_trajectory(history, weeks_forward=4)

            if trajectory.get("historical"):
                st.subheader("1RM Trajectory")
                fig = create_1rm_trajectory_chart(trajectory)
                st.plotly_chart(fig, use_container_width=True)

            # Personal records
            prs = find_personal_records(history)
            if prs:
                st.subheader("Personal Records")

                # Filter to show weight PRs
                weight_prs = [p for p in prs if p["type"] == "weight"][-5:]

                if weight_prs:
                    for pr in reversed(weight_prs):
                        date = pr["date"]
                        date_str = date.strftime("%b %d, %Y") if date else ""
                        st.markdown(
                            f"- **{pr['weight']}kg** x {pr['reps']} ({date_str})"
                        )

    with tab2:
        st.subheader("AI Analysis")

        if not history:
            st.info("Need workout history for AI analysis.")
        else:
            # User context input
            user_context = st.text_area(
                "Additional Context (Optional)",
                placeholder="e.g., 'Shoulder pain resolved', 'Switched to wider grip', 'Feeling strong'",
                key="analysis_context",
            )

            col1, col2 = st.columns(2)

            with col1:
                analyze_btn = st.button("Analyze Progression", type="primary", use_container_width=True)

            with col2:
                suggest_btn = st.button("Suggest Next Weights", type="secondary", use_container_width=True)

            if analyze_btn:
                with st.spinner("Analyzing..."):
                    result = analyze_exercise_progression(
                        exercise_name=exercise_name,
                        muscle_group=get_muscle_name(selected_exercise.mainMuscleWorked),
                        equipment=get_equipment_name(selected_exercise.equipment),
                        history=history,
                        user_context=user_context,
                        use_llm=llm_status["model_ready"],
                    )

                # Display results
                trend = result.get("trend", "unknown")
                trend_icons = {
                    "improving": "📈",
                    "plateau": "➡️",
                    "declining": "📉",
                    "stable": "➡️",
                }

                st.markdown(f"### {trend_icons.get(trend, '❓')} Trend: {trend.title()}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Weight Change", f"{result.get('weight_change', 0):+.1f} kg")
                with col2:
                    st.metric("Change %", f"{result.get('weight_change_percent', 0):+.1f}%")
                with col3:
                    st.metric("PRs", result.get("pr_count", 0))

                st.markdown("#### Rule-Based Recommendation")
                st.info(result.get("rule_based_recommendation", "No recommendation available."))

                if result.get("llm_analysis"):
                    st.markdown("#### AI Analysis")
                    st.markdown(result["llm_analysis"])
                elif not llm_status["model_ready"]:
                    st.warning("Enable Ollama for AI-powered analysis.")

            if suggest_btn:
                with st.spinner("Generating recommendation..."):
                    result = suggest_next_weights(
                        exercise_name=exercise_name,
                        muscle_group=get_muscle_name(selected_exercise.mainMuscleWorked),
                        history=history,
                        user_context=user_context,
                        use_llm=llm_status["model_ready"],
                    )

                # Display suggestion
                suggested = result.get("suggested_weight")
                if suggested:
                    # Check if AI provided structured recommendation
                    if result.get("ai_short_answer") and not result.get("parsing_failed"):
                        # Use AI recommendation if available
                        st.success(f"✅ **Recommended: {result['ai_short_answer']}**")
                        with st.expander("💡 Reasoning"):
                            st.markdown(result.get("ai_reasoning", ""))
                    else:
                        # Fallback to rule-based
                        st.success(f"**Recommended: {suggested} kg**")
                        with st.expander("📊 Analysis"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Last Weight", f"{result.get('last_weight', 'N/A')} kg")
                            with col2:
                                st.metric("Last Reps", result.get("last_avg_reps", "N/A"))
                            st.markdown(result.get("rule_based_reasoning", ""))

                    # Always show last session info
                    with st.expander("📋 Last Session"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Last Weight", f"{result.get('last_weight', 'N/A')} kg")
                        with col2:
                            st.metric("Last Reps", result.get("last_avg_reps", "N/A"))
                else:
                    st.warning("Could not generate weight suggestion.")

    with tab3:
        st.subheader("Workout History")

        if not history:
            st.info("No workout history available.")
        else:
            for workout in reversed(history[-10:]):
                date = workout.get("date")
                date_str = date.strftime("%B %d, %Y") if date else "Unknown"

                sets = workout.get("sets", [])
                sets_str = " | ".join(
                    f"{s.get('weight', 0)}kg x {s.get('reps', 0)}"
                    + (f" (RPE {s.get('rpe')})" if s.get('rpe') else "")
                    for s in sets
                )

                tonnage = workout.get("tonnage", 0)

                with st.container():
                    st.markdown(f"**{date_str}**")
                    st.markdown(sets_str)
                    st.caption(f"Volume: {tonnage:,.0f} kg")
                    st.divider()

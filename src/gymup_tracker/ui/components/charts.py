"""Chart components using Plotly."""

from datetime import datetime
from typing import Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_progression_chart(
    history: list[dict],
    title: str = "Weight Progression",
    height: int = 400,
) -> go.Figure:
    """
    Create a weight progression chart.

    Args:
        history: Workout history with dates and sets
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly figure
    """
    if not history:
        fig = go.Figure()
        fig.add_annotation(
            text="No workout data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray"),
        )
        fig.update_layout(height=height, title=title)
        return fig

    dates = []
    max_weights = []
    avg_weights = []
    volumes = []

    for workout in history:
        date = workout.get("date")
        if not date:
            continue

        sets = workout.get("sets", [])
        weights = [s.get("weight", 0) or 0 for s in sets if s.get("weight")]

        if weights:
            dates.append(date)
            max_weights.append(max(weights))
            avg_weights.append(sum(weights) / len(weights))
            volumes.append(workout.get("tonnage", 0) or 0)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=("Weight (kg)", "Volume (kg)"),
    )

    # Weight traces
    fig.add_trace(
        go.Scatter(
            x=dates, y=max_weights,
            mode="lines+markers",
            name="Max Weight",
            line=dict(color="#2196F3", width=2),
            marker=dict(size=8),
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=dates, y=avg_weights,
            mode="lines+markers",
            name="Avg Weight",
            line=dict(color="#4CAF50", width=2, dash="dash"),
            marker=dict(size=6),
        ),
        row=1, col=1,
    )

    # Volume bars
    fig.add_trace(
        go.Bar(
            x=dates, y=volumes,
            name="Volume",
            marker_color="#FF9800",
            opacity=0.7,
        ),
        row=2, col=1,
    )

    fig.update_layout(
        title=title,
        height=height,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_dark",
    )

    fig.update_xaxes(title_text="Date", row=2, col=1)

    return fig


def create_volume_chart(
    weekly_data: list[dict],
    title: str = "Weekly Volume",
    height: int = 300,
) -> go.Figure:
    """
    Create a weekly volume chart.

    Args:
        weekly_data: Weekly volume summaries
        title: Chart title
        height: Chart height

    Returns:
        Plotly figure
    """
    if not weekly_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No volume data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
        )
        fig.update_layout(height=height, title=title, template="plotly_dark")
        return fig

    weeks = [w["week_start"].strftime("%b %d") for w in weekly_data]
    tonnage = [w["tonnage"] for w in weekly_data]
    workouts = [w["workouts"] for w in weekly_data]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=weeks, y=tonnage,
            name="Tonnage (kg)",
            marker_color="#2196F3",
            text=[f"{int(t):,}" for t in tonnage],
            textposition="auto",
        )
    )

    # Add workout count as line
    fig.add_trace(
        go.Scatter(
            x=weeks, y=[w * max(tonnage) / max(workouts) if max(workouts) > 0 else 0 for w in workouts],
            mode="lines+markers",
            name="Workouts",
            yaxis="y2",
            line=dict(color="#FF9800", width=3),
            marker=dict(size=10),
        )
    )

    fig.update_layout(
        title=title,
        height=height,
        template="plotly_dark",
        yaxis=dict(title="Tonnage (kg)"),
        yaxis2=dict(
            title="Workouts",
            overlaying="y",
            side="right",
            range=[0, max(workouts) * 1.5] if workouts else [0, 10],
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    return fig


def create_muscle_distribution_chart(
    volume_by_muscle: dict[str, float],
    title: str = "Volume by Muscle Group",
    height: int = 400,
) -> go.Figure:
    """
    Create a muscle group volume distribution chart.

    Args:
        volume_by_muscle: Dict mapping muscle names to volume
        title: Chart title
        height: Chart height

    Returns:
        Plotly figure
    """
    if not volume_by_muscle:
        fig = go.Figure()
        fig.add_annotation(
            text="No muscle volume data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
        )
        fig.update_layout(height=height, title=title, template="plotly_dark")
        return fig

    # Sort by volume
    sorted_muscles = sorted(volume_by_muscle.items(), key=lambda x: x[1], reverse=True)
    muscles = [m[0] for m in sorted_muscles]
    volumes = [m[1] for m in sorted_muscles]

    colors = [
        "#2196F3", "#4CAF50", "#FF9800", "#9C27B0",
        "#F44336", "#00BCD4", "#FFEB3B", "#795548",
        "#607D8B", "#E91E63", "#3F51B5", "#8BC34A",
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=muscles, y=volumes,
            marker_color=colors[:len(muscles)],
            text=[f"{int(v):,}" for v in volumes],
            textposition="auto",
        )
    )

    fig.update_layout(
        title=title,
        height=height,
        template="plotly_dark",
        xaxis=dict(title="Muscle Group"),
        yaxis=dict(title="Volume (kg)"),
        showlegend=False,
    )

    return fig


def create_1rm_trajectory_chart(
    trajectory_data: dict,
    title: str = "1RM Trajectory",
    height: int = 350,
) -> go.Figure:
    """
    Create a 1RM trajectory chart with projections.

    Args:
        trajectory_data: Dict with historical and projected data
        title: Chart title
        height: Chart height

    Returns:
        Plotly figure
    """
    historical = trajectory_data.get("historical", [])
    projected = trajectory_data.get("projected", [])

    if not historical:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for 1RM trajectory",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
        )
        fig.update_layout(height=height, title=title, template="plotly_dark")
        return fig

    hist_dates = [h["date"] for h in historical]
    hist_1rm = [h["one_rm"] for h in historical]

    fig = go.Figure()

    # Historical data
    fig.add_trace(
        go.Scatter(
            x=hist_dates, y=hist_1rm,
            mode="markers",
            name="Calculated 1RM",
            marker=dict(size=10, color="#2196F3"),
        )
    )

    # Trend line through historical (linear regression using numpy)
    if len(hist_dates) >= 2:
        import numpy as np

        # Convert dates to numeric values for regression
        x = np.arange(len(hist_dates))
        y = np.array(hist_1rm)

        # Linear regression: y = slope * x + intercept
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator != 0:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n

            # Generate trend line points
            trend_1rm = slope * x + intercept

            fig.add_trace(
                go.Scatter(
                    x=hist_dates, y=trend_1rm,
                    mode="lines",
                    name="Trend Line",
                    line=dict(color="#4CAF50", width=2, dash="dash"),
                )
            )

    # Projected data
    if projected:
        proj_dates = [p["date"] for p in projected]
        proj_1rm = [p["one_rm"] for p in projected]

        fig.add_trace(
            go.Scatter(
                x=proj_dates, y=proj_1rm,
                mode="lines+markers",
                name="Projection",
                line=dict(color="#FF9800", width=2, dash="dot"),
                marker=dict(size=8),
            )
        )

    # Add confidence info
    confidence = trajectory_data.get("confidence", "N/A")
    weekly_gain = trajectory_data.get("weekly_gain", 0)
    r_squared = trajectory_data.get("r_squared", 0)

    fig.add_annotation(
        text=f"Weekly gain: {weekly_gain:.1f}kg | R²: {r_squared:.2f} | Confidence: {confidence}",
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        font=dict(size=11),
    )

    fig.update_layout(
        title=title,
        height=height,
        template="plotly_dark",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Estimated 1RM (kg)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(b=80),
    )

    return fig


def create_exercise_volume_chart(
    exercises: list[dict],
    title: str = "Top Exercises by Volume",
    height: int = 400,
) -> go.Figure:
    """
    Create a chart showing top exercises by total volume.

    Args:
        exercises: List of dicts with name, muscle_group, total_volume, session_count
        title: Chart title
        height: Chart height

    Returns:
        Plotly figure
    """
    if not exercises:
        fig = go.Figure()
        fig.add_annotation(
            text="No exercise volume data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
        )
        fig.update_layout(height=height, title=title, template="plotly_dark")
        return fig

    names = [e["name"] for e in exercises]
    volumes = [e["total_volume"] for e in exercises]
    sessions = [e["session_count"] for e in exercises]
    muscles = [e["muscle_group"] for e in exercises]

    # Color by muscle group
    muscle_colors = {
        "Chest": "#FF6B6B",
        "Back": "#4ECDC4",
        "Shoulders": "#45B7D1",
        "Biceps": "#FFA07A",
        "Triceps": "#98D8C8",
        "Forearms": "#F7DC6F",
        "Quads": "#BB8FCE",
        "Hamstrings": "#85C1E2",
        "Glutes": "#F8B88B",
        "Calves": "#A9DFBF",
    }

    colors = [muscle_colors.get(m, "#95A5A6") for m in muscles]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=names, x=volumes,
            orientation="h",
            marker_color=colors,
            text=[f"{int(v):,} kg" for v in volumes],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Volume: %{x:,.0f} kg<br>Sessions: %{customdata}<extra></extra>",
            customdata=sessions,
        )
    )

    fig.update_layout(
        title=title,
        height=height,
        template="plotly_dark",
        xaxis=dict(title="Total Volume (kg)"),
        yaxis=dict(title="Exercise"),
        showlegend=False,
        margin=dict(l=150),
    )

    return fig

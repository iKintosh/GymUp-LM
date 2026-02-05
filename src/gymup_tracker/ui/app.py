"""Main Streamlit application for GymUp Tracker."""

import sys
from pathlib import Path

import streamlit as st

# Add parent to path for imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gymup_tracker.db.models import get_engine
from gymup_tracker.llm.client import get_ollama_status, get_installation_instructions
from gymup_tracker.ui.views.dashboard import render_dashboard
from gymup_tracker.ui.views.programs import render_programs
from gymup_tracker.ui.views.exercises import render_exercises


def get_db_path() -> Path:
    """Get database path from session state or query params."""
    # Check session state first
    if "db_path" in st.session_state:
        return Path(st.session_state.db_path)

    # Check query params
    params = st.query_params
    if "db" in params:
        return Path(params["db"])

    # Default: look for workout.db in current directory or common locations
    candidates = [
        Path.cwd() / "workout.db",
        Path.cwd() / "data" / "workout.db",
        Path.home() / ".gymup-tracker" / "workout.db",
    ]

    # Also check for any .db file in current directory
    for db_file in Path.cwd().glob("*.db"):
        candidates.insert(0, db_file)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def validate_database(db_path: Path) -> bool:
    """Check if database is valid."""
    if not db_path or not db_path.exists():
        return False

    try:
        from sqlalchemy import text
        engine = get_engine(db_path)
        # Try a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM program LIMIT 1"))
        return True
    except Exception:
        return False


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="GymUp AI Trainer",
        page_icon="🏋️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stMetric {
            background-color: rgba(28, 131, 225, 0.1);
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.title("🏋️ GymUp AI Trainer")
        st.caption("Workout Analysis & AI Recommendations")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigation",
            ["Dashboard", "Programs", "Exercises", "Settings"],
            label_visibility="collapsed",
        )

        st.divider()

        # LLM Status
        llm_status = get_ollama_status()

        if llm_status["model_ready"]:
            st.success(f"AI: {llm_status['configured_model']}", icon="🤖")
        elif llm_status["available"]:
            st.warning("AI: No model loaded", icon="⚠️")
            st.caption(f"Pull a model: `ollama pull {llm_status['configured_model']}`")
        else:
            st.error("AI: Ollama not running", icon="❌")
            st.caption("Start Ollama: `ollama serve`")

        st.divider()

        # Database info
        db_path = get_db_path()
        if db_path and db_path.exists():
            st.caption(f"Database: {db_path.name}")
        else:
            st.warning("No database loaded")

    # Get database path
    db_path = get_db_path()

    # Validate database
    if not db_path:
        st.error("No database found")
        st.markdown("""
        ### Getting Started

        Please provide a GymUp database file:

        1. **Via CLI**: `gymup-tracker start --db /path/to/workout.db`
        2. **Via URL**: Add `?db=/path/to/workout.db` to the URL
        3. **Default location**: Place `workout.db` in the current directory

        """)

        # Allow file upload
        uploaded = st.file_uploader("Or upload a database file", type=["db"])
        if uploaded:
            # Save to temp location
            temp_path = Path.home() / ".gymup-tracker" / "uploaded.db"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_bytes(uploaded.read())
            st.session_state.db_path = str(temp_path)
            st.rerun()

        return

    if not validate_database(db_path):
        st.error(f"Invalid database: {db_path}")
        st.markdown("The file exists but doesn't appear to be a valid GymUp database.")
        return

    # Store in session state
    st.session_state.db_path = str(db_path)

    # Render selected page
    if page == "Dashboard":
        render_dashboard(str(db_path))
    elif page == "Programs":
        render_programs(str(db_path))
    elif page == "Exercises":
        render_exercises(str(db_path))
    elif page == "Settings":
        render_settings(llm_status)


def render_settings(llm_status: dict):
    """Render settings page."""
    st.title("Settings")

    # LLM Configuration
    st.subheader("AI Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Ollama Status**")

        if llm_status["available"]:
            st.success("Ollama is running")
            st.markdown(f"**URL**: {llm_status['base_url']}")

            if llm_status["models"]:
                st.markdown("**Available Models:**")
                for model in llm_status["models"]:
                    if model == llm_status["configured_model"]:
                        st.markdown(f"- {model} ✓ (active)")
                    else:
                        st.markdown(f"- {model}")
            else:
                st.warning("No models installed")
                st.code("ollama pull mistral:7b", language="bash")
        else:
            st.error("Ollama is not running")
            st.markdown(get_installation_instructions())

    with col2:
        st.markdown("**Model Settings**")

        new_model = st.text_input(
            "Model Name",
            value=llm_status["configured_model"],
            help="Ollama model to use for AI analysis",
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Lower = more consistent, Higher = more creative",
        )

        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            help="Maximum response length",
        )

        if st.button("Save Settings"):
            st.success("Settings saved!")
            st.info("Note: Settings are stored in session. For persistent settings, edit ~/.gymup-tracker/config.yaml")

    st.divider()

    # Database Info
    st.subheader("Database Information")

    db_path = get_db_path()
    if db_path and db_path.exists():
        st.markdown(f"**Path**: `{db_path}`")
        st.markdown(f"**Size**: {db_path.stat().st_size / 1024:.1f} KB")

        # Quick stats
        from gymup_tracker.db import QueryService
        query = QueryService(str(db_path))
        stats = query.get_overview_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Workouts", stats["total_trainings"])
        with col2:
            st.metric("Total Volume", f"{stats['total_tonnage']:,.0f} kg")
        with col3:
            programs = query.get_all_programs()
            st.metric("Programs", len(programs))

    st.divider()

    # About
    st.subheader("About")
    st.markdown("""
    **GymUp AI Trainer** v0.1.0

    An AI-powered workout analysis tool that provides intelligent weight progression
    recommendations based on your GymUp training data.

    Built with:
    - Streamlit for the UI
    - SQLAlchemy for database access
    - Ollama for local LLM inference
    - Plotly for visualizations
    """)


if __name__ == "__main__":
    main()

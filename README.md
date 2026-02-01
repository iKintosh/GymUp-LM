# GymUp AI Trainer

AI-powered workout analysis and weight progression recommendations for GymUp data.

## Features

- **Workout Analysis**: Track and visualize your training progress
- **AI Recommendations**: Get intelligent weight progression suggestions powered by local LLMs
- **Exercise Tracking**: View detailed stats for each exercise
- **Trend Detection**: Automatic plateau and overreaching detection
- **Volume Analytics**: Muscle group volume distribution and weekly trends

## Installation

```bash
# Install with uv
uv sync

# Or with pip
pip install -e .
```

## Quick Start

```bash
# Start the web interface
gymup-tracker start --db /path/to/workout.db

# Show database info
gymup-tracker info --db /path/to/workout.db

# Analyze a specific exercise
gymup-tracker analyze --db /path/to/workout.db "Bench Press"
```

## AI Setup

This app uses Ollama for local LLM inference. Install and start Ollama:

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama
ollama serve

# Pull a model
ollama pull mistral:7b
```

## Usage

1. Start the app: `gymup-tracker start --db ./workout.db`
2. Navigate to http://localhost:8501
3. Browse your programs, exercises, and training history
4. Use AI analysis to get weight recommendations

## Development

```bash
# Run the Streamlit app directly
streamlit run src/gymup_tracker/ui/app.py

# Run tests
pytest
```

## License

MIT

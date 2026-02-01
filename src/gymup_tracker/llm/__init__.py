"""LLM integration for AI-powered recommendations."""

from gymup_tracker.llm.client import OllamaClient, LLMResponse, get_ollama_status
from gymup_tracker.llm.functions import (
    analyze_exercise_progression,
    suggest_next_weights,
    generate_workout_plan,
)
from gymup_tracker.llm.setup import ensure_ollama_ready

__all__ = [
    "OllamaClient",
    "LLMResponse",
    "get_ollama_status",
    "analyze_exercise_progression",
    "suggest_next_weights",
    "generate_workout_plan",
    "ensure_ollama_ready",
]

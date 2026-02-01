"""Configuration management for GymUp Tracker."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    path: Path = Field(default=Path("workout.db"))
    auto_backup: bool = True
    backup_dir: Path = Field(default=Path.home() / ".gymup-tracker" / "backups")


class LLMSettings(BaseSettings):
    """LLM configuration for Ollama."""

    base_url: str = "http://localhost:11434"
    model: str = "mistral:7b"
    temperature: float = 0.3
    max_tokens: int = 500
    timeout: int = 120  # Increased timeout for model loading
    fallback_to_rules: bool = True


class UISettings(BaseSettings):
    """UI configuration."""

    port: int = 8501
    theme: str = "dark"
    items_per_page: int = 20


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="GYMUP_",
        env_nested_delimiter="__",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    ui: UISettings = Field(default_factory=UISettings)

    config_dir: Path = Field(default=Path.home() / ".gymup-tracker")

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from environment and optional config file."""
        return cls()


# Global settings instance
settings = Settings()

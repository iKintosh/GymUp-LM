"""Ollama API client for LLM integration."""

import json
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import httpx

from gymup_tracker.config import settings


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    done: bool
    total_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None


class OllamaClient:
    """Client for Ollama API."""

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        timeout: int = None,
    ):
        self.base_url = base_url or settings.llm.base_url
        self.model = model or settings.llm.model
        self.timeout = timeout or settings.llm.timeout

    def _get_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(self._get_url("/api/tags"))
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def list_models(self) -> list[str]:
        """List available models."""
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(self._get_url("/api/tags"))
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        return []

    def has_model(self, model: str = None) -> bool:
        """Check if a specific model is available."""
        model = model or self.model
        models = self.list_models()
        # Check both exact match and base name match
        return any(m == model or m.startswith(model.split(":")[0]) for m in models)

    def generate(
        self,
        prompt: str,
        system: str = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> LLMResponse:
        """Generate a completion from the model."""
        temperature = temperature or settings.llm.temperature
        max_tokens = max_tokens or settings.llm.max_tokens

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self._get_url("/api/generate"),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                return LLMResponse(
                    content=data.get("response", ""),
                    model=data.get("model", self.model),
                    done=data.get("done", True),
                    total_duration=data.get("total_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                )
        except httpx.HTTPError as e:
            return LLMResponse(
                content=f"Error communicating with Ollama: {str(e)}",
                model=self.model,
                done=True,
            )

    def chat(
        self,
        messages: list[dict],
        temperature: float = None,
        max_tokens: int = None,
    ) -> LLMResponse:
        """Chat completion with message history."""
        temperature = temperature or settings.llm.temperature
        max_tokens = max_tokens or settings.llm.max_tokens

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self._get_url("/api/chat"),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                message = data.get("message", {})
                return LLMResponse(
                    content=message.get("content", ""),
                    model=data.get("model", self.model),
                    done=data.get("done", True),
                    total_duration=data.get("total_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                )
        except httpx.HTTPError as e:
            return LLMResponse(
                content=f"Error communicating with Ollama: {str(e)}",
                model=self.model,
                done=True,
            )

    async def generate_stream(
        self,
        prompt: str,
        system: str = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from the model."""
        temperature = temperature or settings.llm.temperature
        max_tokens = max_tokens or settings.llm.max_tokens

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                self._get_url("/api/generate"),
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue


def get_ollama_status() -> dict:
    """Get Ollama status information."""
    client = OllamaClient()

    status = {
        "available": client.is_available(),
        "base_url": client.base_url,
        "configured_model": client.model,
        "models": [],
        "model_ready": False,
    }

    if status["available"]:
        status["models"] = client.list_models()
        status["model_ready"] = client.has_model()

    return status


def get_installation_instructions() -> str:
    """Get Ollama installation instructions."""
    return """
## Ollama Installation

Ollama is required for AI-powered recommendations.

### macOS
```bash
brew install ollama
```
Or download from https://ollama.com/download

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Start Ollama
```bash
ollama serve
```

### Pull a model
```bash
ollama pull mistral:7b
```

After installation, restart the app to enable AI features.
"""

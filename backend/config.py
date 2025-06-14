"""Centralised configuration loader using environment variables (.env)."""

import os
from dotenv import load_dotenv

# Load .env file once
load_dotenv()

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# Default model details – can be overridden in .env
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

__all__ = [
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_TEMPERATURE",
] 
"""Pytest bootstrap — set required env vars before app modules load."""

import os

os.environ.setdefault("GROQ_API_KEY", "test-key-for-pytest")
os.environ.setdefault("LLM_PROVIDER", "GROQ")
os.environ.setdefault(
    "JWT_SECRET",
    "test_jwt_secret_at_least_32_characters_long",
)

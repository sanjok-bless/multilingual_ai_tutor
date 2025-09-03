"""Test the main FastAPI application."""

import os
from unittest.mock import patch


def test_create_app() -> None:
    """Test that the FastAPI app is created successfully."""
    from backend.main import create_app

    # Mock environment with required API key
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-for-testing"}):
        app = create_app()
        assert app is not None
        assert app.title == "Multilingual AI Tutor"
        assert app.version == "0.1.0"

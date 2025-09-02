"""Test the main FastAPI application."""


def test_create_app() -> None:
    """Test that the FastAPI app is created successfully."""
    from backend.main import create_app

    app = create_app()
    assert app is not None
    assert app.title == "Multilingual AI Tutor"
    assert app.version == "0.1.0"

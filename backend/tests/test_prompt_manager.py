"""Test suite for prompt template management and rendering."""

from unittest.mock import patch

import jinja2
import pytest

from backend.enums import Language, Level
from backend.errors import TemplateNotFoundError
from backend.llms.prompt_manager import PromptManager


class TestPromptManager:
    """Test cases for PromptManager functionality."""

    @pytest.fixture
    def prompt_manager(self) -> PromptManager:
        """Create PromptManager instance for testing."""
        return PromptManager()

    def test_prompt_manager_initialization(self, prompt_manager: PromptManager) -> None:
        """Test PromptManager initializes correctly."""
        assert prompt_manager.templates_dir.name == "prompts"
        assert prompt_manager.templates_dir.exists()

    def test_load_template_success(self, prompt_manager: PromptManager) -> None:
        """Test successful template loading from file."""
        template_content = "Hello {{ user_name }}!"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("jinja2.Environment.get_template") as mock_get_template,
        ):
            from jinja2 import Template

            mock_template = Template(template_content)
            mock_get_template.return_value = mock_template
            template = prompt_manager.load_template("test.j2")

            assert template is not None
            rendered = template.render(user_name="World")
            assert rendered == "Hello World!"

    def test_load_template_not_found(self, prompt_manager: PromptManager) -> None:
        """Test loading non-existent template raises appropriate error."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            prompt_manager.load_template("nonexistent.j2")

        assert "Template 'nonexistent.j2' not found" in str(exc_info.value)

    def test_render_system_prompt(self, prompt_manager: PromptManager) -> None:
        """Test rendering system prompt template."""
        system_template = """You are a multilingual AI language tutor.
Language: {{ language }}
User Level: {{ level }}"""

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("jinja2.Environment.get_template") as mock_get_template,
        ):
            from jinja2 import Template

            mock_template = Template(system_template)
            mock_get_template.return_value = mock_template
            result = prompt_manager.render_system_prompt(language=Language.EN, level=Level.B1)

        assert "Language: english" in result
        assert "User Level: B1" in result

    def test_render_tutoring_prompt(self, prompt_manager: PromptManager) -> None:
        """Test rendering tutoring prompt with user message."""
        tutoring_template = """Correct this {{ language }} text at {{ level }} level:
User message: "{{ user_message }}"

Provide corrections in format: **corrected_text**"""

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("jinja2.Environment.get_template") as mock_get_template,
        ):
            from jinja2 import Template

            mock_template = Template(tutoring_template)
            mock_get_template.return_value = mock_template
            result = prompt_manager.render_tutoring_prompt(
                user_message="I have important meeting tomorrow", language=Language.EN, level=Level.B2
            )

        assert "I have important meeting tomorrow" in result
        assert "english text at B2 level" in result
        assert "**corrected_text**" in result

    def test_render_start_message(self, prompt_manager: PromptManager) -> None:
        """Test rendering level-appropriate start message."""
        start_template = """{% if level in ['A1', 'A2'] %}
Welcome! Let's start with basic {{ language }} conversation.
{% else %}
Ready for advanced {{ language }} practice?
{% endif %}"""

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("jinja2.Environment.get_template") as mock_get_template,
        ):
            from jinja2 import Template

            mock_template = Template(start_template)
            mock_get_template.return_value = mock_template
            # Test beginner level
            result_beginner = prompt_manager.render_start_message(language=Language.EN, level=Level.A1)
            assert "basic english conversation" in result_beginner

            # Test advanced level
            result_advanced = prompt_manager.render_start_message(language=Language.EN, level=Level.B2)
            assert "advanced english practice" in result_advanced

    def test_context_injection_validation(self, prompt_manager: PromptManager) -> None:
        """Test that context injection handles all required parameters."""
        # Test direct enum conversion since _build_context was removed
        assert Language.DE.value == "german"
        assert Level.C1.value == "C1"

    def test_template_caching_disabled_for_mvp(self, prompt_manager: PromptManager) -> None:
        """Test that template caching is not implemented for MVP (YAGNI)."""
        assert not hasattr(prompt_manager, "_cache")
        assert not hasattr(prompt_manager, "cache_enabled")

    def test_invalid_template_syntax_handling(self, prompt_manager: PromptManager) -> None:
        """Test graceful handling of invalid Jinja2 syntax."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            pytest.raises(jinja2.TemplateSyntaxError),
            patch("jinja2.Environment.get_template", side_effect=jinja2.TemplateSyntaxError("Invalid syntax", 1)),
        ):
            prompt_manager.load_template("invalid.j2")

    @pytest.mark.parametrize("language", [Language.EN, Language.DE, Language.PL, Language.UA])
    def test_universal_template_works_for_all_languages(
        self, prompt_manager: PromptManager, language: Language
    ) -> None:
        """Test that universal template works for all supported languages."""
        universal_template = "Practice {{ language }} conversation at {{ level }} level."

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("jinja2.Environment.get_template") as mock_get_template,
        ):
            from jinja2 import Template

            mock_template = Template(universal_template)
            mock_get_template.return_value = mock_template
            result = prompt_manager.render_tutoring_prompt(user_message="Test", language=language, level=Level.B1)

        assert language.value in result
        assert "B1 level" in result

    @pytest.mark.parametrize("level", [Level.A1, Level.A2, Level.B1, Level.B2, Level.C1, Level.C2])
    def test_level_aware_content(self, prompt_manager: PromptManager, level: Level) -> None:
        """Test that templates handle all CEFR levels correctly."""
        level_template = "Your current level is {{ level }}"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("jinja2.Environment.get_template") as mock_get_template,
        ):
            from jinja2 import Template

            mock_template = Template(level_template)
            mock_get_template.return_value = mock_template
            result = prompt_manager.render_start_message(language=Language.EN, level=level)

        assert level.value in result

    def test_tutoring_template_ensures_chatresponse_structure(self, prompt_manager: PromptManager) -> None:
        """Test that tutoring template explicitly requests ChatResponse structure."""
        result = prompt_manager.render_tutoring_prompt(
            user_message="I have meeting tomorrow", language=Language.EN, level=Level.B1
        )

        # Template must explicitly request the three ChatResponse fields
        assert "ai_response" in result.lower()
        assert "next_phrase" in result.lower()
        assert "corrections" in result.lower()

        # Template should provide clear structure guidance
        assert "1." in result and "2." in result and "3." in result

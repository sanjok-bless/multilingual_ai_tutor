"""Test suite for prompt template management and rendering."""

from unittest.mock import patch

import jinja2
import pytest

from tutor_ai.enums import Language, Level
from tutor_ai.errors import TemplateNotFoundError
from tutor_ai.llms.prompt_manager import PromptManager


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

    def test_render_tutoring_prompt_without_context(self, prompt_manager: PromptManager) -> None:
        """Test tutoring prompt renders correctly without context messages."""
        result = prompt_manager.render_tutoring_prompt(
            user_message="Hello world", language=Language.EN, level=Level.B1, context_messages=None
        )

        assert "Hello world" in result
        assert "Previous Conversation" not in result

        # Test with explicit empty list
        result_empty = prompt_manager.render_tutoring_prompt(
            user_message="Hello world", language=Language.EN, level=Level.B1, context_messages=[]
        )

        assert "Hello world" in result_empty
        assert "Previous Conversation" not in result_empty

    def test_render_tutoring_prompt_with_context(self, prompt_manager: PromptManager) -> None:
        """Test tutoring prompt includes context messages when provided."""
        context = [
            {"type": "user", "content": "I have meeting tomorrow"},
            {"type": "ai", "content": "That's great! What time?"},
            {"type": "user", "content": "At 10 AM"},
            {"type": "ai", "content": "Perfect. Good luck!"},
            {"type": "user", "content": "Thank you"},
        ]

        result = prompt_manager.render_tutoring_prompt(
            user_message="Can you help me prepare?", language=Language.EN, level=Level.B2, context_messages=context
        )

        # Context section should be present
        assert "Previous Conversation" in result

        # Historical context messages should appear (excluding last user message)
        assert "I have meeting tomorrow" in result
        assert "That's great! What time?" in result
        assert "At 10 AM" in result
        assert "Perfect. Good luck!" in result
        # Last user message from context should NOT appear in history (filtered out)
        assert result.count("Thank you") == 0

        # Current message should be present with explicit header
        assert "Current User Message to Analyze" in result
        assert "Can you help me prepare?" in result

    def test_render_tutoring_prompt_truncates_to_20_messages(self, prompt_manager: PromptManager) -> None:
        """Test tutoring prompt truncates context to last 20 messages."""
        # Create 25 messages with unique prefixes to avoid substring matching issues
        context = [{"type": "user" if i % 2 == 0 else "ai", "content": f"Msg_{i:03d}"} for i in range(25)]

        result = prompt_manager.render_tutoring_prompt(
            user_message="Final message", language=Language.EN, level=Level.B1, context_messages=context
        )

        # First 5 messages (0-4) should be truncated
        assert "Msg_000" not in result
        assert "Msg_001" not in result
        assert "Msg_002" not in result
        assert "Msg_003" not in result
        assert "Msg_004" not in result

        # Last 20 messages (5-24) are processed, but last user message (Msg_024) is filtered
        assert "Msg_005" in result
        assert "Msg_023" in result  # Last AI message before filtering
        assert "Msg_024" not in result  # Filtered as last user message

        # Current message should be present
        assert "Final message" in result

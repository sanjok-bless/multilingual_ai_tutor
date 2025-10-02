"""Test suite for context message processing."""

from backend.llms.context_processor import extract_context_with_user_validated_ai


class TestExtractContextWithUserValidatedAI:
    """Test cases for context extraction logic."""

    def test_empty_messages_returns_empty_array(self) -> None:
        """Test that empty messages array returns empty context."""
        result = extract_context_with_user_validated_ai([], 20)
        assert result == []

    def test_extract_user_messages_correctly(self) -> None:
        """Test that user messages are extracted correctly."""
        messages = [
            {"type": "user", "content": "Hello"},
            {"type": "user", "content": "How are you?"},
        ]

        result = extract_context_with_user_validated_ai(messages, 20)

        assert len(result) == 2
        assert result[0] == {"type": "user", "content": "Hello"}
        assert result[1] == {"type": "user", "content": "How are you?"}

    def test_skip_ai_messages_without_immediate_user_validation(self) -> None:
        """Test that AI messages without user validation are skipped."""
        messages = [
            {"type": "ai", "content": "Hi there!"},
        ]

        result = extract_context_with_user_validated_ai(messages, 20)

        assert result == []

    def test_include_ai_messages_when_immediately_followed_by_user_message(self) -> None:
        """Test that AI messages are included when followed by user message."""
        messages = [
            {"type": "ai", "content": "Hello!"},
            {"type": "user", "content": "Hi back"},
        ]

        result = extract_context_with_user_validated_ai(messages, 20)

        assert len(result) == 2
        assert result[0] == {"type": "ai", "content": "Hello!"}
        assert result[1] == {"type": "user", "content": "Hi back"}

    def test_respect_limit_parameter(self) -> None:
        """Test that the limit parameter is respected."""
        messages = [{"type": "user", "content": f"Message {i}"} for i in range(50)]

        result = extract_context_with_user_validated_ai(messages, 10)

        assert len(result) == 10
        assert result[0]["content"] == "Message 40"
        assert result[9]["content"] == "Message 49"

    def test_return_last_n_validated_messages_when_limit_applied(self) -> None:
        """Test that last N validated messages are returned when limit is applied."""
        messages = [
            {"type": "user", "content": "User 1"},
            {"type": "ai", "content": "AI 1"},
            {"type": "user", "content": "User 2"},
            {"type": "ai", "content": "AI 2"},
            {"type": "user", "content": "User 3"},
            {"type": "ai", "content": "AI 3"},
            {"type": "user", "content": "User 4"},
        ]

        result = extract_context_with_user_validated_ai(messages, 3)

        assert len(result) == 3
        assert result[0]["content"] == "User 3"
        assert result[1]["content"] == "AI 3"
        assert result[2]["content"] == "User 4"

    def test_handle_typical_tutoring_conversation_flow(self) -> None:
        """Test handling of typical tutoring conversation flow."""
        messages = [
            {"type": "ai", "content": "Hello! Ready to practice?"},
            {"type": "user", "content": "Yes, I am ready"},
            {"type": "ai", "content": "Great! Tell me about your day."},
            {"type": "user", "content": "I goed to the park"},
            {"type": "ai", "content": 'Good try! The correct form is "I went to the park"'},
            {"type": "user", "content": "Oh, I went to the park"},
        ]

        result = extract_context_with_user_validated_ai(messages, 20)

        assert len(result) == 6
        assert result[0]["type"] == "ai"
        assert result[0]["content"] == "Hello! Ready to practice?"
        assert result[1]["type"] == "user"
        assert result[5]["type"] == "user"
        assert result[5]["content"] == "Oh, I went to the park"

    def test_exclude_unresponded_ai_message_at_end_of_conversation(self) -> None:
        """Test that unresponded AI message at end is excluded."""
        messages = [
            {"type": "user", "content": "Hello"},
            {"type": "ai", "content": "Hi there!"},
            {"type": "user", "content": "How are you?"},
            {"type": "ai", "content": "I am good! And you?"},
        ]

        result = extract_context_with_user_validated_ai(messages, 20)

        assert len(result) == 3
        assert result[-1]["type"] == "user"
        assert result[-1]["content"] == "How are you?"

    def test_handle_alternating_conversation_with_limit(self) -> None:
        """Test handling of alternating conversation with limit."""
        messages = [
            {"type": "ai", "content": "AI 1"},
            {"type": "user", "content": "User 1"},
            {"type": "ai", "content": "AI 2"},
            {"type": "user", "content": "User 2"},
            {"type": "ai", "content": "AI 3"},
            {"type": "user", "content": "User 3"},
            {"type": "ai", "content": "AI 4"},
            {"type": "user", "content": "User 4"},
        ]

        result = extract_context_with_user_validated_ai(messages, 4)

        assert len(result) == 4
        assert result[0]["content"] == "AI 3"
        assert result[1]["content"] == "User 3"
        assert result[2]["content"] == "AI 4"
        assert result[3]["content"] == "User 4"

    def test_handle_complex_conversation_with_mixed_patterns(self) -> None:
        """Test handling of complex conversation with mixed patterns."""
        messages = [
            {"type": "user", "content": "Hello"},
            {"type": "ai", "content": "Hi!"},
            {"type": "ai", "content": "How can I help?"},
            {"type": "user", "content": "I need help"},
            {"type": "user", "content": "With grammar"},
            {"type": "ai", "content": "Sure!"},
            {"type": "user", "content": "Thanks"},
        ]

        result = extract_context_with_user_validated_ai(messages, 20)

        # AI messages validated only if immediately followed by user:
        # - 'Hi!' at index 1, next is 'How can I help?' (AI) - NOT included
        # - 'How can I help?' at index 2, next is 'I need help' (user) - included
        # - 'Sure!' at index 5, next is 'Thanks' (user) - included
        assert len(result) == 6
        assert result[0]["content"] == "Hello"
        assert result[1]["content"] == "How can I help?"
        assert result[2]["content"] == "I need help"
        assert result[3]["content"] == "With grammar"
        assert result[4]["content"] == "Sure!"
        assert result[5]["content"] == "Thanks"

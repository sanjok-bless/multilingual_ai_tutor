"""Tests for Pydantic schemas and data models."""

import uuid

import pytest
from pydantic import ValidationError

from tutor_ai.chat.schemas import (
    ChatRequest,
    ChatResponse,
    Correction,
    StartMessageRequest,
    StartMessageResponse,
)
from tutor_ai.enums import ErrorType, Language, Level


class TestLanguageEnum:
    """Test Language enum validation."""

    def test_valid_language_codes(self) -> None:
        """Test valid language codes are accepted."""
        assert Language.EN == "english"
        assert Language.DE == "german"
        assert Language.PL == "polish"
        assert Language.UA == "ukrainian"

    def test_invalid_language_code_raises_error(self) -> None:
        """Test invalid language code raises ValidationError."""
        with pytest.raises(ValueError):
            Language("french")


class TestLevelEnum:
    """Test Level enum validation."""

    def test_valid_level_codes(self) -> None:
        """Test valid CEFR level codes are accepted."""
        assert Level.A1 == "A1"
        assert Level.A2 == "A2"
        assert Level.B1 == "B1"
        assert Level.B2 == "B2"
        assert Level.C1 == "C1"
        assert Level.C2 == "C2"

    def test_invalid_level_code_raises_error(self) -> None:
        """Test invalid level code raises ValidationError."""
        with pytest.raises(ValueError):
            Level("D1")


class TestErrorTypeEnum:
    """Test ErrorType enum validation."""

    def test_valid_error_types(self) -> None:
        """Test valid error types are accepted."""
        assert ErrorType.GRAMMAR == "GRAMMAR"
        assert ErrorType.VOCABULARY == "VOCABULARY"
        assert ErrorType.SPELLING == "SPELLING"
        assert ErrorType.PUNCTUATION == "PUNCTUATION"


class TestCorrectionModel:
    """Test Correction Pydantic model with structured explanation format."""

    def test_valid_correction_creation(self) -> None:
        """Test valid correction model creation with structured explanation."""
        correction = Correction(
            original="I have meeting tomorrow",
            corrected="I have a meeting tomorrow",
            explanation=["Missing Article", "'a' before noun (required for countable nouns)"],
            error_type=ErrorType.GRAMMAR,
        )

        assert correction.original == "I have meeting tomorrow"
        assert correction.corrected == "I have a meeting tomorrow"
        assert correction.explanation == ["Missing Article", "'a' before noun (required for countable nouns)"]
        assert correction.error_type == ErrorType.GRAMMAR

    def test_correction_with_vowel_sound_example(self) -> None:
        """Test correction with vowel sound explanation from demo."""
        correction = Correction(
            original="important meeting",
            corrected="an important meeting",
            explanation=["Missing Article", "\"an\" important meeting (use 'an' before vowel sounds)"],
            error_type=ErrorType.GRAMMAR,
        )

        assert correction.explanation[0] == "Missing Article"
        assert correction.explanation[1] == "\"an\" important meeting (use 'an' before vowel sounds)"

    def test_correction_with_infinitive_example(self) -> None:
        """Test correction with infinitive explanation from demo."""
        correction = Correction(
            original="need practice",
            corrected="need to practice",
            explanation=["Infinitive Marker", "\"need to practice\" (infinitive required after 'need')"],
            error_type=ErrorType.GRAMMAR,
        )

        assert correction.explanation[0] == "Infinitive Marker"
        assert correction.explanation[1] == "\"need to practice\" (infinitive required after 'need')"

    def test_correction_requires_all_fields(self) -> None:
        """Test correction model requires all fields."""
        with pytest.raises(ValidationError):
            Correction(
                original="test",
                corrected="test",
                # Missing explanation and error_type
            )

    def test_correction_validates_non_empty_strings(self) -> None:
        """Test correction model validates non-empty strings."""
        with pytest.raises(ValidationError):
            Correction(
                original="",  # Empty string should fail
                corrected="test",
                explanation=["Grammar", "test explanation"],
                error_type=ErrorType.GRAMMAR,
            )

    def test_correction_validates_explanation_length(self) -> None:
        """Test correction validates explanation has exactly 2 elements."""
        with pytest.raises(ValidationError):
            Correction(
                original="test",
                corrected="test fixed",
                explanation=["Grammar"],  # Missing second element
                error_type=ErrorType.GRAMMAR,
            )

        with pytest.raises(ValidationError):
            Correction(
                original="test",
                corrected="test fixed",
                explanation=["Grammar", "explanation", "extra"],  # Too many elements
                error_type=ErrorType.GRAMMAR,
            )

    def test_spelling_error_type(self) -> None:
        """Test spelling error correction."""
        correction = Correction(
            original="recieve",
            corrected="receive",
            explanation=["Spelling", '"receive" (i before e except after c)'],
            error_type=ErrorType.SPELLING,
        )

        assert correction.error_type == ErrorType.SPELLING
        assert correction.explanation[1] == '"receive" (i before e except after c)'

    def test_punctuation_error_type(self) -> None:
        """Test punctuation error correction."""
        correction = Correction(
            original="Hello how are you",
            corrected="Hello, how are you?",
            explanation=["Punctuation", "comma after greeting, question mark for question"],
            error_type=ErrorType.PUNCTUATION,
        )

        assert correction.error_type == ErrorType.PUNCTUATION
        assert correction.explanation[1] == "comma after greeting, question mark for question"

    def test_vocabulary_error_type(self) -> None:
        """Test vocabulary error correction."""
        correction = Correction(
            original="I'm very happy",
            corrected="I'm delighted",
            explanation=["Vocabulary", "\"delighted\" (more formal than 'very happy')"],
            error_type=ErrorType.VOCABULARY,
        )

        assert correction.error_type == ErrorType.VOCABULARY
        assert correction.explanation[1] == "\"delighted\" (more formal than 'very happy')"


class TestChatRequestModel:
    """Test ChatRequest Pydantic model."""

    def test_valid_chat_request_creation(self) -> None:
        """Test valid chat request model creation with UUID session_id."""
        session_id = str(uuid.uuid4())
        request = ChatRequest(
            message="Hello, how are you?",
            language=Language.EN,
            level=Level.B1,
            session_id=session_id,
        )

        assert request.message == "Hello, how are you?"
        assert request.language == Language.EN
        assert request.level == Level.B1
        assert request.session_id == session_id

    def test_chat_request_requires_all_fields(self) -> None:
        """Test chat request requires all fields."""
        with pytest.raises(ValidationError):
            ChatRequest(
                message="Hello",
                language=Language.EN,
                # Missing level and session_id
            )

    def test_chat_request_validates_message_not_empty(self) -> None:
        """Test chat request validates message is not empty."""
        with pytest.raises(ValidationError):
            ChatRequest(
                message="",  # Empty message should fail
                language=Language.EN,
                level=Level.B1,
                session_id=str(uuid.uuid4()),
            )

    def test_chat_request_validates_uuid_session_id_format(self) -> None:
        """Test chat request validates UUID session ID format."""
        # Valid UUID format should pass
        valid_uuid = str(uuid.uuid4())
        request = ChatRequest(
            message="Hello",
            language=Language.EN,
            level=Level.B1,
            session_id=valid_uuid,
        )
        assert request.session_id == valid_uuid

        # Invalid UUID format should fail
        with pytest.raises(ValidationError):
            ChatRequest(
                message="Hello",
                language=Language.EN,
                level=Level.B1,
                session_id="not-a-uuid",
            )


class TestChatResponseModel:
    """Test ChatResponse Pydantic model with ai_response and next_phrase fields."""

    def test_valid_chat_response_creation_with_corrections(self) -> None:
        """Test valid chat response model creation with natural error explanations."""
        correction = Correction(
            original="I have meeting",
            corrected="I have a meeting",
            explanation=["Missing Article", '"a" before noun (required for countable nouns)'],
            error_type=ErrorType.GRAMMAR,
        )

        session_id = str(uuid.uuid4())
        response = ChatResponse(
            ai_response="I have **a** meeting tomorrow. Remember to use 'a' before countable nouns!",
            next_phrase="That sounds important! What's the meeting about?",
            corrections=[correction],
            session_id=session_id,
            tokens_used=50,
        )

        assert "Remember to use 'a' before countable nouns" in response.ai_response
        assert response.next_phrase == "That sounds important! What's the meeting about?"
        assert len(response.corrections) == 1
        assert response.corrections[0] == correction
        assert response.session_id == session_id
        assert response.tokens_used == 50

    def test_chat_response_perfect_english_no_corrections(self) -> None:
        """Test chat response when English is perfect - positive feedback in ai_response."""
        response = ChatResponse(
            ai_response="Excellent! Your English is perfect.",
            next_phrase="Let's continue our conversation. What would you like to talk about?",
            corrections=[],
            session_id=str(uuid.uuid4()),
            tokens_used=30,
        )

        assert response.ai_response == "Excellent! Your English is perfect."
        assert response.next_phrase == "Let's continue our conversation. What would you like to talk about?"
        assert len(response.corrections) == 0

    def test_chat_response_requires_non_negative_tokens(self) -> None:
        """Test chat response requires non-negative token count."""
        # Zero tokens should be allowed (cached responses, errors)
        response = ChatResponse(
            ai_response="Test ai response",
            next_phrase="Test next phrase",
            corrections=[],
            session_id=str(uuid.uuid4()),
            tokens_used=0,  # Zero tokens should pass
        )
        assert response.tokens_used == 0

        # Negative tokens should fail
        with pytest.raises(ValidationError):
            ChatResponse(
                ai_response="Test ai response",
                next_phrase="Test next phrase",
                corrections=[],
                session_id=str(uuid.uuid4()),
                tokens_used=-1,  # Negative tokens should fail
            )

    def test_chat_response_validates_non_empty_next_phrase(self) -> None:
        """Test chat response validates next_phrase is not empty."""
        with pytest.raises(ValidationError):
            ChatResponse(
                ai_response="Test ai response",
                next_phrase="",  # Empty next phrase should fail
                corrections=[],
                session_id=str(uuid.uuid4()),
                tokens_used=10,
            )

    def test_chat_response_validates_non_empty_ai_response(self) -> None:
        """Test chat response validates ai_response is not empty."""
        with pytest.raises(ValidationError):
            ChatResponse(
                ai_response="",  # Empty ai response should fail
                next_phrase="Test next phrase",
                corrections=[],
                session_id=str(uuid.uuid4()),
                tokens_used=10,
            )

    def test_chat_response_with_multiple_corrections_demo_format(self) -> None:
        """Test chat response with multiple corrections and natural explanations."""
        corrections = [
            Correction(
                original="important meeting",
                corrected="an important meeting",
                explanation=["Missing Article", "\"an\" important meeting (use 'an' before vowel sounds)"],
                error_type=ErrorType.GRAMMAR,
            ),
            Correction(
                original="need practice",
                corrected="need to practice",
                explanation=["Infinitive Marker", "\"need to practice\" (infinitive required after 'need')"],
                error_type=ErrorType.GRAMMAR,
            ),
        ]

        ai_response_text = (
            "I have **an** important meeting tomorrow and I need **to** practice my presentation skills. "
            "Great topic! Remember: use 'an' before vowel sounds like 'important', and always include "
            "'to' after 'need' when followed by a verb. These small details make your English sound natural!"
        )
        next_phrase_text = (
            "Great! I'd be happy to help you practice. Presentations can be nerve-wracking, "
            "but practice makes perfect. What's your presentation about?"
        )

        response = ChatResponse(
            ai_response=ai_response_text,
            next_phrase=next_phrase_text,
            corrections=corrections,
            session_id=str(uuid.uuid4()),
            tokens_used=75,
        )

        assert len(response.corrections) == 2
        assert "use 'an' before vowel sounds" in response.ai_response
        assert "include 'to' after 'need'" in response.ai_response
        assert "These small details make your English sound natural!" in response.ai_response
        assert response.next_phrase == next_phrase_text
        assert response.corrections[0].explanation[0] == "Missing Article"
        assert response.corrections[0].explanation[1] == "\"an\" important meeting (use 'an' before vowel sounds)"
        assert response.corrections[1].explanation[0] == "Infinitive Marker"
        assert response.corrections[1].explanation[1] == "\"need to practice\" (infinitive required after 'need')"


class TestMultilingualContent:
    """Test handling of multilingual content with Unicode characters."""

    def test_correction_with_polish_content(self) -> None:
        correction_valid = Correction(
            original="Jutro mam spotkań",
            corrected="Jutro mam spotkanie",
            explanation=["Accusative Case", "spotkanie (accusative singular, not genitive plural)"],
            error_type=ErrorType.GRAMMAR,
        )
        assert correction_valid.original == "Jutro mam spotkań"
        assert correction_valid.corrected == "Jutro mam spotkanie"

    def test_correction_with_german_content(self) -> None:
        """Test correction with German characters and content."""
        correction = Correction(
            original="Ich gehe zu Schule",
            corrected="Ich gehe zur Schule",
            explanation=["Dative Preposition", "zur Schule (zu + der = zur, dative case required)"],
            error_type=ErrorType.GRAMMAR,
        )
        assert "zur Schule" in correction.corrected
        assert "dative case" in correction.explanation[1]

    def test_correction_with_ukrainian_content(self) -> None:
        """Test correction with Ukrainian Cyrillic characters."""
        correction_valid = Correction(
            original="Я є студент",
            corrected="Я студент",
            explanation=["Verb Omission", "є (auxiliary 'to be' usually omitted in present tense)"],
            error_type=ErrorType.GRAMMAR,
        )
        assert "студент" in correction_valid.corrected
        assert "є" not in correction_valid.corrected

    def test_chat_request_with_unicode_content(self) -> None:
        """Test chat request with various Unicode characters."""
        request = ChatRequest(
            message="Привіт! Jak się masz? Wie geht's? 🌟",
            language=Language.UA,
            level=Level.B2,
            session_id=str(uuid.uuid4()),
        )
        assert "🌟" in request.message
        assert "Привіт" in request.message
        assert request.language == Language.UA


class TestStartMessageRequestModel:
    """Test StartMessageRequest Pydantic model."""

    def test_valid_start_message_request_creation(self) -> None:
        """Test valid start message request model creation."""
        session_id = str(uuid.uuid4())
        request = StartMessageRequest(
            language=Language.EN,
            level=Level.B1,
            session_id=session_id,
        )

        assert request.language == Language.EN
        assert request.level == Level.B1
        assert request.session_id == session_id

    def test_start_message_request_requires_all_fields(self) -> None:
        """Test start message request requires all fields."""
        with pytest.raises(ValidationError):
            StartMessageRequest(
                language=Language.EN,
                # Missing level and session_id
            )

    def test_start_message_request_validates_uuid_session_id_format(self) -> None:
        """Test start message request validates UUID session_id format."""
        # Invalid UUID should fail
        with pytest.raises(ValidationError) as exc_info:
            StartMessageRequest(
                language=Language.EN,
                level=Level.B1,
                session_id="not-a-uuid",
            )
        assert "session_id must be a valid UUID format" in str(exc_info.value)


class TestStartMessageResponseModel:
    """Test StartMessageResponse Pydantic model."""

    def test_valid_start_message_response_creation(self) -> None:
        """Test valid start message response model creation."""
        session_id = str(uuid.uuid4())
        response = StartMessageResponse(
            message="Hello! I'm your AI language tutor. Ready to practice English?",
            session_id=session_id,
            tokens_used=25,
        )

        assert response.message == "Hello! I'm your AI language tutor. Ready to practice English?"
        assert response.session_id == session_id
        assert response.tokens_used == 25

    def test_start_message_response_requires_all_fields(self) -> None:
        """Test start message response requires all fields."""
        with pytest.raises(ValidationError):
            StartMessageResponse(
                message="Hello!",
                # Missing session_id and tokens_used
            )

    def test_start_message_response_validates_non_empty_message(self) -> None:
        """Test start message response validates non-empty message."""
        with pytest.raises(ValidationError):
            StartMessageResponse(
                message="",
                session_id=str(uuid.uuid4()),
                tokens_used=10,
            )

    def test_start_message_response_validates_non_negative_tokens(self) -> None:
        """Test start message response validates non-negative token counts."""
        with pytest.raises(ValidationError):
            StartMessageResponse(
                message="Hello!",
                session_id=str(uuid.uuid4()),
                tokens_used=-5,
            )


class TestContextMessagesValidation:
    """Test context_messages field validation for ChatRequest and StartMessageRequest."""

    def test_chat_request_with_valid_context_messages(self) -> None:
        """Test ChatRequest accepts valid context_messages structure."""
        context = [
            {"role": "user", "content": "Hello"},
            {"role": "ai", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        request = ChatRequest(
            message="I'm doing well",
            language=Language.EN,
            level=Level.B1,
            session_id=str(uuid.uuid4()),
            context_messages=context,
        )

        assert request.context_messages == context
        assert len(request.context_messages) == 3
        assert request.context_messages[0]["role"] == "user"
        assert request.context_messages[1]["role"] == "ai"

    def test_chat_request_context_messages_defaults_to_empty_list(self) -> None:
        """Test ChatRequest context_messages defaults to empty list when omitted."""
        request = ChatRequest(
            message="Hello",
            language=Language.EN,
            level=Level.B1,
            session_id=str(uuid.uuid4()),
            # context_messages omitted
        )

        assert request.context_messages == []
        assert isinstance(request.context_messages, list)

    def test_start_message_request_with_context_messages(self) -> None:
        """Test StartMessageRequest accepts valid context_messages structure."""
        context = [
            {"role": "user", "content": "Previous conversation"},
            {"role": "ai", "content": "Previous response"},
        ]

        request = StartMessageRequest(
            language=Language.EN, level=Level.B1, session_id=str(uuid.uuid4()), context_messages=context
        )

        assert request.context_messages == context
        assert len(request.context_messages) == 2

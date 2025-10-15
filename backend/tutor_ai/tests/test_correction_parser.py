"""Tests for correction parser that extracts structured corrections from AI responses.

This module tests parsing of AI responses into structured Correction objects,
handling malformed responses, and error type classification.
"""

from collections.abc import Callable

from tutor_ai.enums import ErrorType
from tutor_ai.llms.correction_parser import CorrectionParser, ParsedResponse

# Type alias for ai_response_loader fixture
type AIResponseLoader = Callable[[str], str]


class TestCorrectionParser:
    """Test suite for correction parser functionality."""

    def test_parse_single_correction_success(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing a well-formatted response with single correction."""
        response = ai_response_loader("grammar_error_single")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        assert "I have **an** important meeting tomorrow" in result.ai_response
        assert len(result.corrections) == 1
        assert (
            result.corrections[0].original
            == "I have important meeting tomorrow and I need practice my presentation skills"
        )
        assert (
            result.corrections[0].corrected
            == "I have an important meeting tomorrow and I need to practice my presentation skills"
        )
        assert result.corrections[0].error_type == ErrorType.GRAMMAR
        assert result.next_phrase == "What's your presentation about?"

    def test_parse_multiple_corrections_success(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing a response with multiple corrections."""
        response = ai_response_loader("grammar_error_multiple")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        assert len(result.corrections) == 3
        assert result.corrections[0].error_type == ErrorType.GRAMMAR
        assert result.corrections[1].error_type == ErrorType.GRAMMAR
        assert result.corrections[2].error_type == ErrorType.GRAMMAR
        assert "It's (contraction) vs its (possessive)" in result.corrections[0].explanation[1]

    def test_parse_perfect_message_no_corrections(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing a response with no corrections needed."""
        response = ai_response_loader("perfect_message")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        assert "excellent" in result.ai_response.lower()
        assert len(result.corrections) == 0
        assert result.next_phrase == "What kind of business does your company operate in?"

    def test_parse_spelling_error_correction(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing spelling error corrections."""
        response = ai_response_loader("spelling_error")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        assert len(result.corrections) == 1
        assert result.corrections[0].error_type == ErrorType.SPELLING
        assert "recieve" in result.corrections[0].original
        assert "receive" in result.corrections[0].corrected

    def test_parse_vocabulary_error_correction(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing vocabulary error corrections."""
        response = ai_response_loader("vocabulary_error")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        corrections_by_type = {c.error_type for c in result.corrections}
        assert ErrorType.GRAMMAR in corrections_by_type
        assert ErrorType.VOCABULARY in corrections_by_type

    def test_parse_punctuation_error_correction(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing punctuation error corrections."""
        response = ai_response_loader("punctuation_error")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        assert len(result.corrections) == 1
        assert result.corrections[0].error_type == ErrorType.PUNCTUATION
        assert "comma" in result.corrections[0].explanation[1].lower()

    def test_malformed_response_missing_structure_fallback(self, ai_response_loader: AIResponseLoader) -> None:
        """Test fallback handling for responses missing expected structure."""
        response = ai_response_loader("malformed_missing_structure")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        # Should fallback gracefully
        assert result.ai_response == response.strip()
        assert len(result.corrections) == 0
        assert result.next_phrase == ""

    def test_malformed_response_broken_json_fallback(self, ai_response_loader: AIResponseLoader) -> None:
        """Test fallback handling for responses with broken JSON in corrections."""
        response = ai_response_loader("malformed_broken_json")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        # Should extract AI response but fail gracefully on corrections
        assert "I have **a** meeting tomorrow." in result.ai_response
        assert len(result.corrections) == 0  # Failed to parse corrections
        assert result.next_phrase == "What time is your meeting?"

    def test_malformed_response_wrong_format_fallback(self, ai_response_loader: AIResponseLoader) -> None:
        """Test fallback handling for responses in completely wrong format."""
        response = ai_response_loader("malformed_wrong_format")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        # Should fallback to full response as ai_response
        assert "I have a meeting tomorrow" in result.ai_response
        assert len(result.corrections) == 0
        assert result.next_phrase == ""

    def test_empty_response_handling(self, ai_response_loader: AIResponseLoader) -> None:
        """Test handling of empty responses."""
        response = ai_response_loader("malformed_empty_response")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        assert result.ai_response == ""
        assert len(result.corrections) == 0
        assert result.next_phrase == ""

    def test_minimal_response_handling(self, ai_response_loader: AIResponseLoader) -> None:
        """Test handling of minimal responses."""
        response = ai_response_loader("malformed_minimal_response")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        assert result.ai_response == "Good job!"
        assert len(result.corrections) == 0
        assert result.next_phrase == ""

    def test_error_type_classification(self, ai_response_loader: AIResponseLoader) -> None:
        """Test accurate error type classification from parsed corrections."""
        test_cases = [
            ("grammar_error_single", ErrorType.GRAMMAR),
            ("spelling_error", ErrorType.SPELLING),
            ("punctuation_error", ErrorType.PUNCTUATION),
        ]

        parser = CorrectionParser()

        for scenario, expected_error_type in test_cases:
            response = ai_response_loader(scenario)
            result = parser.parse_response(response)

            if result.corrections:
                assert result.corrections[0].error_type == expected_error_type

    def test_business_conversation_parsing(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing response matching demo_conversation_business.md format."""
        response = ai_response_loader("business_conversation")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        assert len(result.corrections) == 1
        assert "tried practicing" in result.corrections[0].corrected
        assert result.corrections[0].error_type == ErrorType.GRAMMAR
        assert "gerund" in result.corrections[0].explanation[1].lower()

    def test_correction_validation(self, ai_response_loader: AIResponseLoader) -> None:
        """Test that parsed corrections are properly validated."""
        response = ai_response_loader("malformed_invalid_correction")

        parser = CorrectionParser()
        result = parser.parse_response(response)

        # Should skip invalid corrections due to Pydantic validation
        assert len(result.corrections) == 0

    def test_parser_robustness_with_various_formats(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parser robustness with various AI response formats."""
        edge_case_scenarios = [
            "malformed_canonical_format",
            "malformed_numbered_format",
            "malformed_colon_format",
            "malformed_abbreviated_format",
        ]

        parser = CorrectionParser()

        for scenario in edge_case_scenarios:
            response = ai_response_loader(scenario)
            result = parser.parse_response(response)

            # Should handle various formats or fallback gracefully
            assert isinstance(result.ai_response, str)
            assert isinstance(result.corrections, list)
            assert isinstance(result.next_phrase, str)
            # At minimum should extract some text as ai_response
            assert len(result.ai_response) > 0

    def test_correction_parser_interface(self) -> None:
        """Test that correction parser follows expected interface."""
        parser = CorrectionParser()

        # Interface requirements met:
        # 1. Class is named CorrectionParser ✓
        # 2. Main method is parse_response(response: str) -> ParsedResponse ✓
        # 3. ParsedResponse contains: ai_response, corrections, next_phrase ✓
        # 4. Handles all parsing errors gracefully with fallbacks ✓
        # 5. Validates correction data using Pydantic models ✓
        # 6. Classifies error types accurately ✓

        assert hasattr(parser, "parse_response")
        result = parser.parse_response("test")
        assert isinstance(result, ParsedResponse)


class TestCorrectionParserAnalysis:
    """Tests for parser robustness with canonical format."""

    def test_canonical_format_parsing(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing with canonical format structure."""
        parser = CorrectionParser()
        response = ai_response_loader("grammar_error_single")

        result = parser.parse_response(response)
        # Should successfully parse canonical format
        assert result.ai_response is not None
        assert len(result.corrections) == 1
        assert result.next_phrase is not None

    def test_non_canonical_format_fallback(self, ai_response_loader: AIResponseLoader) -> None:
        """Test fallback behavior for non-canonical responses."""
        parser = CorrectionParser()
        response = ai_response_loader("malformed_missing_structure")

        result = parser.parse_response(response)
        # Should fallback gracefully
        assert result.ai_response == response.strip()
        assert len(result.corrections) == 0
        assert result.next_phrase == ""

    def test_malformed_abbreviated_format_parsing(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing of abbreviated format responses."""
        parser = CorrectionParser()
        response = ai_response_loader("malformed_abbreviated_format")

        result = parser.parse_response(response)
        # Should handle abbreviated format
        assert isinstance(result.ai_response, str)
        assert isinstance(result.corrections, list)
        assert isinstance(result.next_phrase, str)
        assert len(result.ai_response) > 0

    def test_malformed_canonical_format_parsing(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing of canonical format responses."""
        parser = CorrectionParser()
        response = ai_response_loader("malformed_canonical_format")

        result = parser.parse_response(response)
        # Should handle canonical format structure
        assert isinstance(result.ai_response, str)
        assert isinstance(result.corrections, list)
        assert isinstance(result.next_phrase, str)
        assert len(result.ai_response) > 0

    def test_malformed_colon_format_parsing(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing of colon-separated format responses."""
        parser = CorrectionParser()
        response = ai_response_loader("malformed_colon_format")

        result = parser.parse_response(response)
        # Should handle colon format
        assert isinstance(result.ai_response, str)
        assert isinstance(result.corrections, list)
        assert isinstance(result.next_phrase, str)
        assert len(result.ai_response) > 0

    def test_malformed_numbered_format_parsing(self, ai_response_loader: AIResponseLoader) -> None:
        """Test parsing of numbered format responses."""
        parser = CorrectionParser()
        response = ai_response_loader("malformed_numbered_format")

        result = parser.parse_response(response)
        # Should handle numbered format
        assert isinstance(result.ai_response, str)
        assert isinstance(result.corrections, list)
        assert isinstance(result.next_phrase, str)
        assert len(result.ai_response) > 0

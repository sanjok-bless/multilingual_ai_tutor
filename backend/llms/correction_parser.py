"""Correction parser for extracting structured corrections from AI responses."""

import json
import re

from pydantic import BaseModel, ValidationError

from backend.chat.schemas import Correction


class ParsedResponse(BaseModel):
    """Parsed AI response containing corrections and metadata."""

    ai_response: str
    corrections: list[Correction] = []
    next_phrase: str = ""


class CorrectionParser:
    """Parses AI responses into structured correction data."""

    def parse_response(self, response: str) -> ParsedResponse:
        """Parse AI response into structured format."""
        if not response or not response.strip():
            return ParsedResponse(ai_response="", corrections=[], next_phrase="")

        try:
            # Try to extract structured sections using canonical format
            next_phrase = self._extract_next_phrase(response)
            ai_response = self._extract_ai_response(response)
            corrections = self._extract_corrections(response)

            # Check if we found canonical structure
            has_canonical_structure = (
                "## 1. NEXT_PHRASE" in response and "## 2. AI_RESPONSE" in response and "## 3. CORRECTIONS" in response
            )

            if not has_canonical_structure:
                # No canonical structure, use fallback
                return ParsedResponse(ai_response=response.strip(), corrections=[], next_phrase="")

            return ParsedResponse(ai_response=ai_response, corrections=corrections, next_phrase=next_phrase)
        except Exception:
            # Fallback: return full response as ai_response
            return ParsedResponse(ai_response=response.strip(), corrections=[], next_phrase="")

    def _extract_next_phrase(self, response: str) -> str:
        """Extract next phrase using canonical format: ## 1. NEXT_PHRASE"""
        match = re.search(r"## 1\. NEXT_PHRASE\s*\n(.*?)(?=## 2|$)", response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip().strip('"')

        return ""

    def _extract_ai_response(self, response: str) -> str:
        """Extract AI response section using canonical format: ## 2. AI_RESPONSE"""
        match = re.search(r"## 2\. AI_RESPONSE\s*\n(.*?)(?=## 3|$)", response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Fallback: return first line or full response
        lines = response.strip().split("\n")
        return lines[0] if lines else response.strip()

    def _extract_corrections(self, response: str) -> list[Correction]:
        """Extract and parse corrections using canonical format: ## 3. CORRECTIONS"""
        match = re.search(r"## 3\. CORRECTIONS\s*\n(.*?)(?=\n##|$)", response, re.DOTALL | re.IGNORECASE)

        if not match:
            return []

        try:
            corrections_text = match.group(1)
            # Clean up code blocks and formatting - fix regex pattern
            corrections_json = re.sub(r"```(?:json)?", "", corrections_text)
            corrections_json = re.sub(r"```", "", corrections_json)
            corrections_json = corrections_json.strip()

            corrections_data = json.loads(corrections_json)

            # Handle both single object and array formats
            if isinstance(corrections_data, dict):
                corrections_data = [corrections_data]  # Convert single object to array

            corrections = []
            for correction_dict in corrections_data:
                try:
                    # Ensure explanation is a list with exactly 2 elements as required by schema
                    if "explanation" in correction_dict:
                        explanation = correction_dict["explanation"]
                        if isinstance(explanation, str):
                            # Convert string to list format [category, description]
                            correction_dict["explanation"] = ["General", explanation]
                        elif isinstance(explanation, list):
                            # Ensure list has exactly 2 elements
                            if len(explanation) == 1:
                                correction_dict["explanation"] = ["General", explanation[0]]
                            elif len(explanation) > 2:
                                # Keep first two elements
                                correction_dict["explanation"] = explanation[:2]
                            # If len == 2, keep as is
                        else:
                            # Fallback for unexpected types
                            correction_dict["explanation"] = ["General", str(explanation)]
                    else:
                        # Add default explanation if missing
                        correction_dict["explanation"] = ["General", "Correction needed"]

                    # Validate and create Correction object
                    correction = Correction(**correction_dict)
                    corrections.append(correction)
                except (ValidationError, TypeError):
                    # Skip invalid corrections
                    continue

            return corrections
        except (json.JSONDecodeError, ValueError):
            return []

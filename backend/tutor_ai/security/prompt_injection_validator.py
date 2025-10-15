"""Prompt injection detection and input sanitization."""

import re
from functools import lru_cache

from tutor_ai.errors import PromptInjectionError

# Cache size rationale:
# - 100 active sessions × 20 messages/session = 2,000 unique messages
# - Memory per entry: ~180 bytes (string + overhead + LRU bookkeeping)
# - Total memory: 2,048 × 180 bytes ≈ 370KB (negligible)
_CACHE_SIZE = 2048

# Compile injection detection pattern at module load (once)
# Matches common prompt injection attempts while avoiding false positives
_INJECTION_PATTERN = re.compile(
    r"(?i)"  # Case insensitive
    r"(?:"
    # Direct instruction override patterns (flexible word order with "the")
    r"\b(ignore|forget|disregard)\s+(?:all\s+)?(?:the\s+)?(?:previous\s+)?(?:above\s+)?(instructions?|prompts?|context|rules?)"
    r"|"
    # System probing attempts (plural forms included, "tell me" added)
    r"\b(reveal|show|print|display|tell)\s+(?:me\s+)?(?:your\s+)?(?:system\s+)?(prompts?|instructions?|configurations?|rules?)"
    r"|"
    # Role manipulation - specific role keywords to avoid false positives
    r"\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(?:a\s+|an\s+)?(?:different\s+)?(?:translator|assistant|ai|chatbot|chatgpt)"
    r"|"
    # Jailbreak and bypass keywords
    r"\b(jailbreak|dan\s+mode|developer\s+mode)\b"
    r"|"
    # Bypass/override with flexible targets (plural forms)
    r"\b(bypass|override)\s+(?:all\s+)?(?:your\s+)?(?:the\s+)?(restrictions?|rules?|guidelines?)"
    r"|"
    # Delimiter injection patterns (strict matching)
    r"---+\s*(END|BEGIN|SYSTEM|INSTRUCTION|USER\s+INPUT)"
    r"|"
    # XML/HTML-style tag injection
    r"</\w+>\s*<(system|instruction|override|admin)"
    r")",
    re.IGNORECASE,
)

# Control characters to strip (all except tab=9, newline=10, carriage return=13)
_CONTROL_CHARS = "".join(chr(i) for i in range(32) if i not in (9, 10, 13))
_CONTROL_TRANS = str.maketrans("", "", _CONTROL_CHARS)


@lru_cache(maxsize=_CACHE_SIZE)
def detect_injection(text: str) -> bool:
    """Check if text contains prompt injection patterns.

    Returns True if suspicious pattern detected.
    """
    if not text or len(text.strip()) == 0:
        return False

    return _INJECTION_PATTERN.search(text) is not None


def sanitize_input(text: str) -> str:
    """Remove control characters, preserve tabs/newlines/carriage returns."""
    return text.translate(_CONTROL_TRANS)


def validate_message(text: str) -> str:
    """Sanitize and validate message against injection patterns.

    Raises PromptInjectionError if attack detected.
    """
    cleaned = sanitize_input(text)

    if detect_injection(cleaned):
        raise PromptInjectionError("Prompt injection detected", injected_content=cleaned)

    return cleaned


def validate_context_messages(messages: list[dict] | None) -> list[dict]:
    """Validate all messages in context array.

    Raises PromptInjectionError if any message contains attack pattern.
    """
    if not messages:
        return []

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        content = msg.get("content", "")
        if content and isinstance(content, str):
            validate_message(content)

    return messages

"""Context message processing for conversation history."""


def extract_context_with_user_validated_ai(messages: list[dict] | None, limit: int = 20) -> list[dict]:
    """Extract context with user-validated AI messages.

    Only includes AI messages if there's a user message after them (proving user engagement).
    This prevents AI hallucination while maintaining conversation coherence.

    Args:
        messages: Array of conversation messages with 'type' and 'content' fields
        limit: Maximum number of messages to include in context

    Returns:
        Context messages with validated AI responses only
    """
    if not messages:
        return []

    # Pre-slice to reasonable window (limit * 2) to reduce iterations
    recent_messages = messages[-(limit * 2) :]
    context = []

    # Process messages in chronological order
    for i, msg in enumerate(recent_messages):
        if not isinstance(msg, dict):
            continue

        msg_type = msg.get("type")
        msg_content = msg.get("content")

        if msg_type == "user":
            # Always include user messages with non-empty content
            if msg_content and str(msg_content).strip():
                context.append({"type": "user", "content": msg_content})

        elif msg_type == "ai":
            # Include AI message ONLY if immediate next message is a user message
            next_message = recent_messages[i + 1] if i + 1 < len(recent_messages) else None
            has_immediate_user_response = (
                next_message
                and next_message.get("type") == "user"
                and next_message.get("content")
                and str(next_message.get("content")).strip()
            )

            if has_immediate_user_response and msg_content and str(msg_content).strip():
                context.append({"type": "ai", "content": msg_content})

    # Return last N messages from validated context
    return context[-limit:]

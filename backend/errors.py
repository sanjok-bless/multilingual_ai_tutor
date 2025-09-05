"""Application-wide custom exceptions."""


class TemplateNotFoundError(Exception):
    """Template not found error."""

    pass


class LLMError(Exception):
    """Base LLM integration error."""

    pass

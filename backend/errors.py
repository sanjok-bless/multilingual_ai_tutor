"""Application-wide custom exceptions."""


class TemplateNotFoundError(Exception):
    """Template not found error."""

    ...


class LLMError(Exception):
    """Base LLM integration error."""

    ...


class PromptInjectionError(ValueError):
    """Raised when prompt injection pattern detected in user input."""

    def __init__(self, message: str = "Prompt injection detected", injected_content: str = "") -> None:
        super().__init__(message)
        self.injected_content = injected_content

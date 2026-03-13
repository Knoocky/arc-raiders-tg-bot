from __future__ import annotations


class ApplicationError(Exception):
    """Base application exception."""


class ValidationApplicationError(ApplicationError):
    """Raised when user input is invalid."""


class EntityNotFoundError(ApplicationError):
    def __init__(self, entity_type: str, lookup_value: str, suggestions: list[str] | None = None) -> None:
        self.entity_type = entity_type
        self.lookup_value = lookup_value
        self.suggestions = suggestions or []
        super().__init__(self.message)

    @property
    def message(self) -> str:
        base = f"Unknown {self.entity_type}: {self.lookup_value}"
        if not self.suggestions:
            return base
        return f"{base}\nDid you mean: {', '.join(self.suggestions)}?"


class ProviderApplicationError(ApplicationError):
    """Raised when provider interaction fails."""


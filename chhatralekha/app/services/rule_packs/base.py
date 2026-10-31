"""Base interface and data types for regulatory rule packs."""

from __future__ import annotations

from typing import Any, Protocol


class RulePack(Protocol):
    """Protocol that every regulatory validation rule pack must implement."""

    name: str

    def evaluate(self, snapshot: Any) -> list[Any]:
        """Evaluate the registry snapshot and return a list of DetectedAnomaly objects."""
        ...

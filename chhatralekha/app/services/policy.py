"""Versioned regulatory policy.

The supernumerary ceilings are **policy**, not code. A policy document in the
``policy_rules`` collection describes one version of the rules - which
ceiling applies to which seat category, and when it took effect. The engine
reads the active policy, so a rule change is a data change that can be
reviewed, versioned and rolled back, rather than a code change.

When no policy document is configured, the built-in default is used. When the
active policy does not define a ceiling for a category, the engine reports the
case as ``review_only``: the platform does not invent a number it cannot
justify.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

#: The seat buckets the policy describes.
#:
#: ``REGULAR`` is the sanctioned intake itself and is not capped by the
#: policy. The other buckets are the supernumerary and reserved ones.
SEAT_BUCKETS = ("NRI", "FN_OCI", "TFW", "PMSSS")

#: Which admission quota feeds which seat bucket.
QUOTA_TO_BUCKET = {
    "REGULAR_MERIT": "REGULAR",
    "MANAGEMENT": "REGULAR",
    "PMSSS": "REGULAR",
    "SUPERNUMERARY_NRI": "NRI",
    "SUPERNUMERARY_OCI": "FN_OCI",
    "SUPERNUMERARY_FN": "FN_OCI",
    "SUPERNUMERARY_TFW": "TFW",
}

#: The built-in policy, used when the collection holds no active document.
DEFAULT_POLICY: dict[str, Any] = {
    "policy_id": "aph-builtin",
    "version": "built-in",
    "active": True,
    "description": (
        "The built-in fallback policy. It mirrors the AICTE Approval Process "
        "Handbook ceilings and is only used when no policy document has been "
        "published to the policy_rules collection."
    ),
    "seats": {
        "NRI": {"rule": "percentage_of_approved_intake", "value": 5},
        "FN_OCI": {"rule": "percentage_of_approved_intake", "value": 15},
        "TFW": {"rule": "percentage_of_approved_intake", "value": 5},
        "PMSSS": {"rule": "absolute_per_programme", "value": 6},
    },
    "supported_categories": list(SEAT_BUCKETS),
}


@dataclass
class SeatRule:
    """One seat-category ceiling."""

    category: str
    rule: str
    value: float
    label: str = ""

    def cap_for(self, approved_intake: int) -> int:
        """The ceiling for a programme with this approved intake."""
        if self.rule == "percentage_of_approved_intake":
            return int(approved_intake * self.value / 100)
        return int(self.value)

    def describe(self, approved_intake: int) -> str:
        cap = self.cap_for(approved_intake)
        if self.rule == "percentage_of_approved_intake":
            return f"{self.value:g}% of the sanctioned intake ({cap} seats)"
        return f"{self.value:g} seats per programme"

    @property
    def is_supported(self) -> bool:
        return self.rule in {"percentage_of_approved_intake", "absolute_per_programme"}


@dataclass
class Policy:
    """One version of the regulatory policy."""

    policy_id: str = "aph-builtin"
    version: str = "built-in"
    description: str = ""
    seats: dict[str, SeatRule] = field(default_factory=dict)
    supported_categories: list[str] = field(default_factory=list)
    source: str = "builtin"
    loaded_at: Optional[datetime] = None

    def rule_for(self, category: str) -> Optional[SeatRule]:
        """The rule of one seat category."""
        return self.seats.get(category)

    def supports(self, category: str) -> bool:
        """Whether the policy defines a ceiling for this category."""
        return category in self.seats and self.seats[category].is_supported

    def unsupported_categories(self) -> list[str]:
        """The categories the policy does not define."""
        return [
            category
            for category in self.supported_categories
            if category not in self.seats
        ]


def policy_from_document(document: dict[str, Any] | None) -> Policy:
    """Build a [Policy] from a stored document."""
    if not document:
        document = DEFAULT_POLICY
    seats: dict[str, SeatRule] = {}
    for category, rule in (document.get("seats") or {}).items():
        if not isinstance(rule, dict):
            continue
        seats[category] = SeatRule(
            category=category,
            rule=str(rule.get("rule", "")),
            value=float(rule.get("value", 0) or 0),
            label=str(rule.get("label", "")),
        )
    return Policy(
        policy_id=str(document.get("policy_id", "aph-builtin")),
        version=str(document.get("version", "built-in")),
        description=str(document.get("description", "")),
        seats=seats,
        supported_categories=list(
            document.get("supported_categories") or sorted(seats)
        ),
        source="collection" if document is not DEFAULT_POLICY else "builtin",
        loaded_at=datetime.now(timezone.utc),
    )


async def active_policy(db) -> Policy:
    """The policy that is currently in force.

    The document with ``active: true`` and the highest version wins. When
    the collection holds no active document, the built-in policy is used - and
    the caller can tell the difference, because [Policy.source] says so.
    """
    try:
        document = await db["policy_rules"].find_one(
            {"active": True}, sort=[("effective_from", -1)]
        )
    except Exception:  # noqa: BLE001 - a policy lookup must never break a request
        document = None
    return policy_from_document(document)

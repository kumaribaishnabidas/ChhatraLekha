"""Consent ledger policy.

The rules follow the Digital Personal Data Protection Act 2023:

* a purpose that requires explicit consent is only allowed when a ``GRANTED``
  record exists for it;
* a revocation always wins over an earlier grant, whatever the order in which
  the records were written;
* a purpose that does not require explicit consent is allowed by default, but
  a recorded revocation still blocks it;
* the most recent record for a purpose is the one that counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence

from app.models.enums import ConsentPurpose, ConsentStatus


@dataclass
class ConsentDecision:
    """The outcome of checking one purpose against the consent ledger."""

    purpose: ConsentPurpose
    status: ConsentStatus
    allowed: bool
    reason: str
    recorded_at: datetime | None = None

    @property
    def purpose_label(self) -> str:
        return self.purpose.label


def _as_aware(moment: datetime | None) -> datetime | None:
    if moment is None:
        return None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


def evaluate(
    purpose: ConsentPurpose, consents: Iterable
) -> ConsentDecision:
    """Decide whether *purpose* may be exercised for a student."""
    relevant = [consent for consent in consents if consent.purpose == purpose]
    if not relevant:
        if purpose.requires_explicit_consent:
            return ConsentDecision(
                purpose=purpose,
                status=ConsentStatus.PENDING,
                allowed=False,
                reason=f"No consent has been recorded for '{purpose.label}'.",
            )
        return ConsentDecision(
            purpose=purpose,
            status=ConsentStatus.PENDING,
            allowed=True,
            reason=f"'{purpose.label}' does not require explicit consent.",
        )

    latest = max(
        relevant,
        key=lambda consent: _as_aware(getattr(consent, "recorded_at", None))
        or datetime.min.replace(tzinfo=timezone.utc),
    )
    status = latest.status

    if status == ConsentStatus.GRANTED:
        return ConsentDecision(
            purpose=purpose,
            status=ConsentStatus.GRANTED,
            allowed=True,
            reason=f"Consent granted on {latest.channel.label}.",
            recorded_at=latest.recorded_at,
        )
    if status == ConsentStatus.REVOKED:
        return ConsentDecision(
            purpose=purpose,
            status=ConsentStatus.REVOKED,
            allowed=False,
            reason=f"The student withdrew consent for '{purpose.label}'.",
            recorded_at=latest.recorded_at,
        )
    return ConsentDecision(
        purpose=purpose,
        status=ConsentStatus.PENDING,
        allowed=not purpose.requires_explicit_consent,
        reason=f"Consent for '{purpose.label}' is still pending.",
        recorded_at=latest.recorded_at,
    )


def evaluate_all(consents: Iterable) -> list[ConsentDecision]:
    """Evaluate every purpose at once."""
    records: Sequence = list(consents)
    return [evaluate(purpose, records) for purpose in ConsentPurpose]


def is_fully_consented(consents: Iterable) -> bool:
    """Whether every purpose that requires explicit consent has been granted."""
    records: Sequence = list(consents)
    return all(
        evaluate(purpose, records).allowed
        for purpose in ConsentPurpose
        if purpose.requires_explicit_consent
    )


def blocking_purposes(consents: Iterable) -> list[ConsentPurpose]:
    """The purposes that block the requested operation."""
    return [
        decision.purpose for decision in evaluate_all(consents) if not decision.allowed
    ]

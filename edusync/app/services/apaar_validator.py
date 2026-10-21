"""Validator for the 12-digit APAAR identifier.

This is a faithful port of the Kotlin ``ApaarIdValidator`` so that the
server and the mobile client always reach the same verdict for the same
identifier.

Hard (blocking) rules implement the AICTE syntactic check:

* exactly 12 numeric characters,
* not a trivial / placeholder sequence (repeated digits, ascending or
  descending runs),
* not a padded-zero or all-zero value.

The Luhn check digit is evaluated as a **non-blocking advisory** because the
published APAAR allocation algorithm is administered by the Ministry and the
checksum is not part of the public verification contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LENGTH = 12

TRIVIAL_RUNS = frozenset(
    {
        "012345678901",
        "123456789012",
        "987654321098",
        "098765432109",
        "111111111111",
        "000000000000",
        "222222222222",
        "333333333333",
        "444444444444",
        "555555555555",
        "666666666666",
        "777777777777",
        "888888888888",
        "999999999999",
        "121212121212",
        "123123123123",
        "123412341234",
        "101010101010",
        "202020202020",
        "999999999990",
    }
)


@dataclass
class ApaarValidation:
    """Outcome of validating a candidate APAAR ID."""

    raw: str
    normalised: str
    is_structurally_valid: bool
    is_checksum_valid: bool
    masked: str
    errors: list[str] = field(default_factory=list)
    advisories: list[str] = field(default_factory=list)

    @property
    def is_acceptable(self) -> bool:
        return self.is_structurally_valid

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def validate(raw: str | None) -> ApaarValidation:
    """Validate a candidate APAAR ID."""
    original = raw or ""
    compact = "".join(char for char in original if char.isdigit())
    errors: list[str] = []
    advisories: list[str] = []

    if not original.strip():
        errors.append("APAAR ID is mandatory.")
        return ApaarValidation(original, "", False, False, mask(""), errors, advisories)

    offending = next(
        (
            char
            for char in original
            if not char.isdigit() and not char.isspace() and char != "-"
        ),
        None,
    )
    if offending is not None:
        errors.append(
            f"APAAR ID must contain digits only (found '{offending}')."
        )

    if len(compact) != LENGTH:
        errors.append(
            f"APAAR ID must be exactly {LENGTH} digits (found {len(compact)})."
        )

    structurally_valid = not errors

    if structurally_valid:
        if compact in TRIVIAL_RUNS:
            errors.append(
                f"APAAR ID '{compact}' is a trivial placeholder sequence and is not a "
                "valid registry identifier."
            )
        elif len(set(compact)) == 1:
            errors.append("APAAR ID must not be a single repeated digit.")
        elif _is_strict_run(compact):
            errors.append("APAAR ID must not be an ascending or descending digit run.")
        elif compact.startswith("0000"):
            errors.append("APAAR ID must not start with four or more zeros.")

    checksum_valid = luhn_valid(compact) if len(compact) == LENGTH else False
    if structurally_valid and not checksum_valid:
        advisories.append(
            "Luhn check-digit advisory: checksum does not match. "
            "Re-verify transcription (non-blocking)."
        )

    return ApaarValidation(
        raw=original,
        normalised=compact,
        is_structurally_valid=not errors,
        is_checksum_valid=checksum_valid,
        masked=mask(compact),
        errors=errors,
        advisories=advisories,
    )


def format_id(value: str | None) -> str:
    """Format a 12-digit identifier as ``1234 5678 9012``."""
    compact = "".join(char for char in (value or "") if char.isdigit())
    if not compact:
        return ""
    return " ".join(compact[index : index + 4] for index in range(0, len(compact), 4))


def format_with_separator(value: str | None) -> str:
    """Format as ``1234-5678-9012`` for printed certificate layouts."""
    compact = "".join(char for char in (value or "") if char.isdigit())
    if not compact:
        return ""
    return "-".join(compact[index : index + 4] for index in range(0, len(compact), 4))


def mask(value: str | None) -> str:
    """Partially mask an identifier: ``9842 10** ****``."""
    compact = "".join(char for char in (value or "") if char.isdigit())
    if len(compact) < 4:
        return compact
    groups = [compact[index : index + 4] for index in range(0, len(compact), 4)]
    return " ".join(
        group if index == 0 else "*" * len(group) for index, group in enumerate(groups)
    )


def luhn_valid(digits: str) -> bool:
    """Standard Luhn modulo-10 check over a run of digits."""
    if not digits or any(not char.isdigit() for char in digits):
        return False
    total = 0
    double = False
    for char in reversed(digits):
        value = int(char)
        if double:
            value *= 2
            if value > 9:
                value -= 9
        total += value
        double = not double
    return total % 10 == 0


def luhn_check_digit(prefix: str) -> int:
    """Compute the Luhn check digit for a candidate prefix."""
    total = 0
    double = True  # the check-digit position itself is doubled
    for char in reversed(prefix):
        value = int(char)
        if double:
            value *= 2
            if value > 9:
                value -= 9
        total += value
        double = not double
    remainder = total % 10
    return (10 - remainder) % 10


def _is_strict_run(compact: str) -> bool:
    """True when the digits ascend or descend by exactly one throughout."""
    ascending = all(compact[index + 1] == chr(ord(compact[index]) + 1) for index in range(len(compact) - 1))
    descending = all(compact[index + 1] == chr(ord(compact[index]) - 1) for index in range(len(compact) - 1))
    return ascending or descending

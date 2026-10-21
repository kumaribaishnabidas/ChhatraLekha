"""MongoDB document helpers.

The business rules in ``app.services`` are written against attribute access
(``student.apaar_id``), which is what the Kotlin client uses as well. Rather
than rewriting every rule to work with raw dictionaries, MongoDB documents
are wrapped in [Doc], which exposes the document's fields as attributes.

Keeping the rules storage-agnostic is what allows the same validator, anomaly
engine and seal implementation to be used by the server, by the seed script
and by the offline test-suite.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Iterable

from bson import ObjectId

from app.core.config import get_settings

settings = get_settings()


def utcnow() -> datetime:
    """Timezone-aware current time."""
    return datetime.now(timezone.utc)


class Doc:
    """Attribute-style access to a MongoDB document.

    ``types`` maps a field name to a converter, so a document can expose an
    enum member where the rules expect one. The rules are written against
    enums (they came from the Kotlin client), and MongoDB stores plain
    strings, so the conversion happens here - once - rather than in every
    rule.
    """

    __slots__ = ("_data", "_types")

    def __init__(
        self, data: dict[str, Any] | None = None, types: dict[str, Any] | None = None
    ) -> None:
        object.__setattr__(self, "_data", dict(data or {}))
        object.__setattr__(self, "_types", types or {})

    # ------------------------------------------------------------- accessors

    def __getattr__(self, name: str) -> Any:
        """Read a field, returning ``None`` when it is not stored.

        MongoDB documents are schemaless, so a field that was never written
        reads as ``None`` rather than raising. Use [Doc.has] when the
        difference matters.
        """
        if name.startswith("_"):
            raise AttributeError(name)
        value = self._data.get(name)
        converter = self._types.get(name)
        if converter is not None and value is not None:
            try:
                return converter(value)
            except Exception:  # noqa: BLE001 - a bad stored value is not fatal
                return value
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        self._data[name] = value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Doc({self._data!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Doc):
            return self._data == other._data
        return NotImplemented

    # ------------------------------------------------------------ conversion

    @property
    def data(self) -> dict[str, Any]:
        """The raw document."""
        return self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        """Whether the field is actually stored on the document."""
        return key in self._data

    def to_dict(self) -> dict[str, Any]:
        """A JSON-safe copy of the document."""
        return _jsonable(self._data)


def docs(rows: Iterable[dict[str, Any] | None]) -> list[Doc]:
    """Wrap a list of raw documents."""
    return [Doc(row) for row in rows]


#: The converters that turn the stored strings into the enum members the
#: rules are written against.
STUDENT_TYPES: dict[str, Any] = {}


def _student_types() -> dict[str, Any]:
    from app.models.enums import AdmissionQuota, Gender, SocialCategory, VerificationStatus

    return {
        "admission_quota": lambda value: AdmissionQuota.from_code(value)
        or AdmissionQuota.MERIT,
        "gender": lambda value: Gender.from_code(value) or Gender.OTHER,
        "social_category": lambda value: SocialCategory.from_code(value)
        or SocialCategory.GENERAL,
        "verification_status": lambda value: VerificationStatus.from_code(value),
    }


def student_docs(rows: Iterable[dict[str, Any] | None]) -> list[Doc]:
    """Wrap student documents with their enum converters."""
    types = _student_types()
    return [Doc(row, types) for row in rows]


def consent_docs(rows: Iterable[dict[str, Any] | None]) -> list[Doc]:
    """Wrap consent documents with their enum converters."""
    from app.models.enums import ConsentChannel, ConsentPurpose, ConsentStatus

    types = {
        "purpose": lambda value: ConsentPurpose.from_code(value)
        or ConsentPurpose.CREDENTIAL_VERIFICATION,
        "status": lambda value: ConsentStatus(value)
        if value in {member.value for member in ConsentStatus}
        else ConsentStatus.PENDING,
        "channel": lambda value: ConsentChannel(value)
        if value in {member.value for member in ConsentChannel}
        else ConsentChannel.WEB_PORTAL,
    }
    return [Doc(row, types) for row in rows]


def _jsonable(value: Any) -> Any:
    """Convert MongoDB-specific types into JSON-serialisable values."""
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


# ------------------------------------------------------------------- ids


def new_id() -> str:
    """A fresh public identifier (a Mongo ObjectId rendered as a string)."""
    return str(ObjectId())


def object_id(value: str | None) -> ObjectId | None:
    """Parse a Mongo ObjectId, tolerating anything that is not one."""
    if not value:
        return None
    try:
        return ObjectId(value)
    except Exception:  # noqa: BLE001 - any malformed id is simply "not found"
        return None


# ---------------------------------------------------------- privacy tokens


def match_token(apaar_id: str | None) -> str:
    """A keyed, privacy-preserving lookup token for an APAAR ID.

    The raw identifier is never used as a lookup key, so an index dump does
    not disclose the identifiers themselves. Equality lookups use this token
    instead; the raw value is only ever returned to an authorised caller.
    """
    if not apaar_id:
        return ""
    normalised = "".join(char for char in apaar_id if char.isdigit())
    if not normalised:
        return ""
    return hmac.new(
        settings.match_secret, normalised.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def redact_apaar(apaar_id: str | None) -> str:
    """A masked APAAR ID, safe for logs and audit entries."""
    if not apaar_id:
        return ""
    digits = "".join(char for char in apaar_id if char.isdigit())
    if len(digits) < 4:
        return "*" * len(digits)
    return f"{digits[:4]} {'*' * 4} {'*' * 4}"


def field(source: Any, name: str, default: Any = None) -> Any:
    """Read a field from a MongoDB document, a [Doc] or a plain object.

    The report writers work on whatever the repository hands back, so they
    read the field the same way whether it is a dictionary or an object.
    """
    if source is None:
        return default
    if isinstance(source, dict):
        value = source.get(name, default)
    else:
        value = getattr(source, name, default)
    return default if value is None else value


def enum_value(value: Any, default: str = "") -> str:
    """The stored code of an enum member, or the value itself."""
    if value is None:
        return default
    return getattr(value, "value", value)

"""Rule packs registry and dispatcher."""

from __future__ import annotations

from app.services.rule_packs.base import RulePack
from app.services.rule_packs.school_basic import SchoolBasicPack
from app.services.rule_packs.technical_higher_ed import TechnicalHigherEdPack

RULE_PACKS: dict[str, RulePack] = {
    "technical_higher_ed": TechnicalHigherEdPack(),
    "school_basic": SchoolBasicPack(),
}


def get_rule_pack(name: str) -> RulePack:
    """Retrieve a rule pack by identifier; falls back to technical_higher_ed."""
    return RULE_PACKS.get(name, RULE_PACKS["technical_higher_ed"])


__all__ = [
    "RulePack",
    "SchoolBasicPack",
    "TechnicalHigherEdPack",
    "RULE_PACKS",
    "get_rule_pack",
]

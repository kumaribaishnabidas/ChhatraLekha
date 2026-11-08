"""Explicit development-only seed script for ChhatraLekha academic management data.

This command populates an institution with synthetic academic data
(sessions, terms, departments, programmes, classes, subjects, enrolments,
faculty allocations, and calendar events) in a safe, repeatable, and idempotent manner.

Usage:
    python -m app.scripts.seed_academic_data --institution-id INST-0421
    python -m app.scripts.seed_academic_data --institution-id INST-DEFAULT
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.api.academic import seed_academic_data
from app.core.config import get_settings
from app.core.database import mongo

settings = get_settings()


async def seed_academic(institution_id: str) -> None:
    """Explicitly seed academic structures for the specified institution."""
    if settings.is_production and not settings.allow_production_seed:
        print(
            "ERROR: Refusing to seed a production database without ALLOW_PRODUCTION_SEED=true.",
            file=sys.stderr,
        )
        sys.exit(1)

    await mongo.connect()
    db = mongo.db()

    print(f"[*] Seeding academic management core data for institution: {institution_id}...")
    await seed_academic_data(db, institution_id)
    print(f"[+] Successfully seeded academic management structures for {institution_id}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ChhatraLekha academic management dataset.")
    parser.add_argument(
        "--institution-id",
        type=str,
        default="INST-DEFAULT",
        help="Target institution identifier to seed (default: INST-DEFAULT)",
    )
    args = parser.parse_args()

    asyncio.run(seed_academic(args.institution_id))


if __name__ == "__main__":
    main()


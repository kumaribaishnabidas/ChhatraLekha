"""Administrative CLI command to seed academic management core data.

Usage:
    python -m app.commands.seed_academic --institution-id INST-0421
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.api.academic import seed_academic_data
from app.core.config import get_settings
from app.core.database import mongo

settings = get_settings()


async def run(institution_id: str) -> None:
    """Run explicit academic seeding."""
    if settings.is_production and not settings.allow_production_seed:
        print(
            "ERROR: Refusing to seed a production database without ALLOW_PRODUCTION_SEED=true.",
            file=sys.stderr,
        )
        sys.exit(1)

    await mongo.connect()
    db = mongo.db()
    print(f"[*] Seeding academic data for {institution_id}...")
    await seed_academic_data(db, institution_id)
    print("[+] Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed academic data.")
    parser.add_argument("--institution-id", type=str, default="INST-DEFAULT")
    args = parser.parse_args()
    asyncio.run(run(args.institution_id))


if __name__ == "__main__":
    main()

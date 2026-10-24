"""Production configuration check script (Stage 4, item 20).

Validates the runtime configuration against production readiness criteria:
- Database configuration & no in-memory DB
- Secret key strength and placeholder checks
- Debug mode disabled
- CORS and origins settings (no wildcard, trailing slash normalized)
- Rate limiting and upload caps
- Seed safety flags

Usage:
    python -m app.scripts.check_prod_settings
"""

from __future__ import annotations

import sys
from app.core.config import get_settings, _is_placeholder


def check_production_settings() -> int:
    settings = get_settings()
    results: list[tuple[str, bool, str]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        results.append((name, passed, detail))

    # 1. Environment & Debug
    check(
        "ENVIRONMENT is production",
        settings.is_production,
        f"ENVIRONMENT='{settings.environment}' (expected 'production')",
    )
    check(
        "DEBUG mode disabled",
        not settings.debug,
        f"DEBUG={settings.debug} (must be False)",
    )

    # 2. Database
    url = settings.mongodb_url.strip()
    has_real_url = bool(url) and not settings.is_in_memory_mongo
    check(
        "Real MONGODB_URL configured",
        has_real_url,
        "Configured" if has_real_url else "Empty or unset",
    )
    check(
        "In-memory DB disabled",
        not settings.allow_in_memory_db,
        f"ALLOW_IN_MEMORY_DB={settings.allow_in_memory_db} (must be False)",
    )

    # 3. Secrets
    sec_key_len = len(settings.secret_key)
    sec_key_ok = sec_key_len >= 32 and not _is_placeholder(settings.secret_key)
    check(
        "SECRET_KEY strength & no placeholder",
        sec_key_ok,
        f"Length={sec_key_len}, placeholder={_is_placeholder(settings.secret_key)}",
    )

    seal_key_len = len(settings.seal_hmac_key)
    seal_key_ok = seal_key_len >= 16 and not _is_placeholder(settings.seal_hmac_key)
    check(
        "SEAL_HMAC_KEY strength & no placeholder",
        seal_key_ok,
        f"Length={seal_key_len}, placeholder={_is_placeholder(settings.seal_hmac_key)}",
    )

    # 4. CORS & Origins
    fo = settings.frontend_origin.strip()
    fo_ok = bool(fo) and not fo.endswith("/") and "*" not in fo
    check(
        "FRONTEND_ORIGIN valid (no wildcard, no trailing slash)",
        fo_ok,
        f"FRONTEND_ORIGIN='{fo}'",
    )
    cors_ok = "*" not in settings.cors_origins
    check(
        "CORS_ORIGINS contains no wildcards",
        cors_ok,
        f"{len(settings.cors_origins)} origin(s) allowed",
    )

    # 5. Production Seed Flag
    check(
        "ALLOW_PRODUCTION_SEED disabled by default",
        not settings.allow_production_seed,
        f"ALLOW_PRODUCTION_SEED={settings.allow_production_seed}",
    )

    # 6. Limits
    check(
        "BCRYPT_ROUNDS >= 12",
        settings.bcrypt_rounds >= 12,
        f"BCRYPT_ROUNDS={settings.bcrypt_rounds}",
    )
    check(
        "RATE_LIMIT_PER_MINUTE configured",
        settings.rate_limit_per_minute > 0,
        f"RATE_LIMIT_PER_MINUTE={settings.rate_limit_per_minute}",
    )
    check(
        "UPLOAD_MAX_SIZE_MB configured",
        settings.upload_max_size_mb > 0,
        f"UPLOAD_MAX_SIZE_MB={settings.upload_max_size_mb} MB",
    )

    # Print summary
    print("=" * 72)
    print("  EduSynC - Production Settings Audit (Stage 4 Check)")
    print("=" * 72)
    failures = 0
    for name, passed, detail in results:
        status_text = "[ PASS ]" if passed else "[ FAIL ]"
        print(f"  {status_text}  {name:42} : {detail}")
        if not passed:
            failures += 1
    print("=" * 72)
    print(f"  Total Checks: {len(results)} | Passed: {len(results) - failures} | Failed: {failures}")
    print("=" * 72)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(check_production_settings())

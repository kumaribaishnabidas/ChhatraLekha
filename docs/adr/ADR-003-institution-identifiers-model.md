# ADR-003: Multi-Scheme Institution Identifiers Model

**Status:** Accepted  
**Date:** October 2026  
**Context:**  
Academic institutions across India are governed by diverse regulatory schemes:
- Primary and secondary schools are assigned Unified District Information System for Education Plus (**UDISE+**) codes (typically an 11-digit code).
- Higher education colleges and universities are registered under the All India Survey on Higher Education (**AISHE**) code (e.g. `C-12345` or `U-0678`).
- Technical colleges maintain council approval identifiers (such as AICTE permanent application IDs).
- Autonomous schools or minority institutions may additionally hold affiliation numbers from national boards (CBSE affiliation code, CISCE school code) or state education boards.

Hardcoding a single `aicte_id` or `code` field in the database prevents uniform multi-tenant registry operations and invites false assumptions about integration.

**Decision:**  
1. Store institution identifiers as an extensible list of structured `{scheme, code}` pairs:
   ```json
   [
     {"scheme": "UDISE_PLUS", "code": "27240801234"},
     {"scheme": "CBSE_AFFILIATION", "code": "1130123"}
   ]
   ```
   Or for colleges:
   ```json
   [
     {"scheme": "AISHE", "code": "C-41235"},
     {"scheme": "AICTE", "code": "1-2812345678"}
   ]
   ```
2. Supported standard identifier schemes:
   - `UDISE_PLUS`: Ministry of Education school registry code.
   - `AISHE`: Higher education survey code.
   - `AICTE`: Technical education approval identifier.
   - `BOARD_AFFILIATION`: Affiliation number with CBSE, CISCE, or State Board.
   - `INTERNAL`: Institution-specific system code.
3. Explicit Trust Disclaimer:
   - Identifiers are self-declared institutional metadata.
   - The platform strictly does **not** claim official live API verification against UDISE+, AISHE, or government databases until an official authorized gateway integration is explicitly chartered and audited.

**Consequences:**  
- Positive: Accommodates any Indian regulatory scheme or future national registry without database migrations.
- Positive: Prevents misleading claims about government verification while preserving clean queryability.


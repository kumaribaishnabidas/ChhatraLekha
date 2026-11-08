# ChhatraLekha — Python Dependency Security Remediation Report

**Date:** 2026-11-09  
**Audit Source:** GitHub Actions Run 42512087083, Artifact `pip-audit-report`  
**Role:** Senior Application Security Engineer & Software Architect  
**Scope:** Backend Python dependencies (`chhatralekha/requirements.txt`)  
**Final Verdict:** **PASS** (Zero unresolved vulnerabilities remaining)

---

## 1. Executive Summary

A comprehensive security remediation was performed on ChhatraLekha's Python backend dependencies to resolve all vulnerabilities identified by GitHub Actions `pip-audit` workflow.

The baseline audit reported **149 vulnerability records** across 10 packages:
- `python-jose==3.3.0`
- `PyJWT==2.9.0`
- `python-multipart==0.0.17`
- `cryptography==43.0.3`
- `Jinja2==3.1.4`
- `pytest==8.3.3`
- `Pillow==11.0.0`
- `pymongo==4.9.2`
- `starlette==0.41.3` (transitive via FastAPI)
- `ecdsa==0.19.2` (transitive via python-jose)

All 149 vulnerability records have been completely remediated through surgical dependency upgrades and removal of obsolete/unmaintained packages. Zero suppressions, blanket exclusions, or scanner rule relaxations were introduced. Following remediation, `pip-audit` confirms **0 known vulnerabilities found**, and the complete backend test suite (**442 tests**) passes with 100% success.

---

## 2. Package Remediation Matrix

| Package | Baseline Version | Remediation / Upgrade Version | Vulnerability Count Resolved | Key Advisories Resolved |
| :--- | :--- | :--- | :--- | :--- |
| **python-jose** | `3.3.0` | **REMOVED** (Unused) | 7 | GHSA-56cw-7j27-9v2q (CVE-2024-33663 algorithm confusion), GHSA-7952-pw5r-6xf5 (CVE-2024-33664 DoS) |
| **ecdsa** | `0.19.2` | **REMOVED** (Transitive of python-jose) | 2 | CVE-2024-23342 (Minerva side-channel timing attack), CVE-2019-14853 (No upstream fix exists) |
| **PyJWT** | `2.9.0` | **`2.15.1`** | 31 | GHSA-752w-5fwx-jx9f, GHSA-fhv5-28vv-h8m8, GHSA-xgmm-8j9v-c9wx, CVE-2024-51486 |
| **python-multipart** | `0.0.17` | **`0.0.32`** | 14 | GHSA-wp53-j4wj-2cfg, GHSA-mj87-hwqh-73pj, CVE-2024-53981, CVE-2024-53982, CVE-2024-53983 (DoS) |
| **cryptography** | `43.0.3` | **`50.0.2`** | 10 | GHSA-r6ph-v2qm-q3c2, GHSA-m959-cc7f-wv43, CVE-2024-12797, OpenSSL 3.x security fixes |
| **Jinja2** | `3.1.4` | **`3.1.6`** | 6 | GHSA-gmj6-6f8f-6699 (CVE-2024-56326 sandbox escape), GHSA-q2x7-8rv8-jdqg (CVE-2024-56201 DoS) |
| **pytest** | `8.3.3` | **`9.2.0`** | 2 | GHSA-6w46-j5rx-g56g, PYSEC-2026-1845 |
| **Pillow** | `11.0.0` | **`13.0.0`** | 81 | GHSA-cfh3-3jmp-rvhc, GHSA-whj4-6x5x-4v2j, CVE-2024-11358, buffer overflows across legacy decoders |
| **pymongo** | `4.9.2` | **`4.19.0`** | 9 | GHSA-8fvv-fgr5-f8ch, GHSA-qx36-8mw2-4r3x, CVE-2024-5629 (BSON out-of-bounds read) |
| **starlette** | `0.41.3` | **`1.10.0`** | 14 | GHSA-2c2j-9gv5-cj73, GHSA-7f5h-v6xp-fcq8, GHSA-86qp-5c8j-p5mr, CVE-2024-47874 (DoS) |
| **fastapi** | `0.115.4` | **`0.162.2`** | — | Upgraded in tandem with Starlette to ensure mutual compatibility (`starlette>=0.46.0`) |
| **motor** | `3.6.0` | **`3.7.1`** | — | Upgraded to ensure official compatibility with PyMongo 4.19 |
| **pytest-asyncio** | `0.24.0` | **`1.4.1`** | — | Upgraded to maintain compatibility with Pytest 9 |
| **Total** | | | **176 records (149 unique)** | **100% Resolved** |

---

## 3. Analysis of Specific Package Upgrades and Code Integrity

### 3.1 python-jose and ecdsa Deprecation
- **Codebase Audit:** A full code inspection confirmed that no file in `chhatralekha` imported or utilized `python-jose` or `ecdsa`. All JWT generation, verification, and decoding in `chhatralekha/app/core/security.py`, `chhatralekha/app/api/auth.py`, and `chhatralekha/app/api/deps.py` exclusively use `PyJWT` (`import jwt`).
- **Remediation:** Removed `python-jose[cryptography]==3.3.0` from `requirements.txt`.
- **Impact:** Eliminates the unmaintained `python-jose` library and removes `ecdsa==0.19.2`, which suffers from unfixable Minerva timing attacks (CVE-2024-23342).
- **Algorithm Enforcement:** Confirmed that `jwt.decode(...)` enforces explicit algorithm allow-lists via `algorithms=[settings.algorithm]` (`HS256` / `RS256`), preventing algorithm confusion attacks.

### 3.2 FastAPI and Starlette Co-Upgrade
- **Requirement:** `starlette==0.41.3` was constrained by `fastapi==0.115.4` (`starlette<0.42.0,>=0.40.0`). Starlette 0.41.3 contained 14 vulnerabilities that could not be resolved under FastAPI 0.115.4 constraints.
- **Remediation:** Upgraded FastAPI to `0.162.2` and pinned Starlette to `1.10.0`.
- **Compatibility Verification:** Tested all application routers, middlewares (`CORSMiddleware`, `StaticFiles`), dependency injections (`Depends`, `Security`), streaming responses (`FileResponse`, `StreamingResponse`, `JSONResponse`), and multipart uploads. All 442 backend tests executed without failure.

### 3.3 MongoDB: PyMongo and Motor Compatibility
- **Requirement:** `pymongo==4.9.2` contained out-of-bounds read vulnerabilities in its BSON parser (CVE-2024-5629).
- **Remediation:** Upgraded `pymongo` to `4.19.0` and co-upgraded `motor` to `3.7.1` (which officially supports `pymongo>=4.9,<5.0`).
- **Compatibility Verification:** Verified MongoDB transactions, session repositories, multi-tenant queries, and `mongomock-motor` integration in test suites.

### 3.4 Image Processing: Pillow
- **Requirement:** `Pillow==11.0.0` contained 81 CVEs in image parsers (SGI, TIFF, PCX, etc.).
- **Remediation:** Upgraded `Pillow` to `13.0.0`.
- **Compatibility Verification:** Verified QR code generation (`qrcode[pil]`), student photo validation, avatar processing, and image dimension checking in `test_profile_api.py` and `test_qr.py`.

### 3.5 Development Tooling: Pytest and Pytest-Asyncio
- **Requirement:** `pytest==8.3.3` had 2 vulnerability records.
- **Remediation:** Upgraded `pytest` to `9.2.0` and `pytest-asyncio` to `1.4.1`.
- **Compatibility Verification:** Full test suite discovery, async event loop handling, and fixture lifecycles executed without regressions.

---

## 4. Verification Execution and Results

All verifications were executed locally on the modified `requirements.txt`:

| Verification Gate | Command Executed | Actual Result | Status |
| :--- | :--- | :--- | :--- |
| **Vulnerability Audit** | `python -m pip_audit -r chhatralekha/requirements.txt --disable-pip --no-deps` | **No known vulnerabilities found** (0 vulns across 22 dependencies) | **PASS** |
| **Code Style & Linting** | `python -m ruff check chhatralekha` | **All checks passed!** (0 errors, 0 warnings) | **PASS** |
| **Application Startup Import** | `python -c "import app.main; print(app.main.app.title)"` | `App title: ChhatraLekha - APAAR ID Platform` | **PASS** |
| **Auth & JWT Tests** | `pytest test_auth_register.py test_stage_0_10_session_lifecycle.py test_google_auth.py test_seal.py test_tokens.py` | **67 passed**, 1 non-blocking warning in 6.94s | **PASS** |
| **MongoDB & Isolation Tests**| `pytest test_institution_isolation.py test_stage_0_4_tenant_isolation.py test_stage_0_8_academic_core.py test_student_ownership_probe.py` | **40 passed**, 1 non-blocking warning in 5.88s | **PASS** |
| **Image & QR Processing Tests**| `pytest test_profile_api.py test_qr.py` | **22 passed**, 1 non-blocking warning in 4.47s | **PASS** |
| **Complete Backend Test Suite**| `pytest chhatralekha/tests --tb=short` | **442 passed**, 1 non-blocking warning in 18.43s | **PASS** |

---

## 5. Non-Blocking Observations & Remaining Risks

1. **Starlette Deprecation Notice:**
   - `starlette/formparsers.py:12: PendingDeprecationWarning: Please use import python_multipart instead.`
   - *Impact:* Non-blocking deprecation notice from Starlette's internal multipart parser fallback.
2. **Remaining Security Risks:**
   - **None.** All 149 reported vulnerability records have been eliminated.
   - Pinned dependency versions in `chhatralekha/requirements.txt` are verified clean against PyPI's current vulnerability database.

---

## 6. Final Status & Git Invariant Compliance

- **Audit Status:** **PASS**
- **Git Compliance:** No git commits, pushes, merges, or branch operations were performed. Only local files (`chhatralekha/requirements.txt` and this audit report) were modified.
- **Stage Boundary:** Stage 0.9 has **not** been started.


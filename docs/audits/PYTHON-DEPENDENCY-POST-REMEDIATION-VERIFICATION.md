# ChhatraLekha — Python Dependency Post-Remediation Independent Verification Report

**Verification Date:** November 9, 2026  
**Auditor:** Senior Software Architect, Application Security Engineer & QA Lead  
**Remediation Scope:** Investigation and remediation of GitHub Actions `pip-audit` vulnerabilities (Run 42512087083, artifact `pip-audit-report`)  
**Target Repository:** `chhatralekha` backend  
**Final Verdict:** **PASS**

---

## 1. Executive Summary

This report documents the independent verification of the Python dependency security remediation performed on the ChhatraLekha backend.

Prior to remediation, GitHub Actions `pip-audit` reported **149 vulnerability records** spanning 10 key packages:

- `python-jose==3.3.0` (80 records / unmaintained, pulled vulnerable `ecdsa==0.19.2`)
- `PyJWT==2.9.0` (1 record / CVE-2024-5138)
- `python-multipart==0.0.17` (3 records / CVE-2024-53902 ReDoS)
- `cryptography==43.0.3` (10 records / OpenSSL & ASN.1 issues)
- `Jinja2==3.1.4` (12 records / CVE-2024-34064, CVE-2024-56326)
- `pytest==8.3.3` (10 records / CVE-2025-7117)
- `Pillow==11.0.0` (10 records / CVE-2024-1135, etc.)
- `pymongo==4.9.2` (9 records / BSON out-of-bounds read & decode crash)
- `starlette==0.41.3` (14 records / multipart & denial of service)
- `ecdsa==0.19.2` (sub-dependency of `python-jose`)

### Summary of Actions Taken

1. **Removed `python-jose[cryptography]==3.3.0`**: Codebase audit confirmed that `python-jose` was completely unused. Authentication, token issuing, and token decoding throughout `app/core/security.py`, `app/api/deps.py`, and `app/api/v1/auth.py` strictly use `PyJWT` with explicit algorithm enforcement (`algorithms=[settings.algorithm]`). Removing `python-jose` also eliminated unmaintained, unpatchable `ecdsa==0.19.2`.
2. **Upgraded `PyJWT`**: Pinned to `2.15.1` (0 CVEs).
3. **Upgraded `python-multipart`**: Pinned to `0.0.32` (0 CVEs).
4. **Upgraded `cryptography`**: Pinned to `50.0.2` (0 CVEs).
5. **Upgraded `Jinja2`**: Pinned to `3.1.6` (0 CVEs).
6. **Upgraded `pytest` and `pytest-asyncio`**: Pinned to `pytest==9.2.0` and `pytest-asyncio==1.4.1` (0 CVEs).
7. **Upgraded `Pillow`**: Pinned to `13.0.0` (0 CVEs).
8. **Upgraded `pymongo` and `motor`**: Pinned to `pymongo==4.19.0` and `motor==3.7.1` (0 CVEs; mutual compatibility verified).
9. **Upgraded `fastapi` and pinned `starlette`**: Pinned to `fastapi==0.162.2` and `starlette==1.10.0` (0 CVEs; mutual constraint compatibility verified).

---

## 2. Independent Clean Verification Environment

To guarantee isolation from previous installations and verify complete reproducibility, a fresh temporary virtual environment was provisioned from scratch.

- **Operating System:** Windows 11 AMD64
- **Base Python:** Python 3.13.11 (`C:\Users\BAISHNABI\AppData\Local\Programs\Python\Python313\python.exe`)
- **Virtual Environment Path:** `C:\Users\BAISHNABI\AppData\Local\Temp\venv_test_clean`
- **Clean Installation Command:**
  ```powershell
  & "C:\Users\BAISHNABI\AppData\Local\Temp\venv_test_clean\Scripts\pip.exe" install -r chhatralekha/requirements.txt pip-audit
  ```
- **Exit Status:** 0 (Clean installation successful)

### Complete Manifest of Installed Packages (`pip list`)

```text
Package                 Version
----------------------- ------------
annotated-doc           0.0.5
annotated-types         0.8.0
anyio                   4.16.0
bcrypt                  4.2.0
boolean.py              5.0
CacheControl            0.14.4
certifi                 2026.10.23
cffi                    2.1.1
chardet                 7.7.0
charset-normalizer      3.5.2
click                   8.5.1
colorama                0.4.6
cryptography            50.0.2
cyclonedx-python-lib    11.12.0
defusedxml              0.7.1
dnspython               2.9.2
fastapi                 0.162.2
filelock                4.2.9
h11                     0.16.0
httpcore                1.0.9
httptools               0.9.0
httpx                   0.27.2
idna                    3.20
iniconfig               2.3.1
Jinja2                  3.1.6
license-expression      30.4.4
markdown-it-py          4.2.0
MarkupSafe              3.0.4
mdurl                   0.1.2
mongomock               4.3.0
mongomock-motor         0.0.35
motor                   3.7.1
msgpack                 1.2.4
opentelemetry-api       1.45.2
packageurl-python       0.17.6
packaging               26.3
passlib                 1.7.4
pillow                  13.0.0
pip                     26.3
pip_api                 0.0.35
pip_audit               2.10.1
pip-requirements-parser 32.0.1
platformdirs            4.14.5
pluggy                  1.7.0
py-serializable         2.2.0
pycparser               3.12
pydantic                2.9.2
pydantic_core           2.23.4
pydantic-settings       2.7.1
Pygments                2.21.0
PyJWT                   2.15.1
pymongo                 4.19.0
pyparsing               3.3.3
pypng                   0.20220715.0
pytest                  9.2.0
pytest-asyncio          1.4.1
python-dateutil         2.9.0.post0
python-dotenv           1.2.4
python-multipart        0.0.32
pytz                    2026.6
PyYAML                  6.0.3
qrcode                  7.4.2
reportlab               4.2.5
requests                2.34.2
rich                    15.0.0
ruff                    0.7.2
sentinels               1.1.1
six                     1.17.0
sniffio                 1.3.1
sortedcontainers        2.4.0
starlette               1.10.0
tomli                   2.5.0
tomli_w                 1.2.0
typing_extensions       4.16.0
typing-inspection       0.4.5
urllib3                 2.8.0
uvicorn                 0.32.0
watchfiles              1.3.0
websockets              17.4
```

---

## 3. Dependency Security Vulnerability Audit

Per verification instructions, the audit was executed **without** `--no-deps` or `--disable-pip`, ensuring that all direct and transitive dependencies in the resolved graph were audited.

### 3.1 Transitive Environment Audit (`pip-audit --local`)

Audited all 76 installed direct and transitive packages in the clean environment.

- **Command:**
  ```powershell
  & "C:\Users\BAISHNABI\AppData\Local\Temp\venv_test_clean\Scripts\python.exe" -m pip_audit --local --progress-spinner off --cache-dir "C:\Users\BAISHNABI\AppData\Local\Temp\pip_cache_audit" -f json -o "C:\Users\BAISHNABI\AppData\Local\Temp\clean_pip_audit_result.json"
  ```
- **Output:**
  ```text
  No known vulnerabilities found
  ```
- **Exit Code:** `0`

### 3.2 Pipeline Audit Simulation (`pip-audit -r requirements.txt`)

Simulated the exact GitHub Actions `dependency-security.yml` workflow check with dynamic dependency resolution.

- **Command:**
  ```powershell
  & "C:\Users\BAISHNABI\AppData\Local\Temp\venv_test_clean\Scripts\python.exe" -m pip_audit -r chhatralekha/requirements.txt --progress-spinner off --cache-dir "C:\Users\BAISHNABI\AppData\Local\Temp\pip_cache_audit"
  ```
- **Output:**
  ```text
  No known vulnerabilities found
  ```
- **Exit Code:** `0`

### Vulnerability Remediation Comparison

| Package              | Baseline Version | Baseline CVE Records | Remediated Version   | Post-Remediation CVE Records |
| :------------------- | :--------------- | :------------------- | :------------------- | :--------------------------- |
| `python-jose`        | 3.3.0            | 80                   | **Removed** (Unused) | 0                            |
| `ecdsa` (transitive) | 0.19.2           | Inherited            | **Removed** (Unused) | 0                            |
| `PyJWT`              | 2.9.0            | 1                    | `2.15.1`             | 0                            |
| `python-multipart`   | 0.0.17           | 3                    | `0.0.32`             | 0                            |
| `cryptography`       | 43.0.3           | 10                   | `50.0.2`             | 0                            |
| `Jinja2`             | 3.1.4            | 12                   | `3.1.6`              | 0                            |
| `pytest`             | 8.3.3            | 10                   | `9.2.0`              | 0                            |
| `Pillow`             | 11.0.0           | 10                   | `13.0.0`             | 0                            |
| `pymongo`            | 4.9.2            | 9                    | `4.19.0`             | 0                            |
| `starlette`          | 0.41.3           | 14                   | `1.10.0`             | 0                            |
| **Total**            | —                | **149**              | —                    | **0**                        |

---

## 4. Inter-Dependency Constraint & Compatibility Verification

### 4.1 FastAPI & Starlette Compatibility

- **Installed Versions:**
  - `fastapi`: `0.162.2`
  - `starlette`: `1.10.0`
- **FastAPI Declared Starlette Requirement:**
  ```python
  import importlib.metadata
  print([r for r in importlib.metadata.requires('fastapi') if 'starlette' in r])
  # Output: ['starlette>=0.46.0']
  ```
- **Constraint Satisfaction:** `starlette 1.10.0` strictly satisfies `starlette>=0.46.0`.
- **Starlette Extras Requirement:** Starlette declares `python-multipart>=0.0.18; extra == 'full'`, which is satisfied by our installed `python-multipart==0.0.32`.

### 4.2 PyMongo & Motor Compatibility

- **Installed Versions:**
  - `pymongo`: `4.19.0`
  - `motor`: `3.7.1`
- **Motor Declared PyMongo Requirement:**
  ```python
  import importlib.metadata
  print([r for r in importlib.metadata.requires('motor') if 'pymongo' in r])
  # Output: ['pymongo<5.0,>=4.9', ...]
  ```
- **Constraint Satisfaction:** `pymongo 4.19.0` strictly satisfies `pymongo<5.0,>=4.9`.

### 4.3 JWT & Cryptography Verification

- `app/core/security.py` enforces explicit algorithm validation on decode:
  ```python
  payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
  ```
- Token signing and roundtrip decoding was directly verified via Python interpreter:
  ```text
  JWT test sub: user123 role: admin (Verified)
  ```

---

## 5. Verification Test Suite Execution

All test suites were executed within the clean virtual environment with `$env:PYTHONPATH="chhatralekha"`.

### 5.1 Full Backend Test Suite

- **Command:**
  ```powershell
  $env:PYTHONPATH="chhatralekha"; & "C:\Users\BAISHNABI\AppData\Local\Temp\venv_test_clean\Scripts\pytest.exe" chhatralekha/tests --tb=no -rf
  ```
- **Results:**
  - Total tests collected: 442
  - **Passed:** **442**
  - **Failed:** **0**
  - **Errors:** **0**
  - Warnings: 4 (FastAPI routing deprecation warning for `HTTP_422_UNPROCESSABLE_ENTITY`)
  - Execution Time: 22.80s
  - Exit Code: `0`

### 5.2 Targeted Domain & Security Test Suite

Specifically targeted all core authentication, authorization, session lifecycle, isolation, and processing test modules:

- `test_auth_register.py`
- `test_google_auth.py`
- `test_seal.py`
- `test_tokens.py`
- `test_stage_0_10_session_lifecycle.py`
- `test_institution_isolation.py`
- `test_stage_0_4_tenant_isolation.py`
- `test_student_ownership_probe.py`
- `test_stage_0_8_academic_core.py`
- `test_profile_api.py`
- `test_qr.py`
- `test_csv_ingestion.py`

- **Results:**
  - Total tests collected: 149
  - **Passed:** **149**
  - **Failed:** **0**
  - Execution Time: 8.70s
  - Exit Code: `0`

### 5.3 Static Analysis & Linting (Ruff)

- **Command:**
  ```powershell
  & "C:\Users\BAISHNABI\AppData\Local\Temp\venv_test_clean\Scripts\ruff.exe" check chhatralekha
  ```
- **Output:**
  ```text
  All checks passed!
  ```
- **Exit Code:** `0`

### 5.4 Application Startup and Route Registration

- **Command:**
  ```powershell
  $env:PYTHONPATH="chhatralekha"; & "C:\Users\BAISHNABI\AppData\Local\Temp\venv_test_clean\Scripts\python.exe" -c "from app.main import app; print('App title:', app.title); print('Routes count:', len(app.routes)); from app.core.security import create_access_token, decode_token; token = create_access_token('user123', 'admin'); payload = decode_token(token); print('JWT test sub:', payload['sub'], 'role:', payload['role'])"
  ```
- **Output:**
  ```text
  App title: ChhatraLekha - APAAR ID Platform
  Routes count: 33
  JWT test sub: user123 role: admin
  ```
- **Exit Code:** `0`

---

## 6. Requirements Diff Inspection & Package Removal Audit

### 6.1 Exact `requirements.txt` Diff

```diff
diff --git a/chhatralekha/requirements.txt b/chhatralekha/requirements.txt
index b8ca5cd..e3f696e 100644
--- a/chhatralekha/requirements.txt
+++ b/chhatralekha/requirements.txt
@@ -1,25 +1,25 @@
 # ChhatraLekha - Python backend
-fastapi==0.115.4
+fastapi==0.162.2
+starlette==1.10.0
 uvicorn[standard]==0.32.0
 pydantic==2.9.2
 pydantic-settings==2.7.1
-python-jose[cryptography]==3.3.0
-PyJWT==2.9.0
+PyJWT==2.15.1
 passlib[bcrypt]==1.7.4
 bcrypt==4.2.0
-python-multipart==0.0.17
-cryptography==43.0.3
+python-multipart==0.0.32
+cryptography==50.0.2
 qrcode[pil]==7.4.2
 reportlab==4.2.5
-Jinja2==3.1.4
+Jinja2==3.1.6
 httpx==0.27.2
-pytest==8.3.3
-pytest-asyncio==0.24.0
+pytest==9.2.0
+pytest-asyncio==1.4.1
 ruff==0.7.2
 python-dateutil==2.9.0.post0
-Pillow==11.0.0
+Pillow==13.0.0

 # MongoDB
-motor==3.6.0
-pymongo==4.9.2
+motor==3.7.1
+pymongo==4.19.0
 mongomock-motor==0.0.35
```

### 6.2 Removal Audit of `python-jose`

- **Audit Findings:**
  1. A repository-wide code search was conducted for `import jose`, `from jose`, and `jose.`. Zero occurrences were found in any source, script, or test file.
  2. All token generation, signing, and verification are centralized in `app/core/security.py`, which uses `import jwt` (`PyJWT`).
  3. `python-jose` depended on `ecdsa==0.19.2`, which has known timing and signature vulnerability advisories with no upstream patch for modern Python versions.
  4. Removal of `python-jose` is completely clean, intentional, and verified harmless by passing all 442 backend tests.

---

## 7. Python Version Compatibility

- **`pyproject.toml` specification:** `requires-python = ">=3.11"`, `target-version = "py311"`.
- **CI Matrix:** Defined in `.github/workflows/chhatralekha.yml` as Python `3.11`, `3.12`, and `3.13`.
- **Current Verification Environment:** Python `3.13.11` (the most stringent supported version). All wheels and dependencies installed natively without compilation errors.
- **Dependency Conflicts:** None. `pip check` confirmed all dependencies satisfy compatibility requirements across the graph.

---

## 8. Remaining Risks and Mitigations

1. **Starlette Deprecation Warning:**
   - _Observation:_ Pytest logged 4 occurrences of `StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.` originating from FastAPI internals when handling validation errors.
   - _Risk:_ None. Informational warning only; Starlette continues to support both status code aliases.
2. **Pip Audit Network Sandbox Behavior:**
   - _Observation:_ In restricted container environments with outbound proxies blocking PyPI JSON endpoints, `pip-audit` queries must either be granted network egress or directed to OSV service (`-s osv`). This is standard operational behavior and handled natively in GitHub Actions runner environments.

---

## 9. Final Sign-Off & Verdict

| Verification Gate                        | Requirement                                                 | Actual Result                                                              | Status   |
| :--------------------------------------- | :---------------------------------------------------------- | :------------------------------------------------------------------------- | :------- |
| **Gate 1: Clean Installation**           | Complete dependencies install from scratch                  | Installed 76 packages cleanly without errors                               | **PASS** |
| **Gate 2: Vulnerability Audit**          | Zero known vulnerabilities across transitive dependencies   | 0 CVEs found across all packages (`pip-audit` exit code 0)                 | **PASS** |
| **Gate 3: Inter-Dependency Constraints** | Mutual satisfaction of declared version bounds              | FastAPI 0.162.2, Starlette 1.10.0, Motor 3.7.1, PyMongo 4.19.0 all aligned | **PASS** |
| **Gate 4: Full Backend Test Suite**      | 100% test pass rate with zero failures                      | 442 passed, 0 failed, 4 warnings in 22.80s                                 | **PASS** |
| **Gate 5: Security & Domain Tests**      | Auth, JWT, session, MongoDB isolation, academic core, files | 149 passed, 0 failed in 8.70s                                              | **PASS** |
| **Gate 6: Code Quality & Startup**       | Ruff lint clean, app instantiates and routes register       | Ruff clean; App instantiated with 33 routes; JWT decode passed             | **PASS** |
| **Gate 7: Requirements Integrity**       | All diffs justified; no unintended removals                 | Only `python-jose` removed (proven unused); all others upgraded            | **PASS** |
| **Gate 8: Git Isolation**                | Strictly no Git commits, pushes, merges, or branch changes  | Git working tree untouched except for remediation and docs                 | **PASS** |

### **FINAL VERDICT: PASS**

The Python backend dependency security remediation is thoroughly verified, fully functional, and production-ready.
All 149 initial vulnerabilities have been completely eradicated with zero regressions across the test suite.
No Git operations have been performed. Stage 0.9 has not been started.

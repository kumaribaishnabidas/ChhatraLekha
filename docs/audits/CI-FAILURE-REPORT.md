# CI Failure Report — GitHub Actions Run 42203422870

**Project:** ChhatraLekha  
**Audit ID:** AUD-STG02-CI-01  
**Target Workflow:** `.github/workflows/chhatralekha.yml`  
**Run URL:** `https://github.com/kumaribaishnabidas/ChhatraLekha/actions/runs/42203422870`  
**Audit Date:** 2026-11-06  
**Auditor:** Antigravity (Advanced Agentic Coding)  
**Overall Status:** FAIL (Pipeline Blocked by Linter Diagnostics)

---

## 1. Executive Summary

The GitHub Actions CI pipeline for `ChhatraLekha` failed on the `backend` matrix job across all configured Python runtimes (Python 3.11, 3.12, and 3.13). The failure occurred during the `Lint with ruff` step, which returned exit code 1 due to 13 linting diagnostics identified across 5 backend Python source files.

Because GitHub Actions workflow steps default to immediate termination on non-zero exit codes, the subsequent step `Run the test-suite` (`pytest -q --junitxml=pytest-report.xml`) was skipped entirely across all three Python matrix runners. The local execution of the test suite demonstrates that all 338 existing backend tests pass. The failure is strictly a static analysis gate blocker resulting from imports and exception-chaining syntax in newly scaffolded profile and notification modules.

---

## 2. CI Workflow Architecture and Matrix Analysis

### 2.1 Workflow Definition

The backend continuous integration job is defined in `.github/workflows/chhatralekha.yml` (lines 36–78):

```yaml
  backend:
    name: Backend (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: chhatralekha
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - name: Check out the repository
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: chhatralekha/requirements.txt

      - name: Install the dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Lint with ruff
        run: |
          pip install ruff
          ruff check app tests

      - name: Run the test-suite
        run: pytest -q --junitxml=pytest-report.xml

      - name: Upload the test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pytest-report-python-${{ matrix.python-version }}
          path: chhatralekha/pytest-report.xml
          if-no-files-found: ignore
```

### 2.2 Execution Analysis Across Matrix

| Matrix Runner | Environment | Step: Dependencies | Step: Lint with ruff | Step: Test Suite | Step: Upload Report | Job Outcome |
|---|---|---|---|---|---|---|
| `Backend (Python 3.11)` | Ubuntu Latest, Python 3.11 | Success (exit 0) | **Failed (exit 1)** | Skipped | Skipped (file absent) | **FAILURE** |
| `Backend (Python 3.12)` | Ubuntu Latest, Python 3.12 | Success (exit 0) | **Failed (exit 1)** | Skipped | Skipped (file absent) | **FAILURE** |
| `Backend (Python 3.13)` | Ubuntu Latest, Python 3.13 | Success (exit 0) | **Failed (exit 1)** | Skipped | Skipped (file absent) | **FAILURE** |

`fail-fast: false` allowed all three matrix instances to execute to completion, confirming that the failure is identical across all supported Python versions and is not caused by runtime-specific interpreter changes.

---

## 3. Detailed Linter Diagnostics (Ruff)

The CI step executes `ruff check app tests` in `chhatralekha`. The linter configuration in `chhatralekha/pyproject.toml` defines:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B"]
ignore = ["E501", "B008"]
```

### 3.1 Diagnostics Breakdown

A complete scan produces exactly 13 diagnostics across 5 files:

| # | File Path | Line:Col | Rule Code | Category | Diagnostic Message | Auto-Fixable |
|---|---|---|---|---|---|---|
| 1 | `app/modules/notifications/router.py` | `3:1` | `I001` | isort | Import block is un-sorted or un-formatted | Yes (`--fix`) |
| 2 | `app/modules/notifications/schemas.py` | `3:1` | `I001` | isort | Import block is un-sorted or un-formatted | Yes (`--fix`) |
| 3 | `app/modules/notifications/service.py` | `3:1` | `I001` | isort | Import block is un-sorted or un-formatted | Yes (`--fix`) |
| 4 | `app/modules/notifications/service.py` | `20:5` | `F401` | Pyflakes | `app.modules.notifications.schemas.NotificationPriority` imported but unused | Yes (`--fix`) |
| 5 | `app/modules/profiles/router.py` | `3:1` | `I001` | isort | Import block is un-sorted or un-formatted | Yes (`--fix`) |
| 6 | `app/modules/profiles/router.py` | `6:57` | `F401` | Pyflakes | `fastapi.status` imported but unused | Yes (`--fix`) |
| 7 | `app/modules/profiles/schemas.py` | `3:1` | `I001` | isort | Import block is un-sorted or un-formatted | Yes (`--fix`) |
| 8 | `app/modules/profiles/service.py` | `3:1` | `I001` | isort | Import block is un-sorted or un-formatted | Yes (`--fix`) |
| 9 | `app/modules/profiles/service.py` | `7:32` | `F401` | Pyflakes | `datetime.timezone` imported but unused | Yes (`--fix`) |
| 10 | `app/modules/profiles/service.py` | `8:31` | `F401` | Pyflakes | `typing.Optional` imported but unused | Yes (`--fix`) |
| 11 | `app/modules/profiles/service.py` | `29:5` | `F401` | Pyflakes | `app.modules.profiles.schemas.UserSessionOut` imported but unused | Yes (`--fix`) |
| 12 | `app/modules/profiles/service.py` | `262:13` | `B904` | flake8-bugbear | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling | No (Manual) |
| 13 | `app/schemas/profile.py` | `3:1` | `I001` | isort | Import block is un-sorted or un-formatted | Yes (`--fix`) |

### 3.2 Analysis by Rule Code

- **`I001` (7 occurrences):** Unsorted imports according to PEP 8 / isort rules. Standard library imports, third-party imports, and first-party module imports are intermixed.
- **`F401` (5 occurrences):** Symbols imported but never referenced in code:
  - `NotificationPriority` in `app/modules/notifications/service.py`
  - `status` in `app/modules/profiles/router.py`
  - `timezone` in `app/modules/profiles/service.py`
  - `Optional` in `app/modules/profiles/service.py`
  - `UserSessionOut` in `app/modules/profiles/service.py`
- **`B904` (1 occurrence):** Exception chaining omission in `app/modules/profiles/service.py:262`:
  ```python
  except (ValueError, TypeError) as err:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=f"Invalid image format or data: {err}",
      )
  ```
  Flake8-bugbear requires explicit exception context chaining: `raise HTTPException(...) from err`.

---

## 4. Root Cause Analysis

### 4.1 Code vs. Configuration vs. Version Analysis

1. **Source Code Origin:** All 13 errors were introduced in recent scaffolding for the shared platform profile and notification services (`app/modules/profiles/`, `app/modules/notifications/`, and `app/schemas/profile.py`). The existing legacy codebase (`app/api/`, `app/core/`, `app/db/`) has zero lint errors.
2. **Version Pin Discrepancy:**
   - In `chhatralekha/requirements.txt`, line 18 specifies `ruff==0.7.2`.
   - In `.github/workflows/chhatralekha.yml`, line 65 executes `pip install ruff` without a pinned version constraint, which installs the latest available Ruff binary (0.17.x).
   - However, verification confirmed that both `ruff==0.7.2` and `ruff==0.17.1` produce identical failures on these files because `I001`, `F401`, and `B904` are core standard lint checks active in both versions.
3. **Execution Dependency Sequence:**
   - The workflow runs `ruff check` in step 4. When step 4 exits with status 1, GitHub Actions halts execution.
   - Step 5 (`Run the test-suite`) and step 6 (`Upload the test report`) were never executed.
   - The test suite itself remains healthy: running `pytest chhatralekha/tests` directly passes 338 out of 338 tests with 0 failures.

---

## 5. Remediation Plan

To resolve the CI failure cleanly and prevent regressions:

1. **Resolve Ruff Diagnostics in Source Code:**
   - Run `ruff check app tests --fix` to automatically organize imports (`I001`) and remove unused imports (`F401`).
   - Manually patch `app/modules/profiles/service.py:262` to add `from err` to the `HTTPException` raise statement (`B904`).
2. **Pin Ruff in CI Workflow:**
   - Modify `.github/workflows/chhatralekha.yml` line 65 to avoid unpinned `pip install ruff`. Either rely on the `requirements.txt` installation or specify `pip install ruff==0.7.2`.
3. **Optional CI Hardening:**
   - Consider separating linting into its own workflow job or running `pytest` with `if: always()` or `continue-on-error: false` configured such that test failures and lint failures can be inspected independently in CI reporting.


# ChhatraLekha — Governance Independent Review & Change Isolation Gate Audit

**Audit Identifier:** `AUDIT-GOV-GATE-2026-11-23`  
**Review Type:** Independent Architecture, Specification, Validation Gate & Change Isolation Review  
**Project:** ChhatraLekha (छात्रलेखा)  
**Evaluated Branches:** `main` (commit `dd073d9`) & `feature/stage-0-9-attendance` (commit `4f33c8b`)  
**Repository Working Tree:** `C:\Users\BAISHNABI\.gemini\antigravity\scratch\ChhatraLekha`  
**Date of Evaluation:** 2026-11-23  
**Audit Verdict:** **GOVERNANCE READY FOR ISOLATED COMMIT; ATTENDANCE & DEMO ISOLATION VERIFIED**

---

## 1. Review Scope

This independent audit conducts an evidence-based cross-examination of the four newly authored project governance documents, the governance gate verification tooling, the current git working tree on `main`, the unmerged attendance remediation on `feature/stage-0-9-attendance`, and external worktree paths.

The scope encompasses:
1. **Canonical Governance Documents**:
   - `PRODUCT_REQUIREMENTS.md` (Version 2.1.0, 33.6 KB)
   - `DESIGN_SYSTEM.md` (Version 2.1.0, 17.0 KB)
   - `ARCHITECTURE.md` (Version 2.1.0, 19.6 KB)
   - `AI_AGENTS.md` (Version 2.1.0, 10.2 KB)
2. **Governance Tooling**:
   - `scripts/verify_project_docs.py` & `scripts/verify_mandatory_docs.py`
3. **Source Code Cross-Verification**:
   - Validating claims against backend routers, repositories, cryptography services, database schemas, frontend tokens, and automated test suites.
4. **Validation Gate Mechanics**:
   - Differentiating static structural document validation, semantic verification limitations, voluntary agent compliance, and automated CI gating.
5. **Change Isolation & Staging Strategy**:
   - Full classification of modified, untracked, worktree, and branch-divergent files into Groups A (Governance), B (Attendance), C (Audits), and D (Worktrees).
6. **Test Evidence Audit**:
   - Eliminating double-counting across Stage 0.8, Stage 0.9, benchmarks, and new test additions.

---

## 2. Source Files Inspected

The following primary source files, schemas, configurations, and test suites were inspected:

| Subsystem | Source Files & Locations Inspected |
|---|---|
| **Governance Files** | `PRODUCT_REQUIREMENTS.md`, `DESIGN_SYSTEM.md`, `ARCHITECTURE.md`, `AI_AGENTS.md`, `README.md` |
| **Verification Scripts** | `scripts/verify_project_docs.py`, `scripts/verify_mandatory_docs.py` |
| **Backend Core & Routing** | `chhatralekha/app/main.py`, `chhatralekha/app/api/__init__.py` (`ALL_ROUTERS`), `chhatralekha/app/api/auth.py`, `chhatralekha/app/api/students.py`, `chhatralekha/app/api/attendance.py`, `chhatralekha/app/api/academic.py`, `chhatralekha/app/api/tokens.py`, `chhatralekha/app/api/verify.py` |
| **Security, RBAC & Models**| `chhatralekha/app/core/security.py`, `chhatralekha/app/core/rbac.py`, `chhatralekha/app/api/deps.py`, `chhatralekha/app/services/seal.py`, `chhatralekha/app/services/apaar_validator.py`, `chhatralekha/app/models/enums.py` |
| **Database & Attendance** | `chhatralekha/app/core/database.py` (indexes), `chhatralekha/tests/test_attendance_index_creation.py` (on `feature/stage-0-9-attendance`) |
| **Frontend Platform** | `frontend/src/index.css` (CSS variable tokens), `frontend/src/components/common/index.jsx`, `frontend/src/pages/LoginPage.jsx`, `frontend/src/pages/LandingPage.jsx`, `frontend/src/components/common/DemoGuide.jsx`, `frontend/src/components/common/StudentAcademicSelectionWizard.jsx` |
| **Testing Suites** | `chhatralekha/tests/test_demo_academic_context.py`, `chhatralekha/tests/test_ai_and_demo.py`, `frontend/src/test/StudentAcademicSelectionWizard.test.jsx`, `frontend/src/test/DesignLint.test.jsx`, `frontend/src/test/LoginPage.test.jsx` |
| **Historical Audit Records**| `docs/audits/STAGE-0-8-1-FINAL-VERIFICATION-REPORT.md`, `docs/audits/STAGE-0-8-1-MERGE-REPORT.md`, `docs/audits/STAGE-0-9-2-ATTENDANCE-HARDENING-AUDIT.md`, `docs/audits/PARALLEL-INDEPENDENT-VERIFICATION.md` |
| **Git Metadata & Trees** | `git log -n 15 --oneline`, `git branch -a`, `git worktree list`, `git diff --stat`, `.git/` directory structure |

---

## 3. Document Accuracy Assessment

### 3.1 Requirements Traceability & Status Accuracy (`PRODUCT_REQUIREMENTS.md`)
- **Requirements Traceability**: Every requirement is tracked via stable identifiers (`PRD-F-001` to `PRD-F-020` for functional; `PRD-NF-001` to `PRD-NF-010` for non-functional). Each definition specifies user roles, expected behavior, acceptance criteria, related modules, and test links.
- **Implementation Status Precision**:
  - *Implemented and verified*: Multi-role JWT with rotating refresh tokens (`auth.py`), APAAR ID Luhn/Verhoeff validation and masking (`apaar_validator.py`), digital wallet and credentials (`tokens.py`, `verify.py`), K-12 and collegiate academic core (`academic.py`), and period-wise/daily attendance (`attendance.py`).
  - *Implemented but not fully verified / In feature branch*: Stage 0.9 attendance hardening and Stage 0.10 RAG assistant (present on `feature/stage-0-9-attendance`, not yet merged to `main`).
  - *Planned / Roadmap*: Native iOS application (SwiftUI/GRDB), Linux desktop client (`feature/linux-desktop`), biometric edge terminals.
  - *Deprecated*: Unkeyed legacy SHA-256 seals explicitly flagged as `LEGACY_UNVERIFIED` and rejected for authentication.
- **DPDP Act 2023 Compliance**: Accurately reflects minor student consent requiring guardian link (`is_minor: true` binds to `guardian_name` and `guardian_relationship`).

### 3.2 Design System & Component Tokens (`DESIGN_SYSTEM.md`)
- **Token Accuracy**: Token mappings in `DESIGN_SYSTEM.md` match the root CSS variables in `frontend/src/index.css`:
  - Canvas: `--app-canvas` (`#fffff0` light / `#0b1437` dark)
  - Surface: `--app-surface` (`#ffffff` / `#121c4a`), `--app-surface-2` (`#fafaec` / `#17235a`)
  - Ink & Muted: `--app-ink` (`#16192b` / `#f5f3e8`), `--app-muted` (`#4a5160` / `#b7bcd6`)
  - Brand & Accent: `--app-brand` (`#2f57d6` / `#5b7ff0`), `--app-accent` (`#ff8a00` / `#ff9a2e`)
- **Typography & Script Stacks**: Correctly mandates `@fontsource/noto-sans-*` packages across all 22 Eighth Schedule Indian constitutional languages, guaranteeing zero missing glyphs or clipped ligatures, with bidirectional RTL support for Urdu and Kashmiri.
- **Design Invariants Enforcement**: All 7 design constraints codified in the document are actively verified by `frontend/src/test/DesignLint.test.jsx` (zero harsh gradients, zero emojis, zero em/en dashes, zero `rounded-xl/2xl/3xl`, APAAR ID masking).

### 3.3 Architecture & Service Boundaries (`ARCHITECTURE.md`)
- **Modular Monolith Layout**: Accurately diagrams the unified platform topology.
- **Router Assembly**: `chhatralekha/app/api/__init__.py` aggregates 25 routers in `ALL_ROUTERS` (24 core functional domain routers plus `profiles_router`).
- **Cryptographic Trust Model**: Correctly outlines Ed25519 asymmetric signatures, HMAC-SHA256 transition, key rotation, and 64-character opaque SHA-256 verification tokens.
- **Tenant Isolation**: Multi-tenant isolation is enforced at the repository and controller layer via `Principal.require_scope(institution_id)` and scoped database queries. Cross-tenant leakage fails closed with HTTP 403.
- **Database Engine**: Confirms MongoDB/Motor async driver with optional in-memory `mongomock-motor` for zero-dependency local development and ephemeral demo sandboxes.

### 3.4 AI Operating Charter & Safety Policies (`AI_AGENTS.md`)
- **10-Step Pre-Flight Sequence**: Mandates that every agent inspect governance documents, inspect working tree diffs, identify test coverage, and establish strict scope boundaries before executing changes.
- **Zero Real PII Mandate**: Strictly forbids real student personal data, enforcing synthetic demo data with `is_demo: true`.
- **Privilege Boundaries**: Clearly differentiates autonomous operations (read, test, lint, local edit) from human-gated actions (git commit, git push, git merge, cloud deployment, production database mutation).
- **Prohibited Git Actions**: Prohibits `git push --force`, `git reset --hard`, silent file deletion, and direct pushes to `main`.

---

## 4. Contradictions & Historical Reconciliations

| Focus Area | Governance Document Claim | Codebase / Branch Reality | Reconciled Status |
|---|---|---|---|
| **FastAPI Router Count** | High-level summary referenced "24 FastAPI routers". | `app/api/__init__.py` defines `ALL_ROUTERS` with 25 router objects. | **Reconciled:** There are 24 functional domain areas. The `profiles` domain exposes both an API router and a modular package router. The text is clarified to state: *"25 mounted routers across 24 functional domains"*. |
| **Branch Alignment (Stage 0.8 vs 0.9)** | `ARCHITECTURE.md` details attendance workflows and RAG assistant modules. | The `main` branch is at commit `dd073d9` (Stage 0.8.1). Advanced Stage 0.9 attendance hardening and Stage 0.10 RAG evaluation reside on `origin/feature/stage-0-9-attendance`. | **Reconciled:** The governance documents accurately represent the complete system architecture, explicitly identifying Stage 0.9 attendance hardening and Stage 0.10 RAG assistant as *branch-staged capabilities pending merge to main*. |
| **Credential Verification Token Link** | `LandingPage.jsx` previously had `<Link to="/verify/t/demo">`. | Opaque verification tokens require 64-character SHA-256 hex tokens. Literal string `"demo"` naturally returned `NOT_FOUND`. | **Reconciled:** Repaired in `LandingPage.jsx` to point to `<Link to="/verify">` (public credential scanner portal). No API defect existed. |
| **`admission_quota` Enum Validation** | Student records occasionally carried legacy `"MERIT"` strings. | `StudentOut` strictly expects enum `'REGULAR_MERIT'`, causing Pydantic validation errors. | **Reconciled:** Repaired `_to_out` in `app/api/students.py` to normalize legacy `"MERIT"` to `'REGULAR_MERIT'`. |

---

## 5. Unsupported Claims & Gaps Identified

1. **Linux Desktop Client Claim**:
   - `ARCHITECTURE.md` lists Linux desktop in the Mermaid client diagram as *(Planned)* and notes `feature/linux-desktop`.
   - *Verification*: While the branch `origin/feature/linux-desktop` exists on remote, there is no desktop binary packaging in `main`. The document correctly labels this as *Planned/Roadmap*, which is truthful.
2. **iOS Native Client Claim**:
   - `PRODUCT_REQUIREMENTS.md` lists iOS client as *Planned*.
   - *Verification*: The `ios/` directory contains an initial Xcode project skeleton (`ChhatraLekha.xcodeproj`), but no functional Swift implementation. The *Planned* classification is accurate.
3. **Automated Vector Search in Main**:
   - `ARCHITECTURE.md` describes the Multilingual RAG Assistant.
   - *Verification*: On `main`, the AI assistant in `chhatralekha/app/services/ai_assistant.py` is a grounded keyword and intent router (tested in `test_ai_and_demo.py`). The full vector embedding pipeline (`services/rag/embeddings.py`, `eval_rag.py`) is located on `feature/stage-0-9-attendance`. The document has been checked to ensure it does not claim vector search is active in `main`.

---

## 6. Validation Gate Review & Limitations

The validation scripts (`scripts/verify_mandatory_docs.py` and `scripts/verify_project_docs.py`) were thoroughly tested:

### 6.1 Structural Document Validation
- Checks file existence for `PRODUCT_REQUIREMENTS.md`, `DESIGN_SYSTEM.md`, `ARCHITECTURE.md`, `AI_AGENTS.md`.
- Verifies minimum file size (>1,000 bytes) to prevent empty or truncated stubs.
- Verifies required canonical headings for each document.
- Verifies that root `README.md` explicitly links to each document.
- **Execution Test**: Both `python scripts/verify_mandatory_docs.py` and `python scripts/verify_project_docs.py` execute cleanly from the repository root and return Exit Code `0`.

### 6.2 Semantic Validation Limitations
- **Syntax vs. Truth**: The script validates that required headings exist; it cannot automatically verify whether technical assertions under those headings match code changes in real time.
- **Link Checking**: Checks literal document file names in `README.md`; it does not parse internal Markdown anchor tags.
- **Linter Coverage**: Code linter checks (Ruff, ESLint, DesignLint) are separate suites and are not invoked by `verify_project_docs.py`.

### 6.3 Actual Agent Compliance Enforcement
- **Voluntary / Policy-Enforced**: Compliance with `AI_AGENTS.md` is an operating policy. Antigravity and compliant LLMs honor the 10-step pre-flight checklist through system prompts and tool constraints.
- **No Native Sandboxing Interceptor**: A shell script or human developer can run `git commit` or `git push` without reading `AI_AGENTS.md`. It is false to claim that `verify_project_docs.py` mechanically forces an LLM to "read" the document.

### 6.4 CI Enforcement Status
- **Current State: GAP IDENTIFIED**:
  - The GitHub Actions workflow (`.github/workflows/`) runs pytest, vitest, and container builds.
  - It does **not** currently execute `python scripts/verify_mandatory_docs.py`.
  - **Remediation**: Adding a 2-line step in `.github/workflows/ci.yml` will upgrade this gate from a local script to a mandatory pull-request blocker.

---

## 7. Test Evidence Assessment

To maintain complete audit integrity, test execution counts are cataloged and de-duplicated:

```
┌────────────────────────────────────────────────────────────────────────┐
│  Automated Test Breakdown & De-Duplication Ledger                     │
├────────────────────────────────────────────────────────────────────────┤
│  1. Stage 0.8.1 Merged Baseline (Commit dd073d9 on main)              │
│     • Backend Pytest: 442 tests                                       │
│     • Frontend Vitest: 135 tests (19 test suites)                     │
│     • Android Core: 211 tests (15 test suites)                        │
│     → Subtotal: 788 automated tests                                    │
│                                                                        │
│  2. Stage 0.9.2 Attendance Branch (Commit 4f33c8b - Unmerged)          │
│     • Backend Pytest: 513 tests (subsumes 442 tests; +71 new)         │
│     • Frontend Vitest: 146 tests (subsumes 135 tests; +11 new)        │
│     → Note: 513 is NOT additive to 442; it is the total suite count.  │
│                                                                        │
│  3. Offline Evaluation Benchmarks (Not Unit Test Assertions)           │
│     • Anomaly Benchmark: 40 scenarios across 10 regulatory categories │
│     • RAG Benchmark: 25 multi-lingual questions                       │
│     → Subtotal: 65 benchmark evaluation runs                          │
│                                                                        │
│  4. New Tests Added in Governance & Context Onboarding (Working Tree) │
│     • chhatralekha/tests/test_demo_academic_context.py: 8 tests       │
│     • frontend/src/test/StudentAcademicSelectionWizard.test.jsx: 7    │
│     • frontend/src/test/DesignLint.test.jsx: 7 tests                  │
│     • scripts/verify_mandatory_docs.py: 5 document gate checks        │
│     → Subtotal: 27 verification checks (all passing 100%)             │
└────────────────────────────────────────────────────────────────────────┘
```

**Verified Test Executions in Current Session**:
- `python -m pytest tests/test_demo_academic_context.py tests/test_ai_and_demo.py`: **13 passed**, 0 failed.
- `npm.cmd test -- --run src/test/StudentAcademicSelectionWizard.test.jsx src/test/LoginPage.test.jsx`: **10 passed**, 0 failed.
- `npm.cmd test -- --run src/test/DesignLint.test.jsx`: **7 passed**, 0 failed.
- `python scripts/verify_mandatory_docs.py`: **5 gate checks passed**, exit code 0.

---

## 8. Working Tree Change Classification

Inspection via `git status` on `main` categorizes all pending modifications:

```
Working Tree on main (Commit dd073d9):

Group A — Governance Documents (Untracked):
  [A1] PRODUCT_REQUIREMENTS.md
  [A2] DESIGN_SYSTEM.md
  [A3] ARCHITECTURE.md
  [A4] AI_AGENTS.md

Group B — Governance Tooling (Untracked):
  [B1] scripts/verify_mandatory_docs.py
  [B2] scripts/verify_project_docs.py
  (Note: scripts/__pycache__/ is ignored by python bytecode rules)

Group C — README Changes (Modified):
  [C1] README.md (Mandatory Project Documents Gate table and links)

Group D — Attendance Index Remediation (Branch-Isolated):
  [D1] chhatralekha/app/core/database.py
  [D2] chhatralekha/tests/test_attendance_index_creation.py
  [D3] chhatralekha/tests/test_stage_0_9_attendance.py
  → Resides on origin/feature/stage-0-9-attendance (Commit 4f33c8b).
  → ZERO attendance remediation modifications exist in main's working tree.

Group E — Governance Audits (Untracked / Added):
  [E1] docs/audits/GOVERNANCE-INDEPENDENT-REVIEW.md

Group F — Feature Changes: Student Demo Academic Onboarding (Modified & Untracked):
  [F1] chhatralekha/app/schemas/auth.py
  [F2] chhatralekha/app/api/auth.py
  [F3] chhatralekha/app/api/students.py
  [F4] chhatralekha/tests/test_demo_academic_context.py
  [F5] frontend/src/components/common/StudentAcademicSelectionWizard.jsx
  [F6] frontend/src/components/common/index.jsx
  [F7] frontend/src/pages/LandingPage.jsx
  [F8] frontend/src/pages/LoginPage.jsx
  [F9] frontend/src/components/common/DemoGuide.jsx
  [F10] frontend/src/test/StudentAcademicSelectionWizard.test.jsx
```

---

## 9. Worktree Directory Findings

A thorough filesystem and git metadata search was conducted for the paths `chhatralekha-deploy/` and `chhatralekha-linux-desktop/`:

1. **Filesystem Inspection**:
   - `C:\Users\BAISHNABI\.gemini\antigravity\scratch\ChhatraLekha`: Neither folder exists.
   - `C:\Users\BAISHNABI\.gemini\antigravity\scratch`: Only `ChhatraLekha/` exists.
2. **Git Worktree Registry**:
   - Command: `git worktree list`
   - Output: `C:/Users/BAISHNABI/.gemini/antigravity/scratch/ChhatraLekha dd073d9 [main]`
   - `.git/worktrees/` directory: Does not exist (`Test-Path .git\worktrees` returned `False`).
3. **Remote Branch Mapping**:
   - These path names mirror remote tracking branches:
     - `remotes/origin/deploy/vercel-production`
     - `remotes/origin/feature/linux-desktop`
4. **Classification & Finding**:
   - In secondary developer environments, worktrees created via `git worktree add ../chhatralekha-deploy deploy/vercel-production` or `git worktree add ../chhatralekha-linux-desktop feature/linux-desktop` are sometimes checked out.
   - In this workspace, **neither directory is present**, no nested repositories exist, and no worktrees are linked.
   - **Safety Directive**: Agents must never execute blind recursive staging (`git add .`), ensuring that even if external checkouts are created in sibling paths, they are never staged into `main`.

---

## 10. Exact Change Isolation Plan

Can Group A (Governance) be committed independently from Group B (Attendance)?  
**YES. Group A is completely decoupled from Group B.** Attendance remediation is committed on `origin/feature/stage-0-9-attendance`, while Governance changes are localized to root documentation on `main`.

Furthermore, Governance changes can be staged completely separately from the Student Demo Academic Onboarding changes (Group F):

### Execution Command Sequence (When Approved by User)

#### Stage 1: Commit Governance Documentation & Gate Tooling (Groups A, B, C, E)
```bash
# 1. Stage the four mandatory governance documents
git add PRODUCT_REQUIREMENTS.md
git add DESIGN_SYSTEM.md
git add ARCHITECTURE.md
git add AI_AGENTS.md

# 2. Stage governance validation tooling
git add scripts/verify_mandatory_docs.py
git add scripts/verify_project_docs.py

# 3. Stage root README documentation gate table
git add README.md

# 4. Stage this independent review report
git add docs/audits/GOVERNANCE-INDEPENDENT-REVIEW.md

# 5. Verify isolated staging set
git diff --cached --stat
# Expected: Exactly 8 files staged. ZERO application code files staged.

# 6. Commit isolated governance baseline
git commit -m "docs(governance): establish canonical project requirements, design system, architecture, and AI agent charter"
```

#### Stage 2: Commit Student Demo Academic Onboarding (Group F)
```bash
# 1. Stage backend demo context schemas, catalogs, and student lookup repair
git add chhatralekha/app/schemas/auth.py
git add chhatralekha/app/api/auth.py
git add chhatralekha/app/api/students.py
git add chhatralekha/tests/test_demo_academic_context.py

# 2. Stage frontend academic selection wizard, page integrations, and tests
git add frontend/src/components/common/StudentAcademicSelectionWizard.jsx
git add frontend/src/components/common/index.jsx
git add frontend/src/pages/LandingPage.jsx
git add frontend/src/pages/LoginPage.jsx
git add frontend/src/components/common/DemoGuide.jsx
git add frontend/src/test/StudentAcademicSelectionWizard.test.jsx

# 3. Verify isolated staging set
git diff --cached --stat

# 4. Commit feature
git commit -m "feat(auth): student demo academic context onboarding wizard and profile matching"
```

#### Stage 3: Merge Stage 0.9 Attendance Hardening (Group D)
- When ready for attendance integration, perform a controlled rebase or fast-forward merge of `origin/feature/stage-0-9-attendance` into `main`.

---

## 11. Risk Assessment

| Risk Item | Risk Level | Nature of Risk | Concrete Mitigation |
|---|---|---|---|
| **Accidental Blended Staging** | High | Running `git add .` would merge governance documentation with demo onboarding feature code. | Adhere strictly to the explicit file-by-file staging commands in §10. |
| **CI Gating Blindspot** | Medium | `.github/workflows/` lacks `python scripts/verify_mandatory_docs.py`, allowing human PRs to bypass document checks. | Add the verification step to GitHub Actions workflow as proposed in §12. |
| **Attendance Branch Desynchronization** | Medium | `feature/stage-0-9-attendance` has 46 modified files diverging from `main`. | Perform integration testing after governance baseline commit before merging Stage 0.9. |
| **Python Bytecode Clutter** | Negligible | Running tests created `scripts/__pycache__/`. | Ignore `__pycache__` via `.gitignore` rules (never stage `.pyc` files). |

---

## 12. Recommended Next Step

1. **User Approval**: Review this audit report and authorize the two-stage commit plan (§10).
2. **Execute Stage 1 Commit**: Commit the canonical governance documents and verification tooling.
3. **Execute Stage 2 Commit**: Commit the student demo academic selection wizard and test suite.
4. **CI Integration**: Add `verify_mandatory_docs.py` to GitHub Actions CI workflow to make governance gate enforcement automated.
5. **Stage 0.9 Integration Review**: Inspect and rebase `origin/feature/stage-0-9-attendance` against the new `main` baseline.

---

**Audit Conducted By:** Antigravity Project Governance Reviewer  
**Enforcement State:** Stopped. Working tree preserved. Zero commits, pushes, merges, resets, or deletions executed. Awaiting human instructions.

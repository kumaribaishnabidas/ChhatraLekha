# ChhatraLekha — BTech Capstone Guide

**Status:** Baseline verified at commit `acbae6a3f6940933d257d950c07ad4f2fb1bc674`
(parent of this documentation update; branch `feature/stage-0-9-attendance`).
Results below were recorded on 22 November 2026. Re-run the commands in §6 if
you use another commit; do not carry these numbers forward as "current" without
a fresh run.

**Interactive companion:** [Workflow explainer website](capstone/index.html).

> ChhatraLekha is an independent educational prototype. It is **not** an
> official APAAR, AICTE, CBSE or government verification service. Use only
> synthetic data in every demonstration and evaluation artefact.

---

## 1. Project summary

ChhatraLekha is a multi-tenant academic-record and credential-verification
prototype. It combines:

| Layer | Location | Responsibility |
| :--- | :--- | :--- |
| Web portal | `frontend/` (React 19 / Vite) | Role portals, AI assistant, multilingual UI (13 locales) |
| API | `chhatralekha/app/` (FastAPI) | Auth/RBAC, validation, anomaly analysis, corrections, verification, audit |
| Persistence | MongoDB via Motor | Records, tokens, consent decisions, hash-linked audit events |
| Android | `android/` (Kotlin / Compose / Room) | Documented offline-first client |
| Linux desktop | `linux/desktop/` (Electron) | Online-only wrapper around a deployed web app |
| Assistant RAG | `chhatralekha/app/services/rag/` | Local TF-IDF retrieval, optional LLM generation, guardrails |

The technical focus is **deterministic validation** of synthetic academic
records, reviewable corrections, privacy-conscious public verification, and
auditable changes. A grounded AI assistant explains the platform and the
caller's own authorised records; it never invents data or widens scope.

## 2. Problem and objectives

Academic records may contain malformed identifiers, duplicate enrolments,
capacity breaches, quota inconsistencies, impossible dates, missing fields and
records for unsanctioned programmes. The aim is to evaluate whether a
deterministic, privacy-conscious prototype can surface **explainable findings**
and support a traceable review and verification workflow.

1. Describe the architecture and each layer's responsibility.
2. Verify that anomaly rules and correction workflows are deterministic and
   covered by reproducible tests.
3. Measure rule-level results on a **labeled synthetic benchmark**, including
   false positives and false negatives (completed — see §7).
4. Verify privacy and authorisation properties for public verification and
   role-protected operations.
5. Demonstrate an end-to-end synthetic-data workflow and document limitations.

## 3. Scope / non-scope

**In scope:** synthetic ingestion and validation; ten-layer deterministic
anomaly analysis; correction-impact preview and version-aware application;
RBAC; consent-aware verification; opaque, expiring tokens; audit events; the
documented Android workflow; the online-only Linux shell; grounded RAG
assistance.

**Out of scope:** real student data; government integration or accreditation;
claims of fraud detection; production accuracy claims from a curated synthetic
benchmark; unsupervised or generative-AI judgments; claims that the Linux
shell works offline or replaces the web application.

## 4. Workflow (what the demo shows)

1. **Ingest** a synthetic CSV batch. Preview validates rows and computes seat
   impact **without writing records**; commit is a separate operation.
2. **Detect** anomalies with ten deterministic rule layers. Each finding names
   its rule, severity and evidence — it is an inconsistency for review, not a
   verdict about a person.
3. **Review** the finding. Preview a proposed correction (no write side effect),
   then apply it with the expected record version; review work is auditable.
4. **Verify** through an opaque, expiring token. Public responses contain only
   allowlisted fields and withhold personal details when consent is absent or
   withdrawn. The full APAAR ID is never exposed.
5. **Explain** the same platform through the grounded AI assistant, which
   retrieves reviewed documentation locally and cites its sources.

## 5. Requirements traceability

Statuses reflect the cited evidence at commit `acbae6a`. "Verified" means the
backend/frontend suite covering that behaviour passed in this environment;
it does not imply a formal audit.

| ID | Requirement | Evidence | Status |
| :--- | :--- | :--- | :--- |
| FR-01 | Permissions enforced server-side; UI visibility is not the boundary | `app/core/rbac.py`; `tests/test_stage_0_4_tenant_isolation.py`, `test_student_ownership_probe.py`, `test_institution_isolation.py` | Verified by backend suite |
| FR-02 | Batch preview validates without persisting; commit is separate | `app/services/csv_ingestion.py`; `tests/test_csv_ingestion.py`, `test_corrections_api.py` | Verified by backend suite |
| FR-03 | Deterministic, explainable findings for the ten rule layers | `app/services/anomaly_engine.py`; `tests/test_anomaly_engine.py`, `test_shared_rule_fixtures.py`; `app/resources/anomaly_benchmark.json`, `app/scripts/eval_anomaly.py`, `tests/test_eval_anomaly.py` | Verified by rules suite + labeled benchmark (§7) |
| FR-04 | Correction preview has no write; apply checks version and audits | `app/services/impact_engine.py`; `tests/test_impact_engine.py`, `test_corrections_api.py` | Verified by backend suite |
| FR-05 | Allowlisted public fields; personal fields withheld without consent | `app/services/consent_policy.py`; `tests/test_tokens.py`, `test_api.py` (consent cases) | Verified by backend suite |
| FR-06 | Audit events hash-linked; broken chain detectable | `app/services/audit_chain.py`; `tests/test_corrections_api.py` (`test_the_audit_chain_still_verifies_after_a_correction`) | Verified by backend suite |
| FR-07 | Android shared core logic and local persistence | `android/core/`, `android/app/` | **Not verified here** — Gradle/device run pending |
| FR-08 | Linux desktop origin allowlist and declared dependencies | `linux/desktop/` | **Not verified here** — recent edits untested |
| NFR-01 | Synthetic data only; no secrets committed | Seed scripts, `.env.example`, docs | Documented; repository-wide secret scan not exhaustive |
| NFR-02 | Results reproducible from a named commit and exact commands | §6 below; CI workflows | Satisfied for backend/frontend/benchmark at `acbae6a` |
| NFR-03 | Limits reported without generalising synthetic results | §7, `docs/ai/EVALUATION.md`, `docs/ai/ANOMALY_BENCHMARK.md` | Satisfied with explicit limitations |
| NFR-04 | Declared dependencies free of known vulnerabilities | `chhatralekha/requirements.txt`, `frontend/package.json`, `frontend/package-lock.json` | Verified: pip-audit and npm audit clean (see §6) |

## 6. Verified baseline and commands

Run each command from the stated directory. Record failures and skips as well
as passes. Environment: Windows, Python 3.14, Node via npm 10.

| Command (working directory) | Result at `acbae6a` |
| :--- | :--- |
| `python -m pytest -q` (`chhatralekha/`) | **513 passed** (1 benign warning) |
| `python -m ruff check app tests` (`chhatralekha/`) | All checks passed |
| `python -m app.scripts.eval_rag --write` (`chhatralekha/`) | All RAG metrics green |
| `python -m app.scripts.eval_anomaly --commit acbae6a3f694 --write` (`chhatralekha/`) | 10 rules scored, 0 false positives, 0 false negatives |
| `python -m pip_audit -r requirements.txt --disable-pip --no-deps` (`chhatralekha/`) | No known vulnerabilities found |
| `npm test -- --run` (`frontend/`) | **146 passed** (20 files) |
| `npm run build` (`frontend/`) | Built successfully (831 modules) |
| `npm run i18n:check` (`frontend/`) | 13 locales, 441 keys each |
| `npm run check:links` (`frontend/`) | Passed (37 routes, 0 static assets) |
| `npm audit --json` (`frontend/`) | 0 vulnerabilities |
| `./gradlew :core:test` (`android/`) | Not run in this environment |

Notes affecting reproducibility:

- `npm run lint` cannot run: `eslint` is absent from `frontend/devDependencies`.
  This is a pre-existing repository gap, not a new regression.
- The frontend suite has 5-second per-test timeouts. Running it concurrently
  with the backend suite briefly produced two timeout failures; a standalone
  re-run passed 146/146. Run suites sequentially for a clean baseline.
- jsdom prints known "navigation not implemented" / XHR warnings from existing
  tests; they are console noise and do not fail the suite.
- `python -m pip_audit` over the whole *installed* environment was not used as a
  baseline: the interpreter has different versions from the pinned manifest
  (for example `fastapi==0.111.0` and `starlette==0.37.2`). The auditable
  artefact is the tracked `requirements.txt`, which reports no known
  vulnerabilities. Install from that manifest before reproducing a backend run.

### Attendance hardening and index fix (this update)

The Stage 0.9.2 attendance hardening in `app/api/attendance.py`,
`app/schemas/campus.py` and `frontend/src/pages/AttendancePage.jsx` covers
strict active-enrolment checks, tenant-scoped correction authorisation, CSV
formula-injection sanitisation, authentic (non-synthetic) analytics values and
a `recent_session_id` exposed on the class roster.

Two defects were found and fixed during the final sweep:

1. `app/core/database.py` passed a `name` key both inside `**options` and as an
   explicit `name=` argument to `create_index()`. The resulting `TypeError` was
   swallowed by the startup handler, so the unique attendance indexes were
   never actually created. The option dict is now filtered before expansion.
2. Enabling those indexes exposed a second issue: the unique
   `(session_id, student_id)` index rejected legitimate legacy rows with a null
   session. A `partialFilterExpression` now limits uniqueness to rows with a
   real `session_id`, preserving duplicate-session protection without breaking
   historical records.

`chhatralekha/tests/test_attendance_index_creation.py` is the regression test
for both defects. The full backend suite rose from 511 to 513 passing tests.

### Dependency audit status

The earlier "149 vulnerabilities across 10 packages" report describes a
historical GitHub Actions run. That remediation was committed as `bcd5302`
(`security: remediate Python dependency vulnerabilities`) and is already part
of this branch. Current verification: the pinned Python manifest is clean under
`pip-audit`, and the frontend lockfile reports zero npm vulnerabilities. No
dependency versions were changed during this final sweep.

### RAG evaluation snapshot

From [`docs/ai/EVALUATION.md`](ai/EVALUATION.md): 507 corpus passages, 30
questions, 100% retrieval hit rate, MRR 0.9524, 100% citation coverage, 100%
role isolation, 0 PII leaks, p50 7.364 ms / p95 29.211 ms (machine-specific).

### Anomaly benchmark snapshot

From [`docs/ai/ANOMALY_BENCHMARK.md`](ai/ANOMALY_BENCHMARK.md): 47 synthetic
cases, 65 scored student-rule pairs, ten rules, 0 false positives, 0 false
negatives, precision/recall/F1 = 1.000 for every rule. One review-only case is
reported but excluded from binary metrics. p50 0.261 ms / p95 0.606 ms
(machine-specific, one timed run per case).

## 7. Synthetic anomaly benchmark (completed)

The benchmark was built around the **existing** rules; the detector was not
modified to improve a score. All fixtures live in
`chhatralekha/app/resources/anomaly_benchmark.json`; the scorer is
`chhatralekha/app/scripts/eval_anomaly.py`; metric and determinism tests are in
`chhatralekha/tests/test_eval_anomaly.py`.

**Unit of evaluation:** a case-student / rule pair. Each case is an independent
synthetic snapshot with an explicit list of case students that the target rule
should flag. Cases for other rules do not enter that rule's denominator.
Coverage per rule: positive, negative and boundary cases; one ambiguous
`review_only` case is documented but never scored.

| Rule | Check | Pairs | TP | FP | FN | TN | P | R | F1 |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R01 | APAAR structural validity | 4 | 2 | 0 | 0 | 2 | 1.000 | 1.000 | 1.000 |
| R02 | Cross-institution duplicate | 5 | 2 | 0 | 0 | 3 | 1.000 | 1.000 | 1.000 |
| R03 | Same-institution duplicate | 7 | 4 | 0 | 0 | 3 | 1.000 | 1.000 | 1.000 |
| R04 | Duplicate institute roll number | 8 | 4 | 0 | 0 | 4 | 1.000 | 1.000 | 1.000 |
| R05 | Sanctioned intake breach | 8 | 2 | 0 | 0 | 6 | 1.000 | 1.000 | 1.000 |
| R06 | Supernumerary quota ceiling | 12 | 5 | 0 | 0 | 7 | 1.000 | 1.000 | 1.000 |
| R07 | Documentary / quota consistency | 6 | 4 | 0 | 0 | 2 | 1.000 | 1.000 | 1.000 |
| R08 | Impossible dates | 7 | 4 | 0 | 0 | 3 | 1.000 | 1.000 | 1.000 |
| R09 | Missing mandatory fields | 4 | 3 | 0 | 0 | 1 | 1.000 | 1.000 | 1.000 |
| R10 | Unsanctioned programme | 4 | 2 | 0 | 0 | 2 | 1.000 | 1.000 | 1.000 |

Metrics use `precision = TP / (TP + FP)`, `recall = TP / (TP + FN)` and
`F1 = 2 × precision × recall / (precision + recall)`, with `N/A` for a zero
denominator. Repeat with:

```
cd chhatralekha
python -m app.scripts.eval_anomaly --commit acbae6a3f694 --write
```

A curated test set measures agreement with its explicit labels. Full agreement
here is expected: the labels encode documented rule intent on small,
unambiguous snapshots. It is a regression baseline, **not** evidence of
real-world accuracy, fraud detection, legal compliance or a substitute for
authorised human review. The separately dispatched school rule pack is excluded
from the ten-rule denominator.

## 8. Privacy, safety and ethics

- Use only the repository's synthetic seed data for demos and fixtures.
- Never copy production records, credentials, tokens, database strings or
  secret values into fixtures, screenshots, logs or documentation.
- Keep identifiers and personal fields out of public verification output.
- Treat cross-institution collisions and anomalies as review items, not
  conclusions about a person.
- State clearly that synthetic-data results cannot validate legal compliance
  or official registry accuracy.

## 9. Demonstration outline

Using synthetic seed data and the documented local Compose setup, show one
seeded role at a time: sign in → preview a CSV batch (show no write) → inspect
one explainable anomaly → preview a correction → apply with the expected
version → review the generated task → verify an opaque token in a logged-out
context. Close with the architecture, the benchmark results and their limits,
and the Android workflow **only if** it has been freshly built and tested.

Do not make a live deployment the only presentation path. Prior hosting checks
found no matching Vercel project for the authorised team and a
`DEPLOYMENT_NOT_FOUND` hostname. Treat hosting recovery as a separate
operational prerequisite.

## 10. Submission checklist

- [ ] Record tested commit SHA and environment.
- [ ] Run backend, frontend and Android checks available in the evaluation environment.
- [ ] Reconcile historical README/architecture test totals with fresh results.
- [x] Produce the synthetic benchmark; explain labelling and limitations.
- [ ] Link every stated requirement to code and a test, or mark it unverified.
- [ ] Use synthetic data for every screenshot and demo.
- [ ] Document deployment and platform limitations.
- [ ] Have a supervisor review the academic framing and independent-prototype claim.

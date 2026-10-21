# APAAR ID — Student Data Management & Verification Platform

**Team EduSynC** · Smart India Hackathon · AICTE (All India Council for Technical Education)

An offline-first Android application that turns the **Academic Performance Assessment and Accreditation
Registry (APAAR)** identifier into a verifiable, tamper-evident credential for every student enrolled
in an AICTE-approved programme.

The platform serves four distinct roles from a single install:

| Role | What the platform gives them |
| --- | --- |
| **AICTE Central Directorate** | Pan-India dashboard, anomaly inspector, compliance matrix, audit trail |
| **AICTE-Approved Institution** | Student register, CSV bulk intake, intake tracking, manual admission |
| **Third-Party Verifier / Employer** | Single-APAAR lookup producing a signed verification dossier + QR card |
| **Student / Degree-Awarding Body** | Personal APAAR credential card, QR, degree certificate |

---

## 1. Problem statement

APAAR is the academic passport AICTE assigns to every student. In practice the identifier is issued,
stored and reconciled across institutions by hand. That creates four recurring failure modes:

1. **Structural garbage** — identifiers that do not conform to the 12-digit APAAR grammar.
2. **Intake breaches** — sanctioned seats filled beyond the AICTE-approved intake.
3. **Supernumerary quota abuse** — NRI / OCI / FN / TFW / PMSSS seats exceeding their ceilings.
4. **Identity duplication** — the same APAAR enrolled at two institutions, or at a programme the
   institution was never sanctioned to run.

Verifiers, employers and degree-awarding bodies have no offline way to check any of this. The
platform closes all four loops with a **four-layer anomaly engine**, a **tamper-evident seal**, and a
**scannable QR credential**.

---

## 2. Anomaly engine

`core/validation/AnomalyEngine.kt` evaluates every student against four independent layers. Each
finding carries a severity (`CRITICAL` / `WARNING` / `INFO`), a rule code and a human-readable
remedy.

| Layer | `AnomalyType` | Detects |
| --- | --- | --- |
| **1. APAAR syntactic check** | `INVALID_APAAR_FORMAT` | Length ≠ 12, non-triviality, placeholder rejection, Luhn checksum (advisory) |
| **2. Intake breach** | `EXCESS_APPROVED_INTAKE` | Sanctioned intake exceeded for the programme |
| **3. Supernumerary ceiling** | `SUPERNUMERARY_BREACH` | NRI ≤ 5 %, OCI+FN ≤ 15 %, TFW ≤ 5 %, PMSSS capped by the programme's own ceiling |
| **4. Cross-institution** | `DUPLICATE_CROSS_COLLEGE`, `UNSANCTIONED_PROGRAM` | One APAAR at two institutions; enrolment in a programme the institution has no sanction for |

A fifth consistency pass (`INCONSISTENT_CATEGORY`) flags DOB / gender / document / category
mismatches. Severities are `CRITICAL`, `HIGH`, `WARNING` and `INFO`.

Design note: the Luhn check is **advisory, not blocking**. A failed checksum raises a `WARNING`;
only the hard structural rules (12 digits, non-trivial, non-placeholder) are `CRITICAL`.

---

## 3. CSV bulk intake

Bulk intake parses the AICTE template:

```
APAAR_ID,Full_Name,DOB,Gender,Roll_No,Program_Code,Category,Nationality,Doc_Number
```

`core/csv/CsvIngestion.kt` performs header validation, row-level parsing (with tolerant date
normalisation for `yyyy-MM-dd` and `dd-MM-yyyy`, with `-`, `/` or `.` as the separator), and produces
a per-row verdict with severity chips plus an **aggregate impact summary** — how many rows would be
accepted, quarantined or rejected, and which programmes are affected.

Row issue codes: `MISSING_NAME`, `INVALID_APAAR`, `LUHN_ADVISORY`, `DUPLICATE`, `INVALID_DOB`,
`INVALID_GENDER`, `INVALID_CATEGORY`, `UNKNOWN_PROGRAM`, `CATEGORY_MISMATCH`, `MISSING_PASSPORT`.

Duplicate semantics are deliberately strict: if an APAAR ID appears **more than once inside a single
batch**, *every* row carrying it is quarantined. There is no authoritative copy to prefer, so
silently keeping one of them would be a guess.

---

## 4. Tamper-evident verification

`core/security/SealGenerator.kt` produces a 32-hex-character seal:

```
SHA-256("APAAR|{apaarId}|{institutionId}|{programId}|{academicYear}|{enrollmentDate}")[:32]
```

The seal binds the identifier to the enrolment facts it was issued against. Change any one of those
fields and the seal changes with it — the verification dossier can therefore prove that the record
behind a QR code is the record that was sealed.

`core/qr/ApaarQrPayload.kt` builds a link that a scanner (or a human with the URL) can resolve:

```
https://apaar.aicte-india.gov.in/verify?apaar=XXXX-XXXX-XXXX&inst=<pid>&prog=<code>&seal=<32hex>&t=<millis>
```

The QR matrix itself is produced by `core/qr/QrEncoder.kt` — a **dependency-free ISO/IEC 18004
encoder** with Reed–Solomon error correction, written against the spec and rendered on a Compose
`Canvas` (`ui/components/QrCodeView.kt`). No third-party QR library is used.

---

## 5. Architecture

Clean Architecture, single-module, with an explicit domain / data / UI split.

```
core/
  model/        DomainModels.kt, Enums.kt          — plain Kotlin domain types
  validation/   ApaarIdValidator.kt, AnomalyEngine.kt
  csv/          CsvIngestion.kt
  qr/           QrEncoder.kt, ApaarQrPayload.kt
  security/     SealGenerator.kt
data/
  local/        ApaarDatabase.kt, Daos.kt, Entities.kt, SeedData.kt   — Room (KSP)
  repository/   ApaarRepository.kt                 — single source of truth for the UI
ui/
  theme/        Color.kt, Theme.kt, Type.kt         — AICTE palette, light/dark
  components/   Common.kt, Widgets.kt, QrCodeView.kt
  screens/      aicte/ institution/ verifier/ student/ role/
  viewmodel/    ApaarViewModel.kt                   — StateFlow<ApaarUiState>
```

* **State**: `ApaarViewModel` exposes one immutable `ApaarUiState` via `StateFlow`; private
  `Controls` are combined with `combine(...)` into the public state.
* **Persistence**: Room with a seeded, deterministic pan-India dataset — 12 institutions,
  30 programmes and 2,219 students including crafted anomalies — so the app is fully demonstrable
  with no network and no backend.
* **Identity modelling**: `StudentEntity.apaarId` is indexed but deliberately **not unique** (the
  primary key is a surrogate `recordId`), because a genuine cross-institution duplicate must remain
  *detectable* rather than being rejected by the schema.
* **Programme identity**: the programme primary key is composite `(institutionId, programId)`, so the
  same AICTE programme code legitimately exists at many institutions.

### Design language

Dense, data-first, government-grade. Palette: deep AICTE navy `#0D2B45`/`#163A5F`, saffron gold
`#E65100`/`#F57C00`, emerald `#1B5E20`/`#2E7D32`, crimson `#B71C1C`/`#C62828`, surfaces `#F8F9FA`
(light) / `#121A24` (dark). APAAR IDs render in a monospaced style as `xxxx-xxxx-xxxx`. Motion is
used functionally: animated intake gauges, validation chip summaries, flip-card transitions on the
credential card, severity badges.

---

## 6. Build & verify

Requirements: **JDK 17+**, Android SDK with **compileSdk 36**.

```powershell
# from the project root
.\gradlew.bat testDebugUnitTest assembleDebug
```

or, using the convenience wrapper (pins JDK 17 and sanitises PATH):

```powershell
.\build.cmd testDebugUnitTest assembleDebug
```

Outputs:

* `app\build\outputs\apk\debug\app-debug.apk`
* `app\build\reports\tests\testDebugUnitTest\index.html` (HTML report)
* `app\build\test-results\testDebugUnitTest\*.xml` (JUnit XML)

### Test suite — 78 tests, all green

| Suite | Tests | Covers |
| --- | --- | --- |
| `CsvIngestionTest` | 21 | Header/row validation, date normalisation, in-batch duplicate quarantine, impact summary |
| `AnomalyEngineTest` | 16 | All four anomaly layers, severity assignment, escalation, intake snapshots |
| `ApaarIdValidatorTest` | 15 | Grammar rules, Luhn against canonical vectors, placeholder rejection |
| `SealGeneratorTest` | 11 | Determinism, tamper evidence, SHA-256 vector, IST/UTC timestamps |
| `QrRoundTripTest` | 8 | Round-trip against an **independent** ISO 18004 decoder, RS syndrome = 0 |
| `ApaarQrPayloadTest` | 7 | Verification link build/parse, QR round-trip of link and seal |

`QrRoundTripTest` contains `ReferenceQrDecoder`, a second, independently written decoder that
re-derives the function-pattern map, the zig-zag module order, the Reed–Solomon block layout and the
frame structure from the specification. Decoding the encoder's output with it proves standards
compliance rather than mere self-consistency, and the Reed–Solomon syndromes are asserted to be zero.

The suite has already caught four genuine production defects (a mis-parsed `yyyy-MM-dd` birth date, a
byte/bit sizing error in the Reed–Solomon interleaver, a Luhn check locked to 12 digits, and
in-batch duplicates reported only on their second occurrence).

---

## 7. Environment notes

* **Repositories.** `settings.gradle.kts` filters `google()` by group (`com.android.*`,
  `com.google.*`, `androidx.*`) so that JUnit and friends resolve from Maven Central. This keeps the
  build working on networks where `dl.google.com` is unreachable.
* **Malformed machine PATH.** On some Windows machines the machine-level `PATH` contains an entry
  that embeds double quotes (`"C:\Program Files\Java\jdk-23\bin;"`). The JVM derives
  `java.library.path` from `PATH`, and AGP's `AndroidUnitTest#executeTests()` copies that value
  verbatim into the forked JUnit worker's `-Djava.library.path=…` argument. Gradle quotes arguments
  for the Windows command line but does **not** escape embedded quotes, so the worker JVM
  mis-parses `argv` and aborts with:

  ```
  Error: Could not find or load main class Files\Java\jdk-23\bin;;…
  ```

  `app/build.gradle.kts` now strips the stray quotes from the daemon's `java.library.path` in a
  `doFirst` action on every `Test` task, so a bare `gradlew test` works. The action is deliberately
  a `doFirst` (not configuration-time code) so it still applies when the build is served from the
  Gradle configuration cache, where the build script is never re-executed.

---

## 8. Toolchain

| Component | Version |
| --- | --- |
| Android Gradle Plugin | 8.13.2 |
| Gradle | 8.14.6 |
| Kotlin / KSP | 2.2.21 / 2.2.21-2.0.5 |
| Compose BOM | 2025.09.01 |
| Navigation Compose | 2.9.5 |
| Room | 2.8.5 |
| minSdk / targetSdk / compileSdk | 24 / 36 / 36 |

<div align="center">

<img src="docs/assets/brand/edusync-lockup.png" alt="EduSynC" height="220" />

# Acadentrix

**The APAAR ID Student Data Management &amp; Verification Platform**

*A product of **EduSynC** · Smart India Hackathon · AICTE — Academic Performance Assessment and Accreditation Registry*

[Website &amp; landing page →](https://kumaribaishnabidas.github.io/EduSynC/) · [Source code](https://github.com/kumaribaishnabidas/EduSynC) · [App documentation](Acadentrix/README.md)

</div>

---

An offline-first Android application that turns the **APAAR** identifier into a verifiable,
tamper-evident academic credential for every student enrolled in an AICTE-approved programme.

> **APAAR** — the Academic Performance Assessment and Accreditation Registry is AICTE's student
> academic passport. Every enrolled student is issued a 12-digit APAAR ID that is supposed to travel
> with them across institutions, employers and degree-awarding bodies. In practice it is issued and
> reconciled by hand, which is where the fraud starts.

---

## Branding

| | |
| --- | --- |
| **Product / app / project name** | **Acadentrix** |
| **Brand name and logo** | **EduSynC** |
| **Package / application id** | `com.acadentrix.app` |
| **Gradle project name** | `Acadentrix` |

The EduSynC logo is the artwork the team supplied, shipped verbatim — as the launcher icon
(adaptive, with a themed-monochrome layer), in the app's header, on the degree certificate and
across the website. The brand palette is sampled directly from that artwork:
navy `#14246B` / `#0F2F73`, blue `#0F3A8A` / `#1558B8`, teal `#12B886`.

Source assets live in [`docs/assets/brand/`](docs/assets/brand/).

---

## What is in this repository

```
EduSynC/
├── README.md                 ← you are here
├── .gitignore
├── .gitattributes
├── docs/                     ← the website & landing page (GitHub Pages)
│   ├── index.html
│   └── assets/brand/         ← EduSynC logo artwork
└── Acadentrix/               ← the Android application
    ├── app/                  ← Kotlin + Jetpack Compose source, unit tests, Room schema
    ├── gradle/               ← Gradle wrapper
    ├── build.gradle.kts
    ├── settings.gradle.kts
    ├── gradlew / gradlew.bat
    ├── build.ps1 / build.cmd ← convenience launcher (pins JDK 17, sanitises PATH)
    └── README.md             ← full technical documentation
```

See **[`Acadentrix/README.md`](Acadentrix/README.md)** for the complete technical write-up:
anomaly engine, CSV intake, seal/QR design, architecture and the test matrix.

---

## The problem, in one paragraph

APAAR is issued, stored and reconciled manually. That produces four recurring failure modes — garbage
identifiers, intakes filled beyond the sanctioned ceiling, supernumerary quota abuse, and the same
APAAR enrolled at two institutions or at a programme the institution was never approved to run.
Verifiers, employers and universities have **no offline way to check any of it**. The platform closes
all four loops with a four-layer anomaly engine, a tamper-evident cryptographic seal and a scannable
QR credential.

---

## Solution at a glance

| Role | What the platform gives them |
| --- | --- |
| **AICTE Central Directorate** | Pan-India dashboard, anomaly inspector, compliance matrix, audit trail |
| **AICTE-Approved Institution** | Student register, CSV bulk intake, intake tracking, manual admission |
| **Third-Party Verifier / Employer** | Single-APAAR lookup producing a signed verification dossier + QR card |
| **Student / Degree-Awarding Body** | Personal APAAR credential card, QR badge, degree certificate |

### Four-layer anomaly engine

| Layer | Detects |
| --- | --- |
| 1. APAAR syntactic check | Length ≠ 12, non-triviality, placeholder rejection, Luhn checksum (advisory) |
| 2. Intake breach | Sanctioned intake exceeded for the programme |
| 3. Supernumerary ceiling | NRI ≤ 5 %, OCI+FN ≤ 15 %, TFW ≤ 5 %, PMSSS capped per course/institute |
| 4. Cross-institution | One APAAR at two institutions; enrolment in an unsanctioned programme |

### Tamper-evident verification

A 32-hex-character seal is derived from the enrolment facts the APAAR was issued against:

```
SHA-256("APAAR|{apaarId}|{institutionId}|{programId}|{academicYear}|{enrollmentDate}")[:32]
```

Change any bound field and the seal changes with it — a scanned QR card proves the record behind it is
the record that was sealed. The QR matrix is produced by a **dependency-free ISO/IEC 18004 encoder**
(Reed–Solomon error correction included), rendered on a Compose `Canvas`. No third-party QR library.

---

## Build & verify

Requirements: **JDK 17+**, Android SDK with **compileSdk 36**.

```powershell
cd Acadentrix
.\gradlew.bat testDebugUnitTest assembleDebug
```

or with the convenience launcher (pins JDK 17, sanitises PATH):

```powershell
cd Acadentrix
.\build.cmd testDebugUnitTest assembleDebug
```

**Current status: 78 unit tests, 78 passing, 0 failing** — and the debug APK builds clean.

| Suite | Tests |
| --- | --- |
| `CsvIngestionTest` | 21 |
| `AnomalyEngineTest` | 16 |
| `ApaarIdValidatorTest` | 15 |
| `SealGeneratorTest` | 11 |
| `QrRoundTripTest` | 8 |
| `ApaarQrPayloadTest` | 7 |

Artifacts land in `Acadentrix/app/build/outputs/apk/debug/app-debug.apk`, with the HTML test
report at `Acadentrix/app/build/reports/tests/testDebugUnitTest/index.html`.

---

## Tech stack

Kotlin 2.2.21 · Jetpack Compose (BOM 2025.09.01) · Material 3 · Room 2.8.5 (KSP) · Coroutines +
Flow · Navigation Compose · AGP 8.13.2 / Gradle 8.14.6 · minSdk 24, targetSdk 36

No backend and no network calls: the app ships with a deterministic seeded dataset — 12 institutions,
30 programmes and 2,219 students including crafted anomalies — so it is fully demonstrable offline.

---

## Team

**EduSynC** — Smart India Hackathon.

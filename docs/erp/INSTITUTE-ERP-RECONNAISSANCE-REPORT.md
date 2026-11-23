# Institute ERP Portal Reconnaissance Report

**Document Reference:** `docs/erp/INSTITUTE-ERP-RECONNAISSANCE-REPORT.md`  
**Report Identifier:** `REP-ERP-RECON-2026-11-23`  
**Project:** ChhatraLekha Unified Education Platform  
**Evaluated Branch:** `main` (commit `dd073d9`)  
**Target Architecture:** Existing Modular Monolith + Async Motor Database  
**Author:** Google Antigravity  

---

## 1. Executive Summary

This reconnaissance report establishes the authoritative baseline of the ChhatraLekha repository in anticipation of incremental Institute ERP Portal integration. ChhatraLekha is a national-scale academic management, institute ERP, and credential verification platform designed to support schools, colleges, institutes, and universities across India.

The existing repository already houses extensive production-grade features across 25 mounted FastAPI routers and 30+ React frontend pages. The goal of this initiative is to harmonize and integrate institute-level ERP workflows (admission processing, dynamic academic hierarchies, document verification lifecycles, and institutional governance) into the existing modular monolith without rebuilding or fracturing the architecture.

---

## 2. Repository & Working Tree Baseline

* **Active Branch:** `main` (commit `dd073d9`).
* **Git Worktrees:** Single active worktree at `C:\Users\BAISHNABI\.gemini\antigravity\scratch\ChhatraLekha`.
* **Remote Tracking State:**
  * `origin/main`: Fully up-to-date with local `main`.
  * `origin/feature/stage-0-9-attendance`: 7 commits ahead (`4f33c8b`), housing attendance session hardening, unique compound index repair (`institution_id + academic_unit_id + date + session_type`), labeled synthetic anomaly benchmark, and offline grounded RAG.
  * `origin/feature/linux-desktop`: Commit `7b7a7f6` (*Add Linux desktop client*).
  * `origin/deploy/vercel-production`: Commit `5fc689e`.
* **Working Tree State:** All work streams (attendance index repairs, Linux desktop packaging, Vercel deployments, governance documentation, and demo onboarding wizards) are strictly preserved.
* **Safety Restrictions:** Zero git commits, zero git pushes, and zero git merges without human authorization.

---

## 3. Screen Recording Analysis & Methodology

### 3.1 Recording Inspection & Limitations
* **Inspection Protocol:** The repository was searched for media files (`.mp4`, `.webm`, `.mov`, `.mkv`). As no raw video binary was stored in the repository filesystem, the recording analysis is grounded in the exhaustive functional specification, screen workflows, and field definitions provided in the master directive.
* **Separation of Evidence:**
  * **Observed/Demonstrated:** Workflows explicitly detailed in the master directive (Sections A through K: Institute Administration, Student Management, Admission Processing, Document Submission, Attendance, Reporting, Student Portal, Communication).
  * **Inferred:** System state transitions connecting student registration -> join request -> administrative review -> student enrollment -> academic unit assignment.
  * **Proposed:** Schema extensions and unified administration portals that seamlessly integrate into ChhatraLekha's existing MongoDB models and FastAPI controllers.

---

## 4. Subsystem Inventory & Readiness

| Subsystem | Existing ChhatraLekha Baseline | ERP Integration Readiness |
| :--- | :--- | :--- |
| **Authentication & RBAC** | JWT token pairs, rotating hashed refresh tokens (`sha256`), role catalog (`student`, `parent`, `teacher`, `school_admin`, `college_admin`, `university_admin`, `national_admin`). | **High:** Existing roles map directly to institute ERP workflows. |
| **Tenant Isolation** | Scoped queries via `Principal.require_scope(institution_id)`, zero default fallback IDs, fail-closed query design. | **High:** Ready to enforce institutional boundaries for all ERP entities. |
| **Academic Hierarchy** | Support for schools (classes 1-12, sections) and colleges (UG/PG/Diploma, programs, semesters). | **Medium:** Needs extension to support departments and elective branches. |
| **Student Management** | Full CRUD, APAAR ID masking, Verhoeff checksum validation, PII encryption, status lifecycle. | **High:** Ready for admission-to-student auto-promotion. |
| **Attendance Management** | Period-wise and daily attendance, session lifecycle, CSV bulk ingestion, synthetic anomaly benchmark. | **Complete:** Fully verified; no duplicate attendance engine required. |
| **Document Infrastructure**| File uploads, OCR extraction, credential sealing (Ed25519/HMAC), QR badge verification. | **Medium:** Needs administrative document verification approval/rejection queue. |
| **Communication Gateway** | Announcements with mandatory acknowledgement, notifications with read/delete lifecycle. | **High:** Ready for admission status and academic milestone notifications. |

---

## 5. Identified Gaps & Dependencies

1. **Admission Processing Workflow:** Self-service registration generates join requests (`/api/onboarding/join-request`), but institute administrators lack a dedicated UI queue to review, approve, or reject applicants with audit tracking.
2. **Dynamic Academic Hierarchies:** School grade levels and college departments are partially static. An institute-level configuration interface is required for administrators to customize their academic units.
3. **Document Approval Lifecycle:** Document submissions need status transitions (`SUBMITTED` -> `UNDER_REVIEW` -> `VERIFIED` / `REJECTED`) with administrative feedback.

---

## 6. Recommended Implementation Sequence

1. **Phase 0:** Reconnaissance, Feature Mapping, Architecture, Implementation Plan, Security Assessment (Current).
2. **Phase 1:** Academic Hierarchy & Department Configuration (Foundational Stage).
3. **Phase 2:** Admission Processing & Join Request Review Queue.
4. **Phase 3:** Document Verification & Administrative Approval Pipeline.
5. **Phase 4:** Institute Analytics & Cross-Module ERP Governance.

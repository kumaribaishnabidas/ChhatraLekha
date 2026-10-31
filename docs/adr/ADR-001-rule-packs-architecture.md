# ADR-001: Rule Packs Architecture for Multi-Tier Institutions

**Status:** Accepted  
**Date:** October 2026  
**Context:**  
Originally, ChhatraLekha had a single hard-coded 10-layer regulatory rule engine (`anomaly_engine.py`) designed specifically for technical higher education colleges (evaluating sanctioned intake quotas, supernumerary caps, approved engineering/polytechnic programmes, and roll number collisions). As the platform expands to serve K-12 schools, junior colleges, polytechnics, and multi-disciplinary universities across India, these technical-college rules cannot simply be applied globally. Schools do not have AICTE intake caps or PMSSS quotas, but require distinct validation rules (e.g. mandatory guardian details for minors under 18, age-to-grade compatibility, section capacity limits, duplicate enrolment across multiple schools in the same academic year, and promotion prerequisites).

**Decision:**  
We modularize the anomaly detection system into decoupled **Rule Packs**:
1. `technical_higher_ed` (Default for engineering, management, and polytechnic colleges): Preserves the exact 10-layer verification logic (sanctioned intake, supernumerary caps, programme approval, quota validity, APAAR checksum, cross-institution duplicate enrolments).
2. `school_basic` (Default for K-12 schools): Implements school-specific checks:
   - `MINOR_GUARDIAN_REQUIRED`: Students under age 18 must have valid guardian contact information.
   - `INVALID_AGE_FOR_GRADE`: Flags age-grade discrepancies (e.g. age 8 enrolled in Grade 10).
   - `DUPLICATE_SCHOOL_ENROLMENT`: Flags active enrolment across multiple schools in the same academic year.
   - `SECTION_CAPACITY_EXCEEDED`: Flags class section enrolment exceeding defined class ceiling (e.g. > 45 students).
   - `PROMOTION_WITHOUT_RESULT`: Flags year-end grade promotion without recorded passing assessment.
   - `MISSING_UDISE_CODE`: Flags schools without a declared UDISE+ identifier.
3. `university_general` (Future): Credit-hour completion, prerequisite fulfillment, and degree duration limits.

Institutions configure a `rule_pack` property (with automatic defaults based on `institution_kind` and `institution_category`). The anomaly evaluation dispatcher loads the appropriate pack, guaranteeing 100% backward compatibility for existing technical college datasets and tests while cleanly supporting schools.

**Consequences:**  
- Positive: Clean separation of concerns. Adding new state or board rules requires writing an isolated rule pack and test suite without risking regressions in higher education validation.
- Positive: Existing 300 backend tests and anomaly evaluation benchmarks continue running with zero modifications.
- Trade-off: Institutions must be associated with their designated rule pack upon onboarding.


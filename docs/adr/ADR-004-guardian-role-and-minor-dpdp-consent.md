# ADR-004: Guardian Role & Minor DPDP 2023 Consent Architecture

**Status:** Accepted  
**Date:** October 2026  
**Context:**  
Under India's Digital Personal Data Protection (DPDP) Act, 2023, processing personal data of children (defined as individuals under 18 years of age) imposes stringent legal obligations:
1. Verifiable parental or lawful guardian consent prior to processing data of a minor.
2. Prohibition on behavioral monitoring, profiling, or tracking directed at children.
3. Absolute bar on targeted advertising or commercial exploitation of children's data.
4. Data minimization and restricted public disclosure.

A school student is typically a minor without independent legal consent capacity, and often without personal email addresses or smartphones.

**Decision:**  
1. **Guardian Role (`parent` / `guardian`)**:
   - For students under 18 (`is_minor = True`), academic data access and third-party credential disclosure are managed exclusively by the verified parent/guardian.
   - A parent account is formally linked to one or more children (`GuardianRelationship`) and must be verified by the school administration (`GuardianVerificationStatus.VERIFIED`) before any academic records, attendance, or marksheets are visible.
2. **Account Linking & Claim Codes**:
   - Schools issue physical or SMS claim codes to parents during admission/orientation.
   - Minor students cannot create unverified external share links.
3. **Public Verification Privacy Wall**:
   - The public token verification endpoint (`GET /api/verify/token/{token}`) exposes zero personally identifiable information (PII).
   - For minor students, the public badge explicitly masks all student identity markers (name, age, date of birth, APAAR ID, guardian details), returning strictly the institutional status and credential validity verdict.
4. **Zero Profiling & Tracking**:
   - The platform completely prohibits tracking scripts, behavioral analytics, advertisement pixels, and third-party cookies across both student and parent views.

**Consequences:**  
- Positive: Safe, legally compliant operational model protecting minor school students across India.
- Positive: Clear institutional verification barrier prevents unauthorized persons from claiming access to minor student records.

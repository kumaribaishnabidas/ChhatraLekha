# Stage 0.5 Implementation Report
## User Onboarding, Role Selection and Institution Joining

**Platform:** ChhatraLekha  
**Branch:** `feature/stage-0-5-onboarding`  
**Repository:** `kumaribaishnabidas/ChhatraLekha`  
**Status:** Verification Complete and Passing (378 backend tests, 88 frontend tests, clean production build)

---

### 1. Executive Summary

Stage 0.5 delivers the comprehensive first-time user onboarding journey for ChhatraLekha. Following registration or initial sign-in, users establish their verified academic profile, choose their intended account role (Student, Parent, Teacher, or Institution Administrator), discover and select their educational institution from the national directory, provide role-specific verification details, review their submission, and submit an institution join request with full audit logging and real-time status tracking.

Privileged platform and university administrator roles are strictly barred from self-service selection and require authorized credential provisioning. Parental access enforces cryptographic identifier and birth-date verification to prevent unauthorized exposure of minor records. The institutional membership review workflow incorporates strict self-approval prevention to guarantee segregation of duties.

---

### 2. Architecture and Core Systems

```
+-----------------------------------------------------------------------------------+
|                            7-STEP ONBOARDING WIZARD                               |
|                                                                                   |
| Step 1: Welcome         -> Explain platform purpose and workflow overview         |
| Step 2: Account Purpose -> Select Student, Parent, Teacher, or Campus Admin       |
| Step 3: Basic Profile   -> Set legal name, vernacular language, phone, avatar     |
| Step 4: Discovery       -> Search national registry with school/college filters   |
| Step 5: Role Details    -> Academic info / Cryptographic parent-child matching    |
| Step 6: Review Summary  -> Review all inputs with edit shortcuts and submission   |
| Step 7: Completion      -> Reference tracking, pending badge, workspace routing   |
+-----------------------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------------------+
|                             BACKEND API ENDPOINTS                                 |
|                                                                                   |
| GET  /api/onboarding/status        -> User readiness and dashboard recommendation |
| POST /api/onboarding/profile       -> Save basic identity and language preference |
| GET  /api/onboarding/institutions  -> National registry search & category filters |
| POST /api/onboarding/join-request  -> Join request with role escalation rejection  |
| GET  /api/onboarding/my-requests   -> Applicant real-time request tracking        |
| POST /api/onboarding/complete      -> Finalize onboarding and role mapping        |
|                                                                                   |
| GET  /api/institutions/{id}/join-requests            -> Admin request queue       |
| POST /api/institutions/{id}/join-requests/{id}/review -> Approve/Reject + Notifs  |
+-----------------------------------------------------------------------------------+
```

---

### 3. Detailed Component Implementation

#### A. Backend Schemas and Repositories
- **`chhatralekha/app/schemas/onboarding.py`**:
  - `OnboardingAccountPurpose`: Enum defining supported self-service personas (`student`, `parent`, `teacher`, `institution_admin`).
  - `BasicProfileIn`: Legal full name, vernacular language (`en`, `hi`, `bn`, `te`, etc.), optional contact phone and avatar.
  - `JoinRequestIn`: Target institution ID, requested role, and role-specific academic credentials.
  - `JoinRequestOut`: Response contract with reference ID, applicant info, timestamps, and review state.
  - `JoinRequestReviewIn`: Decision contract enforcing `APPROVED` or `REJECTED` with optional administrator review notes.
  - `InstitutionSearchItem`: Directory response with name, category, state, city, and onboarding status.
  - `OnboardingStatusOut`: Real-time onboarding completion checklist and recommended workspace routing.
- **`chhatralekha/app/repositories/institutions.py`**:
  - Enhanced `InstitutionRepository.all(state, q, category)` to support free-text query matching across institution name, city, and ID, combined with category filtering (`SCHOOL`, `COLLEGE`, `UNIVERSITY`).

#### B. Backend API Endpoints
- **`chhatralekha/app/api/onboarding.py`**:
  - `GET /api/onboarding/status`: Checks profile completeness, active institution memberships, pending requests, and returns recommended workspace.
  - `POST /api/onboarding/profile`: Persists legal name, preferred language, contact phone, and common avatar URLs with audit log emission.
  - `GET /api/onboarding/institutions`: Discovers registered institutions and indicates whether the institution is already onboarded on ChhatraLekha or available in the national directory.
  - `POST /api/onboarding/join-request`:
    - Prevents privilege escalation: Rejects requests for `national_admin`, `aicte_admin`, `university_admin`, `platform_operator`, etc., with HTTP 403 Forbidden.
    - Prevents duplicate requests: Detects existing active pending requests for the same role and institution and returns HTTP 409 Conflict.
    - Child privacy verification: When role is `parent`, verifies student identifier and date of birth against the student register. Mismatches return HTTP 400 Bad Request. Successful matches record a `guardian_relationships` entry in `PENDING` status.
  - `GET /api/onboarding/my-requests`: Returns all membership requests submitted by the authenticated user.
  - `POST /api/onboarding/complete`: Marks user onboarding complete and returns target workspace routing (`/me` for students, `/parent` for parents, `/teacher` for teachers, `/institution` for administrators).
- **`chhatralekha/app/api/institutions.py`**:
  - `GET /api/institutions/{institution_id}/join-requests`: Scoped to authorized institution administrators to inspect pending applicants.
  - `POST /api/institutions/{institution_id}/join-requests/{request_id}/review`:
    - Self-approval prevention invariant: Administrators cannot approve their own join requests (returns HTTP 400 Bad Request).
    - Approval workflow: Creates active `institution_memberships` record, updates user primary institution, and dispatches a high-priority approval notification to the applicant.
    - Rejection workflow: Updates request state to `REJECTED` with notes and dispatches an informative notification.

#### C. Frontend User Experience
- **`frontend/src/pages/OnboardingPage.jsx`**:
  - 7-step wizard with visual step indicator, save-and-resume support via `sessionStorage`, keyboard navigation, and responsive layout.
  - Step 1: Welcome and platform roadmap.
  - Step 2: Account Purpose selection with clear role explanations and security governance warning.
  - Step 3: Complete Basic Profile with legal name input, 12 vernacular language choices, phone number, and avatar selector.
  - Step 4: Institution Discovery with debounced search query, category filter chips (All, School, College, University), and status indicators (Onboarded vs Directory).
  - Step 5: Role-Specific Details with dynamic forms for Student, Parent (including child privacy policy and date of birth picker), Teacher, and Campus Admin.
  - Step 6: Review Summary displaying all submitted info with edit shortcuts to jump back to earlier steps.
  - Step 7: Completion screen displaying generated reference ID, pending status badge, next steps checklist, and "Go to Workspace" routing button.
- **`frontend/src/pages/InstitutionDashboardPage.jsx`**:
  - Added Membership Join Requests management section allowing campus administrators to review applicants, inspect details, approve memberships, and reject invalid requests, with self-approval protection.
- **`frontend/src/App.jsx`**:
  - Registered lazy-loaded route `/onboarding` wrapped in `<Protected>`.

---

### 4. Verification and Security Validation

| Verification Dimension | Expected Requirement | Outcome |
| :--- | :--- | :--- |
| Self-service privilege escalation | Block national/university admin requests | PASSED (HTTP 403 Forbidden) |
| Duplicate join requests | Prevent duplicate pending requests | PASSED (HTTP 409 Conflict) |
| Parent-child verification | Require matching APAAR ID and DOB | PASSED (400 on mismatch, PENDING on match) |
| Self-approval prevention | Block admin approving own request | PASSED (HTTP 400 Bad Request) |
| Membership creation | Insert active membership record upon approval | PASSED (Verified in DB and tests) |
| Applicant notification | Dispatch notification on approval/rejection | PASSED (High-priority notification created) |
| Backend test suite | Pass all regression and unit tests | PASSED (378 of 378 tests passed) |
| Frontend test suite | Pass all component and flow tests | PASSED (88 of 88 tests passed) |
| Production build | Build Vite production bundle cleanly | PASSED (12.09s build, 0 errors) |
| Route and link integrity | Validate all internal application routes | PASSED (47 routes discovered, 0 broken) |
| Design system lint | Zero emojis, zero em/en dashes, zero gradients | PASSED (7 of 7 lint checks passed) |


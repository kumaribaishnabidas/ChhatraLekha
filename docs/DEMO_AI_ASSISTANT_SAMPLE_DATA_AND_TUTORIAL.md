# ChhatraLekha: Demo Account, AI Assistant, Sample Data and Tutorial Video Specification

## 1. Product Vision

ChhatraLekha is a free, multilingual, multi-tenant digital education platform connecting institutions, students, parents, teachers, and verified educational administrations across India.

**Core Vision:**

> One Platform. Every Institution. Every Learner. Every Indian Language.

The platform is engineered to be approachable, transparent, and instantly demonstrable for first-time visitors without compromising privacy or regulatory rigor.

---

## 2. Demo Account Architecture and Demo Mode

### 2.1 Objectives
- Enable any visitor (student, parent, teacher, educator, administrator, or verifier) to explore full platform capabilities without entering personally identifiable information or accessing production records.
- Provide a prominent **Explore Demo** interface on the landing page and throughout the application shell.
- Deliver single-click role switching with temporary, cryptographically signed, restricted JWT sessions.

### 2.2 Six Dedicated Demo Personas

| Role | Demo Email | Demo Password | Portal Destination | Primary Workflows |
|---|---|---|---|---|
| **Student** | `student.demo@example.com` | `Student@Demo123` | `/me` | APAAR ID Card, QR Credential, Consent Ledger, Results, Timetable, AI Assistant |
| **Parent / Guardian** | `parent.demo@example.com` | `Parent@Demo123` | `/parent` | Ward Attendance, Academic Performance, Class Announcements, Direct Verification |
| **Teacher / Faculty** | `teacher.demo@example.com` | `Teacher@Demo123` | `/teacher` | Attendance Session Marking, Subject Marks Entry, Homework/Notices, Student Notes |
| **School Administrator** | `schooladmin.demo@example.com` | `School@Demo123` | `/institution` | K-12 Class Sections, Teacher Assignments, Student Enrolment, Attendance Overview |
| **College Administrator** | `collegeadmin.demo@example.com` | `College@Demo123` | `/institution` | Undergraduate/Postgraduate Quotas, Department Roasters, CSV Ingestion, Review Tasks |
| **University Administrator** | `universityadmin.demo@example.com` | `University@Demo123` | `/dashboard` | Multi-Collegiate Oversight, State-wide Anomaly Detection, Change Impact Previews, Reports |

### 2.3 Demo Safety Rules
- **Data Isolation:** All demo assets, sessions, and records reside in an isolated demo environment or carry `is_demo: true`.
- **Restricted Privileges:** Demo accounts have read-write access only to ephemeral sandbox state and cannot modify canonical registries.
- **Zero Real Communications:** Demo accounts cannot dispatch real SMS, emails, push notifications, or external webhook calls.
- **Audited Session:** All demo actions are logged with category `DEMO` in the audit ledger.
- **Reset Capability:** Users can reset demo data at any time via a single-click action.

---

## 3. Pan-India 5,000 Fictional Student Database

### 3.1 Dataset Scope
- **5,000 Fictional Student Records** spanning schools, polytechnics, colleges, and universities.
- **100 Fictional Educational Institutions** covering 28 Indian States and 8 Union Territories.
- **Institutional Typologies:**
  - Government Primary, Secondary, and Senior Secondary Schools
  - Private CBSE, ICSE, and State Board Schools
  - Government Engineering Colleges and Polytechnics
  - Private Engineering Colleges and Autonomous Institutes
  - State and Central Universities
- **Academic Hierarchy:**
  - Departments, Programmes, Courses, and Subjects
  - Academic Years (2023-24, 2024-25, 2025-26)
  - Timetable sessions, Daily Attendance Records, and Examination CGPA/SGPA marks
- **Linguistic Distribution:**
  - Preferred language preferences distributed across all 22 Eighth Schedule Indian constitutional languages.

### 3.2 Synthetic Data Safeguards
- All records are procedurally generated with fictional Indian names and masked synthetic APAAR tokens (`CL-STU-XXXXXX`).
- No genuine Aadhaar numbers, phone numbers, or residential addresses are stored or generated.
- Every record is explicitly marked with `is_demo: true`.

---

## 4. Multilingual AI Assistant Architecture

### 4.1 Overview
An intelligent assistant grounded in ChhatraLekha platform documentation, user guides, statutory rules, and role-authorized database records.

### 4.2 Knowledge Base and Capabilities
1. **Platform Guidance:**
   - How to check attendance and timetable
   - How to change UI language across 22 scheduled languages
   - How to use voice input and listen to announcements
   - How to generate and share opaque verification QR tokens
   - How to record attendance as a teacher or manage class sections as an administrator
2. **Authorized Record Querying:**
   - Grounded answering based on user permissions without bypassing backend role-based access control.
   - Zero hallucination policy: Factual data is queried through internal service APIs; if a metric is unavailable, the assistant clarifies rather than guessing.
3. **Multilingual Text & Voice:**
   - Responds in the active UI locale (English, Hindi, Odia, Bengali, Tamil, Telugu, Marathi, Gujarati, etc.).
   - Text-to-speech reading support via browser Web Speech API.

### 4.3 REST API Interface
- `POST /api/ai/chat`: Processes user queries with context, active locale, and authorization headers.
- `GET /api/ai/prompts`: Returns contextual quick prompt recommendations tailored to the current role.

---

## 5. How-to-Use Tutorial Video and Walkthrough

### 5.1 Landing Page Placement
Positioned directly beneath the primary hero section on the landing page, titled **"How to Use ChhatraLekha"**.

### 5.2 Interactive Player Features
- **Visual Product Walkthrough:** Interactive, accessible HTML5 playback showing actual live working screens.
- **Chapter Markers:** Quick navigation to key segments:
  - `0:00` Platform Introduction & Mission
  - `0:30` All Indian Languages & Voice Navigation
  - `1:00` Student Digital APAAR ID & Credential Wallet
  - `1:45` Parent Portal & Teacher Workspaces
  - `2:15` Institution Administration & Anomaly Detection
- **Accessibility:** Closed caption toggle, mobile-friendly touch scrubber, and complete searchable transcript accordion.
- **Zero Third-Party Tracking:** Privacy-respecting local player without external ad trackers or cookie requirements.

---

## 6. Landing Page Structure

1. **Top Navigation:** Brand Lockup, Navigation Links, Explore Demo CTA, Sign In CTA, Theme Toggle, Language Selector.
2. **Hero Section:** "One trusted record for every student." Value proposition, Explore Demo button, Apply for Early Access, Sign In.
3. **Interactive Demo Role Modal:** One-click instant login for Student, Parent, Teacher, School Admin, College Admin, and University Admin.
4. **How to Use ChhatraLekha Section:** 2-3 minute video walkthrough with chapter markers and transcript.
5. **Role-Specific Feature Showcases:** Student, Parent, Teacher, School & College, University.
6. **22 Constitutional Indian Languages Vision:** Native script showcase and voice capabilities.
7. **Multilingual AI Assistant Showcase:** Contextual assistance demo.
8. **Statutory Privacy & Verification Standards:** DPDP Act 2023, offline cryptographic validation.
9. **Frequently Asked Questions (FAQ):** Searchable common questions.
10. **Footer:** Contact, grievance redressal, legal policies, and accessibility declaration.


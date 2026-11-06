# ChhatraLekha - Landing Page Structure & Component Guide
## Section-by-Section Architecture

**Document Version:** 1.0  
**Updated:** Stage 0.4  

---

### 1. Overview

The ChhatraLekha landing page serves as the entry point for students, parents, faculty, school administrators, and university regulators. It introduces the platform's mission, presents live interactive mobile and desktop previews, details core capabilities, answers critical questions, and provides immediate onboarding paths.

---

### 2. Section Hierarchy

The landing page implements the following exact section hierarchy in sequence:

```
[ Section A: Navigation Bar ]
       │
[ Section B: Hero Section & Mobile App Preview ]
       │
[ Section C: Trust & Social Proof ]
       │
[ Section D: Feature Section (10 Systems) ]
       │
[ Section E: Benefits Section (5 Roles) ]
       │
[ Section F: Product Preview (Campus & Student) ]
       │
[ Section G: Testimonials (Sample Personas) ]
       │
[ Section H: FAQ Section (8 Key Questions) ]
       │
[ Section I: Final Call to Action ]
       │
[ Section J: Public Footer ]
```

---

### 3. Detailed Section Specifications

#### Section A: Navigation Bar
- **Location:** `frontend/src/components/layout/PublicLayout.jsx`
- **Elements:**
  - Official brand lockup and high-resolution logo.
  - Desktop nav links: Home, Features (`/#features`), For Students (`/#for-students`), For Institutions (`/#for-institutions`), About (`/about`), FAQ (`/#faq`).
  - Interactive language switcher across 22 scheduled Indian languages.
  - Interactive theme switcher (Light, Dark, System).
  - Direct authentication CTAs: "Sign In" (`/login`) and "Get Started" (`/signup`).
  - Mobile hamburger toggle and responsive slide-down navigation drawer.

#### Section B: Hero Section & Mobile App Preview
- **Location:** `frontend/src/pages/LandingPage.jsx`
- **Headline:** *"One trusted record for every student."*
- **Badge:** National Multilingual Education Platform - 22 Languages.
- **Description:** Emphasizes that ChhatraLekha authenticates academic records, tracks daily period attendance, verifies credentials, and connects learners, guardians, faculty, and institutions.
- **CTAs:**
  - `Get Started`: Direct route to `/signup`.
  - `Explore Demo`: Opens 6-persona demo sandbox modal.
  - `Verify a credential`: Direct route to `/verify/t/demo`.
- **Interactive Smartphone Preview:**
  - Device container with speaker notch, battery, 5G indicator, and time.
  - 3-Way In-Phone Role Switcher:
    - *Student View:* Masked APAAR ID card (`9921 **** 0001`), 94.2% attendance ring, today's timetable periods, and marksheet badge.
    - *Parent View:* Linked child card, attendance standing notice, upcoming exam schedule, and faculty contact channel.
    - *Teacher View:* Active lecture period (`CS302`), roll-call stats (39 Present, 2 Absent, 1 Late), and roll-call submission button.

#### Section C: Trust & Social Proof
- **Location:** `frontend/src/pages/LandingPage.jsx`
- **Core Pillars:**
  1. *Opaque Verification:* Zero raw Aadhaar or phone numbers on public URLs.
  2. *22 Scheduled Languages:* Native script typography and speech synthesis.
  3. *High-Entropy QR Seals:* Offline-verifiable cryptographic badges.
  4. *Immutable Audit Trail:* Hash-chained ledger for complete regulatory transparency.
- **Verification Integrity Banner:** Grounded in 5,000+ synthetic student records and automated regression tests. No fabricated institutional claims.

#### Section D: Feature Section
- **Location:** `frontend/src/pages/LandingPage.jsx` (Anchor: `#features`)
- **Grid of 10 Cards:**
  1. Student Dashboard (Available Now)
  2. Academic Records (Available Now)
  3. Attendance & Timetable (Available Now)
  4. Assignments & Resources (Coming Soon)
  5. Exams & Results (Available Now)
  6. Notifications & Bulletins (Available Now)
  7. Parent / Guardian Access (Available Now)
  8. Teacher & Faculty Tools (Available Now)
  9. Institution Administration (Available Now)
  10. Multilingual & Voice Experience (Available Now)

#### Section E: Benefits Section
- **Location:** `frontend/src/pages/LandingPage.jsx` (Anchors: `#for-students`, `#for-institutions`)
- **Interactive Tabs:** Switch between Students, Parents & Guardians, Teachers & Faculty, Schools & Colleges, and Universities & Regulators.
- **Card Content:** Concrete advantages, daily time savings, paperless processes, and regulatory compliance features.

#### Section F: Product Preview
- **Location:** `frontend/src/pages/LandingPage.jsx`
- **Synthetic Scenario:** "Vidya Vikas Institute of Technology (INST-0421)".
- **Tabs:** Switch between Institutional Portal View (Sanctioned vs Enrolled, Anomaly Scanner, Audit Ledger) and Student Mobile Experience.

#### Section G: Testimonials (Sample Demonstrative Personas)
- **Location:** `frontend/src/pages/LandingPage.jsx`
- **Banner:** Explicitly labeled as sample illustrative personas with synthetic data.
- **Personas:**
  - Rohan Patel (Sample Student - 3rd Year B.Tech Scholar)
  - Meera Sharma (Sample Parent - Parent of Class X Student)
  - Prof. Ramesh Joshi (Sample Faculty - Department Head, Engineering)

#### Section H: FAQ Section
- **Location:** `frontend/src/pages/LandingPage.jsx` (Anchor: `#faq`)
- **Interactive Accordion:** Covers What is ChhatraLekha, Who can use, How verification works, DPDP privacy protections, CSV data integration, free learner access, parent portal operation, and 22-language support.

#### Section I: Final Call to Action
- **Location:** `frontend/src/pages/LandingPage.jsx`
- **Banner:** High-impact deep navy section encouraging immediate onboarding via `Get Started` (`/signup`), `Explore Demo` (modal), and `Request Institutional Pilot` (`/early-access`).

#### Section J: Public Footer
- **Location:** `frontend/src/components/layout/PublicLayout.jsx`
- **Links:** About, Early Access, Help Center, FAQ, Contact, Transparency Charter, Accessibility Statement, Privacy Policy, Terms of Service.
- **Statement:** DPDP compliance, zero-tracking cookie policy, copyright notice.


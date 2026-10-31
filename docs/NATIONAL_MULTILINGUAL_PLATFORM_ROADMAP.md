# ChhatraLekha - Next Improvements & Refinements
## National Multilingual Education Platform for India

**Document type:** Product Requirements & Engineering Roadmap  
**Project:** ChhatraLekha  
**Platforms:** Web, Android and iOS  
**Target market:** India  
**Business model:** Free platform  
**Primary objective:** Build one inclusive education platform for students, parents, teachers, schools, colleges, universities and educational administrations.

---

# 1. Product Vision

ChhatraLekha should become a unified digital education platform for India's educational ecosystem.

The platform should connect students, parents, teachers, institutions and authorised education administrators through a secure, accessible and multilingual system.

It should work for:

- Government schools.
- Private schools.
- Government colleges.
- Private colleges.
- Government universities.
- Private universities.
- Central universities.
- State universities.
- Autonomous colleges.
- Deemed-to-be universities.
- Affiliated colleges.
- Other eligible educational institutions.

The platform must not be restricted to one institution type, one education board, one state or one language.

## Core mission

**One platform. Every institution. Every learner. Every Indian language.**

## Core principles

1. Free access for students, parents, teachers and institutions.
2. Support for both school and higher education.
3. Government and private institution support.
4. Multilingual interface and communication.
5. Voice-enabled interaction.
6. Strong student privacy and security.
7. Accessible design.
8. Android, iOS and web availability.
9. Configurable academic structures.
10. Reliable performance on low-cost devices and slow networks.

---

# 2. User Types and Role-Based Access

Build the platform around clearly defined user roles.

## Student

- School student.
- Higher secondary student.
- Diploma student.
- Undergraduate student.
- Postgraduate student.
- Research scholar, where supported.

Features:

- Personal dashboard.
- Academic profile.
- Institution information.
- Class/course information.
- Attendance.
- Timetable.
- Academic calendar.
- Examination schedule.
- Published results.
- Announcements.
- Notifications.
- Academic documents.
- Support requests.
- Language preferences.
- Voice assistance.

## Parent and Guardian

- Access linked student profiles.
- View authorised attendance information.
- View published results.
- Receive institution announcements.
- View timetable and academic calendar.
- Receive important notifications.
- Contact the institution.
- Manage notification preferences.

Guardian access must require an authorised relationship with the student.

## Teacher and Faculty

- Teacher/faculty dashboard.
- Assigned classes and courses.
- Student lists within authorised scope.
- Attendance management.
- Assessment management.
- Marks entry.
- Result review.
- Announcements.
- Student communication.
- Academic reports.
- Voice-assisted workflows.

## Institution Administration

- Institution dashboard.
- Student management.
- Staff management.
- Academic structure management.
- Class and section management.
- Department and programme management.
- Attendance reports.
- Examination management.
- Result publication.
- Announcements.
- Permissions management.
- Audit logs.
- Institution settings.

## University Administration

- University dashboard.
- University profile.
- Constituent and affiliated institution relationships.
- Department management.
- Programme management.
- Academic-year management.
- Semester management.
- Institution-level reports.
- Authorised administrative oversight.
- Policy and configuration management.

## Platform Administration

- Institution onboarding.
- Institution verification workflows.
- Account management.
- Platform configuration.
- Security monitoring.
- Abuse reporting.
- Audit review.
- System health monitoring.

Platform administrators must not automatically receive unrestricted access to student academic records.

---

# 3. Institution Management System

Create a flexible institution onboarding system.

## Institution categories

- Government.
- Private.
- Public-funded.
- Autonomous.
- Other legally recognised categories.

## Institution types

- Primary school.
- Middle school.
- Secondary school.
- Senior secondary school.
- Higher secondary institution.
- Diploma institution.
- College.
- University.
- Autonomous college.
- Other eligible educational institution.

## Institution profile

Every institution should have:

- Institution name.
- Institution type.
- Ownership type.
- Registration or recognition information, where applicable.
- Education board or university affiliation.
- State.
- District.
- Address.
- Contact details.
- Academic calendar.
- Supported languages.
- Institution administrator.
- Official website, if available.

Do not imply government approval or institutional recognition merely because an institution creates an account.

## Institution hierarchy

Support relationships such as:

University
  |-- Constituent College
  |-- Affiliated College
  |-- Department
  `-- Academic Programme

School
  |-- Academic Year
  |-- Class
  |-- Section
  `-- Subject

The hierarchy must be configurable rather than hardcoded.

---

# 4. All Indian Languages - Multilingual System

This is a core product requirement.

ChhatraLekha should support the 22 languages listed in the Eighth Schedule of the Indian Constitution:

1. Assamese
2. Bengali
3. Bodo
4. Dogri
5. Gujarati
6. Hindi
7. Kannada
8. Kashmiri
9. Konkani
10. Maithili
11. Malayalam
12. Manipuri
13. Marathi
14. Nepali
15. Odia
16. Punjabi
17. Sanskrit
18. Santali
19. Sindhi
20. Tamil
21. Telugu
22. Urdu

Future expansion should include additional regional, tribal and community languages.

## Language features

- Language selection during onboarding.
- Language selection in profile settings.
- Language selection independent of institution language.
- Multilingual navigation.
- Multilingual forms.
- Multilingual announcements.
- Multilingual notifications.
- Multilingual FAQs.
- Multilingual support.
- Multilingual help content.
- Right-to-left layout support where required.
- Regional script and font support.

## Translation requirements

- Use central translation resources.
- Avoid hardcoding visible text in application code.
- Maintain translation keys.
- Maintain reviewed translations.
- Support missing-translation fallback.
- Allow administrators to create translated announcements.
- Preserve the original language of official academic records.
- Clearly identify machine-generated translations.
- Allow correction of inaccurate translations.

## Translation technology

Evaluate:

- BHASHINI services.
- Other reliable Indian-language translation services.
- Native platform language capabilities.
- Offline translation models where practical.

Do not assume every provider supports every language, script or domain equally well. Test each language before announcing support.

---

# 5. Voice Input and Voice Assistance

Voice functionality should be a first-class feature.

## Voice input

- Voice search.
- Voice-based navigation.
- Voice-assisted form filling.
- Voice-based help.
- Speech-to-text.
- Voice-assisted attendance workflows.
- Voice-based queries about permitted academic information.

## Voice output

- Read announcements aloud.
- Read timetable information aloud.
- Read attendance information aloud.
- Read published results aloud.
- Read notifications aloud.
- Text-to-speech responses.
- Language-specific speech output.

## Example interaction

A student speaks in Odia:

"ମୋର ଆଜିର ଉପସ୍ଥାନ ଦେଖାଅ"

The application recognises the request and displays the student's attendance.

## Voice interaction pipeline

1. User selects a preferred language.
2. User activates the microphone.
3. Speech recognition converts speech to text.
4. Language understanding identifies the request.
5. Backend verifies the user's identity and permissions.
6. Application retrieves permitted information.
7. Application displays or speaks the response.

## Voice privacy

- Request microphone permission only when needed.
- Show when microphone input is active.
- Avoid recording continuously.
- Avoid retaining recordings unnecessarily.
- Explain whether voice is processed locally or by an external service.
- Protect transcripts and recordings.
- Allow users to disable voice features.
- Never use voice recognition as a replacement for authentication.

Sensitive actions require explicit confirmation.

---

# 6. Android Application Improvements

Continue the existing Kotlin and Jetpack Compose foundation.

## Recommended architecture

- Kotlin.
- Jetpack Compose.
- MVVM or a clearly documented alternative.
- Repository pattern.
- Room database.
- Retrofit or Ktor.
- Kotlin Coroutines.
- Flow.
- Dependency injection.
- WorkManager.
- Android Keystore.

## Required refinements

- Role-based navigation.
- Multilingual interface.
- Voice input.
- Text-to-speech.
- Offline-first functionality.
- Background synchronisation.
- Secure local storage.
- Notification handling.
- Deep links.
- Accessibility support.
- Dark mode.
- Responsive layouts.
- Crash monitoring.
- Performance monitoring.

## Android testing

- Multiple Android versions.
- Different screen sizes.
- Low-memory devices.
- Slow networks.
- Offline mode.
- Background synchronisation.
- Notification handling.
- Language switching.
- Regional scripts.
- Voice recognition.

---

# 7. iOS Application Development

Build a dedicated native iOS application.

## Recommended architecture

- Swift.
- SwiftUI.
- MVVM or a clearly documented alternative.
- Repository pattern.
- SwiftData or Core Data.
- URLSession.
- Swift Concurrency.
- Keychain.
- BackgroundTasks where appropriate.

## Required features

- Same core functionality as Android.
- Role-based dashboards.
- Multilingual interface.
- Voice input.
- Speech output.
- Offline functionality.
- Secure storage.
- Push notifications.
- Deep links.
- Accessibility support.
- Dark mode.
- Dynamic Type support.

## iOS testing

- Supported iOS versions.
- Different iPhone screen sizes.
- iPad layouts, if supported.
- Offline functionality.
- Background synchronisation.
- Voice features.
- Notification handling.
- Language switching.
- VoiceOver accessibility.

---

# 8. Web Application Improvements

The web application should primarily serve:

- Institution administrators.
- University administrators.
- Teachers and faculty.
- Students.
- Parents and guardians.

## Required modules

- Public landing page.
- Institution registration.
- Login and account management.
- Student dashboard.
- Parent dashboard.
- Teacher dashboard.
- Institution administration.
- University administration.
- Academic structure management.
- Student records.
- Staff records.
- Attendance.
- Assessments.
- Results.
- Announcements.
- Reports.
- Audit logs.
- Language settings.

The web experience must be responsive and accessible.

---

# 9. Unified Backend Architecture

Continue using the existing FastAPI foundation after a code and security audit.

## Suggested components

- Authentication service.
- User management service.
- Institution management service.
- Academic structure service.
- Student enrolment service.
- Staff assignment service.
- Attendance service.
- Assessment and results service.
- Announcement service.
- Notification service.
- Translation service.
- Voice processing integration.
- Document service.
- Consent service.
- Audit service.

Avoid unnecessary microservices during the early stages.

Start with a modular backend and separate services only when operational needs justify it.

## Database domain model

Suggested entities:

- Person
- UserAccount
- Institution
- InstitutionMembership
- InstitutionRelationship
- AcademicYear
- Term
- Department
- Programme
- ClassGroup
- Section
- Course
- Subject
- StudentProfile
- Enrolment
- GuardianRelationship
- StaffProfile
- TeacherAssignment
- AttendanceRecord
- Assessment
- Result
- Announcement
- Notification
- Document
- ConsentRecord
- AuditEvent
- Translation
- LanguagePreference
- VoicePreference

## Important data rules

- Separate person identity from institution membership.
- Keep enrolment history.
- Support multiple institutions for a person where appropriate.
- Apply institution-level access restrictions.
- Apply class/course-level permissions.
- Keep guardian access explicitly authorised.
- Protect sensitive identifiers.
- Avoid unnecessary personal-data collection.

---

# 10. Security and Student Privacy

Security is a release requirement.

## Authentication

- Secure login.
- Session expiry.
- Token refresh.
- Logout and session revocation.
- Password recovery.
- Secure password storage.
- Optional biometric access.

## Authorisation

- Backend-enforced role permissions.
- Institution-level tenant isolation.
- Teacher assignment checks.
- Student record restrictions.
- Guardian relationship checks.
- Restricted university administration access.
- Audit of privileged actions.

## Application security

- HTTPS.
- Secure cookies where applicable.
- Input validation.
- XSS protection.
- CSRF protection where applicable.
- Secure file uploads.
- Rate limiting.
- CORS restrictions.
- Secure secrets management.
- Dependency updates.
- Backup and recovery testing.

## Privacy

- Privacy Policy.
- Terms of Service.
- Consent management.
- Data retention policy.
- Data correction workflow.
- Data export workflow.
- Account deletion workflow.
- Minor protection.
- Voice-data privacy.
- Translation-provider privacy review.
- Third-party SDK disclosures.

Before processing real student information, obtain appropriate institutional approvals and qualified legal and security reviews.

---

# 11. Offline and Low-Network Support

The platform must be usable in areas with unreliable internet connectivity.

## Required features

- Cached dashboard information.
- Cached timetable.
- Cached permitted academic records.
- Cached announcements.
- Offline access to selected documents.
- Pending synchronisation queue.
- Retry handling.
- Conflict detection.
- Clear sync status.
- Network status indicator.

## Important rules

- Do not allow offline changes to bypass server-side permissions.
- Keep the server authoritative.
- Make pending changes visible.
- Do not silently overwrite conflicting records.
- Protect locally stored student information.
- Test interrupted synchronisation.

---

# 12. Accessibility and Inclusion

- Screen-reader support.
- TalkBack support.
- VoiceOver support.
- Text scaling.
- High-contrast support.
- Accessible colour combinations.
- Clear labels.
- Keyboard navigation.
- Voice-assisted interaction.
- Regional font support.
- Simple navigation.
- Clear error messages.
- Accessible forms.

Do not assume voice input alone makes an application accessible.

---

# 13. Testing and Quality Assurance

## Functional tests

- Student workflows.
- Guardian workflows.
- Teacher workflows.
- Institution administration.
- University administration.
- Attendance.
- Results.
- Announcements.
- Notifications.
- Language selection.
- Voice input.
- Voice output.
- Offline synchronisation.

## Security tests

- Cross-institution access.
- Unauthorised access.
- Role escalation.
- Guardian access restrictions.
- API permission checks.
- File access restrictions.
- Sensitive-data exposure.
- Session revocation.

## Multilingual tests

Test each supported language for:

- Translation accuracy.
- Font rendering.
- Script rendering.
- Text direction.
- Layout overflow.
- Search.
- Notifications.
- Voice recognition.
- Speech output.
- Accessibility.

Use native-language reviewers for quality assurance.

---

# 14. Development Roadmap

This is a proposed sequence. Adjust the schedule based on engineering capacity and testing results.

| Phase | Work | Expected outcome |
|---|---|---|
| 1 | Audit existing repository | Verified current implementation |
| 2 | Product and domain redesign | Shared school/college/university model |
| 3 | Institution onboarding | Government and private institution support |
| 4 | Identity and permissions | Secure multi-role access |
| 5 | Student and staff management | Core academic records |
| 6 | Attendance and results | Core academic workflows |
| 7 | Android refinement | Stable Android experience |
| 8 | iOS development | Native iOS application |
| 9 | English, Hindi and Odia | First multilingual release |
| 10 | Additional Indian languages | Gradual language expansion |
| 11 | Voice input and output | Voice-enabled experience |
| 12 | Offline improvements | Better low-network usability |
| 13 | Security and accessibility | Production-readiness review |
| 14 | Controlled pilot | Validate with institutions |
| 15 | Wider rollout | Expand based on evidence |

---

# 15. Pilot Strategy

Start with a small and diverse pilot.

Potential pilot participants:

- One government school.
- One private school.
- One government college.
- One private college.

A university pilot can follow after the institution hierarchy and permissions have been validated.

## Pilot requirements

- Use synthetic data during development.
- Obtain institutional approval before real-data use.
- Train staff.
- Provide support documentation.
- Test language preferences.
- Test voice functionality.
- Test Android and iOS independently.
- Test low-network conditions.
- Collect feedback.
- Resolve critical security and usability issues.

---

# 16. Free Platform Sustainability

ChhatraLekha should remain free for students, parents, teachers and institutions.

Potential funding:

- Education grants.
- CSR support.
- Philanthropic support.
- University research partnerships.
- Open-source sponsorship.
- Public-interest technology programmes.

Non-negotiable principles:

- No sale of student data.
- No behavioural advertising.
- No sponsor access to private student records.
- No payment requirement for essential academic access.
- Transparent funding practices.

Maintain a realistic plan for hosting, support, security and maintenance.

---

# 17. Recommended Immediate Backlog

- [ ] Audit the existing repository.
- [ ] Reconcile documentation and test counts.
- [ ] Define school, college and university workflows.
- [ ] Finalise the institution data model.
- [ ] Define user roles and permissions.
- [ ] Implement institution-level isolation tests.
- [ ] Add configurable academic structures.
- [ ] Stabilise the Android application.
- [ ] Define the iOS implementation plan.
- [ ] Design the central language management system.
- [ ] Add English, Hindi and Odia first.
- [ ] Evaluate BHASHINI and other speech/translation providers.
- [ ] Design voice input and output workflows.
- [ ] Implement privacy and consent controls.
- [ ] Test offline functionality.
- [ ] Prepare a controlled institution pilot.

---

# 18. Definition of Success

ChhatraLekha should eventually allow:

- A school student to access academic information.
- A college student to access academic information.
- A university student to access academic information.
- A parent to access authorised student information.
- A teacher to manage assigned classes and courses.
- An institution to manage its academic workflows.
- A university to oversee authorised institutional relationships.
- A government institution to use the same platform as a private institution.
- A user to select their preferred Indian language.
- A user to speak instead of typing where supported.
- A user to use the application on Android, iOS or web.

All these capabilities must operate with correct permissions, reliable data and strong privacy protections.

---

# Final Product Principle

ChhatraLekha should not be designed only for English-speaking students, only for colleges, or only for private institutions.

It should be designed for the diversity of India's education system.

**One ChhatraLekha for India's educational ecosystem - inclusive, multilingual, voice-enabled, accessible and free.**


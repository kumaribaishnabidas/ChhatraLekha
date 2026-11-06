# Architecture Specification: Core Navigation Workflow

**Module:** Global Navigation & Routing  
**Version:** 2.0.0  
**Status:** Approved  
**Date:** 2026-11-06  

---

## 1. Overview

The ChhatraLekha navigation system establishes a predictable, role-tailored routing and breadcrumb framework across the platform. Navigation definitions are centralized in `frontend/src/modules/navigation/NavigationConfig.js` and resolved dynamically through the `useNavigation` hook.

---

## 2. Shared Navigation Groups

All platform features are organized into 13 canonical navigation groups:

1. **Dashboard (`dashboard`):** Role-specific primary home views (`/me`, `/parent`, `/teacher`, `/school`, `/college`, `/university`, `/institution`, `/dashboard`).
2. **My Profile (`profile`):** Personal demographic details, credentials, and preferences (`/profile`).
3. **Academics (`academics`):** Classes, departments, programmes, curricula, and student registries (`/academic`, `/students`, `/library`, `/opportunities`).
4. **Attendance (`attendance`):** Roll call taking, session logs, and attendance percentages (`/teacher`, `/me/attendance`, `/parent`).
5. **Timetable (`timetable`):** Daily period grids, laboratory slots, and room allocations (`/me/timetable`, `/parent`, `/teacher`).
6. **Assignments (`assignments`):** Coursework problem sets, deadlines, and submissions (`/me/assignments`, `/teacher`).
7. **Examinations (`examinations`):** Periodic tests, external examination schedules, and question paper moderation (`/assessments`).
8. **Results (`results`):** Published marks, grade cards, SGPA/CGPA analytics (`/me/results`, `/assessments`).
9. **Announcements (`announcements`):** Official circulars, notifications, and directives (`/announcements`).
10. **Notifications (`notifications`):** Interactive alerts, status updates, and reminders (`/notifications`).
11. **Documents (`documents`):** Digital ID cards, cryptographic share proofs, verified certificates, and CSV imports (`/me/id-card`, `/wallet`, `/upload`, `/reports`).
12. **Help and Support (`help`):** Platform documentation, FAQs, and helpdesk contact (`/help`).
13. **Settings (`settings`):** Account configurations, theme, and language preferences (`/profile`).

---

## 3. Role-Based Navigation Routing Flowchart

```
                          User Authentication / Login
                                       |
                                       v
                             [Extract Role Claim]
                                       |
            +------------+-------------+-------------+------------+
            |            |             |             |            |
            v            v             v             v            v
        [Student]     [Parent]     [Teacher]     [School]     [College/Univ]
            |            |             |             |            |
            v            v             v             v            v
         Route:       Route:        Route:        Route:       Route:
          /me        /parent       /teacher      /school     /college or
                                                             /university
            |            |             |             |            |
            +------------+-------------+-------------+------------+
                                       |
                                       v
                       Render Common AppLayout Shell
                         ├── Dynamic Breadcrumbs
                         ├── User Profile Popover
                         ├── Active Institution Switcher
                         └── Role-Scoped Modular Widgets
```

---

## 4. Role-Specific Menu Registries

### 4.1 Student Navigation (`student`)
- Dashboard: `/me`
- Academics: `/me/academics`
- Attendance: `/me/attendance`
- Timetable: `/me/timetable`
- Assignments: `/me/assignments`
- Results: `/me/results`
- Documents: `/me/id-card`
- Announcements: `/announcements`
- Notifications: `/notifications` (with unread badge)
- Help: `/help`
- Settings: `/profile`

### 4.2 Parent Navigation (`parent`)
- Dashboard: `/parent`
- Children Overview: `/parent`
- Attendance Log: `/parent`
- Child Timetable: `/parent`
- Results & Marks: `/assessments`
- Circulars: `/announcements`
- Notifications: `/notifications` (with unread badge)
- Help: `/help`
- Settings: `/profile`

### 4.3 Teacher Navigation (`teacher`)
- Workspace Dashboard: `/teacher`
- Assigned Classes: `/teacher`
- Roll Call Attendance: `/teacher`
- Timetable Schedule: `/teacher`
- Coursework Assignments: `/teacher`
- Examinations & Grades: `/assessments`
- Announcements: `/announcements`
- Notifications: `/notifications` (with unread badge)
- Help: `/help`
- Settings: `/profile`

### 4.4 School Administrator (`school_admin`)
- School Dashboard: `/school`
- Student Register: `/students`
- Teaching Staff: `/teacher`
- Grade & Class Setup: `/academic`
- Attendance Overview: `/teacher`
- School Circulars: `/announcements`
- TC & Board Reports: `/reports`
- Bulk Data Ingestion: `/upload`
- Notifications: `/notifications`
- Help: `/help`
- Settings: `/profile`

### 4.5 College Administrator (`college_admin`)
- College Dashboard: `/college`
- Departments & Programmes: `/academic`
- Student Directory: `/students`
- Faculty Directory: `/teacher`
- Attendance Risk Monitor: `/teacher`
- Semester Examinations: `/assessments`
- College Notices: `/announcements`
- AICTE / UGC Reports: `/reports`
- Bulk Data Ingestion: `/upload`
- Notifications: `/notifications`
- Help: `/help`
- Settings: `/profile`

### 4.6 University Administrator (`university_admin`)
- University Dashboard: `/university`
- Affiliated Colleges Roster: `/institutions`
- Programme Sanctioning: `/academic`
- Examination Moderation: `/assessments`
- Syndicate Directives: `/announcements`
- Compliance Matrix: `/reports`
- Notifications: `/notifications`
- Help: `/help`
- Settings: `/profile`

---

## 5. Breadcrumb Generation Strategy

The `<Breadcrumbs />` component inspects the active `location.pathname` split by `/` segments and dynamically generates cumulative path links:
- Route segment tokens are mapped through `ROUTE_LABELS` (e.g., `me` -> `Student Portal`, `school` -> `School Administration`, `assignments` -> `Assignments`).
- Trailing segment receives `aria-current="page"` and is rendered as static bold text.
- Intermediate segments render as accessible navigation links.
- Breadcrumb navigation is responsive and collapses gracefully on narrow viewports without triggering horizontal scrollbars.

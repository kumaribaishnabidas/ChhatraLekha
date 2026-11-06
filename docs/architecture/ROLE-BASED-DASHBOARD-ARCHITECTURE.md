# Architecture Specification: Role-Based Dashboards

**Module:** Dashboards & Core Navigation  
**Version:** 2.0.0  
**Status:** Approved  
**Date:** 2026-11-06  

---

## 1. Architectural Principles

The ChhatraLekha role-based dashboard architecture adheres to four foundational design principles:

1. **Shared Foundation, Differentiated Views:**  
   All personas operate within the same unified application shell (`AppLayout.jsx`), consuming shared UI component primitives, theme controls, language selectors, notification centers, and authentication contexts.

2. **Server-Side Authoritative Boundaries:**  
   Role-specific UI views are not mere frontend visibility toggles. Every underlying endpoint (`/me/*`, `/teacher/*`, `/parent/*`, `/{institution_id}/*`, `/dashboard/*`) independently enforces identity, tenant boundaries, and permissions using JWT claims and principal scoping.

3. **Statutory Tenant & Guardian Isolation:**  
   - Parents can only retrieve records of students with an active, institution-verified `GuardianVerificationStatus.VERIFIED` link.
   - Institutional administrators can only query and mutate records belonging to their assigned `institution_id`.
   - University administrators receive aggregated telemetry, network quotas, and compliance statuses; they cannot inspect individual student transcripts across unaffiliated institutions.

4. **Progressive Responsiveness:**  
   The application shell adapts seamlessly across desktop (collapsible sidebar, multi-column grid), tablet (responsive grid, condensed navigation), and mobile (off-canvas drawer, mobile bottom bar, touch-friendly tap targets).

---

## 2. Dashboard Persona Taxonomy

```
+------------------------------------------------------------------------------------+
|                                ChhatraLekha Platform                               |
+------------------------------------------------------------------------------------+
       |                     |                     |                    |
       v                     v                     v                    v
+--------------+      +--------------+      +--------------+     +-------------------+
|   Student    |      |    Parent    |      |   Teacher    |     |   Institutional   |
|   Portal     |      |    Portal    |      |  Workspace   |     |   Administrators  |
|   (/me)      |      |   (/parent)  |      |  (/teacher)  |     +-------------------+
+--------------+      +--------------+      +--------------+       |        |        |
                                                                   v        v        v
                                                              +--------++-------++------------+
                                                              | School ||College|| University |
                                                              | Admin  || Admin ||  Oversight |
                                                              |(/school)||(/college)||(/university)|
                                                              +--------++-------++------------+
```

### 2.1 Persona Matrix

| Role Key | Route | Primary Objective | Authoritative Backend Scope |
| :--- | :--- | :--- | :--- |
| `student` | `/me` | Identity, credentials, schedule, results | Authenticated student principal ID |
| `parent` | `/parent` | Ward progress, attendance, circulars | Verified guardian-student links only |
| `teacher` | `/teacher` | Assigned classes, roll call, assignments | Assigned classes and department subjects |
| `school_admin` | `/school` | Grade cohorts, staff, TC, attendance | Own school institution ID |
| `college_admin` | `/college` | Departments, programmes, exam, risk | Own college institution ID |
| `university_admin`| `/university`| Affiliated network, quotas, compliance | Aggregated network telemetry |

---

## 3. Component Architecture & Reusability

All dashboards are composed of standardized, modular UI widgets located in `frontend/src/components/dashboard/`:

```
frontend/src/components/dashboard/
├── Breadcrumbs.jsx                 # Dynamic route segment mapper
├── UserProfileMenu.jsx             # User identity, avatar & quick actions
├── SummaryCard.jsx                 # KPI metric tile with tone & trend
├── UpcomingEventsWidget.jsx        # Calendar & examination schedule list
├── RecentActivityWidget.jsx        # Chronological audit & activity feed
├── NotificationPreviewWidget.jsx   # Priority announcements & circulars
├── ProgressIndicatorWidget.jsx     # Linear multi-target progress bars
├── DataTableWidget.jsx             # Responsive search-enabled table
├── QuickActionWidget.jsx           # Action shortcut card grid
├── EmptyStateWidget.jsx            # Fallback zero-state display
├── LoadingSkeleton.jsx             # Pulse loading state primitives
└── index.js                        # Clean barrel export
```

### 3.1 Widget Contract Specifications

- **`SummaryCard`**:  
  Accepts `label`, `value`, `hint`, `tone` (`good`, `warning`, `critical`, `accent`, `default`), `icon`, and optional `trend`. Renders high-contrast, accessible typography with appropriate semantic background tints.

- **`UpcomingEventsWidget`**:  
  Accepts an array of structured events (`title`, `subtitle`, `month`, `day`, `time`, `location`, `status`). Formats date chips using bold typography without harsh visual noise.

- **`ProgressIndicatorWidget`**:  
  Calculates normalized percentage (`value / max * 100`) and renders an accessible HTML5 progress bar with `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, and `aria-valuemax`.

- **`DataTableWidget`**:  
  Encapsulates client-side text filtering across all columns, rendering accessible table headers, zebra-hover rows, and empty-state placeholders.

---

## 4. Layout & Responsive Shell Architecture

The core shell in `frontend/src/components/layout/AppLayout.jsx` orchestrates:

1. **Top Navigation Bar:**
   - Brand logo and mobile drawer toggle button.
   - Dynamic `<Breadcrumbs />` indicating the user's active hierarchy.
   - Modular `<NotificationBell />` with live unread counter popover.
   - Modular `<UserProfileMenu />` with avatar initials, role badge, institution name, and sign-out handler.
   - Global `<ThemeToggle />` and `<LanguageSwitcher />`.
   - Voice assistant button and AI assistant drawer launcher.

2. **Collapsible Sidebar (`Sidebar.jsx`):**
   - Retains state in `localStorage` (`chhatralekha.sidebar_collapsed`).
   - Integrated `<InstitutionSwitcher />` for switching between affiliated institutions when user holds multiple memberships.
   - Role-specific navigation items rendered with active route highlighting.

3. **Mobile Bottom Navigation (`MobileBottomBar.jsx`):**
   - Automatically surfaces primary navigation items on mobile viewports (< 1024px) with touch-friendly spacing and zero horizontal overflow.

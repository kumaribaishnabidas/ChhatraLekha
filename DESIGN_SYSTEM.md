# ChhatraLekha — Design System & Visual Specification

**Document Version:** 2.1.0  
**Authority:** Mandatory Core Governance Document 2 of 4  
**Status:** Canonical Source of Truth  
**Repository:** [ChhatraLekha](https://github.com/kumaribaishnabidas/ChhatraLekha.git)  
**Last Updated:** 2026-11-23  

---

## 1. Design Philosophy, Brand Identity & UI Audit

### 1.1 Design Philosophy
**ChhatraLekha** (छात्रलेखा) is the national digital academic identity and operations platform for schools and colleges across India. Its visual design balances statutory authority, institutional trustworthiness, high visual clarity, and universal accessibility.

The visual system adheres to three foundational tenets:
1. **Utility Over Decoration:** Visual elements exist to convey status, verify identity, or facilitate classroom tasks. Disallowed are superficial decorative fads (such as heavy backdrop-blur filters, multi-colored gradients, or oversized floating drop shadows) that reduce text readability and tax lower-end mobile chipsets.
2. **Pan-Indian Inclusivity:** The interface must render all 22 official Eighth Schedule Indian languages natively with dedicated typography, zero clipped conjuncts, and bidirectional (RTL) support for Urdu and Kashmiri.
3. **High-Contrast Legibility:** The color scheme is calibrated for high-contrast viewing on affordable TN/IPS displays under bright outdoor sunlight in schoolyards and rural campuses.

### 1.2 Official Brand Marks & Assets
Source vector assets reside in `docs/assets/brand/`:
- **Primary Emblem:** An open academic book layered with a verified circular checkmark, dynamic saffron orange arcs representing upward mobility, crowned with a formal academic mortarboard cap.
- **Wordmark:** "ChhatraLekha" rendered in deep navy (`#16257A` / `#2F57D6`) and vibrant saffron orange (`#FF8A00`), paired with the bilingual Devanagari sub-lockup "छात्रलेखा".
- **Statutory Tagline:** `"Authenticate · Verify · Empower"` (separated by middle dots `·`, never dashes or emojis).
- **Usage Rules:**
  - The emblem and wordmark must be rendered unmodified with proportional aspect ratio lock.
  - Clear space of at least 50% of the emblem's width must surround the lockup.
  - Never place the logo on unapproved gradient backgrounds or unverified color washes.

---

## 2. Color Palette & Semantic Tokens

All color styling is implemented through custom CSS variables declared in `frontend/src/index.css`. The application supports full light and dark theming driven by the `data-theme` attribute on the `<html>` root element (`[data-theme='light']` or `[data-theme='dark']`).

```
Light Mode: Warm Ivory Canvas (#FFFFF0) + Royal Navy (#2F57D6) + Saffron Accent (#FF8A00)
Dark Mode:  Deep Obsidian Navy Canvas (#0B1437) + Midnight Surface (#121C4A) + Golden Saffron (#FF9A2E)
```

### 2.1 Complete Token Palette Reference

| Token Name | Light Theme Value | Dark Theme Value | Semantic Role & Context |
|---|---|---|---|
| `--app-canvas` | `#fffff0` | `#0b1437` | Main page canvas background (warm ivory vs deep navy) |
| `--app-surface` | `#ffffff` | `#121c4a` | Primary card, modal, and drawer background |
| `--app-surface-2` | `#fafaec` | `#17235a` | Secondary card background, table headers, hover rows |
| `--app-surface-3` | `#f1f0dc` | `#1e2c6b` | Selected item states, active tabs, sub-panels |
| `--app-ink` | `#16192b` | `#f5f3e8` | Primary reading text, headings, data values |
| `--app-muted` | `#4a5160` | `#b7bcd6` | Secondary labels, timestamps, metadata, captions |
| `--app-line` | `#e4e2cc` | `#2a3980` | Subtle container dividers, card outlines, table borders |
| `--app-line-strong` | `#c9c6a8` | `#3b4c9c` | Emphasized input borders, active focus indicators |
| `--app-brand` | `#2f57d6` | `#5b7ff0` | Primary interactive brand action, active nav, primary buttons |
| `--app-brand-deep` | `#16257a` | `#0b1437` | Deep header background, split hero showcase panels |
| `--app-brand-text` | `#1f3fbf` | `#8fa8ff` | Primary branded section headers, emphasis links |
| `--app-brand-mid` | `#3655c9` | `#4a6de5` | Secondary brand interactive states |
| `--app-brand-bright` | `#4169e1` | `#7092ff` | High-visibility accent links and highlight indicators |
| `--app-on-brand` | `#ffffff` | `#ffffff` | Text and icons placed on top of brand backgrounds |
| `--app-accent` | `#ff8a00` | `#ff9a2e` | Vibrant saffron orange for primary CTAs and verification seals |
| `--app-accent-strong` | `#c2410c` | `#ffb35c` | Emphasized warning highlights, active orange badges |
| `--app-on-accent` | `#16257a` | `#0b1437` | Dark contrast text placed on top of orange accent fills |
| `--app-success` | `#0f7a44` | `#5ad07f` | Successful verification verdicts, present attendance status |
| `--app-success-surface`| `#e2f6ec` | `#0f3822` | Alert background, valid credential pill background |
| `--app-warning` | `#b26a00` | `#f0b03a` | Intake cap alerts, review pending queue items, late attendance |
| `--app-warning-surface`| `#fef3dc` | `#3d2800` | Alert background, pending review card background |
| `--app-danger` | `#c62828` | `#ff8a80` | Intake breaches, revoked credentials, absent attendance |
| `--app-danger-surface` | `#fde7e7` | `#401010` | Critical alert background, error message containers |
| `--app-info` | `#4169e1` | `#90caf9` | Institutional notices, advisory tips, help bubbles |
| `--app-info-surface` | `#e7effc` | `#10244d` | Info banners, help box backgrounds |

---

## 3. Typography & Pan-Indian Script Stacks

To guarantee that all 22 official Eighth Schedule languages render crisply without missing glyphs, tofu blocks (`□`), or improper conjunct ligatures, ChhatraLekha specifies dedicated regional font packages via `@fontsource/noto-sans-*`.

```css
/* Universal Base Typography */
--app-font-sans: 'Noto Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
--app-font-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
```

### 3.1 Regional Script Font Stack Mapping
- **Latin & Universal English:** `'Noto Sans', sans-serif`
- **Devanagari (Hindi, Marathi, Sanskrit, Konkani, Bodo, Dogri, Maithili, Nepali):** `'Noto Sans Devanagari'`
- **Bengali & Assamese:** `'Noto Sans Bengali'`
- **Odia (Oriya):** `'Noto Sans Oriya'`
- **Tamil:** `'Noto Sans Tamil'`
- **Telugu:** `'Noto Sans Telugu'`
- **Kannada:** `'Noto Sans Kannada'`
- **Malayalam:** `'Noto Sans Malayalam'`
- **Gujarati:** `'Noto Sans Gujarati'`
- **Gurmukhi (Punjabi):** `'Noto Sans Gurmukhi'`
- **Urdu & Kashmiri (Arabic Nastaliq Script, RTL):** `'Noto Nastaliq Urdu'`

### 3.2 Type Scale
- **Display 1:** `2.25rem` (`36px`), line-height: `1.2`, font-weight: `800`
- **Display 2:** `1.875rem` (`30px`), line-height: `1.25`, font-weight: `700`
- **Heading 1:** `1.5rem` (`24px`), line-height: `1.3`, font-weight: `700`
- **Heading 2:** `1.25rem` (`20px`), line-height: `1.35`, font-weight: `600`
- **Heading 3:** `1.125rem` (`18px`), line-height: `1.4`, font-weight: `600`
- **Body Regular:** `1.0rem` (`16px`), line-height: `1.5`, font-weight: `400`
- **Body Small:** `0.875rem` (`14px`), line-height: `1.5`, font-weight: `400` / `500`
- **Caption / Meta:** `0.75rem` (`12px`), line-height: `1.4`, font-weight: `500`

---

## 4. Design Tokens & Structural Scale

### 4.1 Spacing Scale (4px / 8px Grid)
- `space-1`: `0.25rem` (`4px`)
- `space-2`: `0.5rem` (`8px`)
- `space-3`: `0.75rem` (`12px`)
- `space-4`: `1.0rem` (`16px`)
- `space-6`: `1.5rem` (`24px`)
- `space-8`: `2.0rem` (`32px`)
- `space-12`: `3.0rem` (`48px`)

### 4.2 Structural Radius Tokens (Strict Invariant)
To maintain structural crispness and avoid toy-like roundness:
- `rounded-none`: `0px`
- `rounded-sm`: `0.125rem` (`2px`)
- `rounded`: `0.25rem` (`4px`)
- `rounded-md`: `0.375rem` (`6px`)
- `rounded-lg`: `0.5rem` (`8px`)
- `rounded-full`: `9999px` (Exclusively for circular avatars, status dots, and pill tags)
- **STRICT PROHIBITION:** Never use soft corner classes: `rounded-xl`, `rounded-2xl`, or `rounded-3xl`. The automated `DesignLint.test.jsx` test suite enforces zero occurrences of these classes across the entire codebase.

### 4.3 Borders & Outlines
- Standard Border: `1px solid var(--app-line)`
- Emphasized Border: `1px solid var(--app-line-strong)`
- Active / Selected Border: `2px solid var(--app-brand)`
- Error Border: `1px solid var(--app-danger)`

### 4.4 Shadows & Elevation
To ensure optimal performance on mobile processors:
- Ambient Shadow: `0 1px 3px rgba(31, 63, 191, 0.08)` (`shadow-xs` / `shadow-sm`)
- Modal / Popover Shadow: `0 4px 12px rgba(31, 63, 191, 0.12)`
- **STRICT PROHIBITION:** Never use heavy drop shadows (`shadow-lg`, `shadow-xl`, `shadow-2xl`). Elevation is established via 1px crisp borders (`border border-line`) and subtle surface tonal contrast (`--app-surface-2`).

### 4.5 Breakpoints & Layout Widths
- `sm`: `640px` (Compact mobile landscape & tablets)
- `md`: `768px` (Portrait tablets & small laptops)
- `lg`: `1024px` (Desktop workspaces & split-panel layouts)
- `xl`: `1280px` (High-resolution dashboards)
- Container Max Width: `1280px` (centered with `mx-auto px-4 sm:px-6 lg:px-8`)

---

## 5. Automated Design Invariants & Lint Rules

All UI additions must pass the automated Vitest suite `frontend/src/test/DesignLint.test.jsx`. The suite mechanically checks all source files for the following invariants:

1. **Zero Harsh Gradients:**
   - **Rule:** `bg-gradient`, `gradient-to-`, and radial gradients are strictly disallowed.
   - **Reason:** Flat, subtle surfaces render with higher contrast in bright sunlight and consume significantly fewer GPU cycles on affordable smartphones.
2. **Zero `backdrop-blur`:**
   - **Rule:** `backdrop-blur-*` utility classes are prohibited across all CSS and JSX files.
   - **Reason:** Blur filters force frequent browser compositing layer repaints, introducing noticeable scrolling stutter on mobile browsers.
3. **Zero Large Soft Corner Radii:**
   - **Rule:** Disallow `rounded-xl`, `rounded-2xl`, and `rounded-3xl`.
   - **Standard:** Use `rounded-sm`, `rounded`, `rounded-md`, or `rounded-lg`.
4. **Zero Heavy Drop Shadows:**
   - **Rule:** Disallow `shadow-lg`, `shadow-xl`, and `shadow-2xl`.
   - **Standard:** Rely on structural 1px borders (`border-line`) and `shadow-xs` / `shadow-sm`.
5. **Zero Emojis in Code & Locales:**
   - **Rule:** Disallow raw Unicode emojis in code, markup, and locale strings.
   - **Standard:** Use accessible, scalable SVG vector icons (`lucide-react` or custom inline SVGs) with semantic ARIA labels.
6. **Zero Em or En Dashes:**
   - **Rule:** Disallow Unicode em dash (`\u2014`) and en dash (`\u2013`) in user-facing copy.
   - **Standard:** Use regular ASCII hyphens (`-`) or semantic middle-dot bullets (`·` / `&middot;`).
7. **Zero Raw 12-Digit Identifier Exposure:**
   - **Rule:** Student APAAR and Aadhaar identifiers must always be masked (`****-****-0001`) in displays, tables, and copy clipboards via `sanitizeCopyPayload()`.

---

## 6. Component Standards

### 6.1 Buttons
- **Primary Action:** Solid `--app-brand` background, white ink, `rounded-md`, `font-medium`, `px-4 py-2`. Hover shifts to `--app-brand-deep`.
- **Accent CTA:** Solid `--app-accent` background, dark ink (`--app-on-accent`), `rounded-md`, `font-semibold`. Used for primary conversions (e.g. "Explore Demo", "Verify Credential").
- **Secondary / Outline:** Background `--app-surface`, border `1px solid var(--app-line)`, text `--app-ink`. Hover fills `--app-surface-2`.
- **Danger Action:** Solid `--app-danger` background, white ink. Used for destructive confirmations (e.g. "Revoke Credential", "Dismiss Case").
- **Ghost Action:** Transparent background, text `--app-muted`. Hover fills `--app-surface-2`.
- **Focus State:** `focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:outline-hidden`.

### 6.2 Form Inputs & Controls
- **Text / Number / Select:**
  - Background: `--app-surface`
  - Border: `1px solid var(--app-line)`
  - Radius: `rounded-md`
  - Padding: `px-3 py-2 text-sm`
  - Focus Ring: `focus:border-brand focus:ring-1 focus:ring-brand`
  - Error State: Border `--app-danger`, error caption rendered in `--app-danger` text below the input with `aria-invalid="true"`.
- **Masked APAAR Input:** 12-digit formatter that automatically formats inputs into `XXXX-XXXX-XXXX` blocks with instant checksum validation feedback.

### 6.3 Cards & Containers
- Clean container with background `--app-surface`, border `1px solid var(--app-line)`, and radius `rounded-lg`.
- Card Header: `border-b border-line px-5 py-4` with subtitle rendered in `--app-muted`.
- Card Body: `p-5`.
- Card Footer: `border-t border-line px-5 py-3 bg-surface-2`.

### 6.4 Data Tables
- Responsive wrapper with horizontal scroll (`overflow-x-auto`).
- `<thead>`: Background `--app-surface-2`, text `--app-muted`, uppercase caption font (`text-xs font-semibold tracking-wider`), border bottom `1px solid var(--app-line)`.
- `<tbody>`: Alternating row hover `--app-surface-3`, border bottom `1px solid var(--app-line)`.
- Cell Alignment: Numeric and code identifiers right-aligned or monospace; text left-aligned; status pills centered.

### 6.5 Modals & Dialogs
- Overlay: High-contrast backdrop `rgba(11, 20, 55, 0.6)`.
- Dialog Container: Background `--app-surface`, border `1px solid var(--app-line-strong)`, radius `rounded-lg`, max width `max-w-lg`.
- Accessibility: Focus trapped within dialog, `ESC` key dismisses, `aria-modal="true"`, autofocus placed on first interactive element.

### 6.6 Status Badges & Pills
- Shape: `rounded-full px-2.5 py-0.5 text-xs font-medium inline-flex items-center gap-1.5`.
- Status `VALID` / `ACTIVE`: Background `--app-success-surface`, text `--app-success`.
- Status `WARNING` / `PENDING`: Background `--app-warning-surface`, text `--app-warning`.
- Status `DANGER` / `REVOKED` / `ABSENT`: Background `--app-danger-surface`, text `--app-danger`.
- Status `NEUTRAL` / `INFO`: Background `--app-info-surface`, text `--app-info`.

### 6.7 Loading, Empty, and Error States
- **Loading:** Shimmering structural skeletons or crisp CSS spinners (`Spinner.jsx`); disallow layout shifts during async data resolution.
- **Empty State:** Centered card with descriptive vector icon, title in `--app-ink`, explanatory caption in `--app-muted`, and a prominent primary action button.
- **Error State:** Accessible alert banner with `--app-danger-surface` background, `--app-danger` border, clear recovery instruction, and optional retry button.

### 6.8 Student Academic Onboarding Wizard UX (`StudentAcademicSelectionWizard.jsx`)
- **Workflow:** 3-step contextual onboarding modal for students:
  - **Step 1 (Education Tier):** Dual card picker comparing "School Student" (K-12 Primary / Secondary / Higher Secondary) and "College / University Student" (UG / PG / Diploma / Engineering / Polytechnic) with prominent badge pills and high-contrast selection outlines.
  - **Step 2 (Academic Details):** Dynamic cascading dropdowns populated from `/api/auth/demo-academic-context`:
    - Institution search and selection filter.
    - *School mode:* Dynamic Class dropdown (populated from institution's real grade configuration, e.g. Class 8 through 12) + Section selector.
    - *College mode:* Dynamic Course/Program dropdown (e.g. B.Tech CSE, MCA, MBA) + Semester/Year selector.
  - **Step 3 (Confirmation & Launch):** Summary card displaying selected institution name, affiliation board/university, academic program/class, and semester before launching the persona session.
- **States:**
  - Loading: Centered `Spinner` while loading `/api/auth/demo-academic-context` options.
  - Error: Inline warning banner with retry CTA if network fails.
  - Submitting: Disabled inputs with animated "Entering Academic Dashboard..." button label.
- **Accessibility & Keyboard Navigation:**
  - Standard modal overlay with `Escape` key dismiss and backdrop click.
  - Explicit `aria-label` on all select controls.
  - Visible focus rings (`focus:ring-2 focus:ring-brand`).
- **Responsive Layout:**
  - Mobile (< 640px): Full-width stacked form controls with touch targets >= 44px.
  - Desktop (>= 640px): Centered modal dialog with two-column institution/course details.

### 6.9 Demo Persona Showcase & Indicator Tokens
- **One-Click Persona Grid:** Displayed on `LoginPage.jsx` and floating `DemoGuide.jsx`.
- **Supported Personas:** Student, Parent, Faculty (`teacher`), School Admin, College Admin, Directorate (`aicte_admin`).
- **Synthetic Data Label:** Mandatory warning pill rendered on all demo access interfaces: `"Synthetic demonstration data only. Verification is against this prototype database."`
- **Interactive Button Tokens:** `px-2 py-1.5 rounded border border-line bg-surface-2 hover:border-brand hover:bg-surface text-xs font-semibold text-ink`.

### 6.10 Institute ERP Administrative Tables & Workflows
- **Data Table Layout:** Paginated data tables wrapped in `bg-surface border border-line rounded-lg overflow-hidden`.
- **Header Rows:** `bg-surface-2 text-xs font-bold uppercase tracking-wider text-muted px-4 py-3 border-b border-line`.
- **Table Cells:** `px-4 py-3 text-sm text-ink border-b border-line/50 hover:bg-surface-2/40 transition-colors`.
- **Status Badges:** Pill-shaped status indicators (`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase`):
  - `VERIFIED` / `APPROVED`: `bg-success-surface text-success-strong`
  - `PENDING_REVIEW` / `UNDER_REVIEW`: `bg-accent-light text-accent-strong`
  - `REJECTED` / `SUSPENDED`: `bg-danger-surface text-danger-strong`
- **Review Queues:** Administrative action controls positioned on row actions with explicit modal confirmations.

---

## 7. Layout Standards & Multi-Form-Factor UX

### 7.1 Split-Hero Authentication Layout (`LoginPage.jsx`)
- `lg:grid lg:grid-cols-2 min-h-screen`:
  - **Left Showcase Panel:** Deep navy background (`--app-brand-deep`), white ink, displaying brand logo, security assurances (DPDP 2023, Ed25519 signatures), and live platform stats.
  - **Right Form Panel:** Warm ivory canvas (`--app-canvas`), rendering clean white login card (`--app-surface`), demo persona picker, and localized inputs.

### 7.2 Role-Based Dashboard Layout (`AppLayout.jsx`)
- **Header:** Sticky top header with brand lockup, active institution indicator, language switcher dropdown, theme toggle, and user profile avatar.
- **Navigation Bar / Drawer:** Role-scoped navigation pills linking to authorized sections.
- **Content Canvas:** Centered max-w-7xl area with responsive padding.
- **Footer:** Mandatory statutory disclaimer, link to Transparency Charter, and language selection.

### 7.3 Multi-Device Experience Standards
- **Mobile UX (< 640px):** Single-column stacked layouts, minimum touch targets >= `44px x 44px`, mobile navigation drawer, thumb-reachable bottom action sheets for attendance saving.
- **Tablet UX (640px - 1024px):** 2-column feature grids, adapted navigation drawer, compressed card layouts.
- **Desktop UX (>= 1024px):** 3-column feature grids, split-panel forms, full persistent horizontal menu navigation.
- **Android Platform:** Jetpack Compose with Material 3 token mapping matching `--app-*` tokens (`ChhatraLekhaTheme.kt`).
- **iOS Platform:** SwiftUI Asset Catalog Color Sets matching `--app-*` tokens with light/dark appearances.
- **Linux Desktop Considerations:** Standard DPI rendering, responsive web container scaling cleanly to institutional desktop monitors (1920x1080 and 1366x768).

---

## 8. UI Quality Review Checklist

Before approving any UI modification, verify:
- [ ] Theme switches cleanly between light and dark (`data-theme="dark"`) with no un-themed hex colors.
- [ ] Automated test `npm test -- frontend/src/test/DesignLint.test.jsx` passes with 0 violations.
- [ ] No raw APAAR/Aadhaar 12-digit numbers are rendered unmasked.
- [ ] Contrast ratio meets WCAG 2.1 AA (4.5:1 for normal text, 3:1 for large text/icons).
- [ ] Keyboard navigation: all interactive elements can be reached via `Tab` and show visible focus ring.
- [ ] Regional typography: text renders cleanly across Hindi, Odia, Tamil, Bengali, Telugu, and Urdu locales.

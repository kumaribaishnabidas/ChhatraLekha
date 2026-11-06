# ChhatraLekha - Design System Documentation
## Design Tokens, Component Standards & Accessibility Guidelines

**Version:** 2.0  
**Status:** Living Design System  
**Last Updated:** Stage 0.4  

---

### 1. Brand Identity & Visual Language

ChhatraLekha (छात्रलेखा) is the national digital academic identity and operations platform for India. Its visual language communicates security, authority, clarity, and accessibility across all 22 constitutional languages.

#### Official Logo & Brand Mark
- **Emblem:** Open academic book with a verified circular checkmark, dynamic orange arcs representing upward mobility and energy, crowned with an academic mortarboard cap.
- **Wordmark:** "ChhatraLekha" in deep navy and vibrant saffron orange with Devanagari "छात्रलेखा" sub-lockup.
- **Tagline Pill:** "Authenticate &middot; Verify &middot; Empower".

---

### 2. Color Palette & Semantic Tokens

All colors are implemented using CSS variables supporting automatic high-contrast theme switching (`[data-theme='light']` and `[data-theme='dark']`).

| Token Name | Light Theme Value | Dark Theme Value | Semantic Role |
| :--- | :--- | :--- | :--- |
| `--app-brand` | `#2f57d6` | `#5b7ff0` | Primary brand action, buttons, header |
| `--app-brand-deep` | `#16257a` | `#0b1437` | Deep navy background for split hero & side panels |
| `--app-brand-text` | `#1f3fbf` | `#8fa8ff` | Primary headings and emphasized names |
| `--app-accent` | `#ff8a00` | `#ff9a2e` | Vibrant saffron orange for primary CTAs |
| `--app-accent-strong` | `#c2410c` | `#ffb35c` | Emphasized orange text and borders |
| `--app-canvas` | `#fffff0` | `#0b1437` | Base application canvas (warm ivory in light mode) |
| `--app-surface` | `#ffffff` | `#121c4a` | Primary card background |
| `--app-surface-2` | `#fafaec` | `#17235a` | Secondary card background, table headers |
| `--app-surface-3` | `#f1f0dc` | `#1e2c6b` | Hover state and active background |
| `--app-ink` | `#16192b` | `#f5f3e8` | Primary text content |
| `--app-muted` | `#4a5160` | `#b7bcd6` | Subtitles, descriptive text, labels |
| `--app-line` | `#e4e2cc` | `#2a3980` | Subtle component dividers and card borders |
| `--app-line-strong` | `#c9c6a8` | `#3b4c9c` | Emphasized borders, device bezels |
| `--app-success` | `#0f7a44` | `#5ad07f` | Verification success, active attendance |
| `--app-warning` | `#b26a00` | `#f0b03a` | In-progress tasks, pending reviews |
| `--app-danger` | `#c62828` | `#ff8a80` | Quota breaches, errors, absent status |
| `--app-info` | `#4169e1` | `#90caf9` | Information notices, system bulletins |

---

### 3. Typography & Regional Script Font Stacks

To prevent broken glyphs or font misalignment across 22 regional languages, ChhatraLekha specifies dedicated Noto Sans font families:

- **Latin / General:** `'Noto Sans', 'Segoe UI', system-ui, -apple-system, sans-serif`
- **Devanagari (Hindi, Marathi, Sanskrit, Konkani, Bodo, Dogri, Maithili, Nepali):** `'Noto Sans Devanagari'`
- **Bengali & Assamese:** `'Noto Sans Bengali'`
- **Odia:** `'Noto Sans Oriya'`
- **Tamil:** `'Noto Sans Tamil'`
- **Telugu:** `'Noto Sans Telugu'`
- **Kannada:** `'Noto Sans Kannada'`
- **Malayalam:** `'Noto Sans Malayalam'`
- **Gujarati:** `'Noto Sans Gujarati'`
- **Gurmukhi (Punjabi):** `'Noto Sans Gurmukhi'`
- **Urdu & Kashmiri (Arabic Script, RTL):** `'Noto Nastaliq Urdu'`

---

### 4. Design Linter Constraints & Invariants

To maintain enterprise-grade design integrity and accessibility, all code must pass the automated `DesignLint.test.jsx` test suite enforcing the following rules:

1. **Zero Harsh Gradients (`bg-gradient`, `gradient-to-`):** Solid surfaces with subtle borders provide clearer contrast and faster rendering on low-power mobile devices.
2. **Zero `backdrop-blur` Classes:** Eliminates GPU rendering lag on budget smartphones commonly used by rural students and teachers.
3. **Zero Large Soft Corner Tokens (`rounded-xl`, `rounded-2xl`, `rounded-3xl`):** UI components strictly use crisp structural radii: `rounded-sm`, `rounded`, `rounded-md`, `rounded-lg`, and `rounded-full` (for badges and circular progress).
4. **Zero Heavy Drop Shadows (`shadow-lg`, `shadow-xl`, `shadow-2xl`):** Replaced with crisp 1px borders (`border border-line`) and subtle ambient shadows (`shadow-xs`, `shadow-sm`).
5. **Zero Emojis in Source Code and Locales:** Replaced with accessible SVG vector icons and text labels to avoid platform-dependent emoji rendering discrepancies.
6. **Zero Unicode Em Dashes (`\u2014`) or En Dashes (`\u2013`):** Replaced with standard keyboard hyphens (`-`) or semantic separators (`&middot;`) to prevent encoding corruptions in regional text renderers.
7. **Zero Raw APAAR ID Exposure:** 12-digit student identifiers must always be masked (`****-****-0001`) in UI displays and public URLs.

---

### 5. Layout Architecture & Responsive Breakpoints

- **Mobile (< 640px):** Single-column stacked layouts, touch targets >= 44px, sticky header with mobile navigation drawer.
- **Tablet (640px - 1024px):** 2-column feature grids, adapted navigation drawer, compressed card layouts.
- **Desktop (>= 1024px):**
  - Split-panel two-column authentication layouts (`grid lg:grid-cols-2`). Left panel showcases brand identity and security guarantees; right panel renders clean card-based interaction forms.
  - 3-column feature grids and structured product previews.
  - Sticky navigation header with full horizontal menu, theme toggle, language switcher, and action buttons.


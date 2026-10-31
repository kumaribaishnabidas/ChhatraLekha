# Translation review register

ChhatraLekha's browser keeps English as the source locale. `npm run i18n:check`
requires every locale to have exactly the English key set and the same
`{{placeholder}}` names; it does **not** certify linguistic quality.

## Status

| Language | Code | Structural coverage | Status | Native reviewer | Review date |
|---|---:|---:|---|---|---|
| English | `en` | 100% | source locale | — | — |
| Hindi | `hi` | 100% | **draft, needs native-speaker review** | unassigned | — |
| Bengali | `bn` | 100% | **draft, needs native-speaker review** | unassigned | — |
| Tamil | `ta` | 100% | **draft, needs native-speaker review** | unassigned | — |
| Telugu | `te` | 100% | **draft, needs native-speaker review** | unassigned | — |
| Marathi | `mr` | 100% | **draft, needs native-speaker review** | unassigned | — |
| Gujarati | `gu` | 100% | Tier 2 draft / fallback text, needs translation and review | unassigned | — |
| Kannada | `kn` | 100% | Tier 2 draft / fallback text, needs translation and review | unassigned | — |
| Malayalam | `ml` | 100% | Tier 2 draft / fallback text, needs translation and review | unassigned | — |
| Punjabi | `pa` | 100% | Tier 2 draft / fallback text, needs translation and review | unassigned | — |
| Odia | `or` | 100% | Tier 2 draft / fallback text, needs translation and review | unassigned | — |
| Assamese | `as` | 100% | Tier 2 draft / fallback text, needs translation and review | unassigned | — |
| Urdu (RTL) | `ur` | 100% | **draft, needs native-speaker review** | unassigned | — |

“Structural coverage” means that the automated key/placeholder checker passes.
It is intentionally not a claim that every sentence is already translated or
approved. The picker labels every non-English locale **Beta** until a named
native reviewer signs off.

## Priority legal and verdict terms

A reviewer must inspect these before a locale loses its Beta label:

* **Valid / verified**
* **Could not be verified / invalid**
* **Revoked**
* **Expired**
* **Needs refresh / reissue**
* **Consent withdrawn / personal fields withheld**
* **Verification against this prototype's database, not official APAAR or
  AICTE verification**

## Review checklist

1. Check every string in context at narrow and wide browser widths.
2. Verify legal/verdict terms above with the institution's approved wording.
3. Check plural forms, numbers and dates with the native locale.
4. Test screen-reader labels and voice commands with native speakers.
5. For Urdu, verify `dir="rtl"`, icon placement and mixed APAAR/Latin labels.
6. Add reviewer and date to this table; only then change the registry status.

## Adding a locale

1. Copy `frontend/src/i18n/locales/en/common.json` to
   `frontend/src/i18n/locales/<code>/common.json` and translate it.
2. Add one registry entry and resource import in `frontend/src/i18n/index.js`.
3. Add an on-demand Noto font mapping if its script needs one.
4. Run `npm run i18n:check`, then complete the review checklist.

The Android `values-*` folders are also drafts until native review; their
current strings cover the system-visible and Settings copy.

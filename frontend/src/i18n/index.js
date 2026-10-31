/**
 * The client-side translation registry.
 *
 * Locale JSON files contain the same key shape as English. English is always
 * the source/fallback. Adding a language means adding its JSON file and one
 * entry to `LANGUAGES`; `npm run i18n:check` enforces the contract.
 */
import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'

import en from './locales/en/common.json'
import hi from './locales/hi/common.json'
import bn from './locales/bn/common.json'
import ta from './locales/ta/common.json'
import te from './locales/te/common.json'
import mr from './locales/mr/common.json'
import gu from './locales/gu/common.json'
import kn from './locales/kn/common.json'
import ml from './locales/ml/common.json'
import pa from './locales/pa/common.json'
import or from './locales/or/common.json'
import as from './locales/as/common.json'
import ur from './locales/ur/common.json'

export const LANGUAGES = [
  { code: 'en', bcp47: 'en-IN', dir: 'ltr', font: 'Noto Sans', review: 'source' },
  { code: 'hi', bcp47: 'hi-IN', dir: 'ltr', font: 'Noto Sans Devanagari', review: 'beta' },
  { code: 'bn', bcp47: 'bn-IN', dir: 'ltr', font: 'Noto Sans Bengali', review: 'beta' },
  { code: 'ta', bcp47: 'ta-IN', dir: 'ltr', font: 'Noto Sans Tamil', review: 'beta' },
  { code: 'te', bcp47: 'te-IN', dir: 'ltr', font: 'Noto Sans Telugu', review: 'beta' },
  { code: 'mr', bcp47: 'mr-IN', dir: 'ltr', font: 'Noto Sans Devanagari', review: 'beta' },
  { code: 'gu', bcp47: 'gu-IN', dir: 'ltr', font: 'Noto Sans Gujarati', review: 'beta', tier: 2 },
  { code: 'kn', bcp47: 'kn-IN', dir: 'ltr', font: 'Noto Sans Kannada', review: 'beta', tier: 2 },
  { code: 'ml', bcp47: 'ml-IN', dir: 'ltr', font: 'Noto Sans Malayalam', review: 'beta', tier: 2 },
  { code: 'pa', bcp47: 'pa-IN', dir: 'ltr', font: 'Noto Sans Gurmukhi', review: 'beta', tier: 2 },
  { code: 'or', bcp47: 'or-IN', dir: 'ltr', font: 'Noto Sans Oriya', review: 'beta', tier: 2 },
  { code: 'as', bcp47: 'as-IN', dir: 'ltr', font: 'Noto Sans Bengali', review: 'beta', tier: 2 },
  { code: 'ur', bcp47: 'ur-IN', dir: 'rtl', font: 'Noto Nastaliq Urdu', review: 'beta', tier: 2 },
]

export const LANGUAGE_BY_CODE = Object.fromEntries(LANGUAGES.map((item) => [item.code, item]))

/**
 * Complete list of all 22 languages in the Eighth Schedule of the Indian Constitution.
 * Languages active in Phase 1-4 are flagged with active: true; Phase 5 expansion languages
 * are mapped with their respective script, direction, and rollout status.
 */
export const ALL_SCHEDULED_LANGUAGES_22 = [
  { code: 'as', name: 'Assamese', nativeName: 'অসমীয়া', script: 'Bengali-Assamese', active: true },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', script: 'Bengali', active: true },
  { code: 'brx', name: 'Bodo', nativeName: 'बर’', script: 'Devanagari', active: false },
  { code: 'doi', name: 'Dogri', nativeName: 'डोगरी', script: 'Devanagari', active: false },
  { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', script: 'Gujarati', active: true },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', script: 'Devanagari', active: true },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', script: 'Kannada', active: true },
  { code: 'ks', name: 'Kashmiri', nativeName: 'کٲشُر', script: 'Perso-Arabic', dir: 'rtl', active: false },
  { code: 'kok', name: 'Konkani', nativeName: 'कोंकणी', script: 'Devanagari', active: false },
  { code: 'mai', name: 'Maithili', nativeName: 'मैथिली', script: 'Devanagari', active: false },
  { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', script: 'Malayalam', active: true },
  { code: 'mni', name: 'Manipuri', nativeName: 'ꯃꯤꯇꯩꯂꯣꯟ', script: 'Meitei Mayek', active: false },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', script: 'Devanagari', active: true },
  { code: 'ne', name: 'Nepali', nativeName: 'नेपाली', script: 'Devanagari', active: false },
  { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ', script: 'Odia', active: true },
  { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', script: 'Gurmukhi', active: true },
  { code: 'sa', name: 'Sanskrit', nativeName: 'संस्कृतम्', script: 'Devanagari', active: false },
  { code: 'sat', name: 'Santali', nativeName: 'ᱥᱟᱱᱛᱟᱲᱤ', script: 'Ol Chiki', active: false },
  { code: 'sd', name: 'Sindhi', nativeName: 'سنڌي', script: 'Perso-Arabic', dir: 'rtl', active: false },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', script: 'Tamil', active: true },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', script: 'Telugu', active: true },
  { code: 'ur', name: 'Urdu', nativeName: 'اردو', script: 'Perso-Arabic', dir: 'rtl', active: true },
]

const resources = {
  en: { common: en }, hi: { common: hi }, bn: { common: bn }, ta: { common: ta },
  te: { common: te }, mr: { common: mr }, gu: { common: gu }, kn: { common: kn },
  ml: { common: ml }, pa: { common: pa }, or: { common: or }, as: { common: as }, ur: { common: ur },
}

/** Load only the script face that the selected locale needs. */
const fontImports = {
  en: () => import('@fontsource/noto-sans/latin-400.css'),
  hi: () => import('@fontsource/noto-sans-devanagari/devanagari-400.css'),
  mr: () => import('@fontsource/noto-sans-devanagari/devanagari-400.css'),
  bn: () => import('@fontsource/noto-sans-bengali/bengali-400.css'),
  as: () => import('@fontsource/noto-sans-bengali/bengali-400.css'),
  ta: () => import('@fontsource/noto-sans-tamil/tamil-400.css'),
  te: () => import('@fontsource/noto-sans-telugu/telugu-400.css'),
  gu: () => import('@fontsource/noto-sans-gujarati/gujarati-400.css'),
  kn: () => import('@fontsource/noto-sans-kannada/kannada-400.css'),
  ml: () => import('@fontsource/noto-sans-malayalam/malayalam-400.css'),
  pa: () => import('@fontsource/noto-sans-gurmukhi/gurmukhi-400.css'),
  or: () => import('@fontsource/noto-sans-oriya/oriya-400.css'),
  ur: () => import('@fontsource/noto-nastaliq-urdu/arabic-400.css'),
}

function normaliseLanguage(language) {
  const code = String(language || '').toLowerCase().split('-')[0]
  return LANGUAGE_BY_CODE[code] ? code : 'en'
}

export function applyLocale(language) {
  const code = normaliseLanguage(language)
  const locale = LANGUAGE_BY_CODE[code]
  const root = document.documentElement
  root.lang = code
  root.dir = locale.dir
  root.style.setProperty('--app-font-sans', `'${locale.font}', 'Noto Sans', 'Segoe UI', system-ui, sans-serif`)
  fontImports[code]?.().catch(() => {
    // The operating system fallback remains usable if a font chunk fails.
  })
  return locale
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    supportedLngs: LANGUAGES.map((item) => item.code),
    ns: ['common'],
    defaultNS: 'common',
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'chhatralekha.language',
      caches: ['localStorage'],
    },
    react: { useSuspense: false },
  })

applyLocale(i18n.language)
i18n.on('languageChanged', applyLocale)

export default i18n

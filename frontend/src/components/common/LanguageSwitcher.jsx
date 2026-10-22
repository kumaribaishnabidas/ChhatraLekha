import { useTranslation } from 'react-i18next'

import { LANGUAGES } from '../../i18n'

/** An accessible, persistent language picker. */
export default function LanguageSwitcher({ variant = 'header' }) {
  const { i18n, t } = useTranslation()
  const current = i18n.resolvedLanguage || i18n.language || 'en'

  return (
    <label className={variant === 'header' ? 'sr-only sm:not-sr-only sm:flex sm:items-center' : 'flex items-center gap-2 text-sm text-muted'}>
      <span className={variant === 'header' ? 'sr-only' : ''}>{t('settings.language')}</span>
      <select
        aria-label={t('settings.language')}
        value={current}
        onChange={(event) => i18n.changeLanguage(event.target.value)}
        className={
          variant === 'header'
            ? 'max-w-28 rounded-lg border border-[var(--app-header-line)] bg-[var(--app-header-hover)] px-2 py-1.5 text-xs font-semibold text-white cursor-pointer'
            : 'input max-w-56 py-2'
        }
      >
        {LANGUAGES.map((language) => (
          <option key={language.code} value={language.code} className="text-ink bg-surface">
            {t(`language.${language.code}`)}{language.review === 'beta' ? ` (${t('common.beta')})` : ''}
          </option>
        ))}
      </select>
    </label>
  )
}

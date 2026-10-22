import { useTranslation } from 'react-i18next'

/** Opens the optional, privacy-gated voice panel. */
export default function VoiceButton({ onClick }) {
  const { t } = useTranslation()
  return (
    <button type="button" className="rounded-full border border-[var(--app-header-line)] bg-[var(--app-header-hover)] p-2 text-white cursor-pointer" onClick={onClick} aria-label={t('voice.open')} title={t('voice.open')}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3" stroke="currentColor" strokeWidth="1.8"/><path d="M6 11a6 6 0 0 0 12 0M12 17v4M8 21h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
    </button>
  )
}

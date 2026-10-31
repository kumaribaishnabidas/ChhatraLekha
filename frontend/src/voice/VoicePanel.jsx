import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { LANGUAGE_BY_CODE } from '../i18n'
import { useTheme } from '../context/ThemeContext'
import { api } from '../services/api'
import { formatNumber } from '../utils/format'
import { matchIntent } from './intents'
import { useSpeechRecognition } from './useSpeechRecognition'
import { useSpeechSynthesis } from './useSpeechSynthesis'

const CONSENT_KEY = 'chhatralekha.voice.consent'
const ROUTES = { 'navigate.dashboard': '/dashboard', 'navigate.institutions': '/institutions', 'navigate.students': '/students', 'navigate.anomalies': '/anomalies', 'navigate.reports': '/reports', 'navigate.impact': '/impact', 'navigate.verify': '/verify' }

function voiceConsent() { try { return localStorage.getItem(CONSENT_KEY) === 'true' } catch { return false } }

/**
 * Fixed-catalogue voice assistant. It navigates and reads API statistics but
 * has no path for correction, review, token revocation or any other mutation.
 */
export default function VoicePanel({ onClose }) {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { setTheme } = useTheme()
  const language = LANGUAGE_BY_CODE[i18n.resolvedLanguage || i18n.language]?.bcp47 || 'en-IN'
  const [consented, setConsented] = useState(voiceConsent)
  const [message, setMessage] = useState('')
  const recognition = useSpeechRecognition(language)
  const synthesis = useSpeechSynthesis(language)

  const announce = (text) => { setMessage(text); synthesis.speak(text) }
  const enable = () => { try { localStorage.setItem(CONSENT_KEY, 'true') } catch {} setConsented(true) }

  const dispatch = async (spoken) => {
    const intent = matchIntent(spoken, (i18n.resolvedLanguage || i18n.language || 'en').split('-')[0])
    if (!intent) return announce(`${t('voice.notUnderstood')} ${t('voice.commands')}`)
    if (intent === 'stop') { synthesis.stop(); return setMessage(t('voice.stopCommand')) }
    if (ROUTES[intent]) { navigate(ROUTES[intent]); return announce(t('nav.' + ROUTES[intent].slice(1).replace('impact', 'impact').replace('verify', 'verify'))) }
    if (intent === 'theme.dark') { setTheme('dark'); return announce(t('settings.theme.dark')) }
    if (intent === 'theme.light') { setTheme('light'); return announce(t('settings.theme.light')) }
    if (intent === 'help') return announce(t('voice.commands'))
    try {
      if (intent === 'tasks.open') {
        const { data } = await api.get('/review-tasks', { params: { limit: 100 } })
        return announce(`${(data || []).filter((task) => task.status === 'open').length} ${t('impact.reviewChecklist')}`)
      }
      const { data } = await api.get('/dashboard/national')
      const value = intent === 'dashboard.students' ? data.total_enrolled : data.flagged_anomalies
      return announce(formatNumber(value))
    } catch { return announce(t('errors.server')) }
  }

  return (
    <aside className="fixed end-4 top-20 z-50 w-[min(25rem,calc(100vw-2rem))] card p-4" aria-label={t('voice.title')}>
      <div className="flex items-center justify-between gap-3"><h2 className="m-0 text-base">{t('voice.title')}</h2><button type="button" className="btn btn-ghost px-2 py-1" onClick={onClose}>{t('common.close')}</button></div>
      {!consented ? (
        <div className="mt-3"><h3 className="text-sm">{t('voice.privacyTitle')}</h3><p className="text-sm text-muted">{t('voice.privacy')}</p><div className="flex flex-wrap gap-2"><button type="button" className="btn btn-navy" onClick={enable}>{t('voice.allow')}</button><button type="button" className="btn btn-outline" onClick={onClose}>{t('voice.decline')}</button></div></div>
      ) : !recognition.supported ? <p role="status" className="mt-3 text-sm text-warning-strong">{t('voice.unsupported')}</p> : (
        <div className="mt-3"><p aria-live="polite" className="min-h-6 text-sm text-muted">{recognition.state === 'listening' ? t('voice.listening') : recognition.error ? t(`voice.${recognition.error}`) : message || recognition.transcript}</p><div className="flex gap-2"><button type="button" className="btn btn-navy" onClick={() => recognition.state === 'listening' ? recognition.stop() : recognition.start(dispatch)}>{recognition.state === 'listening' ? t('voice.stop') : t('voice.start')}</button><button type="button" className="btn btn-outline" onClick={() => announce(t('voice.commands'))}>{t('voice.whatCanAsk')}</button></div>{synthesis.notice && <p className="text-xs text-warning-strong" role="status">{t(`voice.${synthesis.notice}`, { language })}</p>}</div>
      )}
    </aside>
  )
}

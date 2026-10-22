import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { useTranslation } from 'react-i18next'

import ThemeToggle from '../components/common/ThemeToggle'
import { ThemeProvider } from '../context/ThemeContext'
import i18n from '../i18n'
import { errorMessage } from '../services/api'
import { matchIntent } from '../voice/intents'

function Controls() {
  const { t } = useTranslation()
  return <><ThemeToggle variant="surface" /><p>{t('nav.dashboard')}</p></>
}

describe('theme, locale and deterministic voice', () => {
  it('persists a selected dark theme', async () => {
    render(<ThemeProvider><Controls /></ThemeProvider>)
    await userEvent.setup().click(screen.getByTitle('Dark'))
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(window.localStorage.getItem('edusync.theme')).toBe('dark')
  })

  it('changes language and html direction', async () => {
    await i18n.changeLanguage('hi')
    render(<Controls />)
    await waitFor(() => expect(screen.getByText('डैशबोर्ड')).toBeInTheDocument())
    expect(document.documentElement.lang).toBe('hi')
    await i18n.changeLanguage('ur')
    expect(document.documentElement.dir).toBe('rtl')
    await i18n.changeLanguage('en')
  })

  it('maps stable HTTP errors without parsing the backend English message', () => {
    const t = vi.fn((key) => key)
    expect(errorMessage({ response: { status: 403, data: { detail: 'English only' } } }, 'fallback', t)).toBe('errors.forbidden')
  })

  it('matches fixed English and Hindi commands and rejects unknown speech', () => {
    expect(matchIntent('open dashboard', 'en')).toBe('navigate.dashboard')
    expect(matchIntent('डैशबोर्ड खोलें', 'hi')).toBe('navigate.dashboard')
    expect(matchIntent('apply correction now', 'en')).toBeNull()
  })
})

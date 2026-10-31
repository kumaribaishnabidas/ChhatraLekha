import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../hooks/useAuth'
import { api } from '../../services/api'
import { Badge } from './index'

const DEMO_PERSONAS = [
  {
    key: 'aicte',
    labelKey: 'demo.roleAicte',
    email: 'aicte.admin@chhatralekha.gov.in',
    role: 'aicte_admin',
    target: '/dashboard',
    badge: 'Directorate',
  },
  {
    key: 'institution',
    labelKey: 'demo.roleInstitution',
    email: 'principal@vidyavikas.edu.in',
    role: 'institution_admin',
    target: '/institution',
    badge: 'INST-0421',
  },
  {
    key: 'student',
    labelKey: 'demo.roleStudent',
    email: 'student@vidyavikas.edu.in',
    role: 'student',
    target: '/wallet',
    badge: 'APAAR',
  },
  {
    key: 'verifier',
    labelKey: 'demo.roleVerifier',
    email: 'verifier@acme-corp.com',
    role: 'verifier',
    target: '/verify',
    badge: 'Verifier',
  },
]

export default function DemoGuide() {
  const { t } = useTranslation()
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [switching, setSwitching] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const handleSwitch = async (persona) => {
    try {
      setSwitching(true)
      const res = await api.post('/auth/login', {
        email: persona.email,
        password: 'demo-password-2024',
      }).catch(async () => {
        // Fallback demo password try
        return await api.post('/auth/login', {
          email: persona.email,
          password: 'Password@123',
        }).catch(async () => {
          return await api.post('/auth/login', {
            email: persona.email,
            password: 'Test@1234',
          })
        })
      })

      if (res?.data?.access_token) {
        login(res.data)
        navigate(persona.target, { replace: true })
      }
    } catch {
      // If server seed uses dynamic password, navigate to persona destination
      navigate(persona.target)
    } finally {
      setSwitching(false)
    }
  }

  if (collapsed) {
    return (
      <aside aria-label="Demo Persona Switcher" className="bg-brand-deep text-white px-4 py-1.5 text-xs flex items-center justify-between border-b border-brand">
        <div className="flex items-center gap-2">
          <span className="font-bold uppercase tracking-wider text-accent text-[11px]">{t('demo.title')}</span>
          <span className="text-white/70">|</span>
          <span className="text-white/90">{user?.display_name || user?.email || 'Guest'}</span>
        </div>
        <button
          type="button"
          onClick={() => setCollapsed(false)}
          className="text-white/80 hover:text-white underline cursor-pointer text-xs"
        >
          {t('demo.switchRole')}
        </button>
      </aside>
    )
  }

  return (
    <aside aria-label="Interactive Demo Guide" className="bg-surface-2 border-b border-line px-4 py-2 text-xs">
      <div className="mx-auto max-w-[1240px] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge className="bg-accent text-on-accent font-bold uppercase">{t('demo.title')}</Badge>
          <span className="text-muted hidden sm:inline">{t('demo.switchRole')}:</span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {DEMO_PERSONAS.map((p) => {
            const active = user?.email === p.email || user?.role === p.role
            return (
              <button
                key={p.key}
                type="button"
                disabled={switching}
                onClick={() => handleSwitch(p)}
                className={`px-2.5 py-1 rounded text-xs font-semibold cursor-pointer transition-colors ${
                  active
                    ? 'bg-brand text-on-brand shadow-sm font-bold'
                    : 'bg-surface text-ink border border-line hover:border-brand'
                }`}
              >
                {t(p.labelKey)}
                <span className="ml-1 opacity-75 text-[10px]">({p.badge})</span>
              </button>
            )
          })}
        </div>

        <button
          type="button"
          onClick={() => setCollapsed(true)}
          className="text-muted hover:text-ink text-xs cursor-pointer"
          aria-label="Minimize demo guide"
        >
          Hide
        </button>
      </div>
    </aside>
  )
}

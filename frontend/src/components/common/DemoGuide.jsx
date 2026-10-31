import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../hooks/useAuth'
import { api } from '../../services/api'
import { Badge } from './index'

export const DEMO_PERSONAS = [
  {
    key: 'student',
    role_key: 'student',
    label: 'Student',
    email: 'student.demo@example.com',
    role: 'student',
    target: '/me',
    badge: 'Student ID',
  },
  {
    key: 'parent',
    role_key: 'parent',
    label: 'Parent',
    email: 'parent.demo@example.com',
    role: 'parent',
    target: '/parent',
    badge: 'Parent Portal',
  },
  {
    key: 'teacher',
    role_key: 'teacher',
    label: 'Teacher',
    email: 'teacher.demo@example.com',
    role: 'teacher',
    target: '/teacher',
    badge: 'Faculty',
  },
  {
    key: 'school_admin',
    role_key: 'school_admin',
    label: 'School Admin',
    email: 'schooladmin.demo@example.com',
    role: 'institution_admin',
    target: '/institution',
    badge: 'School',
  },
  {
    key: 'college_admin',
    role_key: 'college_admin',
    label: 'College Admin',
    email: 'collegeadmin.demo@example.com',
    role: 'institution_admin',
    target: '/institution',
    badge: 'College',
  },
  {
    key: 'university_admin',
    role_key: 'university_admin',
    label: 'University Admin',
    email: 'universityadmin.demo@example.com',
    role: 'aicte_admin',
    target: '/dashboard',
    badge: 'National',
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
      // First attempt dedicated instant demo session endpoint
      const res = await api.post('/auth/demo-login', {
        role: persona.role_key,
      }).catch(async () => {
        // Fallback to standard login
        return await api.post('/auth/login', {
          email: persona.email,
          password: 'Password@123',
        }).catch(async () => {
          return await api.post('/auth/login', {
            email: persona.email,
            password: 'ChhatraLekha2026!',
          })
        })
      })

      if (res?.data?.access_token) {
        login(res.data)
        navigate(persona.target, { replace: true })
      }
    } catch {
      // If server seed uses dynamic session, navigate to persona destination
      navigate(persona.target)
    } finally {
      setSwitching(false)
    }
  }

  if (collapsed) {
    return (
      <aside aria-label="Demo Persona Switcher" className="w-full bg-brand-deep text-white px-4 py-1.5 text-xs flex items-center justify-between border-b border-brand">
        <div className="flex items-center gap-2">
          <span className="font-bold uppercase tracking-wider text-accent text-[11px]">{t('demo.title')}</span>
          <span className="text-white/70">|</span>
          <span className="text-white/90">{user?.display_name || user?.email || 'Guest'}</span>
          <span className="rounded bg-accent/20 text-accent px-1.5 py-0.5 text-[10px] font-bold">DEMO MODE</span>
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
    <aside aria-label="Interactive Demo Guide" className="w-full bg-surface-2 border-b border-line px-4 py-2 text-xs">
      <div className="w-full flex flex-wrap items-center justify-between gap-3 px-2">
        <div className="flex items-center gap-2">
          <Badge className="bg-accent text-on-accent font-bold uppercase">{t('demo.title')}</Badge>
          <span className="text-muted hidden sm:inline">{t('demo.switchRole')}:</span>
          <span className="rounded bg-accent/15 text-accent-strong border border-accent/30 px-1.5 py-0.5 text-[10px] font-bold">
            DEMO DATA
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {DEMO_PERSONAS.map((p) => {
            const active = user?.email === p.email || (user?.role === p.role && (p.role !== 'institution_admin' || user?.institution_id === p.email.includes('school') ? 'SCH-DEL-001' : 'INST-0421'))
            return (
              <button
                key={p.key}
                type="button"
                disabled={switching}
                onClick={() => handleSwitch(p)}
                className={`px-2.5 py-1 rounded text-xs font-semibold cursor-pointer transition-colors ${
                  active
                    ? 'bg-brand text-on-brand shadow-xs font-bold'
                    : 'bg-surface text-ink border border-line hover:border-brand'
                }`}
              >
                {p.label}
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

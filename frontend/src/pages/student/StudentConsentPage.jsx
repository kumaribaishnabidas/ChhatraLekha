import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../../hooks/usePageMeta'
import { api, errorMessage } from '../../services/api'
import { Card, Badge, Table } from '../../components/common'

const PURPOSE_META = {
  CREDENTIAL_VERIFICATION: {
    title: 'Credential Verification',
    description: 'Allows universities, scholarship bodies, and verifiers to check your academic standing.',
    revokedWarning: 'If revoked, external verification scans will be unable to confirm your enrolled credentials.',
  },
  DATA_SHARING_WITH_EMPLOYER: {
    title: 'Employment Background Checks',
    description: 'Permits prospective employers and recruiting platforms to verify your degrees and marksheets.',
    revokedWarning: 'If revoked, job background check services cannot verify your educational certificates.',
  },
  RESEARCH: {
    title: 'Academic & Educational Research',
    description: 'Allows anonymised academic progression analytics for research and curriculum improvement.',
    revokedWarning: 'If revoked, your academic data will be completely excluded from all research cohorts.',
  },
  ANALYTICS_AND_REPORTING: {
    title: 'Regulatory Reporting',
    description: 'Statutory compliance tracking and seat matrix auditing by regulatory bodies.',
    revokedWarning: 'Statutory reporting is mandated for active AICTE-approved institution enrolments.',
  },
}

export default function StudentConsentPage() {
  const { t } = useTranslation()
  usePageMeta({
    title: t('student.consent.title', { defaultValue: 'Consent Centre' }),
    description: 'Manage your academic privacy and purpose-wise verification permissions with complete ledger transparency.',
  })

  const [consentData, setConsentData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(null)
  const [error, setError] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  const fetchConsent = async () => {
    try {
      setLoading(true)
      setError('')
      const { data } = await api.get('/me/consent')
      setConsentData(data)
    } catch (err) {
      setError(errorMessage(err, 'Unable to load consent preferences.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConsent()
  }, [])

  const handleToggle = async (purpose, currentStatus) => {
    const nextStatus = currentStatus === 'GRANTED' ? 'REVOKED' : 'GRANTED'
    try {
      setUpdating(purpose)
      setError('')
      setSuccessMsg('')
      await api.post('/me/consent', { purpose, status: nextStatus })
      setSuccessMsg(`Consent for ${purpose} updated to ${nextStatus}.`)
      fetchConsent()
    } catch (err) {
      setError(errorMessage(err, 'Failed to update consent.'))
    } finally {
      setUpdating(null)
    }
  }

  return (
    <div className="mx-auto max-w-[1200px] px-5 py-8 space-y-8">
      <div>
        <h1 className="m-0 text-2xl font-black text-brand-deep sm:text-3xl">
          {t('student.consent.header', { defaultValue: 'Academic Privacy & Consent Centre' })}
        </h1>
        <p className="m-0 mt-1 text-sm text-muted">
          {t('student.consent.subHeader', { defaultValue: 'Under Digital Personal Data Protection principles, you control how your academic credentials are used and shared.' })}
        </p>
      </div>

      {error && (
        <Card className="border-danger/30 bg-danger/5 p-4 text-xs font-semibold text-danger">
          {error}
        </Card>
      )}

      {successMsg && (
        <Card className="border-success/30 bg-success/5 p-4 text-xs font-semibold text-success-strong">
          {successMsg}
        </Card>
      )}

      {/* Purpose Cards Grid */}
      <div className="grid gap-6 sm:grid-cols-2">
        {loading ? (
          [1, 2, 3, 4].map((i) => (
            <div key={i} className="h-44 rounded-lg bg-surface-2 animate-pulse" />
          ))
        ) : (
          (consentData?.purposes || []).map((item) => {
            const meta = PURPOSE_META[item.purpose] || {
              title: item.label,
              description: item.reason,
              revokedWarning: 'Permission is currently revoked.',
            }
            const isGranted = item.status === 'GRANTED'

            return (
              <Card key={item.purpose} className="flex flex-col justify-between p-6 space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="m-0 text-base font-bold text-ink">{meta.title}</h3>
                    <Badge variant={isGranted ? 'success' : 'danger'}>
                      {item.status}
                    </Badge>
                  </div>
                  <p className="m-0 text-xs text-muted leading-relaxed">
                    {meta.description}
                  </p>
                </div>

                <div className="space-y-3 pt-2 border-t border-line">
                  {!isGranted && (
                    <p className="m-0 text-[11px] font-semibold text-warning-strong bg-warning/10 border border-warning/30 rounded p-2">
                      {meta.revokedWarning}
                    </p>
                  )}

                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-ink">
                      {isGranted ? 'Status: Allowed' : 'Status: Revoked'}
                    </span>
                    <button
                      type="button"
                      disabled={updating === item.purpose}
                      onClick={() => handleToggle(item.purpose, item.status)}
                      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        isGranted ? 'bg-brand' : 'bg-line'
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          isGranted ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </Card>
            )
          })
        )}
      </div>

      {/* Consent Ledger History */}
      <div className="space-y-4">
        <h2 className="m-0 text-lg font-black text-brand-deep">
          {t('student.consent.ledgerHeader', { defaultValue: 'Consent Audit Ledger History' })}
        </h2>

        {loading ? (
          <div className="h-32 rounded-lg bg-surface-2 animate-pulse" />
        ) : (consentData?.history || []).length === 0 ? (
          <Card className="p-8 text-center text-muted text-sm">
            {t('student.consent.emptyHistory', { defaultValue: 'No consent modifications logged yet.' })}
          </Card>
        ) : (
          <Table
            headers={['Purpose', 'Action', 'Channel', 'Timestamp']}
            rows={(consentData?.history || []).map((h, idx) => [
              <span key={`p-${idx}`} className="font-semibold text-ink text-xs">{h.purpose}</span>,
              <Badge key={`s-${idx}`} variant={h.status === 'GRANTED' ? 'success' : 'danger'}>
                {h.status}
              </Badge>,
              <code key={`c-${idx}`} className="text-xs font-mono">{h.channel}</code>,
              new Date(h.timestamp).toLocaleString(),
            ])}
          />
        )}
      </div>
    </div>
  )
}


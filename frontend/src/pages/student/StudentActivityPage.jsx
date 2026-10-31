import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../../hooks/usePageMeta'
import { api, errorMessage } from '../../services/api'
import { Card, Badge, Table } from '../../components/common'

export default function StudentActivityPage() {
  const { t } = useTranslation()
  usePageMeta({
    title: t('student.activity.title', { defaultValue: 'Audit & Activity Timeline' }),
    description: 'Immutable chronological record of academic identity events, verifications, and permissions.',
  })

  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadActivity() {
      try {
        setLoading(true)
        setError('')
        const { data } = await api.get('/me/activity')
        setActivities(Array.isArray(data) ? data : data?.events || data?.activity || [])
      } catch (err) {
        setError(errorMessage(err, 'Unable to load activity logs.'))
      } finally {
        setLoading(false)
      }
    }
    loadActivity()
  }, [])

  return (
    <div className="mx-auto max-w-[1200px] px-5 py-8 space-y-8">
      <div>
        <h1 className="m-0 text-2xl font-black text-brand-deep sm:text-3xl">
          {t('student.activity.header', { defaultValue: 'Academic Identity Audit Trail' })}
        </h1>
        <p className="m-0 mt-1 text-sm text-muted">
          {t('student.activity.subHeader', { defaultValue: 'Every credential issuance, verification scan, share creation, and consent update is recorded in the cryptographically chained audit log.' })}
        </p>
      </div>

      {error && (
        <Card className="border-danger/30 bg-danger/5 p-4 text-xs font-semibold text-danger">
          {error}
        </Card>
      )}

      {loading ? (
        <div className="h-64 rounded-lg bg-surface-2 animate-pulse" />
      ) : activities.length === 0 ? (
        <Card className="p-8 text-center text-muted text-sm">
          {t('student.activity.emptyHistory', { defaultValue: 'No activity records found for this account.' })}
        </Card>
      ) : (
        <Table
          headers={['Action', 'Event Details', 'Category', 'Timestamp']}
          rows={activities.map((a, idx) => [
            <span key={`act-${idx}`} className="font-bold text-ink text-xs">
              {a.action.replace(/_/g, ' ')}
            </span>,
            <span key={`det-${idx}`} className="text-xs text-muted">
              {a.details}
            </span>,
            <Badge key={`cat-${idx}`} variant="neutral">
              {a.category}
            </Badge>,
            new Date(a.timestamp).toLocaleString(),
          ])}
        />
      )}
    </div>
  )
}


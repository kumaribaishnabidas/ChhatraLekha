import { useState } from 'react'

import PageHeader from '../components/layout/PageHeader'
import { Card, ErrorState, Spinner } from '../components/common'
import { useApi } from '../hooks/useApi'
import { API_BASE, api } from '../services/api'
import { formatDateTime } from '../utils/format'

const REPORTS = [
  {
    path: '/reports/students.csv',
    name: 'Student register',
    format: 'CSV',
    description: 'Every enrolment record with the APAAR ID, quota and verification status.',
  },
  {
    path: '/reports/students.pdf',
    name: 'Student register',
    format: 'PDF',
    description: 'The same register as a printable, paginated report.',
  },
  {
    path: '/reports/anomalies.csv',
    name: 'Anomaly register',
    format: 'CSV',
    description: 'Every finding with its rule code, severity and explanation.',
  },
  {
    path: '/reports/anomalies.pdf',
    name: 'Anomaly register',
    format: 'PDF',
    description: 'The anomaly register as a printable report.',
  },
  {
    path: '/reports/utilisation.csv',
    name: 'Intake utilisation',
    format: 'CSV',
    description: 'Enrolment against the sanctioned seats of every programme.',
  },
  {
    path: '/reports/audit.csv',
    name: 'Audit trail',
    format: 'CSV',
    description: 'The tamper-evident audit trail, including the chain hashes.',
  },
]

export default function ReportsPage() {
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const audit = useApi(() => api.get('/reports/audit.csv', { responseType: 'text' }).then((r) => r.data), [])

  const download = async (report) => {
    setBusy(report.path)
    setError('')
    try {
      const { data, headers } = await api.get(report.path, { responseType: 'blob' })
      const disposition = headers['content-disposition'] || ''
      const match = disposition.match(/filename="?([^";]+)"?/)
      const blob = new Blob([data], { type: 'application/octet-stream' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = match ? match[1] : report.name
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (caught) {
      setError(caught?.response?.data?.detail || 'The report could not be generated.')
    } finally {
      setBusy('')
    }
  }

  return (
    <>
      <PageHeader
        title="Regulatory reports"
        lead="Download official academic registers and reports. Every export is written to the audit trail."
      />

      {error && <ErrorState message={error} />}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-6">
        {REPORTS.map((report) => (
          <Card key={report.path} title={report.name} subtitle={report.description}>
            <div className="flex items-center justify-between gap-3">
              <span className="text-[11px] font-bold uppercase tracking-widest text-muted">
                {report.format}
              </span>
              <button
                type="button"
                className="btn btn-navy"
                onClick={() => download(report)}
                disabled={busy === report.path}
              >
                {busy === report.path ? 'Generating...' : 'Download'}
              </button>
            </div>
          </Card>
        ))}
      </div>

      <Card
        title="Recent audit events"
        subtitle="The most recent entries of the hash-chained trail."
      >
        {audit.loading ? (
          <Spinner />
        ) : (
          <p className="m-0 text-sm text-muted">
            The full trail is available as a CSV export above - it carries the chain hashes, so
            an auditor can re-verify it offline.
          </p>
        )}
      </Card>
    </>
  )
}

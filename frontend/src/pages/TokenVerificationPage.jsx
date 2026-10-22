/**
 * The public token verification page.
 *
 * A QR badge carries an opaque, expiring, revocable token, and the link is
 * `{origin}/verify/t/{token}`. This page resolves it through the public
 * `GET /api/verify/token/{token}` endpoint, which returns an **allowlist**:
 * the record status, the institution, the programme, the academic year, the
 * issue date and the verdict - never the APAAR ID, the date of birth or any
 * contact detail.
 *
 * The page is deliberately reachable without signing in: that is the point of
 * a verification link.
 */
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import PageHeader from '../components/layout/PageHeader'
import { Badge, Card, EmptyState, Spinner } from '../components/common'
import { api, errorMessage } from '../services/api'
import { formatDateTime } from '../utils/format'

export default function TokenVerificationPage() {
  const { token } = useParams()
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    api
      .get(`/verify/token/${encodeURIComponent(token || '')}`)
      .then((response) => {
        if (!cancelled) setResult(response.data)
      })
      .catch((caught) => {
        if (!cancelled) setError(errorMessage(caught, 'The verification failed.'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  return (
    <>
      <PageHeader
        title="Credential verification"
        lead="This page resolves an opaque verification token against this prototype's own database."
      />

      {loading && <Spinner label="Checking the token..." />}

      {!loading && error && (
        <div
          role="alert"
          className="rounded-2xl border border-danger/30 bg-danger-surface p-5 text-sm text-danger-strong"
        >
          <p className="m-0 font-semibold">The token could not be checked.</p>
          <p className="m-0 mt-1">{error}</p>
        </div>
      )}

      {!loading && !error && result && (
        <div className="grid gap-4">
          <div
            className={`rounded-2xl p-5 ${
              result.valid
                ? 'bg-success-surface text-success-strong'
                : 'bg-danger-surface text-danger-strong'
            }`}
          >
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-lg font-extrabold">
                {result.valid ? 'Credential verified' : 'Credential could not be verified'}
              </span>
              <Badge className="bg-surface/70">{result.verdict}</Badge>
              {result.needs_refresh && (
                <Badge className="bg-surface/70">needs refresh</Badge>
              )}
            </div>
            <p className="mt-2 mb-0 text-sm">{result.reason}</p>
          </div>

          {result.valid && (
            <Card title="What the token discloses" subtitle="An allowlist - nothing more.">
              <div className="table-wrap">
                <table className="data-table">
                  <tbody>
                    {[
                      ['Record status', result.record_status],
                      ['Institution', result.institution],
                      ['Programme', result.programme],
                      ['Academic year', result.academic_year],
                      ['Issued at', formatDateTime(result.issued_at)],
                      ['Expires at', formatDateTime(result.expires_at)],
                    ].map(([label, value]) => (
                      <tr key={label}>
                        <th className="w-48">{label}</th>
                        <td>{value || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {result.notice && (
            <p className="m-0 rounded-xl border border-line bg-surface p-4 text-sm text-muted">
              {result.notice}
            </p>
          )}
        </div>
      )}

      {!loading && !error && !result && (
        <EmptyState title="Nothing to verify" description="The link is missing its token." />
      )}
    </>
  )
}

import { useState } from 'react'

import PageHeader from '../components/layout/PageHeader'
import { Badge, Card, EmptyState, ErrorState, FilterBar, KpiCard, Spinner } from '../components/common'
import { useApi } from '../hooks/useApi'
import { api, errorMessage } from '../services/api'
import { anomalyLabel, formatNumber, formatApaar, severityClass } from '../utils/format'

const SEVERITIES = ['', 'CRITICAL', 'HIGH', 'WARNING', 'INFO']
const TYPES = [
  '',
  'EXCESS_APPROVED_INTAKE',
  'DUPLICATE_CROSS_COLLEGE',
  'DUPLICATE_SAME_INSTITUTION',
  'DUPLICATE_ROLL_NUMBER',
  'INVALID_APAAR_FORMAT',
  'SUPERNUMERARY_BREACH',
  'INCONSISTENT_CATEGORY',
  'IMPOSSIBLE_DATE',
  'MISSING_REQUIRED_FIELD',
  'UNSANCTIONED_PROGRAM',
]

export default function AnomaliesPage() {
  const [severity, setSeverity] = useState('')
  const [anomalyType, setAnomalyType] = useState('')
  const [busy, setBusy] = useState('')

  const summary = useApi(() => api.get('/anomalies/summary').then((r) => r.data), [])
  const anomalies = useApi(
    () =>
      api
        .get('/anomalies', {
          params: {
            severity: severity || undefined,
            anomaly_type: anomalyType || undefined,
            limit: 300,
          },
        })
        .then((r) => r.data),
    [severity, anomalyType],
  )

  const review = async (id, reviewStatus) => {
    setBusy(id)
    try {
      await api.post(`/anomalies/${id}/review`, null, { params: { review_status: reviewStatus } })
      anomalies.reload()
    } catch (caught) {
      // eslint-disable-next-line no-alert
      window.alert(errorMessage(caught, 'The review could not be recorded.'))
    } finally {
      setBusy('')
    }
  }

  return (
    <>
      <PageHeader
        title="Anomaly inspector"
        lead="Every finding carries a rule code, a severity, an explanation and a recommended next step. An anomaly is an indication for investigation, not proof of fraud."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <KpiCard label="Findings" value={formatNumber(summary.data?.total)} />
        <KpiCard
          label="Critical"
          value={formatNumber(summary.data?.critical)}
          tone="critical"
        />
        <KpiCard label="High" value={formatNumber(summary.data?.high)} tone="warning" />
        <KpiCard label="Warning" value={formatNumber(summary.data?.warning)} />
      </div>

      <FilterBar>
        <div className="w-48">
          <label className="label" htmlFor="severity">
            Severity
          </label>
          <select
            id="severity"
            className="input"
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
          >
            {SEVERITIES.map((code) => (
              <option key={code} value={code}>
                {code || 'All severities'}
              </option>
            ))}
          </select>
        </div>
        <div className="w-64">
          <label className="label" htmlFor="type">
            Rule
          </label>
          <select
            id="type"
            className="input"
            value={anomalyType}
            onChange={(event) => setAnomalyType(event.target.value)}
          >
            {TYPES.map((code) => (
              <option key={code} value={code}>
                {code ? anomalyLabel(code) : 'All rules'}
              </option>
            ))}
          </select>
        </div>
      </FilterBar>

      {anomalies.error && <ErrorState message={anomalies.error} onRetry={anomalies.reload} />}

      <Card title="Findings" subtitle="Newest first.">
        {anomalies.loading ? (
          <Spinner />
        ) : (anomalies.data || []).length === 0 ? (
          <EmptyState
            title="Nothing to review"
            description="No finding matches the current filters. That is good news."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Rule</th>
                  <th>APAAR ID</th>
                  <th>Institution</th>
                  <th>Explanation</th>
                  <th>Next step</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.data.map((row) => (
                  <tr key={row.anomaly_id}>
                    <td>
                      <Badge className={severityClass(row.severity)}>{row.severity}</Badge>
                    </td>
                    <td className="text-xs font-semibold text-navy">
                      {anomalyLabel(row.anomaly_type)}
                    </td>
                    <td className="font-mono text-xs">{formatApaar(row.student_apaar_id)}</td>
                    <td className="text-xs">{row.institution_id}</td>
                    <td className="text-xs max-w-[320px]">{row.details}</td>
                    <td className="text-xs max-w-[280px] text-muted">
                      {row.recommended_action || '-'}
                    </td>
                    <td>
                      {row.review_status === 'PENDING' ? (
                        <button
                          type="button"
                          className="btn btn-outline text-xs"
                          disabled={busy === row.anomaly_id}
                          onClick={() => review(row.anomaly_id, 'IN_REVIEW')}
                        >
                          Start review
                        </button>
                      ) : (
                        <Badge className="bg-info-surface text-info-strong">
                          {row.review_status}
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  )
}

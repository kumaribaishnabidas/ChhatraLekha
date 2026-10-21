import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import PageHeader from '../components/layout/PageHeader'
import { Card, ErrorState, KpiCard, Spinner } from '../components/common'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { formatNumber, formatPercent, riskClass } from '../utils/format'
import { Badge } from '../components/common'

const QUOTA_COLOURS = ['#1558B8', '#12B886', '#F2A413', '#0F3A8A', '#C62828', '#5A6472', '#14246B']

export default function DashboardPage() {
  const kpis = useApi(() => api.get('/dashboard/national').then((r) => r.data), [])
  const intake = useApi(() => api.get('/dashboard/intake').then((r) => r.data), [])
  const quota = useApi(() => api.get('/dashboard/quota').then((r) => r.data), [])
  const risk = useApi(() => api.get('/dashboard/risk').then((r) => r.data), [])
  const compliance = useApi(() => api.get('/dashboard/compliance').then((r) => r.data), [])

  const quotaChart = useMemo(
    () =>
      (quota.data || []).map((row) => ({
        name: row.label,
        Enrolled: row.enrolled,
        Sanctioned: row.sanctioned,
      })),
    [quota.data],
  )

  const intakeChart = useMemo(
    () =>
      (intake.data || [])
        .filter((row) => row.total_enrolled > 0)
        .slice(0, 12)
        .map((row) => ({
          name: `${row.institution_id} ${row.program_id}`,
          Enrolled: row.total_enrolled,
          Sanctioned: row.total_sanctioned,
        })),
    [intake.data],
  )

  if (kpis.loading) return <Spinner label="Loading the national picture..." />

  return (
    <>
      <PageHeader
        title="AICTE Directorate dashboard"
        lead="Sanctioned intake against actual enrolment, with the supernumerary ceilings, the duplicates and the programme-level compliance matrix already worked out."
      />

      {kpis.error && <ErrorState message={kpis.error} onRetry={kpis.reload} />}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <KpiCard
          label="Institutions"
          value={formatNumber(kpis.data?.institution_count)}
          hint="Approved by AICTE"
        />
        <KpiCard
          label="Programmes"
          value={formatNumber(kpis.data?.programme_count)}
          hint="Sanctioned seats tracked"
        />
        <KpiCard
          label="Enrolled"
          value={formatNumber(kpis.data?.total_enrolled)}
          hint={`${formatPercent(kpis.data?.utilisation_percent)} of the sanctioned intake`}
          tone="good"
        />
        <KpiCard
          label="Anomalies in force"
          value={formatNumber(kpis.data?.flagged_anomalies)}
          hint={`${formatNumber(kpis.data?.critical_anomalies)} critical`}
          tone="critical"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2 mb-6">
        <Card
          title="Quota distribution"
          subtitle="Enrolment against the sanctioned seats of every quota bucket"
        >
          {quota.loading ? (
            <Spinner />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={quotaChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4EAF3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={70} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="Enrolled" fill="#12B886" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Sanctioned" fill="#1558B8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card
          title="Intake utilisation"
          subtitle="The twelve busiest programmes"
        >
          {intake.loading ? (
            <Spinner />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={intakeChart} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E4EAF3" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={140} />
                <Tooltip />
                <Legend />
                <Bar dataKey="Enrolled" fill="#1558B8" radius={[0, 4, 4, 0]} />
                <Bar dataKey="Sanctioned" fill="#D6DEEA" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card
          title="Institution risk scores"
          subtitle="Every contributing anomaly family is listed, so the score is explainable"
        >
          {risk.loading ? (
            <Spinner />
          ) : (risk.data || []).length === 0 ? (
            <p className="m-0 text-sm text-muted">
              No institution currently carries an anomaly.
            </p>
          ) : (
            <ul className="m-0 p-0 list-none grid gap-3">
              {risk.data.map((row) => (
                <li key={row.institution_id} className="flex items-start justify-between gap-3">
                  <div>
                    <p className="m-0 font-semibold text-navy">{row.institution_id}</p>
                    <p className="m-0 text-xs text-muted">
                      {row.reasons.join(' ')}
                    </p>
                    <p className="m-0 mt-1 text-[11px] text-muted">
                      {row.families.join(', ')}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <Badge className={riskClass(row.band)}>{row.band}</Badge>
                    <p className="m-0 mt-1 text-sm font-bold text-navy">{row.score}/100</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card
          title="Compliance matrix"
          subtitle="Every institution against its sanctioned intake"
        >
          {compliance.loading ? (
            <Spinner />
          ) : (
            <div className="table-wrap max-h-[420px] overflow-y-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Institution</th>
                    <th>Approved</th>
                    <th>Enrolled</th>
                    <th>Utilisation</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {(compliance.data || []).map((row) => (
                    <tr key={row.institution_id}>
                      <td>
                        <p className="m-0 font-semibold text-navy">{row.institution_name}</p>
                        <p className="m-0 text-xs text-muted">{row.institution_id}</p>
                      </td>
                      <td>{formatNumber(row.total_approved)}</td>
                      <td>{formatNumber(row.total_enrolled)}</td>
                      <td>{formatPercent(row.utilisation * 100)}</td>
                      <td>
                        <Badge className={riskClass(row.risk_band)}>{row.risk_band}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}

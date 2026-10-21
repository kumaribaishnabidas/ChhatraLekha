import { useState } from 'react'

import PageHeader from '../components/layout/PageHeader'
import { Badge, Card, EmptyState, ErrorState, FilterBar, Spinner } from '../components/common'
import { useApi } from '../hooks/useApi'
import { useDebounce } from '../hooks/useDebounce'
import { api } from '../services/api'
import { formatApaar, quotaLabel, statusClass } from '../utils/format'

const QUOTAS = [
  '',
  'REGULAR_MERIT',
  'MANAGEMENT',
  'SUPERNUMERARY_NRI',
  'SUPERNUMERARY_OCI',
  'SUPERNUMERARY_FN',
  'SUPERNUMERARY_TFW',
  'PMSSS',
]

export default function StudentsPage() {
  const [search, setSearch] = useState('')
  const [quota, setQuota] = useState('')
  const [recordStatus, setRecordStatus] = useState('ACTIVE')
  const debouncedSearch = useDebounce(search)

  const students = useApi(
    () =>
      api
        .get('/students', {
          params: {
            search: debouncedSearch || undefined,
            quota: quota || undefined,
            record_status: recordStatus || undefined,
            limit: 200,
          },
        })
        .then((r) => r.data),
    [debouncedSearch, quota, recordStatus],
  )

  return (
    <>
      <PageHeader
        title="Student register"
        lead="Every enrolment record the registry holds, with the APAAR ID masked unless the full identifier is needed."
      />

      <FilterBar>
        <div className="w-72">
          <label className="label" htmlFor="search">
            Search
          </label>
          <input
            id="search"
            className="input"
            value={search}
            placeholder="Name or APAAR ID"
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div className="w-56">
          <label className="label" htmlFor="quota">
            Quota
          </label>
          <select
            id="quota"
            className="input"
            value={quota}
            onChange={(event) => setQuota(event.target.value)}
          >
            {QUOTAS.map((code) => (
              <option key={code} value={code}>
                {code ? quotaLabel(code) : 'All quotas'}
              </option>
            ))}
          </select>
        </div>
        <div className="w-48">
          <label className="label" htmlFor="status">
            Record status
          </label>
          <select
            id="status"
            className="input"
            value={recordStatus}
            onChange={(event) => setRecordStatus(event.target.value)}
          >
            <option value="ACTIVE">Active</option>
            <option value="WITHDRAWN">Withdrawn</option>
            <option value="ALL">All</option>
          </select>
        </div>
      </FilterBar>

      {students.error && <ErrorState message={students.error} onRetry={students.reload} />}

      <Card
        title="Enrolments"
        subtitle={
          students.data ? `${students.data.length} record(s) shown` : 'Loading the register...'
        }
      >
        {students.loading ? (
          <Spinner />
        ) : (students.data || []).length === 0 ? (
          <EmptyState
            title="No record found"
            description="Adjust the filters, or upload a batch to add enrolments."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>APAAR ID</th>
                  <th>Student</th>
                  <th>Institution</th>
                  <th>Programme</th>
                  <th>Quota</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {students.data.map((row) => (
                  <tr key={row.record_id}>
                    <td className="font-mono text-xs">{formatApaar(row.apaar_id)}</td>
                    <td>
                      <p className="m-0 font-semibold text-navy">
                        {row.student_name || <span className="text-crimson">Missing</span>}
                      </p>
                      <p className="m-0 text-xs text-muted">
                        {row.student_institute_roll_no || 'No roll number'}
                      </p>
                    </td>
                    <td className="text-xs">{row.institution_id}</td>
                    <td className="text-xs">
                      {row.program_id}
                      <p className="m-0 text-muted">{row.academic_year}</p>
                    </td>
                    <td className="text-xs">{quotaLabel(row.admission_quota)}</td>
                    <td>
                      <Badge className={statusClass(row.verification_status)}>
                        {row.verification_status}
                      </Badge>
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

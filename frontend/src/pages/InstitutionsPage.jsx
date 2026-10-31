import { useState } from 'react'

import PageHeader from '../components/layout/PageHeader'
import { Card, EmptyState, ErrorState, FilterBar, Spinner } from '../components/common'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { formatNumber } from '../utils/format'

export default function InstitutionsPage() {
  const [state, setState] = useState('')
  const [selected, setSelected] = useState(null)

  const institutions = useApi(
    () => api.get('/institutions', { params: { state: state || undefined } }).then((r) => r.data),
    [state],
  )
  const programmes = useApi(
    () =>
      selected
        ? api.get(`/institutions/${selected.institution_id}/programmes`).then((r) => r.data)
        : Promise.resolve([]),
    [selected?.institution_id],
  )

  return (
    <>
      <PageHeader
        title="Institutions"
        lead="Every school, college, and institution in the registry, together with academic unit capacity."
      />

      <FilterBar>
        <div className="w-64">
          <label className="label" htmlFor="state">
            State
          </label>
          <input
            id="state"
            className="input"
            value={state}
            placeholder="e.g. Karnataka"
            onChange={(event) => setState(event.target.value)}
          />
        </div>
      </FilterBar>

      {institutions.error && <ErrorState message={institutions.error} onRetry={institutions.reload} />}

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Card title="Approved institutions">
          {institutions.loading ? (
            <Spinner />
          ) : (institutions.data || []).length === 0 ? (
            <EmptyState title="No institution found" description="Try clearing the filter." />
          ) : (
            <div className="table-wrap max-h-[520px] overflow-y-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Institution</th>
                    <th>State</th>
                    <th>Type</th>
                    <th>Grade</th>
                  </tr>
                </thead>
                <tbody>
                  {institutions.data.map((row) => (
                    <tr
                      key={row.institution_id}
                      onClick={() => setSelected(row)}
                      className="cursor-pointer"
                    >
                      <td>
                        <p className="m-0 font-semibold text-navy">{row.name}</p>
                        <p className="m-0 text-xs text-muted">{row.institution_id}</p>
                      </td>
                      <td>{row.state}</td>
                      <td className="text-xs">{row.institution_type}</td>
                      <td>{row.naac_grade}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card
          title={
            selected ? `Sanctioned capacity - ${selected.institution_id}` : 'Sanctioned capacity'
          }
          subtitle={selected ? selected.name : 'Select an institution to see its programmes.'}
        >
          {!selected ? (
            <EmptyState
              title="No institution selected"
              description="Pick one on the left to list its approved programmes."
            />
          ) : programmes.loading ? (
            <Spinner />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Programme</th>
                    <th>Approved</th>
                    <th>Super.</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {programmes.map((row) => (
                    <tr key={`${row.institution_id}-${row.program_id}-${row.academic_year}`}>
                      <td>
                        <p className="m-0 font-semibold text-navy">{row.program_name}</p>
                        <p className="m-0 text-xs text-muted">
                          {row.program_id} &middot; {row.academic_year}
                        </p>
                      </td>
                      <td>{formatNumber(row.approved_intake)}</td>
                      <td>
                        {formatNumber(
                          row.max_supernumerary_nri +
                            row.max_supernumerary_fn_oci +
                            row.max_supernumerary_tfw +
                            row.max_pmsss,
                        )}
                      </td>
                      <td className="font-semibold">{formatNumber(row.total_sanctioned)}</td>
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

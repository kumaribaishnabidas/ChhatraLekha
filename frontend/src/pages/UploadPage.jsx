import { useState } from 'react'

import PageHeader from '../components/layout/PageHeader'
import { Badge, Card, EmptyState, ErrorState, Spinner } from '../components/common'
import { useAuth } from '../hooks/useAuth'
import { api, errorMessage } from '../services/api'

const TEMPLATE = `APAAR_ID,Full_Name,DOB,Gender,Roll_No,Program_Code,Category,Nationality,Doc_Number
984210357890,Aakash Verma,2004-03-12,Male,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,
984210357891,Sanya Kapoor,2005-01-20,Female,CSE-24-011,BTECH_CSE,SUPERNUMERARY_TFW,Indian,`

export default function UploadPage() {
  const { user } = useAuth()
  const [institutionId, setInstitutionId] = useState(user?.institution_id || '')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const reset = () => {
    setPreview(null)
    setResult(null)
    setError('')
  }

  const handleFile = (event) => {
    setFile(event.target.files?.[0] || null)
    reset()
  }

  const runPreview = async (event) => {
    event.preventDefault()
    if (!file || !institutionId) {
      setError('Choose an institution and a CSV file first.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const body = new FormData()
      body.append('file', file)
      const { data } = await api.post('/students/bulk/preview', body, {
        params: { institution_id: institutionId },
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setPreview(data)
    } catch (caught) {
      setError(errorMessage(caught, 'The upload could not be validated.'))
    } finally {
      setBusy(false)
    }
  }

  const commit = async () => {
    setBusy(true)
    setError('')
    try {
      const body = new FormData()
      body.append('file', file)
      const { data } = await api.post('/students/bulk/commit', body, {
        params: { institution_id: institutionId },
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(data)
      setPreview(null)
    } catch (caught) {
      setError(errorMessage(caught, 'The batch could not be committed.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Upload a student batch"
        lead="Validate a spreadsheet against the live registry before anything is written. Rows that fail validation are quarantined for review, never silently dropped."
      />

      <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
        <Card title="Batch" subtitle="The supported CSV template is shown below.">
          <form onSubmit={runPreview}>
            <label className="label" htmlFor="institution">
              Institution
            </label>
            <input
              id="institution"
              className="input"
              value={institutionId}
              placeholder="INST-0421"
              onChange={(event) => setInstitutionId(event.target.value)}
            />

            <label className="label mt-4" htmlFor="file">
              CSV file
            </label>
            <input
              id="file"
              type="file"
              accept=".csv,text/csv"
              className="input"
              onChange={handleFile}
            />

            {error && (
              <p role="alert" className="mt-3 mb-0 text-sm text-crimson">
                {error}
              </p>
            )}

            <div className="flex gap-2 mt-5">
              <button type="submit" className="btn btn-navy" disabled={busy}>
                {busy ? 'Validating...' : 'Validate the batch'}
              </button>
              {preview && (
                <button type="button" className="btn btn-primary" onClick={commit} disabled={busy}>
                  Commit {preview.valid_rows} accepted row(s)
                </button>
              )}
            </div>
          </form>

          <details className="mt-5">
            <summary className="cursor-pointer text-sm font-semibold text-navy">
              Show the CSV template
            </summary>
            <pre className="mt-2 overflow-x-auto rounded-xl bg-[#F4F7FC] p-3 text-xs">
              {TEMPLATE}
            </pre>
          </details>
        </Card>

        <div className="flex flex-col gap-4">
          {result && (
            <Card title="Batch committed">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div>
                  <p className="m-0 text-2xl font-extrabold text-navy">{result.committed}</p>
                  <p className="m-0 text-[11px] uppercase tracking-wider text-muted">Accepted</p>
                </div>
                <div>
                  <p className="m-0 text-2xl font-extrabold text-crimson">{result.critical_rows}</p>
                  <p className="m-0 text-[11px] uppercase tracking-wider text-muted">Quarantined</p>
                </div>
                <div>
                  <p className="m-0 text-2xl font-extrabold text-saffron">{result.warning_rows}</p>
                  <p className="m-0 text-[11px] uppercase tracking-wider text-muted">Warnings</p>
                </div>
                <div>
                  <p className="m-0 text-2xl font-extrabold text-navy">{result.anomalies_detected}</p>
                  <p className="m-0 text-[11px] uppercase tracking-wider text-muted">Anomalies</p>
                </div>
              </div>
            </Card>
          )}

          <Card
            title="Validation preview"
            subtitle={
              preview
                ? `${preview.total_rows} row(s) - ${preview.valid_rows} acceptable, ${preview.critical_rows} quarantined`
                : 'Nothing has been validated yet.'
            }
          >
            {!preview ? (
              <EmptyState
                title="No preview"
                description="Choose a CSV and validate it to see the row-by-row verdicts and the seat impact."
              />
            ) : preview.header_errors?.length ? (
              <div className="rounded-xl border border-crimson/30 bg-[#FDE7E7] p-4 text-sm text-crimson">
                <p className="m-0 font-semibold">The file header was rejected.</p>
                <ul className="mt-2 mb-0 pl-5">
                  {preview.header_errors.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <>
                {preview.program_impacts?.length > 0 && (
                  <div className="mb-4">
                    <p className="m-0 mb-2 text-sm font-semibold text-navy">Seat impact</p>
                    <div className="table-wrap">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Programme</th>
                            <th>Projected regular</th>
                            <th>Overflow</th>
                          </tr>
                        </thead>
                        <tbody>
                          {preview.program_impacts.map((impact) => (
                            <tr key={impact.program_code}>
                              <td className="text-xs">
                                {impact.program_name}
                                <p className="m-0 text-muted">{impact.program_code}</p>
                              </td>
                              <td>
                                {impact.projected_regular} / {impact.approved_intake}
                              </td>
                              <td>
                                {impact.regular_overflow > 0 ? (
                                  <Badge className="bg-[#FDE7E7] text-crimson">
                                    +{impact.regular_overflow}
                                  </Badge>
                                ) : (
                                  <span className="text-xs text-muted">within cap</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {preview.program_impacts.some((i) => i.cap_messages?.length > 0) && (
                      <ul className="mt-2 mb-0 pl-5 text-xs text-crimson">
                        {preview.program_impacts
                          .flatMap((i) => i.cap_messages || [])
                          .map((message) => (
                            <li key={message}>{message}</li>
                          ))}
                      </ul>
                    )}
                  </div>
                )}

                <div className="table-wrap max-h-[420px] overflow-y-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Line</th>
                        <th>APAAR ID</th>
                        <th>Student</th>
                        <th>Programme</th>
                        <th>Findings</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.rows.map((row) => (
                        <tr key={row.line_number}>
                          <td className="text-xs text-muted">{row.line_number}</td>
                          <td className="font-mono text-xs">{row.apaar_id}</td>
                          <td className="text-xs">{row.full_name || '-'}</td>
                          <td className="text-xs">{row.program_code}</td>
                          <td>
                            {row.issues.length === 0 ? (
                              <Badge className="bg-[#E2F6EC] text-[#0A6B3D]">Accepted</Badge>
                            ) : (
                              <ul className="m-0 p-0 list-none grid gap-1">
                                {row.issues.map((issue) => (
                                  <li key={issue.code} className="text-xs">
                                    <Badge
                                      className={
                                        issue.severity === 'CRITICAL'
                                          ? 'bg-[#FDE7E7] text-crimson'
                                          : 'bg-[#FEF3DC] text-[#96650A]'
                                      }
                                    >
                                      {issue.severity}
                                    </Badge>{' '}
                                    {issue.message}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}

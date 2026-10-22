import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import PageHeader from '../components/layout/PageHeader'
import { Badge, Card, EmptyState } from '../components/common'
import { api, errorMessage } from '../services/api'
import { formatApaar, formatDateTime, severityClass } from '../utils/format'

function VerdictBanner({ result }) {
  const valid = result.verified
  return (
    <div
      className={`rounded-2xl p-5 ${
        valid ? 'bg-success-surface text-success-strong' : 'bg-danger-surface text-danger-strong'
      }`}
    >
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-lg font-extrabold">
          {valid ? 'Credential verified' : 'Credential could not be verified'}
        </span>
        <Badge className={valid ? 'bg-surface/70 text-success-strong' : 'bg-surface/70 text-danger-strong'}>
          {result.verdict}
        </Badge>
      </div>
      <p className="mt-2 mb-0 text-sm">{result.reason}</p>
      {result.consent_note && (
        <p className="mt-1 mb-0 text-xs opacity-80">Consent: {result.consent_note}</p>
      )}
    </div>
  )
}

export default function VerificationPage() {
  const [params, setParams] = useSearchParams()
  const [apaarId, setApaarId] = useState(params.get('apaar') || '')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const videoRef = useRef(null)
  const [scanning, setScanning] = useState(false)

  const verify = async (id, seal) => {
    if (!id) {
      setError('An APAAR ID is required.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const { data } = await api.get(`/verify/${encodeURIComponent(id)}`, {
        params: seal ? { seal } : undefined,
      })
      setResult(data)
    } catch (caught) {
      setError(errorMessage(caught, 'The verification failed.'))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    const initial = params.get('apaar')
    if (initial) verify(initial)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = (event) => {
    event.preventDefault()
    setParams(apaarId ? { apaar: apaarId } : {})
    verify(apaarId)
  }

  const startCamera = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('This browser does not expose a camera. Use the APAAR ID field instead.')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setScanning(true)
    } catch {
      setError('Camera access was refused. Use the APAAR ID field instead.')
    }
  }

  const stopCamera = () => {
    const video = videoRef.current
    if (video?.srcObject) {
      video.srcObject.getTracks().forEach((track) => track.stop())
      video.srcObject = null
    }
    setScanning(false)
  }

  return (
    <>
      <PageHeader
        title="Verify an APAAR credential"
        lead="The verdict is always issued. The personal fields are disclosed only when the student has consented to credential verification."
      />

      <div className="grid gap-4 lg:grid-cols-[1fr_1.3fr]">
        <Card title="Verification request">
          <form onSubmit={handleSubmit}>
            <label className="label" htmlFor="apaar">
              APAAR ID
            </label>
            <input
              id="apaar"
              className="input"
              inputMode="numeric"
              maxLength={12}
              value={apaarId}
              onChange={(event) => setApaarId(event.target.value.replace(/\D/g, ''))}
              placeholder="9842 1035 7890"
            />

            {error && (
              <p role="alert" className="mt-3 mb-0 text-sm text-crimson">
                {error}
              </p>
            )}

            <button type="submit" className="btn btn-navy w-full mt-5" disabled={busy}>
              {busy ? 'Verifying...' : 'Verify credential'}
            </button>
          </form>

          <hr className="my-5 border-line" />

          <p className="m-0 mb-2 text-sm font-semibold text-navy">Scan the APAAR QR badge</p>
          <video
            ref={videoRef}
            className="w-full max-w-sm rounded-xl bg-black"
            playsInline
            muted
            aria-label="QR scanner"
          />
          <div className="flex gap-2 mt-3">
            <button type="button" className="btn btn-outline" onClick={startCamera}>
              Start camera
            </button>
            <button type="button" className="btn btn-outline" onClick={stopCamera}>
              Stop
            </button>
          </div>
        </Card>

        <div className="flex flex-col gap-4">
          {!result ? (
            <Card title="Result">
              <EmptyState
                title="No verification yet"
                description="Enter an APAAR ID or scan a badge to see the signed verdict."
              />
            </Card>
          ) : (
            <>
              <VerdictBanner result={result} />

              {result.student ? (
                <Card title="Academic record">
                  <div className="table-wrap">
                    <table className="data-table">
                      <tbody>
                        {[
                          ['APAAR ID', formatApaar(result.apaar_id)],
                          ['Student', result.student.student_name],
                          ['Institution', result.institution_name],
                          ['Programme', result.program_name],
                          ['Academic year', result.student.academic_year],
                          ['Quota', result.student.admission_quota],
                          ['Roll number', result.student.student_institute_roll_no],
                          ['Enrolment date', result.student.enrollment_date],
                          ['Signature', result.algorithm || '-'],
                        ].map(([label, value]) => (
                          <tr key={label}>
                            <th className="w-44">{label}</th>
                            <td>{value || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              ) : (
                <Card title="Academic record">
                  <EmptyState
                    title="Personal fields withheld"
                    description="The student has not consented to credential verification, or has withdrawn it. The verdict above is still issued."
                  />
                </Card>
              )}

              {result.anomalies?.length > 0 && (
                <Card title={`Anomalies on this record (${result.anomalies.length})`}>
                  <ul className="m-0 p-0 list-none grid gap-2">
                    {result.anomalies.map((anomaly) => (
                      <li key={anomaly.anomaly_id} className="text-sm">
                        <Badge className={severityClass(anomaly.severity)}>
                          {anomaly.severity}
                        </Badge>{' '}
                        {anomaly.details}
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              <p className="m-0 text-xs text-muted">
                Verified at {formatDateTime(result.verified_at)}. Every verification is written to
                the tamper-evident audit trail.
              </p>
            </>
          )}
        </div>
      </div>
    </>
  )
}

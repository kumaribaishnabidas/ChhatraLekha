import { useCallback, useEffect, useMemo, useState } from 'react'

import PageHeader from '../components/layout/PageHeader'
import { Badge, Card, EmptyState, ErrorState, FilterBar, Spinner } from '../components/common'
import { useApi } from '../hooks/useApi'
import { useDebounce } from '../hooks/useDebounce'
import { api, errorMessage } from '../services/api'
import { formatApaar, formatDateTime, maskApaar, severityClass } from '../utils/format'

/** The fields a correction may change. */
const CORRECTABLE_FIELDS = [
  ['academic_year', 'Academic year'],
  ['enrollment_date', 'Enrolment date'],
  ['admission_quota', 'Quota bucket'],
  ['nationality', 'Nationality'],
  ['program_id', 'Programme'],
  ['student_institute_roll_no', 'Institute roll number'],
  ['student_name', 'Student name'],
  ['date_of_birth', 'Date of birth'],
  ['contact_email', 'Contact e-mail'],
  ['contact_phone', 'Contact mobile'],
  ['institution_id', 'Institution'],
  ['apaar_id', 'APAAR ID'],
]

const CERTAINTY_CLASS = {
  confirmed: 'bg-[#FDE7E7] text-crimson',
  suspected: 'bg-[#FEF3DC] text-[#96650A]',
  review_only: 'bg-[#E7EFFC] text-mid-blue',
}

const TASK_STATUSES = [
  ['open', 'Open'],
  ['in_progress', 'In progress'],
  ['resolved', 'Resolved'],
  ['dismissed', 'Dismissed'],
]

function BeforeAfter({ field, before, after }) {
  return (
    <tr>
      <td className="font-semibold text-navy">{field}</td>
      <td className="font-mono text-xs">
        <span className="line-through opacity-70">{String(before ?? '-') || '-'}</span>
      </td>
      <td className="font-mono text-xs font-semibold">{String(after ?? '-') || '-'}</td>
    </tr>
  )
}

export default function ImpactPage() {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [changes, setChanges] = useState({})
  const [reason, setReason] = useState('')
  const [preview, setPreview] = useState(null)
  const [applied, setApplied] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const debouncedSearch = useDebounce(search)

  const students = useApi(
    () =>
      api
        .get('/students', { params: { search: debouncedSearch || undefined, limit: 50 } })
        .then((r) => r.data),
    [debouncedSearch],
  )

  const tasks = useApi(
    () =>
      api
        .get('/review-tasks', { params: { limit: 100 } })
        .then((r) => r.data)
        .catch(() => []),
    [],
  )

  const versions = useApi(
    () =>
      selected
        ? api
            .get(`/students/${selected.record_id}/versions`)
            .then((r) => r.data)
            .catch(() => [])
        : Promise.resolve([]),
    [selected?.record_id],
  )

  const reset = useCallback(() => {
    setChanges({})
    setPreview(null)
    setApplied(null)
    setReason('')
    setError('')
  }, [])

  useEffect(() => {
    reset()
  }, [reset, selected?.record_id])

  const changedEntries = useMemo(
    () => Object.entries(changes).filter(([, value]) => value !== ''),
    [changes],
  )

  const runPreview = async () => {
    if (!selected || !changedEntries.length) {
      setError('Choose a student and at least one field to change.')
      return
    }
    setBusy(true)
    setError('')
    setApplied(null)
    try {
      const proposed = Object.fromEntries(changedEntries)
      const { data } = await api.post(
        `/students/${selected.record_id}/correction-preview`,
        { changes: proposed },
      )
      setPreview(data)
    } catch (caught) {
      setError(errorMessage(caught, 'The preview could not be produced.'))
    } finally {
      setBusy(false)
    }
  }

  const applyCorrection = async () => {
    if (!selected || !preview) return
    if (!reason.trim()) {
      setError('A correction has to record why it is being made.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post(`/students/${selected.record_id}/corrections`, {
        changes: Object.fromEntries(changedEntries),
        reason,
        expected_version: preview.current_version,
      })
      setApplied(data)
      setPreview(null)
      setChanges({})
      setReason('')
      versions.reload()
      tasks.reload()
    } catch (caught) {
      setError(errorMessage(caught, 'The correction could not be applied.'))
    } finally {
      setBusy(false)
    }
  }

  const updateTask = async (taskId, patch) => {
    try {
      await api.patch(`/review-tasks/${taskId}`, patch)
      tasks.reload()
    } catch (caught) {
      setError(errorMessage(caught, 'The task could not be updated.'))
    }
  }

  return (
    <>
      <PageHeader
        title="Change Impact"
        lead="Preview a correction, see what it would affect, and then apply it. The preview writes nothing, and applying a correction never modifies a linked record - the linked work becomes a checklist for an authorised reviewer."
      />

      {error && <ErrorState message={error} />}

      <div className="grid gap-4 lg:grid-cols-[1fr_1.3fr]">
        <div className="flex flex-col gap-4">
          <Card title="1. Choose a student" subtitle="Search by name or APAAR ID.">
            <FilterBar>
              <div className="w-full">
                <label className="label" htmlFor="impact-search">
                  Search
                </label>
                <input
                  id="impact-search"
                  className="input"
                  value={search}
                  placeholder="Name or APAAR ID"
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
            </FilterBar>
            {students.loading ? (
              <Spinner />
            ) : (students.data || []).length === 0 ? (
              <EmptyState title="No student found" description="Try a different search." />
            ) : (
              <div className="table-wrap max-h-72 overflow-y-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>APAAR ID</th>
                      <th>Student</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.data.map((row) => (
                      <tr
                        key={row.record_id}
                        className="cursor-pointer"
                        onClick={() => setSelected(row)}
                      >
                        <td className="font-mono text-xs">{maskApaar(row.apaar_id)}</td>
                        <td className="text-xs font-semibold text-navy">
                          {row.student_name || '(no name)'}
                          <p className="m-0 text-muted">
                            {row.institution_id} &middot; {row.program_id}
                          </p>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <Card
            title="2. Propose a correction"
            subtitle={
              selected
                ? `Editing ${maskApaar(selected.apaar_id)}. The current values are shown next to the new ones.`
                : 'Pick a student first.'
            }
          >
            {!selected ? (
              <EmptyState
                title="No student selected"
                description="Choose one above to propose a correction."
              />
            ) : (
              <>
                <div className="table-wrap mb-4">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Field</th>
                        <th>Before</th>
                        <th>After</th>
                      </tr>
                    </thead>
                    <tbody>
                      {CORRECTABLE_FIELDS.map(([name, label]) => {
                        const before = selected[name] ?? ''
                        const after = changes[name] ?? ''
                        if (after === '' && before === '') return null
                        return (
                          <tr key={name}>
                            <td className="font-semibold text-navy">{label}</td>
                            <td className="font-mono text-xs opacity-70">
                              {String(before) || '-'}
                            </td>
                            <td>
                              <input
                                className="input py-1 text-xs"
                                aria-label={`New ${label}`}
                                value={after}
                                onChange={(event) =>
                                  setChanges((current) => ({
                                    ...current,
                                    [name]: event.target.value,
                                  }))
                                }
                              />
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

                <label className="label" htmlFor="reason">
                  Why is this correction being made?
                </label>
                <input
                  id="reason"
                  className="input"
                  value={reason}
                  placeholder="e.g. the admission was made in the 2026-27 session"
                  onChange={(event) => setReason(event.target.value)}
                />

                <div className="flex gap-2 mt-5">
                  <button
                    type="button"
                    className="btn btn-navy"
                    onClick={runPreview}
                    disabled={busy}
                  >
                    {busy ? 'Working...' : 'Preview the impact'}
                  </button>
                  {preview && (
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={applyCorrection}
                      disabled={busy}
                    >
                      Apply the correction
                    </button>
                  )}
                </div>
              </>
            )}
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          {applied && (
            <div className="rounded-2xl border border-[#0A6B3D]/30 bg-[#E2F6EC] p-5 text-[#0A6B3D]">
              <p className="m-0 font-extrabold">Correction applied</p>
              <p className="m-0 mt-1 text-sm">{applied.notice}</p>
              <p className="m-0 mt-2 text-xs">
                Version {applied.version_no} &middot; {applied.tasks_created} review task(s)
                created &middot; {applied.tokens_needing_reissue} verification token(s)
                flagged for reissue.
              </p>
            </div>
          )}

          {preview && (
            <Card
              title="Impact preview"
              subtitle={`${preview.findings.length} finding(s), ${preview.checklist.length} task(s) to review`}
            >
              <div className="mb-4 rounded-xl border border-bright-blue/30 bg-[#E7EFFC] p-3 text-sm text-mid-blue">
                <strong>Preview only: nothing has been saved.</strong> No record has been
                changed and no linked record has been touched. Review the findings, then
                apply the correction if they are acceptable.
              </div>

              {preview.changed_fields.length > 0 && (
                <div className="table-wrap mb-4">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Field</th>
                        <th>Before</th>
                        <th>After</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.changed_fields.map((change) => (
                        <BeforeAfter key={change.field} {...change} />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {preview.findings.length === 0 ? (
                <EmptyState
                  title="No downstream impact"
                  description="This correction does not affect any other record."
                />
              ) : (
                <ul className="m-0 p-0 list-none grid gap-3">
                  {preview.findings.map((finding) => (
                    <li key={`${finding.rule_id}-${finding.title}`} className="rounded-xl border border-line p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge className={severityClass(finding.severity)}>
                          {finding.severity}
                        </Badge>
                        <Badge className={CERTAINTY_CLASS[finding.certainty] || CERTAINTY_CLASS.suspected}>
                          {finding.certainty.replace('_', ' ')}
                        </Badge>
                        <span className="font-mono text-xs text-muted">{finding.rule_id}</span>
                      </div>
                      <p className="m-0 mt-2 font-semibold text-navy">{finding.title}</p>
                      <p className="m-0 mt-1 text-sm text-muted">{finding.explanation}</p>
                      {finding.suggested_action && (
                        <p className="m-0 mt-1 text-xs text-mid-blue">
                          Next: {finding.suggested_action}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          )}

          <Card
            title="Review checklist"
            subtitle="The work a linked correction leaves behind. Nothing is changed automatically."
          >
            {tasks.loading ? (
              <Spinner />
            ) : (tasks.data || []).length === 0 ? (
              <EmptyState
                title="Nothing to review"
                description="No correction has produced a review task yet."
              />
            ) : (
              <ul className="m-0 p-0 list-none grid gap-3">
                {tasks.data.map((task) => (
                  <li key={task.task_id} className="rounded-xl border border-line p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge className={severityClass(task.severity)}>{task.severity}</Badge>
                      <Badge className={CERTAINTY_CLASS[task.certainty] || CERTAINTY_CLASS.suspected}>
                        {task.certainty.replace('_', ' ')}
                      </Badge>
                      <Badge className="bg-[#EDF1F6] text-muted">{task.status}</Badge>
                      <span className="font-mono text-xs text-muted">{task.rule_id}</span>
                    </div>
                    <p className="m-0 mt-2 font-semibold text-navy">{task.title}</p>
                    <p className="m-0 mt-1 text-sm text-muted">{task.explanation}</p>
                    <p className="m-0 mt-1 text-xs text-mid-blue">
                      Next: {task.suggested_action}
                    </p>
                    {task.status !== 'resolved' && task.status !== 'dismissed' && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        <button
                          type="button"
                          className="btn btn-outline text-xs"
                          onClick={() =>
                            updateTask(task.task_id, {
                              status: 'in_progress',
                              review_note: 'Taken up for review.',
                            })
                          }
                        >
                          Start review
                        </button>
                        <button
                          type="button"
                          className="btn btn-primary text-xs"
                          onClick={() =>
                            updateTask(task.task_id, {
                              status: 'resolved',
                              review_note: 'Checked against the source documents.',
                              outcome: 'No further action needed.',
                            })
                          }
                        >
                          Resolve
                        </button>
                        <button
                          type="button"
                          className="btn btn-outline text-xs"
                          onClick={() => {
                            const note = window.prompt(
                              'Why is this finding dismissed? A dismissal has to record a reason.',
                            )
                            if (note && note.trim()) {
                              updateTask(task.task_id, {
                                status: 'dismissed',
                                review_note: note.trim(),
                              })
                            }
                          }}
                        >
                          Dismiss
                        </button>
                      </div>
                    )}
                    {task.review_note && (
                      <p className="m-0 mt-2 text-xs text-muted">
                        Note: {task.review_note}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card
            title="Version history"
            subtitle={
              selected
                ? `Every correction of ${maskApaar(selected.apaar_id)}.`
                : 'Pick a student to see its corrections.'
            }
          >
            {!selected ? (
              <EmptyState title="No student selected" />
            ) : versions.loading ? (
              <Spinner />
            ) : (versions.data || []).length === 0 ? (
              <EmptyState
                title="No corrections yet"
                description="This record has never been corrected."
              />
            ) : (
              <ol className="m-0 p-0 list-none grid gap-2">
                {versions.data.map((version) => (
                  <li key={version.version_id} className="text-sm">
                    <span className="font-mono text-xs text-muted">
                      v{version.version_no}
                    </span>{' '}
                    <span className="font-semibold text-navy">
                      {version.changed_fields.join(', ')}
                    </span>
                    <p className="m-0 text-xs text-muted">
                      {version.reason} &middot; {version.actor} &middot;{' '}
                      {formatDateTime(version.created_at)}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}

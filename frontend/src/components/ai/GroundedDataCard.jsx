/**
 * Render the structured data behind a grounded assistant answer.
 *
 * The backend only sends records the signed-in caller is allowed to see, and
 * it masks identifiers such as the APAAR ID. This component never fetches
 * anything itself - it is a presentation layer for that already-authorised
 * payload, so it must not add or infer fields that the server omitted.
 */

function text(value) {
  if (value === null || value === undefined || value === '') return '-'
  return String(value)
}

function number(value) {
  return typeof value === 'number' ? value.toLocaleString() : text(value)
}

function percent(value) {
  return typeof value === 'number' ? `${value}%` : 'Not recorded'
}

function dateLabel(value) {
  if (!value) return ''
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return String(value)
  return parsed.toLocaleDateString()
}

function Stat({ label, value }) {
  return (
    <div className="rounded bg-surface px-2 py-1.5 border border-line/70">
      <dt className="m-0 text-[9px] uppercase tracking-wide text-muted">{label}</dt>
      <dd className="m-0 text-xs font-bold text-ink">{value}</dd>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="space-y-1.5">
      <p className="m-0 text-[10px] font-bold uppercase tracking-wide text-muted">{title}</p>
      {children}
    </div>
  )
}

function AttendanceCard({ data }) {
  return (
    <Section title="Attendance">
      <div className="space-y-2">
        {(data.students || []).map((student, index) => (
          <div key={`${student.student_ref || student.student_name}-${index}`} className="space-y-1.5">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-xs font-semibold text-ink">
                {text(student.student_name || student.student_ref)}
              </span>
              <span className="text-xs font-bold text-brand">{percent(student.attendance_rate)}</span>
            </div>
            <dl className="grid grid-cols-3 gap-1 m-0">
              <Stat label="Present" value={number(student.present_sessions)} />
              <Stat label="Absent" value={number(student.absent_sessions)} />
              <Stat label="Excused" value={number(student.excused_sessions)} />
            </dl>
            {student.recent?.length > 0 && (
              <ul className="m-0 pl-3 text-[10px] text-muted space-y-0.5">
                {student.recent.map((row, rowIndex) => (
                  <li key={`${row.date}-${rowIndex}`}>
                    {dateLabel(row.date)} · {text(row.status)}
                    {row.class ? ` · ${row.class}` : ''}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </Section>
  )
}

function AttendanceSummaryCard({ data }) {
  return (
    <Section title="Attendance summary">
      <dl className="grid grid-cols-2 gap-1 m-0">
        <Stat label="Attendance rate" value={percent(data.attendance_rate)} />
        <Stat label="Sessions" value={number(data.session_count)} />
        <Stat label="Present records" value={number(data.present_records)} />
        <Stat label="Absent records" value={number(data.absent_records)} />
      </dl>
    </Section>
  )
}

function ResultsCard({ data }) {
  return (
    <Section title="Published results">
      <div className="space-y-2">
        {(data.students || []).map((student, index) => (
          <div key={`${student.student_ref || student.student_name}-${index}`} className="space-y-1">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-xs font-semibold text-ink">
                {text(student.student_name || student.student_ref)}
              </span>
              <span className="text-[10px] text-muted">
                Average {percent(student.average_percentage)}
              </span>
            </div>
            {(student.results || []).length > 0 ? (
              <ul className="m-0 space-y-1">
                {student.results.map((result, resultIndex) => (
                  <li
                    key={`${result.assessment}-${resultIndex}`}
                    className="flex items-center justify-between gap-2 rounded border border-line/70 bg-surface px-2 py-1"
                  >
                    <span className="min-w-0 text-[11px] text-ink truncate">
                      {text(result.subject || result.assessment)}
                      {result.term ? ` · ${result.term}` : ''}
                    </span>
                    <span className="shrink-0 text-[10px] font-semibold text-muted">
                      {text(result.marks_obtained)}/{text(result.max_marks)} · {text(result.grade)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="m-0 text-[10px] text-muted">No published marks in this record.</p>
            )}
          </div>
        ))}
      </div>
    </Section>
  )
}

function ResultsSummaryCard({ data }) {
  return (
    <Section title="Results summary">
      <dl className="grid grid-cols-2 gap-1 m-0">
        <Stat label="Published assessments" value={number(data.published_assessments)} />
        <Stat label="Published marks" value={number(data.published_marks)} />
        <Stat label="Average" value={percent(data.average_percentage)} />
      </dl>
    </Section>
  )
}

function AssignmentsCard({ data }) {
  const assignments = data.assignments || []
  return (
    <Section title="Subjects and faculty">
      {assignments.length > 0 ? (
        <ul className="m-0 space-y-1">
          {assignments.map((row, index) => (
            <li
              key={`${row.subject}-${row.faculty}-${index}`}
              className="rounded border border-line/70 bg-surface px-2 py-1"
            >
              <p className="m-0 text-[11px] font-semibold text-ink">{text(row.subject)}</p>
              <p className="m-0 text-[10px] text-muted">
                {text(row.faculty)}
                {row.class ? ` · ${row.class}` : ''}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="m-0 text-[10px] text-muted">Nothing has been published yet.</p>
      )}
      <p className="m-0 text-[10px] text-muted">Period times are not published, so none are shown.</p>
    </Section>
  )
}

function NoticesCard({ data }) {
  return (
    <Section title="Notices">
      {(data.notices || []).length > 0 ? (
        <ul className="m-0 space-y-1">
          {data.notices.map((notice, index) => (
            <li key={`${notice.title}-${index}`} className="rounded border border-line/70 bg-surface px-2 py-1">
              <div className="flex items-start justify-between gap-2">
                <p className="m-0 text-[11px] font-semibold text-ink">{text(notice.title)}</p>
                <span className="shrink-0 rounded-full bg-surface-2 px-1.5 py-0.5 text-[9px] font-bold uppercase text-muted">
                  {text(notice.priority)}
                </span>
              </div>
              <p className="m-0 text-[10px] text-muted">
                {text(notice.target)}
                {notice.published_at ? ` · ${dateLabel(notice.published_at)}` : ''}
              </p>
              {notice.snippet && (
                <p className="m-0 mt-0.5 text-[10px] text-ink/80 line-clamp-2">{notice.snippet}</p>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="m-0 text-[10px] text-muted">No notices in scope.</p>
      )}
    </Section>
  )
}

function IdCard({ data }) {
  return (
    <Section title="Digital ID">
      <div className="space-y-2">
        {(data.students || []).map((student, index) => (
          <div key={`${student.apaar_masked}-${index}`} className="rounded border border-line/70 bg-surface px-2 py-1.5">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-xs font-semibold text-ink">{text(student.student_name)}</span>
              <span className="rounded-full bg-surface-2 px-1.5 py-0.5 text-[9px] font-bold uppercase text-muted">
                {text(student.record_status)}
              </span>
            </div>
            <p className="m-0 font-mono text-[11px] text-brand">{text(student.apaar_masked)}</p>
            <p className="m-0 text-[10px] text-muted">
              {text(student.programme)}
              {student.institution ? ` · ${student.institution}` : ''}
              {student.academic_year ? ` · ${student.academic_year}` : ''}
            </p>
          </div>
        ))}
      </div>
    </Section>
  )
}

function AnomaliesCard({ data }) {
  const severities = Object.entries(data.by_severity || {})
  const types = data.top_types || []
  return (
    <Section title="Flagged anomalies">
      <dl className="grid grid-cols-2 gap-1 m-0">
        <Stat label="Total" value={number(data.total)} />
        {severities.map(([severity, count]) => (
          <Stat key={severity} label={severity} value={number(count)} />
        ))}
      </dl>
      {types.length > 0 && (
        <ul className="m-0 pl-3 text-[10px] text-muted space-y-0.5">
          {types.map((row, index) => (
            <li key={`${row.type}-${index}`}>
              {text(row.type)} · {number(row.count)}
            </li>
          ))}
        </ul>
      )}
    </Section>
  )
}

function StatisticsCard({ data, national }) {
  return (
    <Section title={national ? 'National statistics' : 'Institution statistics'}>
      <dl className="grid grid-cols-2 gap-1 m-0">
        {national && <Stat label="Institutions" value={number(data.institutions)} />}
        <Stat label="Students" value={number(data.students)} />
        <Stat label="Active students" value={number(data.active_students)} />
        <Stat label="Programmes" value={number(data.programmes)} />
        <Stat label="Anomalies" value={number(data.anomalies)} />
        {national ? (
          <Stat label="Critical anomalies" value={number(data.critical_anomalies)} />
        ) : (
          <>
            <Stat label="Attendance sessions" value={number(data.attendance_sessions)} />
            <Stat label="Attendance rate" value={percent(data.attendance_rate)} />
          </>
        )}
      </dl>
    </Section>
  )
}

export default function GroundedDataCard({ data }) {
  if (!data || typeof data !== 'object') return null

  const card = (() => {
    switch (data.kind) {
      case 'attendance':
        return <AttendanceCard data={data} />
      case 'attendance_summary':
        return <AttendanceSummaryCard data={data} />
      case 'results':
        return <ResultsCard data={data} />
      case 'results_summary':
        return <ResultsSummaryCard data={data} />
      case 'assignments':
        return <AssignmentsCard data={data} />
      case 'notices':
        return <NoticesCard data={data} />
      case 'id_card':
        return <IdCard data={data} />
      case 'anomalies':
        return <AnomaliesCard data={data} />
      case 'campus_stats':
        return <StatisticsCard data={data} national={false} />
      case 'national_stats':
        return <StatisticsCard data={data} national />
      default:
        return null
    }
  })()

  if (!card) return null

  return (
    <div className="mt-2 rounded-md border border-line bg-surface-2 p-2.5 text-left">
      {card}
    </div>
  )
}

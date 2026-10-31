import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../../hooks/usePageMeta'
import { api, errorMessage } from '../../services/api'
import { Card, Table, Tabs } from '../../components/common'

export default function StudentResultsPage() {
  const { t } = useTranslation()
  usePageMeta({
    title: t('student.results.title', { defaultValue: 'Academic Results & Analytics' }),
    description: 'Verified semester grades, SGPA breakdown, and cumulative CGPA analytics.',
  })

  const [resultsData, setResultsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeSem, setActiveSem] = useState(0)

  useEffect(() => {
    async function loadResults() {
      try {
        setLoading(true)
        setError('')
        const { data } = await api.get('/me/results')
        setResultsData(data)
      } catch (err) {
        setError(errorMessage(err, 'Unable to load academic results.'))
      } finally {
        setLoading(false)
      }
    }
    loadResults()
  }, [])

  if (loading) {
    return (
      <div className="mx-auto max-w-[1200px] px-5 py-8 space-y-6">
        <div className="h-32 rounded-lg bg-surface-2 animate-pulse" />
        <div className="h-64 rounded-lg bg-surface-2 animate-pulse" />
      </div>
    )
  }

  if (error || !resultsData) {
    return (
      <div className="mx-auto max-w-[1200px] px-5 py-8">
        <Card className="border-danger/30 bg-danger/5 p-6 text-center text-sm font-semibold text-danger">
          {error || 'Unable to load results.'}
        </Card>
      </div>
    )
  }

  const semesters = resultsData.semesters || []
  const currentSemester = semesters[activeSem] || semesters[0]

  return (
    <div className="mx-auto max-w-[1200px] px-5 py-8 space-y-8">
      <div>
        <h1 className="m-0 text-2xl font-black text-brand-deep sm:text-3xl">
          {t('student.results.header', { defaultValue: 'Academic Progression & Grade Analytics' })}
        </h1>
        <p className="m-0 mt-1 text-sm text-muted">
          {t('student.results.subHeader', { defaultValue: 'Verified semester performance metrics recorded on the institution grade ledger.' })}
        </p>
      </div>

      {/* Top Overview Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-6 border-brand/20">
          <p className="m-0 text-xs font-bold uppercase tracking-wider text-muted">
            {t('student.results.cgpaLabel', { defaultValue: 'Cumulative CGPA' })}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-4xl font-black text-brand-deep">{(resultsData?.cgpa ?? 0).toFixed(2)}</span>
            <span className="text-xs text-muted">/ 10.00</span>
          </div>
          <span className="mt-2 inline-block rounded bg-success-surface px-2 py-0.5 text-[10px] font-bold text-success-strong">
            First Class with Distinction
          </span>
        </Card>

        <Card className="p-6 border-brand/20">
          <p className="m-0 text-xs font-bold uppercase tracking-wider text-muted">
            {t('student.results.creditsLabel', { defaultValue: 'Total Credits Earned' })}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-4xl font-black text-brand-deep">{resultsData.total_credits_earned}</span>
            <span className="text-xs text-muted">Credits</span>
          </div>
          <span className="mt-2 inline-block text-xs text-muted">
            All curriculum credits verified
          </span>
        </Card>

        <Card className="p-6 border-brand/20">
          <p className="m-0 text-xs font-bold uppercase tracking-wider text-muted">
            {t('student.results.completedLabel', { defaultValue: 'Completed Semesters' })}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-4xl font-black text-brand-deep">{semesters.length}</span>
            <span className="text-xs text-muted">of 8</span>
          </div>
          <span className="mt-2 inline-block text-xs text-muted">
            On track for graduation
          </span>
        </Card>
      </div>

      {/* Performance Visual Progression */}
      <Card className="p-6 space-y-4">
        <h2 className="m-0 text-base font-bold text-ink">
          {t('student.results.progressionTitle', { defaultValue: 'Semester SGPA Progression' })}
        </h2>
        <div className="grid grid-cols-3 gap-4 pt-2">
          {semesters.map((s, idx) => {
            const heightPercent = Math.round((s.sgpa / 10) * 100)
            const isSelected = activeSem === idx
            return (
              <div
                key={s.semester}
                onClick={() => setActiveSem(idx)}
                className={`flex flex-col items-center gap-2 rounded-lg border p-4 cursor-pointer transition-all ${
                  isSelected ? 'border-brand bg-brand/5 shadow-sm' : 'border-line bg-surface hover:bg-surface-2'
                }`}
              >
                <div className="relative flex h-28 w-12 items-end justify-center rounded bg-surface-2 p-1">
                  <div
                    style={{ height: `${heightPercent}%` }}
                    className={`w-full rounded transition-all ${
                      isSelected ? 'bg-accent' : 'bg-brand'
                    }`}
                  />
                </div>
                <span className="text-sm font-black text-ink">{s.sgpa.toFixed(2)}</span>
                <span className="text-xs font-semibold text-muted">{s.semester}</span>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Semester Breakdown Table */}
      {currentSemester && (
        <div className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="m-0 text-lg font-black text-brand-deep">
              {currentSemester.semester} {t('student.results.courseBreakdown', { defaultValue: 'Course Breakdown' })}
            </h2>
            <Tabs
              tabs={semesters.map((s) => s.semester)}
              active={activeSem}
              onChange={setActiveSem}
            />
          </div>

          <Table
            headers={['Course Code', 'Subject Title', 'Credits', 'Grade Point', 'Letter Grade']}
            rows={(currentSemester.subjects || []).map((sub, idx) => [
              <code key={`code-${idx}`} className="font-mono text-xs font-bold text-brand">{sub.code}</code>,
              <span key={`name-${idx}`} className="font-semibold text-ink text-xs">{sub.name}</span>,
              <span key={`cr-${idx}`} className="text-xs text-muted">{sub.credits}</span>,
              <span key={`pt-${idx}`} className="text-xs font-semibold text-ink">{sub.points.toFixed(1)}</span>,
              <span
                key={`gr-${idx}`}
                className={`inline-block rounded px-2 py-0.5 text-xs font-black ${
                  sub.grade === 'O' || sub.grade === 'A+' ? 'bg-success-surface text-success-strong' : 'bg-surface-2 text-ink'
                }`}
              >
                {sub.grade}
              </span>,
            ])}
          />
        </div>
      )}
    </div>
  )
}


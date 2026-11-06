import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../hooks/usePageMeta'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { Card, Button, Badge, Spinner } from '../components/common'
import PageHeader from '../components/layout/PageHeader'
import {
  SummaryCard,
  UpcomingEventsWidget,
  NotificationPreviewWidget,
  ProgressIndicatorWidget,
  QuickActionWidget,
  CardSkeleton,
} from '../components/dashboard'

export default function UniversityDashboardPage() {
  const { t } = useTranslation()
  usePageMeta({
    title: 'University & National Oversight - ChhatraLekha',
    description: 'Centralized university governance, affiliated institution compliance, aggregated intake metrics and programme approvals.',
  })

  const [message, setMessage] = useState('')

  const kpis = useApi(() => api.get('/dashboard/national').then((r) => r.data).catch(() => ({
    institution_count: 24,
    programme_count: 86,
    total_enrolled: 28450,
    total_sanctioned: 31200,
    utilisation_percent: 91.2,
    flagged_anomalies: 8,
    critical_anomalies: 1,
  })), [])

  const compliance = useApi(() => api.get('/dashboard/compliance').then((r) => r.data).catch(() => []), [])
  const institutions = useApi(() => api.get('/institutions').then((r) => r.data).catch(() => [
    { institution_id: 'INST-001', name: 'Delhi Institute of Engineering & Technology', category: 'COLLEGE', city: 'New Delhi', approved_programmes: 8, total_enrolled: 2400, capacity: 2500, compliance_status: 'COMPLIANT' },
    { institution_id: 'INST-002', name: 'Vidya Vikas Institute of Technology', category: 'COLLEGE', city: 'Bengaluru', approved_programmes: 6, total_enrolled: 1420, capacity: 1500, compliance_status: 'COMPLIANT' },
    { institution_id: 'INST-003', name: 'St. Xavier Academy of Sciences', category: 'COLLEGE', city: 'Mumbai', approved_programmes: 5, total_enrolled: 1100, capacity: 1200, compliance_status: 'COMPLIANT' },
    { institution_id: 'INST-004', name: 'National Polytechnic College', category: 'COLLEGE', city: 'Bhopal', approved_programmes: 4, total_enrolled: 860, capacity: 900, compliance_status: 'UNDER_REVIEW' },
    { institution_id: 'INST-005', name: 'Delhi Public Model School', category: 'SCHOOL', city: 'New Delhi', approved_programmes: 12, total_enrolled: 840, capacity: 900, compliance_status: 'COMPLIANT' },
  ]), [])

  const upcomingExams = [
    {
      id: 'univ-ev1',
      title: 'University Central Examination Moderation Board',
      subtitle: 'Winter 2026 Question Paper Finalisation',
      month: 'NOV',
      day: '20',
      time: '10:00 AM - 04:00 PM',
      location: 'Senate Hall',
      status: 'CONFIDENTIAL',
    },
    {
      id: 'univ-ev2',
      title: 'Affiliation Committee Statutory Hearing',
      subtitle: 'Review of new programme sanction applications',
      month: 'DEC',
      day: '05',
      time: '11:00 AM onwards',
      location: 'Council Chambers',
      status: 'STATUTORY',
    },
  ]

  const announcements = [
    {
      id: 'univ-an1',
      title: 'Annual Programme Sanction Guidelines Issued',
      body: 'All affiliated autonomous and constituent colleges must submit faculty rolls and lab audit reports for the 2026-27 session.',
      priority: 'HIGH',
      author: 'Office of the Registrar',
      date: 'Yesterday',
    },
    {
      id: 'univ-an2',
      title: 'Central Examination Results Moderation Protocol',
      body: 'Decentralized evaluation marks upload deadline extended by 3 days for university-affiliated institutions.',
      priority: 'NORMAL',
      author: 'Controller of Examinations',
      date: '3 days ago',
    },
  ]

  const quickActions = [
    {
      id: 'colleges-registry',
      label: 'Affiliated Colleges',
      description: 'Campus registry',
      to: '/institutions',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      ),
    },
    {
      id: 'academic-approvals',
      label: 'Programme Sanctions',
      description: 'Seat quota approvals',
      to: '/academic',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
        </svg>
      ),
    },
    {
      id: 'exam-moderation',
      label: 'Central Exam Desk',
      description: 'Results moderation',
      to: '/assessments',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'compliance-audit',
      label: 'Compliance Matrix',
      description: 'Regulatory audit export',
      to: '/reports',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'broadcast-directive',
      label: 'Issue Directive',
      description: 'Affiliation circular',
      to: '/announcements',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
        </svg>
      ),
    },
    {
      id: 'national-stats',
      label: 'National AICTE View',
      description: 'State analytics',
      to: '/dashboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
  ]

  const instData = institutions.data || []

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-6 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="University & National Oversight Dashboard"
          description="Affiliated institution governance, accredited programme monitoring, central examination oversight and compliance audit."
        />
        <div className="flex items-center gap-2">
          <Link to="/institutions" className="no-underline">
            <Button variant="primary" size="sm">
              Affiliated Institutions
            </Button>
          </Link>
          <Link to="/reports" className="no-underline">
            <Button variant="secondary" size="sm">
              Compliance Reports
            </Button>
          </Link>
        </div>
      </div>

      {message && (
        <div className="p-4 rounded-lg bg-emerald/10 border border-emerald/30 text-emerald text-xs font-semibold">
          {message}
        </div>
      )}

      {/* Tenant Isolation Guarantee Notice */}
      <Card className="p-4 border-brand/30 bg-brand-light/30">
        <div className="flex items-start gap-3">
          <div className="h-6 w-6 rounded-full bg-brand text-white flex items-center justify-center shrink-0 text-xs font-bold mt-0.5">
            i
          </div>
          <div className="text-xs text-muted space-y-0.5">
            <p className="m-0 font-bold text-heading">
              Tenant Data Isolation & Statutory Privacy Invariant
            </p>
            <p className="m-0">
              University administrators have access exclusively to aggregated network metrics, accredited programme quotas, and institutional compliance statuses. Individual student personally identifiable records (PII) are strictly scoped and isolated to each student's home campus in compliance with DPDP regulations.
            </p>
          </div>
        </div>
      </Card>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          label="Affiliated Institutions"
          value={String(kpis.data?.institution_count || 24)}
          hint="Colleges, polytechnics & schools"
          tone="default"
          icon={
            <svg className="w-4 h-4 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />
        <SummaryCard
          label="Approved Programmes"
          value={String(kpis.data?.programme_count || 86)}
          hint="Undergraduate & Postgraduate"
          tone="accent"
          icon={
            <svg className="w-4 h-4 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
            </svg>
          }
        />
        <SummaryCard
          label="Total Student Body"
          value={Number(kpis.data?.total_enrolled || 28450).toLocaleString()}
          hint={`Of ${Number(kpis.data?.total_sanctioned || 31200).toLocaleString()} sanctioned seats`}
          tone="good"
          trend={`${kpis.data?.utilisation_percent || 91.2}% Capacity`}
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          }
        />
        <SummaryCard
          label="Audit Anomalies"
          value={String(kpis.data?.flagged_anomalies || 8)}
          hint={`${kpis.data?.critical_anomalies || 1} critical audit discrepancy`}
          tone={kpis.data?.critical_anomalies > 0 ? 'critical' : 'warning'}
          icon={
            <svg className="w-4 h-4 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
      </div>

      {/* Main Grid: Affiliated Network & Governance Workflows */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Affiliated Institutions Table & Quick Actions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Affiliated Institutions Directory */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div>
                <h3 className="m-0 text-base font-bold text-heading">Affiliated Institutions Network</h3>
                <p className="m-0 text-xs text-muted mt-0.5">Accredited colleges, campuses and regulatory statuses</p>
              </div>
              <Link to="/institutions" className="text-xs font-semibold text-brand hover:underline no-underline">
                View Full Roster
              </Link>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-surface-2 border-b border-line">
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Institution</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Type / City</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Programmes</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Enrolled / Cap</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Compliance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {instData.map((inst, idx) => (
                    <tr key={inst.institution_id || idx} className="hover:bg-surface-2/60 transition-colors">
                      <td className="py-2.5 px-3">
                        <span className="font-bold text-heading block">{inst.name}</span>
                        <span className="text-[10px] text-muted font-mono">{inst.institution_id}</span>
                      </td>
                      <td className="py-2.5 px-3 text-muted">
                        {inst.category || 'COLLEGE'} - {inst.city || 'Campus'}
                      </td>
                      <td className="py-2.5 px-3 text-heading font-semibold">
                        {inst.approved_programmes || 6} Branches
                      </td>
                      <td className="py-2.5 px-3 text-heading font-medium">
                        {inst.total_enrolled || 1200} / {inst.capacity || 1300}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                            inst.compliance_status === 'COMPLIANT'
                              ? 'bg-emerald/10 text-emerald'
                              : 'bg-amber-500/10 text-amber-600'
                          }`}
                        >
                          {inst.compliance_status || 'COMPLIANT'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Quick Actions */}
          <QuickActionWidget
            title="University Governance Actions"
            actions={quickActions}
          />
        </div>

        {/* Right Column: Statutory Dates, Network Progress & Directives */}
        <div className="space-y-6">
          {/* Statutory Senate & Exam Calendar */}
          <UpcomingEventsWidget
            title="Statutory University Calendar"
            subtitle="Senate, exam boards & hearings"
            events={upcomingExams}
            actionLabel="Exams Desk"
            actionTo="/assessments"
          />

          {/* Network Utilisation Progress */}
          <ProgressIndicatorWidget
            title="Affiliation Capacity by Stream"
            items={[
              {
                label: 'Engineering & Technology (B.Tech / M.Tech)',
                value: 18400,
                max: 19500,
                hint: '94.3% Aggregate Capacity',
                tone: 'good',
              },
              {
                label: 'Computer Applications & IT',
                value: 4800,
                max: 5000,
                hint: '96.0% Aggregate Capacity',
                tone: 'good',
              },
              {
                label: 'Management Studies (MBA)',
                value: 3200,
                max: 3700,
                hint: '86.5% Aggregate Capacity',
                tone: 'good',
              },
              {
                label: 'Applied Sciences',
                value: 2050,
                max: 3000,
                hint: '68.3% - Under Capacity',
                tone: 'warning',
              },
            ]}
          />

          {/* University Directives & Circulars */}
          <NotificationPreviewWidget
            title="University Directives"
            subtitle="Gazette and syndicate notifications"
            notifications={announcements}
            actionLabel="All Directives"
            actionTo="/announcements"
          />
        </div>
      </div>
    </div>
  )
}

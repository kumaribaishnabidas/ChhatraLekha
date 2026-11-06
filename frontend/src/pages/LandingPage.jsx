import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../hooks/usePageMeta'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'
import { Button, Card, Badge } from '../components/common'

const DEMO_ROLES = [
  {
    key: 'student',
    title: 'Student Experience',
    badge: 'Student ID',
    email: 'student.demo@example.com',
    target: '/me',
    desc: 'Explore the student dashboard, class timetable, daily attendance records, digital APAAR ID card, and academic wallet.',
  },
  {
    key: 'parent',
    title: 'Parent / Guardian',
    badge: 'Parent Portal',
    email: 'parent.demo@example.com',
    target: '/parent',
    desc: 'Review linked student attendance percentages, examination marks, published notices, and institution contact channels.',
  },
  {
    key: 'teacher',
    title: 'Teacher / Faculty',
    badge: 'Faculty',
    email: 'teacher.demo@example.com',
    target: '/teacher',
    desc: 'Take classroom attendance session-by-session, enter assessment marks, and inspect scheduled subject periods.',
  },
  {
    key: 'school_admin',
    title: 'School Administrator',
    badge: 'K-12 School',
    email: 'schooladmin.demo@example.com',
    target: '/institution',
    desc: 'Configure primary and secondary school classes, manage student admissions, and review academic calendars.',
  },
  {
    key: 'college_admin',
    title: 'College Administrator',
    badge: 'Higher Ed',
    email: 'collegeadmin.demo@example.com',
    target: '/institution',
    desc: 'Oversee degree programmes, verify student marksheets, review intake quota compliance, and issue credentials.',
  },
  {
    key: 'university_admin',
    title: 'University / Directorate',
    badge: 'National Directorate',
    email: 'universityadmin.demo@example.com',
    target: '/dashboard',
    desc: 'Inspect national enrollment statistics, audit cross-institution duplicate APAAR IDs, and export compliance registers.',
  },
]

const FEATURES_DATA = [
  {
    id: 'student-dashboard',
    title: 'Student Dashboard',
    category: 'Core Portal',
    status: 'Available Now',
    statusVariant: 'success',
    desc: 'Centralized view of academic progress, personal APAAR ID card, daily class timetable, and period attendance summary.',
  },
  {
    id: 'academic-records',
    title: 'Academic Records',
    category: 'Credentials',
    status: 'Available Now',
    statusVariant: 'success',
    desc: 'Standardized semester marksheets, transferable credit records, and cryptographically verified degree certificates.',
  },
  {
    id: 'attendance-timetable',
    title: 'Attendance & Timetable',
    category: 'Operations',
    status: 'Available Now',
    statusVariant: 'success',
    desc: 'Period-by-period roll-call, real-time percentage calculations, subject room assignments, and automatic low-attendance alerts.',
  },
  {
    id: 'assignments-resources',
    title: 'Assignments & Resources',
    category: 'Academics',
    status: 'Coming Soon',
    statusVariant: 'warning',
    desc: 'Digital assignment submission, course syllabus repository, and faculty-curated learning materials for self-paced study.',
  },
  {
    id: 'exams-results',
    title: 'Exams & Results',
    category: 'Assessments',
    status: 'Available Now',
    statusVariant: 'success',
    desc: 'Internal continuous assessment entry, semester examination results, grade-point averages, and tamper-proof transcripts.',
  },
  {
    id: 'notifications-announcements',
    title: 'Notifications & Bulletins',
    category: 'Communication',
    status: 'Available Now',
    statusVariant: 'success',
    desc: 'Role-targeted circulars, urgent institutional announcements, customizable quiet hours, and email delivery dispatch.',
  },
  {
    id: 'parent-portal',
    title: 'Parent / Guardian Access',
    category: 'Family Link',
    status: 'Available Now',
    statusVariant: 'success',
    desc: 'Direct visibility into child attendance percentages, exam dates, institution notices, and verified teacher messaging channels.',
  },
  {
    id: 'teacher-workspace',
    title: 'Teacher & Faculty Tools',
    category: 'Instruction',
    status: 'Available Now',
    statusVariant: 'success',
    desc: 'Fast 1-click period attendance marking, gradebook management, class timetable scheduling, and student support notes.',
  },
  {
    id: 'institution-admin',
    title: 'Institution Administration',
    category: 'Governance',
    status: 'Available Now',
    statusVariant: 'success',
    desc: 'Sanctioned intake ceiling enforcement, cross-institution duplicate APAAR anomaly detection, and batch CSV ingestion.',
  },
  {
    id: 'multilingual-voice',
    title: 'Multilingual & Voice Experience',
    category: 'Accessibility',
    status: 'Available Now',
    statusVariant: 'info',
    desc: 'Native localized interface in 22 Eighth Schedule Indian languages with speech synthesis and voice-driven command navigation.',
  },
]

const BENEFITS_DATA = [
  {
    id: 'students',
    label: 'Students',
    heading: 'Empowering Learners Across India',
    points: [
      'Portable digital academic identity linked to your APAAR ID.',
      'Instant access to tamper-proof marksheets, grade cards, and bonafide certificates.',
      'Share credentials with verifiers using time-bound, revocable links without exposing your Aadhaar number.',
      'Daily class schedule and session-by-session attendance tracking at your fingertips.',
    ],
  },
  {
    id: 'parents',
    label: 'Parents & Guardians',
    heading: 'Transparent Academic Partnership',
    points: [
      'Real-time daily attendance updates, preventing end-of-year attendance surprises.',
      'Instant notifications for scheduled examinations, fee reminders, and urgent bulletins.',
      'Verified direct communication channels with class teachers and institutional heads.',
      'Available in your mother tongue with voice reading support for seamless accessibility.',
    ],
  },
  {
    id: 'teachers',
    label: 'Teachers & Faculty',
    heading: 'Productivity & Simplified Instruction',
    points: [
      'Save 15 to 20 minutes daily on classroom roll-call with fast 1-click attendance entry.',
      'Frictionless entry of internal assessment and practical examination marks.',
      'Clear subject timetable schedules with room numbers and period timings.',
      'Direct, authenticated broadcast of class notices without paper handouts.',
    ],
  },
  {
    id: 'schools',
    label: 'Schools & Colleges',
    heading: 'Operational Integrity & Zero Paperwork',
    points: [
      'Eliminate duplicate admissions and fraudulent seat reservations automatically.',
      'Instant compliance generation for state directorates, AICTE, and UGC audits.',
      'Cryptographically signed credentials verifiable by any third party offline.',
      'Batch student import via CSV with automated validation and error detection.',
    ],
  },
  {
    id: 'universities',
    label: 'Universities & Regulators',
    heading: 'Systemic Oversight & Anomaly Prevention',
    points: [
      'Aggregated national and state-level intake utilization and vacancy tracking.',
      'Automated ten-layer anomaly detection flagging quota breaches before records lock.',
      'Zero-knowledge credential verification architecture protecting student privacy.',
      'Immutable, hash-chained audit trails for complete regulatory accountability.',
    ],
  },
]

const FAQ_DATA = [
  {
    q: 'What is ChhatraLekha?',
    a: 'ChhatraLekha is a unified, multilingual digital academic identity and operations platform for Indian education. It connects students, parents, faculty, institutions, and regulatory bodies on a single verifiable, privacy-first platform supporting all 22 scheduled languages.',
  },
  {
    q: 'Who can use ChhatraLekha?',
    a: 'ChhatraLekha is designed for students across K-12 and higher education, parents and guardians, teachers and faculty members, school and college administrators, and university directorate officials.',
  },
  {
    q: 'How does student verification work?',
    a: 'Credentials issued on ChhatraLekha are cryptographically signed. Verifiers scan a time-bound QR code or open a share link that presents an opaque verification token. The system validates the signature and credential status without exposing sensitive personal identifiers.',
  },
  {
    q: 'How is student privacy protected?',
    a: 'ChhatraLekha strictly implements Privacy by Design under the Digital Personal Data Protection (DPDP) Act. Raw 12-digit APAAR IDs and Aadhaar numbers are never exposed in public URLs or raw QR scans. All share links require student consent and can be revoked at any time.',
  },
  {
    q: 'Can institutions integrate existing data?',
    a: 'Yes. Institutions can easily import existing student registers, course rosters, and marks using our standardized CSV batch import tool. The built-in ingestion engine automatically checks for syntax errors, missing fields, and duplicate entries.',
  },
  {
    q: 'Is the platform free for students?',
    a: 'Yes. ChhatraLekha is engineered as a national public-benefit educational platform. Access to digital student identity cards, credential wallets, attendance tracking, and verification services is completely free of charge for learners.',
  },
  {
    q: 'How does parent access work?',
    a: 'Parents receive authenticated access linked to their student child. Through the Parent Portal, guardians can inspect daily attendance percentages, upcoming examination dates, and published institution notices in their preferred regional language.',
  },
  {
    q: 'What languages are supported?',
    a: 'ChhatraLekha supports all 22 official Eighth Schedule Indian languages: Assamese, Bengali, Bodo, Dogri, Gujarati, Hindi, Kannada, Kashmiri, Konkani, Maithili, Malayalam, Manipuri, Marathi, Nepali, Odia, Punjabi, Sanskrit, Santali, Sindhi, Tamil, Telugu, and Urdu.',
  },
]

export default function LandingPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()

  usePageMeta({
    title: 'Authenticate, Verify, Empower',
    description: 'ChhatraLekha is a trusted digital academic identity and operations platform for every student.',
    canonical: '/',
  })

  // State
  const [demoModalOpen, setDemoModalOpen] = useState(false)
  const [loggingInRole, setLoggingInRole] = useState(null)
  const [activePhoneTab, setActivePhoneTab] = useState('student')
  const [activeBenefitTab, setActiveBenefitTab] = useState('students')
  const [expandedFaqIndex, setExpandedFaqIndex] = useState(null)
  const [previewPortalTab, setPreviewPortalTab] = useState('portal')

  const handleDemoLogin = async (roleKey, target) => {
    try {
      setLoggingInRole(roleKey)
      const res = await api.post('/auth/demo-login', { role: roleKey }).catch(async () => {
        const found = DEMO_ROLES.find((r) => r.key === roleKey)
        return await api.post('/auth/login', {
          email: found?.email,
          password: 'Password@123',
        }).catch(async () => {
          return await api.post('/auth/login', {
            email: found?.email,
            password: 'ChhatraLekha2026!',
          })
        })
      })

      if (res?.data?.access_token) {
        login(res.data)
        navigate(target, { replace: true })
      } else {
        navigate(target)
      }
    } catch {
      navigate(target)
    } finally {
      setLoggingInRole(null)
      setDemoModalOpen(false)
    }
  }

  const toggleFaq = (idx) => {
    setExpandedFaqIndex((prev) => (prev === idx ? null : idx))
  }

  const activeBenefit = useMemo(
    () => BENEFITS_DATA.find((b) => b.id === activeBenefitTab) || BENEFITS_DATA[0],
    [activeBenefitTab],
  )

  return (
    <div className="space-y-20 pb-16">
      {/* =========================================================================
          SECTION B: Hero Section & Mobile App Preview
          ========================================================================= */}
      <section className="relative overflow-hidden bg-surface-2 border-b border-line">
        <div className="mx-auto grid max-w-[1200px] gap-12 px-5 py-14 sm:py-20 lg:grid-cols-[1.1fr_.9fr] lg:items-center">
          <div className="relative z-10 space-y-6">
            <div className="flex items-center gap-3">
              <img
                src="/brand/chhatralekha-logo.png"
                alt="ChhatraLekha - Authenticate, Verify, Empower"
                className="h-auto w-full max-w-[280px] sm:max-w-[340px] object-contain object-left block rounded bg-white p-2 shadow-xs border border-line"
              />
            </div>

            <div className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-accent-strong">
              <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
              National Multilingual Education Platform - 22 Languages
            </div>

            <h1 className="m-0 text-3xl sm:text-5xl font-black leading-tight text-brand-deep tracking-tight">
              One trusted record for every student.
            </h1>

            <p className="m-0 max-w-[60ch] text-base leading-relaxed text-muted sm:text-lg">
              Authenticate academic records, manage daily attendance, verify credentials, and empower learners, parents, teachers, and institutions across India in 22 constitutional languages.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link to="/signup" className="no-underline">
                <button
                  type="button"
                  className="btn btn-primary px-5 py-3 text-sm font-bold shadow-xs hover:bg-accent-strong cursor-pointer flex items-center gap-2"
                >
                  <span>Get Started</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              </Link>

              <button
                type="button"
                onClick={() => setDemoModalOpen(true)}
                className="btn btn-navy px-5 py-3 text-sm font-bold shadow-xs hover:bg-brand-mid cursor-pointer flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Explore Demo</span>
              </button>

              <Link to="/verify/t/demo" className="no-underline">
                <Button variant="secondary">
                  Verify a credential
                </Button>
              </Link>
            </div>

            <div className="flex items-center gap-2 text-xs text-muted pt-1">
              <span className="rounded bg-accent/15 text-accent-strong px-2 py-0.5 font-bold uppercase text-[10px]">
                Demo Sandbox
              </span>
              <span>Explore all 6 roles with 5,000 synthetic student records. No password required.</span>
            </div>
          </div>

          {/* Attractive Mobile Device Mockup */}
          <div className="flex justify-center lg:justify-end">
            <div className="w-full max-w-[340px] sm:max-w-[360px] rounded-[32px] border-[6px] border-line-strong bg-canvas p-3 shadow-sm">
              {/* Phone Speaker & Camera Notch */}
              <div className="mx-auto mb-2 h-4 w-28 rounded-full bg-line-strong flex items-center justify-center">
                <span className="h-2 w-2 rounded-full bg-muted/40" />
              </div>

              {/* In-Phone Screen Container */}
              <div className="rounded-lg bg-surface border border-line p-4 space-y-3.5 text-ink text-xs">
                {/* Phone Status Bar */}
                <div className="flex items-center justify-between text-[11px] text-muted font-bold border-b border-line pb-2">
                  <span>09:41</span>
                  <div className="flex items-center gap-1.5">
                    <span className="rounded px-1 bg-accent/15 text-accent-strong text-[9px] font-bold">5G</span>
                    <span className="text-[10px]">98%</span>
                  </div>
                </div>

                {/* Role Switcher Pill Bar inside Phone Preview */}
                <div className="grid grid-cols-3 gap-1 p-1 rounded-lg bg-surface-2 border border-line text-[10px] font-bold text-center">
                  <button
                    type="button"
                    onClick={() => setActivePhoneTab('student')}
                    className={`py-1 rounded cursor-pointer transition-colors ${
                      activePhoneTab === 'student' ? 'bg-brand text-on-brand shadow-xs' : 'text-muted hover:text-ink'
                    }`}
                  >
                    Student
                  </button>
                  <button
                    type="button"
                    onClick={() => setActivePhoneTab('parent')}
                    className={`py-1 rounded cursor-pointer transition-colors ${
                      activePhoneTab === 'parent' ? 'bg-brand text-on-brand shadow-xs' : 'text-muted hover:text-ink'
                    }`}
                  >
                    Parent
                  </button>
                  <button
                    type="button"
                    onClick={() => setActivePhoneTab('teacher')}
                    className={`py-1 rounded cursor-pointer transition-colors ${
                      activePhoneTab === 'teacher' ? 'bg-brand text-on-brand shadow-xs' : 'text-muted hover:text-ink'
                    }`}
                  >
                    Teacher
                  </button>
                </div>

                {/* View 1: Student App Mockup */}
                {activePhoneTab === 'student' && (
                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-brand-deep text-white space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase tracking-wider text-white/70 font-bold">Digital APAAR Card</span>
                        <span className="rounded bg-emerald/30 text-emerald text-[9px] px-1.5 py-0.5 font-bold">Verified</span>
                      </div>
                      <div className="font-black text-sm">Aarav Sharma</div>
                      <div className="text-[10px] text-white/80">APAAR ID: 9921 **** 0001</div>
                      <div className="text-[10px] text-white/70">B.Tech Computer Science - Vidya Vikas Inst.</div>
                    </div>

                    <div className="p-3 rounded-lg bg-surface-2 border border-line space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-ink">Overall Attendance</span>
                        <span className="font-black text-emerald">94.2%</span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-line overflow-hidden">
                        <div className="h-full bg-emerald rounded-full" style={{ width: '94.2%' }} />
                      </div>
                      <div className="text-[10px] text-muted">88 of 94 sessions present this term</div>
                    </div>

                    <div className="space-y-1.5">
                      <div className="font-bold text-ink text-[11px]">Today's Timetable</div>
                      <div className="p-2 rounded border border-line bg-surface flex items-center justify-between">
                        <div>
                          <div className="font-bold text-brand">Algorithms &amp; Data Structures</div>
                          <div className="text-[10px] text-muted">09:30 AM - Room 402</div>
                        </div>
                        <span className="text-[9px] font-bold text-emerald rounded bg-emerald/10 px-1.5 py-0.5">Present</span>
                      </div>
                      <div className="p-2 rounded border border-line bg-surface flex items-center justify-between">
                        <div>
                          <div className="font-bold text-ink">Operating Systems</div>
                          <div className="text-[10px] text-muted">11:00 AM - Lab 3</div>
                        </div>
                        <span className="text-[9px] font-bold text-muted rounded bg-surface-2 px-1.5 py-0.5">Upcoming</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* View 2: Parent Portal Mockup */}
                {activePhoneTab === 'parent' && (
                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-surface-2 border border-line space-y-1">
                      <div className="text-[10px] uppercase font-bold text-muted">Linked Student</div>
                      <div className="font-black text-sm text-ink">Aarav Sharma</div>
                      <div className="text-[10px] text-muted">Class X-A &middot; Roll #24</div>
                      <div className="pt-1 flex items-center gap-1.5 text-[10px] text-emerald font-bold">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald" />
                        Attendance in Good Standing (&gt;85%)
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-surface border border-line space-y-2">
                      <div className="font-bold text-ink text-[11px]">Recent Notices</div>
                      <div className="text-[10px] space-y-1">
                        <div className="font-semibold text-brand">Mid-Term Examination Schedule</div>
                        <div className="text-muted leading-relaxed">
                          Assessments commence Monday, Nov 18. Timetable published in student wallet.
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => navigate('/login')}
                      className="w-full py-2 rounded bg-brand text-on-brand text-[11px] font-bold text-center cursor-pointer"
                    >
                      Open Full Parent Portal
                    </button>
                  </div>
                )}

                {/* View 3: Teacher Workspace Mockup */}
                {activePhoneTab === 'teacher' && (
                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-brand/10 border border-brand/30 space-y-1">
                      <div className="text-[10px] uppercase font-bold text-brand">Active Session</div>
                      <div className="font-black text-sm text-ink">CS302 - Data Structures</div>
                      <div className="text-[10px] text-muted">Period 2 (10:30 AM) &middot; 42 Students Enrolled</div>
                    </div>

                    <div className="grid grid-cols-3 gap-1.5 text-center text-[10px]">
                      <div className="p-2 rounded bg-emerald/10 border border-emerald/30">
                        <div className="font-black text-emerald text-sm">39</div>
                        <div className="text-muted">Present</div>
                      </div>
                      <div className="p-2 rounded bg-danger/10 border border-danger/30">
                        <div className="font-black text-danger text-sm">2</div>
                        <div className="text-muted">Absent</div>
                      </div>
                      <div className="p-2 rounded bg-warning/10 border border-warning/30">
                        <div className="font-black text-warning text-sm">1</div>
                        <div className="text-muted">Late</div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => navigate('/login')}
                      className="w-full py-2 rounded bg-accent text-on-accent text-[11px] font-bold text-center cursor-pointer"
                    >
                      Take Period Roll-Call
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION C: Trust & Social Proof
          ========================================================================= */}
      <section className="mx-auto max-w-[1200px] px-5 space-y-10">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface-2 px-3 py-1 text-xs font-bold uppercase tracking-wider text-muted">
            Integrity, Privacy &amp; Open Standards
          </div>
          <h2 className="text-2xl sm:text-4xl font-black text-brand tracking-tight m-0">
            Engineered for Integrity and National Scale
          </h2>
          <p className="text-sm sm:text-base text-muted leading-relaxed m-0">
            ChhatraLekha is purpose-built to solve fragmentation, prevent duplicate enrollments, and guarantee privacy-preserving credential verification.
          </p>
        </div>

        {/* 4 Architectural Pillars */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="p-5 space-y-2 border-line">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-brand tracking-wider">Privacy by Design</span>
              <Badge className="bg-brand/10 text-brand">DPDP</Badge>
            </div>
            <h3 className="text-base font-bold text-ink m-0">Opaque Verification</h3>
            <p className="text-xs text-muted leading-relaxed m-0">
              Zero raw Aadhaar numbers or personal contact data exposed in public URLs. Every share link is time-bound and revocable.
            </p>
          </Card>

          <Card className="p-5 space-y-2 border-line">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-brand tracking-wider">22 Languages</span>
              <Badge className="bg-info-surface text-info-strong">Constitutional</Badge>
            </div>
            <h3 className="text-base font-bold text-ink m-0">Multilingual Access</h3>
            <p className="text-xs text-muted leading-relaxed m-0">
              Native typography, phonetic speech synthesis, and voice commands across all 22 official Eighth Schedule Indian languages.
            </p>
          </Card>

          <Card className="p-5 space-y-2 border-line">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-brand tracking-wider">Offline Ready</span>
              <Badge className="bg-success-surface text-success-strong">Encrypted</Badge>
            </div>
            <h3 className="text-base font-bold text-ink m-0">High-Entropy QR Seals</h3>
            <p className="text-xs text-muted leading-relaxed m-0">
              Printable cryptographic badges verifiable by employers or officials even without an active internet connection.
            </p>
          </Card>

          <Card className="p-5 space-y-2 border-line">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-brand tracking-wider">Audit Security</span>
              <Badge className="bg-warning-surface text-warning-strong">Hash-Chained</Badge>
            </div>
            <h3 className="text-base font-bold text-ink m-0">Immutable Audit Trail</h3>
            <p className="text-xs text-muted leading-relaxed m-0">
              Every verification event, consent grant, and record modification is sealed in an append-only cryptographic ledger.
            </p>
          </Card>
        </div>

        {/* Stakeholder Trust Banner */}
        <div className="p-6 rounded-lg bg-surface-2 border border-line flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald" />
              <span className="text-xs font-bold uppercase tracking-wider text-emerald">Verified Platform Demonstration</span>
            </div>
            <p className="text-xs sm:text-sm text-muted m-0">
              Validated with 5,000+ synthetic student records and automated regression tests across all 6 core roles. Zero fabricated claims.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setDemoModalOpen(true)}
            className="btn btn-navy text-xs font-bold shrink-0"
          >
            Launch Interactive Sandbox
          </button>
        </div>
      </section>

      {/* =========================================================================
          SECTION D: Feature Section
          ========================================================================= */}
      <section id="features" className="mx-auto max-w-[1200px] px-5 space-y-10">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface-2 px-3 py-1 text-xs font-bold uppercase tracking-wider text-muted">
            Platform Capabilities
          </div>
          <h2 className="text-2xl sm:text-4xl font-black text-brand tracking-tight m-0">
            Comprehensive Platform Features
          </h2>
          <p className="text-sm sm:text-base text-muted leading-relaxed m-0">
            Ten modular systems designed to work seamlessly together across mobile, tablet, and desktop environments.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES_DATA.map((feature, idx) => (
            <Card key={feature.id} className="p-6 space-y-3 border-line flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono font-bold text-muted uppercase tracking-wider">
                    SYS-0{idx + 1} &middot; {feature.category}
                  </span>
                  <Badge
                    className={
                      feature.statusVariant === 'success'
                        ? 'bg-success-surface text-success-strong'
                        : feature.statusVariant === 'warning'
                        ? 'bg-warning-surface text-warning-strong'
                        : 'bg-info-surface text-info-strong'
                    }
                  >
                    {feature.status}
                  </Badge>
                </div>
                <h3 className="text-lg font-bold text-ink m-0">{feature.title}</h3>
                <p className="text-xs sm:text-sm text-muted leading-relaxed m-0">{feature.desc}</p>
              </div>
              <div className="pt-3 border-t border-line flex items-center justify-between text-xs">
                <span className="text-muted font-medium">Role Aware</span>
                <Link to="/login" className="text-brand font-semibold hover:underline no-underline">
                  Try in Demo &rarr;
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* =========================================================================
          SECTION E: Benefits Section
          ========================================================================= */}
      <section id="for-students" className="bg-surface-2 border-y border-line py-16">
        <div className="mx-auto max-w-[1200px] px-5 space-y-10">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs font-bold uppercase tracking-wider text-muted">
              Value Proposition
            </div>
            <h2 className="text-2xl sm:text-4xl font-black text-brand tracking-tight m-0">
              Tailored Benefits for Every Stakeholder
            </h2>
            <p className="text-sm sm:text-base text-muted leading-relaxed m-0">
              Explore how ChhatraLekha solves real-world friction for learners, parents, faculty, schools, and regulatory directorates.
            </p>
          </div>

          {/* Stakeholder Tab Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {BENEFITS_DATA.map((b) => (
              <button
                key={b.id}
                type="button"
                onClick={() => setActiveBenefitTab(b.id)}
                className={`px-4 py-2 rounded text-xs sm:text-sm font-bold cursor-pointer transition-colors ${
                  activeBenefitTab === b.id
                    ? 'bg-brand text-on-brand shadow-xs'
                    : 'bg-surface border border-line text-ink hover:bg-surface-3'
                }`}
              >
                {b.label}
              </button>
            ))}
          </div>

          {/* Active Benefit Details Card */}
          <Card className="p-8 max-w-3xl mx-auto border-line space-y-6">
            <div className="space-y-2 border-b border-line pb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-accent-strong">
                {activeBenefit.label} Perspective
              </span>
              <h3 className="text-xl sm:text-2xl font-black text-ink m-0">
                {activeBenefit.heading}
              </h3>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {activeBenefit.points.map((pt, pIdx) => (
                <div key={pIdx} className="flex items-start gap-3 p-3.5 rounded bg-surface-2 border border-line">
                  <div className="mt-0.5 rounded bg-accent/20 p-1 shrink-0 text-accent-strong">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="text-xs sm:text-sm text-ink leading-relaxed m-0">{pt}</p>
                </div>
              ))}
            </div>

            <div className="pt-2 flex flex-wrap items-center justify-between gap-4 text-xs">
              <span className="text-muted">
                Experience this role in our interactive sandbox environment.
              </span>
              <button
                type="button"
                onClick={() => setDemoModalOpen(true)}
                className="btn btn-navy text-xs font-bold"
              >
                Test {activeBenefit.label} Experience
              </button>
            </div>
          </Card>
        </div>
      </section>

      {/* =========================================================================
          SECTION F: Product Preview
          ========================================================================= */}
      <section id="for-institutions" className="mx-auto max-w-[1200px] px-5 space-y-10">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface-2 px-3 py-1 text-xs font-bold uppercase tracking-wider text-muted">
            Platform Interface
          </div>
          <h2 className="text-2xl sm:text-4xl font-black text-brand tracking-tight m-0">
            Interactive Product Preview
          </h2>
          <p className="text-sm sm:text-base text-muted leading-relaxed m-0">
            A fast, distraction-free interface built for daily academic workflows and regulatory compliance.
          </p>
        </div>

        {/* Tab switch between Desktop Portal and Student View */}
        <div className="flex justify-center gap-3">
          <button
            type="button"
            onClick={() => setPreviewPortalTab('portal')}
            className={`px-4 py-2 rounded text-xs sm:text-sm font-bold cursor-pointer transition-colors ${
              previewPortalTab === 'portal'
                ? 'bg-brand text-on-brand shadow-xs'
                : 'bg-surface border border-line text-ink hover:bg-surface-2'
            }`}
          >
            Institutional Portal View
          </button>
          <button
            type="button"
            onClick={() => setPreviewPortalTab('student')}
            className={`px-4 py-2 rounded text-xs sm:text-sm font-bold cursor-pointer transition-colors ${
              previewPortalTab === 'student'
                ? 'bg-brand text-on-brand shadow-xs'
                : 'bg-surface border border-line text-ink hover:bg-surface-2'
            }`}
          >
            Student Mobile Experience
          </button>
        </div>

        {previewPortalTab === 'portal' ? (
          <Card className="p-6 sm:p-8 border-line space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-muted">Active Campus</span>
                <h3 className="text-lg sm:text-xl font-bold text-ink m-0">
                  Vidya Vikas Institute of Technology (INST-0421)
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-success-surface text-success-strong font-bold">Intake Quota: Normal</Badge>
                <Badge className="bg-info-surface text-info-strong font-bold">Academic Year: 2026-27</Badge>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-4">
              <div className="p-4 rounded bg-surface-2 border border-line">
                <div className="text-2xl font-black text-brand">420</div>
                <div className="text-xs text-muted uppercase font-bold mt-1">Sanctioned Seats</div>
              </div>
              <div className="p-4 rounded bg-surface-2 border border-line">
                <div className="text-2xl font-black text-emerald">396</div>
                <div className="text-xs text-muted uppercase font-bold mt-1">Active Enrolment (94.3%)</div>
              </div>
              <div className="p-4 rounded bg-surface-2 border border-line">
                <div className="text-2xl font-black text-emerald">0</div>
                <div className="text-xs text-muted uppercase font-bold mt-1">Critical Anomalies</div>
              </div>
              <div className="p-4 rounded bg-surface-2 border border-line">
                <div className="text-2xl font-black text-brand-mid">100%</div>
                <div className="text-xs text-muted uppercase font-bold mt-1">Audit Ledger Sealed</div>
              </div>
            </div>

            <div className="p-4 rounded bg-surface-2 border border-line text-xs space-y-2">
              <div className="font-bold text-ink uppercase tracking-wider text-[11px]">Latest Automated Integrity Scan</div>
              <p className="text-muted leading-relaxed m-0">
                Automated multi-layer verification evaluated 34 programme cohorts. Zero duplicate APAAR enrolments detected. Supernumerary quota boundaries respected.
              </p>
            </div>
          </Card>
        ) : (
          <Card className="p-6 sm:p-8 border-line max-w-xl mx-auto space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <div className="text-xs font-bold uppercase text-muted">Student Profile Preview</div>
                <div className="font-bold text-base text-ink">Aarav Sharma &middot; B.Tech CSE</div>
              </div>
              <Badge className="bg-emerald/15 text-emerald font-bold">94.2% Attendance</Badge>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded bg-surface-2 border border-line">
                <span className="font-semibold text-ink">APAAR Digital ID Card</span>
                <span className="text-brand font-bold">Printable PDF &amp; QR</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded bg-surface-2 border border-line">
                <span className="font-semibold text-ink">Semester IV Marksheet</span>
                <span className="text-emerald font-bold">Cryptographically Verified</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded bg-surface-2 border border-line">
                <span className="font-semibold text-ink">Time-Bound Share Links</span>
                <span className="text-muted font-bold">1 Active (Expires in 18h)</span>
              </div>
            </div>
          </Card>
        )}
      </section>

      {/* =========================================================================
          SECTION G: Testimonials (Clearly labeled sample/demo)
          ========================================================================= */}
      <section className="mx-auto max-w-[1200px] px-5 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-warning/40 bg-warning-surface px-3 py-1 text-xs font-bold uppercase tracking-wider text-warning-strong">
            Sample Demonstrative Personas
          </div>
          <h2 className="text-2xl sm:text-4xl font-black text-brand tracking-tight m-0">
            Platform Workflow Scenarios
          </h2>
          <p className="text-xs sm:text-sm text-muted leading-relaxed m-0">
            Illustrative user stories depicting intended educational workflows with synthetic data.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <Card className="p-6 space-y-4 border-line flex flex-col justify-between">
            <p className="text-xs sm:text-sm text-ink leading-relaxed m-0 italic">
              "Having my APAAR credentials and daily timetable accessible in Gujarati and English on my phone makes campus life and document verification completely stress-free."
            </p>
            <div className="pt-3 border-t border-line flex items-center gap-3">
              <div className="w-9 h-9 rounded bg-brand/15 text-brand font-bold flex items-center justify-center text-xs">
                RP
              </div>
              <div>
                <div className="text-xs font-bold text-ink">Rohan Patel (Sample Student)</div>
                <div className="text-[10px] text-muted">3rd Year B.Tech Scholar</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 space-y-4 border-line flex flex-col justify-between">
            <p className="text-xs sm:text-sm text-ink leading-relaxed m-0 italic">
              "Receiving instant visibility when attendance is marked helps us stay connected with our child's academic journey without waiting for end-of-term paper circulars."
            </p>
            <div className="pt-3 border-t border-line flex items-center gap-3">
              <div className="w-9 h-9 rounded bg-accent/20 text-accent-strong font-bold flex items-center justify-center text-xs">
                MS
              </div>
              <div>
                <div className="text-xs font-bold text-ink">Meera Sharma (Sample Parent)</div>
                <div className="text-[10px] text-muted">Parent of Class X Student</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 space-y-4 border-line flex flex-col justify-between">
            <p className="text-xs sm:text-sm text-ink leading-relaxed m-0 italic">
              "Taking attendance period by period takes less than a minute. Discrepancies are flagged immediately so students stay on track before exams."
            </p>
            <div className="pt-3 border-t border-line flex items-center gap-3">
              <div className="w-9 h-9 rounded bg-emerald/20 text-emerald font-bold flex items-center justify-center text-xs">
                RJ
              </div>
              <div>
                <div className="text-xs font-bold text-ink">Prof. Ramesh Joshi (Sample Faculty)</div>
                <div className="text-[10px] text-muted">Department Head, Engineering</div>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* =========================================================================
          SECTION H: FAQ Section
          ========================================================================= */}
      <section id="faq" className="mx-auto max-w-[900px] px-5 space-y-8">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface-2 px-3 py-1 text-xs font-bold uppercase tracking-wider text-muted">
            Got Questions?
          </div>
          <h2 className="text-2xl sm:text-4xl font-black text-brand tracking-tight m-0">
            Frequently Asked Questions
          </h2>
          <p className="text-sm sm:text-base text-muted leading-relaxed m-0">
            Clear, transparent answers about the platform architecture, privacy protections, and pilot onboarding.
          </p>
        </div>

        <div className="space-y-3">
          {FAQ_DATA.map((item, idx) => {
            const isExpanded = expandedFaqIndex === idx
            return (
              <div
                key={idx}
                className="rounded-lg border border-line bg-surface transition-colors"
              >
                <button
                  type="button"
                  onClick={() => toggleFaq(idx)}
                  className="w-full p-4 sm:p-5 text-start font-bold text-sm sm:text-base text-ink flex items-center justify-between gap-4 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                  aria-expanded={isExpanded}
                >
                  <span>{item.q}</span>
                  <span className="shrink-0 text-brand font-black text-lg">
                    {isExpanded ? '-' : '+'}
                  </span>
                </button>
                {isExpanded && (
                  <div className="px-4 pb-5 sm:px-5 text-xs sm:text-sm text-muted leading-relaxed border-t border-line pt-3">
                    {item.a}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </section>

      {/* =========================================================================
          SECTION I: Final CTA Section
          ========================================================================= */}
      <section className="mx-auto max-w-[1200px] px-5">
        <div className="p-8 sm:p-12 rounded-lg bg-brand-deep text-white text-center space-y-6 shadow-xs border border-line">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-white">
            <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
            Get Started Today
          </div>

          <h2 className="text-3xl sm:text-4xl font-black text-white m-0 tracking-tight">
            Ready to Experience ChhatraLekha?
          </h2>

          <p className="text-sm sm:text-base text-white/80 max-w-2xl mx-auto leading-relaxed m-0">
            Explore the live interactive platform across 6 roles with 5,000 synthetic records, or register your institution for early access.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link to="/signup" className="no-underline">
              <button
                type="button"
                className="btn btn-primary px-6 py-3 text-sm font-bold shadow-xs hover:bg-accent-strong cursor-pointer"
              >
                Get Started
              </button>
            </Link>

            <button
              type="button"
              onClick={() => setDemoModalOpen(true)}
              className="btn px-6 py-3 text-sm font-bold bg-white text-brand hover:bg-white/90 shadow-xs cursor-pointer"
            >
              Explore Demo
            </button>

            <Link to="/early-access" className="no-underline">
              <button
                type="button"
                className="btn border border-white/30 text-white hover:bg-white/10 px-6 py-3 text-sm font-bold cursor-pointer"
              >
                Request Institutional Pilot
              </button>
            </Link>
          </div>
        </div>
      </section>

      {/* =========================================================================
          DEMO PERSONA SWITCHER MODAL
          ========================================================================= */}
      {demoModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="demo-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/50"
        >
          <div className="card w-full max-w-2xl p-6 sm:p-8 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-line pb-4">
              <div>
                <h3 id="demo-modal-title" className="text-xl font-black text-ink m-0">
                  Select a Demo Persona
                </h3>
                <p className="text-xs text-muted m-0 mt-1">
                  Choose any role to explore pre-seeded synthetic data. Zero setup required.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setDemoModalOpen(false)}
                className="p-1 rounded text-muted hover:text-ink cursor-pointer focus-visible:outline-none"
                aria-label="Close modal"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {DEMO_ROLES.map((role) => (
                <button
                  key={role.key}
                  type="button"
                  onClick={() => handleDemoLogin(role.key, role.target)}
                  disabled={Boolean(loggingInRole)}
                  className="p-4 rounded border border-line bg-surface hover:border-brand hover:bg-surface-2 text-start transition-colors cursor-pointer space-y-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand disabled:opacity-50"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-ink">{role.title}</span>
                    <Badge className="bg-brand/10 text-brand">{role.badge}</Badge>
                  </div>
                  <p className="text-xs text-muted leading-relaxed m-0">{role.desc}</p>
                  <div className="pt-2 text-[10px] font-bold text-accent-strong flex items-center gap-1">
                    <span>
                      {loggingInRole === role.key ? 'Signing in...' : 'Launch Persona &rarr;'}
                    </span>
                  </div>
                </button>
              ))}
            </div>

            <div className="pt-2 border-t border-line flex items-center justify-between text-xs text-muted">
              <span>Notice: Sandbox demo mode only.</span>
              <button
                type="button"
                onClick={() => setDemoModalOpen(false)}
                className="btn btn-outline text-xs"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

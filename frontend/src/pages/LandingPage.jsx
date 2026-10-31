import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../hooks/usePageMeta'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'
import { Button, Card, Badge } from '../components/common'
import AiAssistantDrawer from '../components/ai/AiAssistantDrawer'

const FEATURES = [
  ['01', 'Digital ID', 'A portable academic identity that keeps the student record clear, current, and easy to present.'],
  ['02', 'Academic Wallet', 'Keep credentials, certificates, and verification history together in one trusted place.'],
  ['03', 'QR Verification', 'Share a time-bound QR credential without exposing personal data on the public page.'],
  ['04', 'Fraud Detection', 'Surface duplicate enrolments, quota breaches, and suspicious changes before they spread.'],
  ['05', 'Audit Trail', 'Every consent, review, correction, and verification stays traceable for accountable decisions.'],
]

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

const CHAPTERS = [
  {
    time: '0:00',
    title: 'Platform Overview & Mission',
    summary: 'One digital education platform for all Indian schools, colleges, universities, students, parents, and administrators.',
    bulletPoints: [
      'Constitutional vision supporting all 22 scheduled Indian languages.',
      'Unified architecture connecting K-12 schools and higher education universities.',
      'Public-benefit system with strict data protection and student privacy.',
    ],
    enCaption: 'Welcome to ChhatraLekha, India\'s unified and inclusive education platform.',
    hiCaption: 'छात्रलेखा में आपका स्वागत है, भारत का एकीकृत और समावेशी शिक्षा मंच।',
    orCaption: 'ଛାତ୍ରଲେଖାକୁ ସ୍ୱାଗତ, ଭାରତର ସମନ୍ୱିତ ଏବଂ ସମାବେଶୀ ଶିକ୍ଷା ମଞ୍ଚ।',
  },
  {
    time: '0:30',
    title: '22 Indian Languages & Voice Navigation',
    summary: 'Speak, listen, and navigate in your mother tongue without literacy or keyboard barriers.',
    bulletPoints: [
      'Instant language switching across Assamese, Bengali, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Tamil, Telugu, Urdu, and more.',
      'Voice input to search timetables, ask about attendance, and find notices.',
      'Text-to-speech audio playback for all announcements and exam results.',
    ],
    enCaption: 'Select any of India\'s 22 languages and speak naturally to navigate.',
    hiCaption: 'भारत की किसी भी 22 भाषाओं में से चुनें और सहजता से बोलकर नेविगेट करें।',
    orCaption: 'ଭାରତର ୨୨ଟି ଭାଷା ମଧ୍ୟରୁ ଯେକୌଣସି ଗୋଟିଏ ବାଛନ୍ତୁ ଏବଂ କହିକରି ନେଭିଗେଟ୍ କରନ୍ତୁ।',
  },
  {
    time: '1:00',
    title: 'Student ID, APAAR ID & Credential Wallet',
    summary: 'A tamper-evident digital student identity that protects student privacy by design.',
    bulletPoints: [
      'Printable and downloadable digital ID card with opaque cryptographic verification token.',
      'Zero Aadhaar or personal data exposed in public URLs or raw QR scans.',
      'Verifiable marksheets, bonafide certificates, and time-limited share links.',
    ],
    enCaption: 'Your APAAR ID and academic credentials stay securely protected in your personal wallet.',
    hiCaption: 'आपका अपार पहचान पत्र और शैक्षणिक दस्तावेज आपके वॉलेट में सुरक्षित रहते हैं।',
    orCaption: 'ଆପଣଙ୍କ ଅପାର୍ ଆଇଡି ଏବଂ ଶିକ୍ଷାଗତ ପ୍ରମାଣପତ୍ର ଆପଣଙ୍କ ୱାଲେଟରେ ସୁରକ୍ଷିତ ରହିଥାଏ।',
  },
  {
    time: '1:45',
    title: 'Teacher Workspace & Parent Portal',
    summary: 'Coordinating daily academic life between instructors, guardians, and students.',
    bulletPoints: [
      'Teachers mark session attendance in seconds with Present, Absent, and Late toggles.',
      'Parents receive real-time visibility into attendance percentages and exam schedules.',
      'Direct school-parent notices and urgent announcements without paper circulars.',
    ],
    enCaption: 'Teachers manage classroom sessions while parents stay informed on student progress.',
    hiCaption: 'शिक्षक कक्षा सत्र संचालित करते हैं जबकि अभिभावक विद्यार्थी की प्रगति से जुड़े रहते हैं।',
    orCaption: 'ଶିକ୍ଷକମାନେ କ୍ଲାସ ପରିଚାଳନା କରନ୍ତି ଏବଂ ଅଭିଭାବକମାନେ ଛାତ୍ରଛାତ୍ରୀଙ୍କ ଅଗ୍ରଗତି ବିଷୟରେ ଜାଣିପାରନ୍ତି।',
  },
  {
    time: '2:15',
    title: 'Institution Administration, Anomaly Engine & Audit',
    summary: 'AI-assisted regulatory compliance, fraud detection, and immutable hash-chained audit logs.',
    bulletPoints: [
      'Automated detection of cross-institution duplicate enrolments and quota breaches.',
      'Change impact preview before records are altered.',
      'Cryptographically sealed audit trail ready for independent offline inspection.',
    ],
    enCaption: 'Automated anomaly detection keeps regulatory records accurate and fully audited.',
    hiCaption: 'स्वचालित विसंगति जांच नियामक रिकॉर्ड को सटीक और पूर्णतः ऑडिट योग्य रखती है।',
    orCaption: 'ସ୍ୱୟଂଚାଳିତ ତ୍ରୁଟି ଯାଞ୍ଚ ନିୟାମକ ରେକର୍ଡକୁ ସଠିକ୍ ଏବଂ ସମ୍ପୂର୍ଣ୍ଣ ଅଡିଟ୍ ଯୋଗ୍ୟ ରଖେ।',
  },
]

export default function LandingPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const { i18n } = useTranslation()

  usePageMeta({
    title: 'Authenticate, Verify, Empower',
    description: 'ChhatraLekha is a trusted digital academic identity for every student.',
    canonical: '/',
  })

  // State for Demo Modal and Walkthrough Video
  const [demoModalOpen, setDemoModalOpen] = useState(false)
  const [loggingInRole, setLoggingInRole] = useState(null)
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false)

  // Walkthrough state
  const [activeChapterIndex, setActiveChapterIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedCaptionLang, setSelectedCaptionLang] = useState('en')
  const [transcriptSearch, setTranscriptSearch] = useState('')
  const [transcriptExpanded, setTranscriptExpanded] = useState(false)

  const activeChapter = CHAPTERS[activeChapterIndex]

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

  const filteredChapters = useMemo(() => {
    if (!transcriptSearch.trim()) return CHAPTERS
    const q = transcriptSearch.toLowerCase()
    return CHAPTERS.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        c.summary.toLowerCase().includes(q) ||
        c.bulletPoints.some((b) => b.toLowerCase().includes(q))
    )
  }, [transcriptSearch])

  return (
    <div className="space-y-16 pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-surface-2 border-b border-line">
        <div className="mx-auto grid max-w-[1200px] gap-10 px-5 py-14 sm:py-20 lg:grid-cols-[1.15fr_.85fr] lg:items-center">
          <div className="relative z-10 space-y-6">
            <img
              src="/brand/chhatralekha-logo.png"
              alt="ChhatraLekha - Authenticate, Verify, Empower"
              className="h-auto w-full max-w-[380px] object-contain object-left block rounded bg-white p-2 shadow-xs border border-line"
            />
            <div className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-accent-strong">
              <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
              National Multilingual Education Platform
            </div>
            <h1 className="m-0 text-3xl sm:text-5xl font-black leading-tight text-brand-deep">
              One trusted record for every student.
            </h1>
            <p className="m-0 max-w-[62ch] text-base leading-relaxed text-muted sm:text-lg">
              Authenticate academic records, manage daily attendance, verify credentials, and empower 
              learners and parents across India in 22 constitutional languages.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDemoModalOpen(true)}
                className="rounded-lg bg-accent text-on-accent px-5 py-3 text-sm font-bold shadow-xs hover:bg-accent-strong hover:text-white transition-colors cursor-pointer flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Explore Demo</span>
              </button>
              <a
                href="#tutorial"
                className="rounded-lg bg-surface border border-line text-ink px-4 py-3 text-sm font-bold hover:border-brand hover:text-brand transition-colors no-underline shadow-xs flex items-center gap-2"
              >
                <svg className="w-4 h-4 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Watch Tutorial</span>
              </a>
              <Link to="/login" className="no-underline">
                <Button variant="primary">Sign In</Button>
              </Link>
              <Link to="/verify/t/demo" className="no-underline">
                <Button variant="secondary">Verify a credential</Button>
              </Link>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted pt-1">
              <span className="rounded bg-accent/15 text-accent-strong px-2 py-0.5 font-bold uppercase text-[10px]">
                Demo Mode Available
              </span>
              <span>Explore all 6 roles with 5,000 synthetic student records. No password required.</span>
            </div>
          </div>

          {/* Right Hero Visual Card */}
          <div className="relative">
            <div className="rounded-lg border border-line bg-surface p-6 shadow-md">
              <div className="mb-5 flex items-center justify-between border-b border-line pb-3">
                <div>
                  <p className="m-0 text-xs font-bold uppercase tracking-widest text-muted">Academic Journey</p>
                  <p className="m-0 mt-0.5 text-base font-bold text-brand-deep">Enrolment &rarr; Attendance &rarr; Wallet</p>
                </div>
                <span className="rounded-full bg-success-surface border border-success/30 px-3 py-1 text-xs font-bold text-success-strong">
                  Protected System
                </span>
              </div>
              <div className="grid gap-3 text-xs">
                {[
                  { step: '01', title: 'Multilingual Voice & Language', sub: '22 Eighth Schedule languages supported natively' },
                  { step: '02', title: 'Student Identity & APAAR Card', sub: 'Opaque QR token verification without Aadhaar exposure' },
                  { step: '03', title: 'Teacher & Parent Workspace', sub: 'Real-time attendance marking and marksheet review' },
                  { step: '04', title: 'Institution Compliance & AI Audit', sub: 'Cross-institution duplicate prevention and seat caps' },
                ].map((item) => (
                  <div key={item.step} className="flex items-start gap-3 rounded-lg border border-line bg-surface-2 p-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand text-xs font-black text-on-brand">
                      {item.step}
                    </span>
                    <div>
                      <p className="m-0 font-bold text-ink">{item.title}</p>
                      <p className="m-0 text-muted text-[11px]">{item.sub}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-lg bg-brand p-4 text-on-brand flex items-center justify-between">
                <div>
                  <p className="m-0 text-[10px] font-bold uppercase tracking-widest text-white/70">Multilingual Assistant</p>
                  <p className="m-0 text-xs font-semibold">Ask questions in English, Hindi, Odia, and more</p>
                </div>
                <button
                  type="button"
                  onClick={() => setAiAssistantOpen(true)}
                  className="rounded bg-white text-brand px-2.5 py-1 text-xs font-bold cursor-pointer hover:bg-surface-2 shadow-xs"
                >
                  Ask Assistant
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Tutorial Video Walkthrough Section */}
      <section id="tutorial" className="mx-auto max-w-[1200px] px-5">
        <div className="mb-8">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-brand">
            Interactive Walkthrough
          </div>
          <h2 className="m-0 mt-2 text-2xl sm:text-3xl font-black text-brand-deep">
            How to Use ChhatraLekha in 2 to 3 Minutes
          </h2>
          <p className="m-0 mt-1 text-sm text-muted max-w-2xl">
            A comprehensive tour of the platform features for students, parents, faculty, and institutions.
            Jump between chapter markers or search the interactive transcript.
          </p>
        </div>

        {/* Video Player Presentation Frame */}
        <div className="rounded-lg border border-line bg-surface overflow-hidden shadow-md">
          {/* Chapter Timeline Tabs */}
          <div className="flex border-b border-line bg-surface-2 overflow-x-auto">
            {CHAPTERS.map((ch, idx) => (
              <button
                key={ch.time}
                type="button"
                onClick={() => {
                  setActiveChapterIndex(idx)
                  setIsPlaying(false)
                }}
                className={`px-4 py-3 text-xs font-bold border-r border-line flex items-center gap-2 whitespace-nowrap cursor-pointer transition-colors ${
                  activeChapterIndex === idx
                    ? 'bg-brand text-on-brand shadow-xs'
                    : 'text-muted hover:text-ink hover:bg-surface'
                }`}
              >
                <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-black/20 text-white">
                  {ch.time}
                </span>
                <span>{ch.title}</span>
              </button>
            ))}
          </div>

          {/* Active Chapter Screen Simulation */}
          <div className="p-6 sm:p-8 bg-surface space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-line pb-4">
              <div>
                <span className="text-xs font-mono font-bold text-accent-strong">
                  Chapter {activeChapterIndex + 1} of {CHAPTERS.length} ({activeChapter.time})
                </span>
                <h3 className="m-0 mt-1 text-xl font-bold text-brand-deep">{activeChapter.title}</h3>
                <p className="m-0 mt-1 text-xs text-muted max-w-2xl">{activeChapter.summary}</p>
              </div>

              {/* Player Controls & Captions Selector */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="rounded-lg bg-brand text-on-brand px-3 py-1.5 text-xs font-bold hover:bg-brand-deep cursor-pointer flex items-center gap-1.5 shadow-xs"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isPlaying ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    )}
                  </svg>
                  <span>{isPlaying ? 'Pause Tour' : 'Play Tour'}</span>
                </button>

                <div className="flex items-center rounded border border-line bg-surface-2 p-0.5 text-xs">
                  <span className="px-2 text-[10px] font-bold text-muted uppercase">Captions:</span>
                  {['en', 'hi', 'or'].map((lang) => (
                    <button
                      key={lang}
                      type="button"
                      onClick={() => setSelectedCaptionLang(lang)}
                      className={`px-2 py-0.5 rounded text-[11px] font-bold cursor-pointer ${
                        selectedCaptionLang === lang ? 'bg-brand text-on-brand' : 'text-muted hover:text-ink'
                      }`}
                    >
                      {lang.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Screen Content Simulator */}
            <div className="grid gap-6 md:grid-cols-2 items-center">
              <div className="space-y-3">
                <p className="m-0 text-xs font-bold uppercase tracking-wider text-muted">Key Learning Points:</p>
                <div className="space-y-2">
                  {activeChapter.bulletPoints.map((bp, bpIdx) => (
                    <div key={bpIdx} className="flex items-start gap-2.5 rounded-lg border border-line bg-surface-2 p-3 text-xs">
                      <div className="h-5 w-5 rounded-full bg-accent/20 text-accent-strong flex items-center justify-center font-bold text-[10px] flex-shrink-0">
                        {bpIdx + 1}
                      </div>
                      <span className="text-ink leading-relaxed">{bp}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Subtitles & Visual Mockup */}
              <div className="rounded-lg border border-line bg-surface-2 p-5 space-y-4">
                <div className="flex items-center justify-between text-xs text-muted border-b border-line pb-2">
                  <span className="font-bold uppercase tracking-wider text-[10px]">Closed Caption Preview</span>
                  <span className="font-mono text-[10px]">{activeChapter.time} / 3:00</span>
                </div>
                <div className="rounded bg-brand-deep text-white p-4 text-xs font-medium leading-relaxed min-h-[70px] flex items-center justify-center text-center">
                  &ldquo;
                  {selectedCaptionLang === 'hi'
                    ? activeChapter.hiCaption
                    : selectedCaptionLang === 'or'
                    ? activeChapter.orCaption
                    : activeChapter.enCaption}
                  &rdquo;
                </div>
                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    disabled={activeChapterIndex === 0}
                    onClick={() => setActiveChapterIndex((prev) => Math.max(0, prev - 1))}
                    className="rounded border border-line px-3 py-1 text-xs font-bold hover:border-brand cursor-pointer disabled:opacity-40"
                  >
                    &larr; Previous Chapter
                  </button>
                  <button
                    type="button"
                    disabled={activeChapterIndex === CHAPTERS.length - 1}
                    onClick={() => setActiveChapterIndex((prev) => Math.min(CHAPTERS.length - 1, prev + 1))}
                    className="rounded bg-brand text-on-brand px-3 py-1 text-xs font-bold hover:bg-brand-deep cursor-pointer disabled:opacity-40"
                  >
                    Next Chapter &rarr;
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Searchable Transcript Accordion */}
          <div className="border-t border-line bg-surface-2 p-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setTranscriptExpanded(!transcriptExpanded)}
                className="text-xs font-bold text-brand hover:underline cursor-pointer flex items-center gap-1.5"
              >
                <span>{transcriptExpanded ? 'Hide Full Video Transcript' : 'Show Searchable Transcript'}</span>
                <span className="text-[10px] text-muted">({CHAPTERS.length} chapters)</span>
              </button>

              {transcriptExpanded && (
                <input
                  type="text"
                  value={transcriptSearch}
                  onChange={(e) => setTranscriptSearch(e.target.value)}
                  placeholder="Filter transcript (e.g. attendance, voice, APAAR)..."
                  className="rounded border border-line bg-surface px-3 py-1 text-xs text-ink focus:outline-none focus:border-brand w-full sm:w-64"
                />
              )}
            </div>

            {transcriptExpanded && (
              <div className="mt-4 space-y-2 max-h-60 overflow-y-auto pt-2 border-t border-line">
                {filteredChapters.map((c) => (
                  <div
                    key={c.time}
                    className="rounded border border-line bg-surface p-3 text-xs flex items-start gap-3"
                  >
                    <button
                      type="button"
                      onClick={() => {
                        const originalIdx = CHAPTERS.findIndex((item) => item.time === c.time)
                        if (originalIdx >= 0) setActiveChapterIndex(originalIdx)
                      }}
                      className="font-mono text-[10px] px-2 py-0.5 rounded bg-brand text-on-brand font-bold cursor-pointer hover:bg-brand-deep flex-shrink-0"
                    >
                      {c.time}
                    </button>
                    <div>
                      <p className="m-0 font-bold text-ink">{c.title}</p>
                      <p className="m-0 text-muted mt-0.5">{c.summary}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Feature Pillars */}
      <section className="mx-auto max-w-[1200px] px-5">
        <div className="mb-6 max-w-2xl">
          <p className="m-0 text-xs font-bold uppercase tracking-widest text-accent-strong">Built for the Full Academic Journey</p>
          <h2 className="m-0 mt-2 text-2xl sm:text-3xl font-black text-brand-deep">A Calm, Accountable Way to Prove Learning.</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {FEATURES.map(([number, title, description]) => (
            <Card key={title} className="p-5 transition-transform hover:-translate-y-1">
              <span className="text-xs font-black tracking-widest text-accent-strong">{number}</span>
              <h3 className="m-0 mt-6 text-base font-bold text-ink">{title}</h3>
              <p className="m-0 mt-2 text-xs leading-relaxed text-muted">{description}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* AI Assistant Showcase */}
      <section className="bg-brand py-12 text-on-brand">
        <div className="mx-auto grid max-w-[1200px] gap-6 px-5 lg:grid-cols-[1fr_auto] lg:items-center">
          <div>
            <p className="m-0 text-xs font-bold uppercase tracking-widest text-white/70">Multilingual AI Guidance</p>
            <h2 className="m-0 mt-2 text-2xl sm:text-3xl font-black text-white">Grounded answers in your language.</h2>
            <p className="m-0 mt-3 max-w-2xl text-xs sm:text-sm leading-relaxed text-white/80">
              ChhatraLekha integrates a role-aware AI Assistant grounded in official documentation and regulatory rules.
              Get instant help with class schedules, attendance verification, APAAR ID cards, or administration workflows.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setAiAssistantOpen(true)}
            className="rounded-lg bg-accent text-on-accent px-5 py-3 text-sm font-bold shadow-xs hover:bg-accent-strong hover:text-white transition-colors cursor-pointer flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Open AI Assistant</span>
          </button>
        </div>
      </section>

      {/* Demo Account Chooser Modal */}
      {demoModalOpen && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center bg-black/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Choose a Demo Persona"
        >
          <div className="w-full max-w-3xl rounded-lg bg-surface border border-line p-6 shadow-md space-y-5">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="m-0 text-lg font-bold text-brand-deep">Explore ChhatraLekha in Demo Mode</h3>
                  <Badge className="bg-accent text-on-accent uppercase text-[10px]">DEMO DATA</Badge>
                </div>
                <p className="m-0 mt-1 text-xs text-muted">
                  Select any of the 6 roles below to enter an interactive session. Fictional sample data only. No real PII.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setDemoModalOpen(false)}
                className="p-1 rounded text-muted hover:text-ink cursor-pointer"
                aria-label="Close dialog"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {DEMO_ROLES.map((r) => (
                <div
                  key={r.key}
                  className="rounded-lg border border-line bg-surface-2 p-4 flex flex-col justify-between hover:border-brand transition-colors"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-ink">{r.title}</span>
                      <span className="rounded bg-brand/10 text-brand px-2 py-0.5 text-[10px] font-bold">
                        {r.badge}
                      </span>
                    </div>
                    <p className="m-0 text-[10px] font-mono text-muted truncate">{r.email}</p>
                    <p className="m-0 text-xs text-muted leading-relaxed pt-1">{r.desc}</p>
                  </div>

                  <button
                    type="button"
                    disabled={loggingInRole !== null}
                    onClick={() => handleDemoLogin(r.key, r.target)}
                    className="mt-4 w-full rounded bg-brand text-on-brand py-1.5 text-xs font-bold hover:bg-brand-deep cursor-pointer transition-colors shadow-xs disabled:opacity-50"
                  >
                    {loggingInRole === r.key ? 'Entering Demo...' : 'Open Demo &rarr;'}
                  </button>
                </div>
              ))}
            </div>

            <div className="border-t border-line pt-3 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-muted gap-2">
              <span>Safety Guarantee: Demo mode runs on isolated in-memory test data without altering live records.</span>
              <button
                type="button"
                onClick={() => setDemoModalOpen(false)}
                className="text-xs text-brand font-semibold hover:underline cursor-pointer"
              >
                Close Window
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating AI Assistant Trigger */}
      <div className="fixed bottom-5 right-5 z-40">
        <button
          type="button"
          onClick={() => setAiAssistantOpen(true)}
          className="rounded-full bg-accent text-on-accent px-4 py-2.5 text-xs font-bold shadow-md hover:bg-accent-strong hover:text-white transition-all cursor-pointer flex items-center gap-2"
          aria-label="Open AI Assistant"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span>Ask AI Assistant</span>
        </button>
      </div>

      <AiAssistantDrawer isOpen={aiAssistantOpen} onClose={() => setAiAssistantOpen(false)} />
    </div>
  )
}

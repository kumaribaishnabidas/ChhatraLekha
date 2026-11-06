import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'
import { Card, Badge, Button, Spinner, ErrorState } from '../components/common'

const ACCOUNT_ROLES = [
  {
    id: 'student',
    title: 'Student',
    subtitle: 'Access your academic journey, digital credentials, and APAAR identity.',
    details: 'View verifiable results, attendance records, digital ID card, and academic wallet.',
    iconName: 'user',
  },
  {
    id: 'parent',
    title: 'Parent / Guardian',
    subtitle: 'Monitor attendance, academic growth, and institutional notifications.',
    details: 'Securely link child profile with verified date of birth and enrollment credentials.',
    iconName: 'shield',
  },
  {
    id: 'teacher',
    title: 'Teacher / Faculty',
    subtitle: 'Manage assigned classes, mark period roll-call, and submit assessments.',
    details: 'Submit internal assessments, verify student submissions, and view classroom analytics.',
    iconName: 'book',
  },
  {
    id: 'institution_admin',
    title: 'Institution Administrator',
    subtitle: 'Administer campus records, programme intakes, and compliance verification.',
    details: 'Approve student memberships, review faculty records, and manage affiliation credentials.',
    iconName: 'building',
  },
]

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi (हिंदी)' },
  { code: 'bn', label: 'Bengali (বাংলা)' },
  { code: 'te', label: 'Telugu (తెలుగు)' },
  { code: 'mr', label: 'Marathi (मराठी)' },
  { code: 'ta', label: 'Tamil (தமிழ்)' },
  { code: 'gu', label: 'Gujarati (ગુજરાતી)' },
  { code: 'kn', label: 'Kannada (ಕನ್ನಡ)' },
  { code: 'ml', label: 'Malayalam (മലയാളം)' },
  { code: 'or', label: 'Odia (ଓଡ଼ିଆ)' },
  { code: 'pa', label: 'Punjabi (ਪੰਜਾਬੀ)' },
  { code: 'as', label: 'Assamese (অসমীয়া)' },
]

const AVATARS = [
  { id: 'avatar-1', label: 'Avatar 1', url: '/avatars/avatar-1.png' },
  { id: 'avatar-2', label: 'Avatar 2', url: '/avatars/avatar-2.png' },
  { id: 'avatar-3', label: 'Avatar 3', url: '/avatars/avatar-3.png' },
  { id: 'avatar-4', label: 'Avatar 4', url: '/avatars/avatar-4.png' },
]

const STEPS = [
  { number: 1, label: 'Welcome' },
  { number: 2, label: 'Purpose' },
  { number: 3, label: 'Profile' },
  { number: 4, label: 'Institution' },
  { number: 5, label: 'Details' },
  { number: 6, label: 'Review' },
  { number: 7, label: 'Completion' },
]

export default function OnboardingPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { user } = useAuth()

  // Step state
  const [currentStep, setCurrentStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Form states
  const [accountPurpose, setAccountPurpose] = useState('student')
  const [fullName, setFullName] = useState(user?.displayName || user?.full_name || '')
  const [preferredLanguage, setPreferredLanguage] = useState(i18n.language || 'en')
  const [phone, setPhone] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')

  // Institution discovery states
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('ALL')
  const [institutions, setInstitutions] = useState([])
  const [selectedInstitution, setSelectedInstitution] = useState(null)
  const [searching, setSearching] = useState(false)

  // Role-specific fields
  const [studentCourse, setStudentCourse] = useState('')
  const [studentClass, setStudentClass] = useState('')
  const [studentAcademicYear, setStudentAcademicYear] = useState('2024-25')
  const [studentIdentifier, setStudentIdentifier] = useState('')
  const [studentDob, setStudentDob] = useState('')
  const [parentRelationship, setParentRelationship] = useState('Guardian')
  const [teacherDepartment, setTeacherDepartment] = useState('')
  const [teacherSpecialization, setTeacherSpecialization] = useState('')
  const [teacherEmployeeId, setTeacherEmployeeId] = useState('')
  const [adminDesignation, setAdminDesignation] = useState('')
  const [adminProofNotes, setAdminProofNotes] = useState('')

  // Submission result
  const [submittedRequest, setSubmittedRequest] = useState(null)
  const [targetDashboard, setTargetDashboard] = useState('/dashboard')

  // Load saved draft on mount
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem('chhatralekha_onboarding_draft')
      if (saved) {
        const data = JSON.parse(saved)
        if (data.currentStep && data.currentStep < 7) setCurrentStep(data.currentStep)
        if (data.accountPurpose) setAccountPurpose(data.accountPurpose)
        if (data.fullName) setFullName(data.fullName)
        if (data.preferredLanguage) setPreferredLanguage(data.preferredLanguage)
        if (data.phone) setPhone(data.phone)
        if (data.avatarUrl) setAvatarUrl(data.avatarUrl)
        if (data.selectedInstitution) setSelectedInstitution(data.selectedInstitution)
        if (data.studentCourse) setStudentCourse(data.studentCourse)
        if (data.studentClass) setStudentClass(data.studentClass)
        if (data.studentAcademicYear) setStudentAcademicYear(data.studentAcademicYear)
        if (data.studentIdentifier) setStudentIdentifier(data.studentIdentifier)
        if (data.studentDob) setStudentDob(data.studentDob)
        if (data.parentRelationship) setParentRelationship(data.parentRelationship)
        if (data.teacherDepartment) setTeacherDepartment(data.teacherDepartment)
        if (data.teacherSpecialization) setTeacherSpecialization(data.teacherSpecialization)
        if (data.teacherEmployeeId) setTeacherEmployeeId(data.teacherEmployeeId)
        if (data.adminDesignation) setAdminDesignation(data.adminDesignation)
        if (data.adminProofNotes) setAdminProofNotes(data.adminProofNotes)
      }
    } catch {
      // Ignore sessionStorage parsing errors
    }
  }, [])

  // Persist draft on changes
  useEffect(() => {
    if (currentStep >= 7) return
    const draft = {
      currentStep,
      accountPurpose,
      fullName,
      preferredLanguage,
      phone,
      avatarUrl,
      selectedInstitution,
      studentCourse,
      studentClass,
      studentAcademicYear,
      studentIdentifier,
      studentDob,
      parentRelationship,
      teacherDepartment,
      teacherSpecialization,
      teacherEmployeeId,
      adminDesignation,
      adminProofNotes,
    }
    try {
      sessionStorage.setItem('chhatralekha_onboarding_draft', JSON.stringify(draft))
    } catch {
      // Ignore
    }
  }, [
    currentStep,
    accountPurpose,
    fullName,
    preferredLanguage,
    phone,
    avatarUrl,
    selectedInstitution,
    studentCourse,
    studentClass,
    studentAcademicYear,
    studentIdentifier,
    studentDob,
    parentRelationship,
    teacherDepartment,
    teacherSpecialization,
    teacherEmployeeId,
    adminDesignation,
    adminProofNotes,
  ])

  // Institution search
  useEffect(() => {
    if (currentStep !== 4) return
    const fetchInstitutions = async () => {
      setSearching(true)
      try {
        const params = new URLSearchParams()
        if (searchQuery.trim()) params.append('q', searchQuery.trim())
        if (categoryFilter !== 'ALL') params.append('category', categoryFilter)

        const res = await api.get(`/onboarding/institutions?${params.toString()}`).catch(() => ({ data: [] }))
        setInstitutions(res.data || [])
      } catch (err) {
        setError('Failed to fetch institutions.')
      } finally {
        setSearching(false)
      }
    }

    const timer = setTimeout(fetchInstitutions, 250)
    return () => clearTimeout(timer)
  }, [currentStep, searchQuery, categoryFilter])

  // Save profile step
  const handleProfileSubmit = async () => {
    if (!fullName.trim()) {
      setError('Please provide your full legal name.')
      return false
    }
    setError('')
    try {
      setLoading(true)
      await api.post('/onboarding/profile', {
        full_name: fullName.trim(),
        preferred_language: preferredLanguage,
        phone: phone.trim() || null,
        avatar_url: avatarUrl || null,
      })
      if (i18n.changeLanguage) {
        i18n.changeLanguage(preferredLanguage)
      }
      return true
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to update basic profile.')
      return false
    } finally {
      setLoading(false)
    }
  }

  // Handle final join request submission
  const handleFinalSubmit = async () => {
    if (!selectedInstitution) {
      setError('Please select an educational institution.')
      return
    }

    setError('')
    setLoading(true)
    try {
      const payload = {
        institution_id: selectedInstitution.institution_id,
        requested_role: accountPurpose,
      }

      if (accountPurpose === 'student') {
        payload.course_name = studentCourse.trim() || undefined
        payload.class_grade = studentClass.trim() || undefined
        payload.academic_year = studentAcademicYear || '2024-25'
        payload.student_identifier = studentIdentifier.trim() || undefined
      } else if (accountPurpose === 'parent') {
        if (!studentIdentifier.trim() || !studentDob.trim()) {
          setError('Parent verification requires both Student Identifier and Date of Birth.')
          setLoading(false)
          return
        }
        payload.student_identifier = studentIdentifier.trim()
        payload.student_dob = studentDob.trim()
        payload.relationship = parentRelationship
      } else if (accountPurpose === 'teacher') {
        payload.department = teacherDepartment.trim() || undefined
        payload.subject_specialization = teacherSpecialization.trim() || undefined
        payload.employee_id = teacherEmployeeId.trim() || undefined
      } else if (accountPurpose === 'institution_admin') {
        payload.designation = adminDesignation.trim() || undefined
        payload.authority_proof_notes = adminProofNotes.trim() || undefined
      }

      const reqRes = await api.post('/onboarding/join-request', payload)
      setSubmittedRequest(reqRes.data)

      // Complete onboarding journey
      const compRes = await api.post('/onboarding/complete', {
        selected_role: accountPurpose,
        institution_id: selectedInstitution.institution_id,
      })
      setTargetDashboard(compRes.data?.target_dashboard || '/dashboard')

      sessionStorage.removeItem('chhatralekha_onboarding_draft')
      setCurrentStep(7)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Submission failed.')
    } finally {
      setLoading(false)
    }
  }

  const goNext = async () => {
    setError('')
    if (currentStep === 1) {
      setCurrentStep(2)
    } else if (currentStep === 2) {
      if (!accountPurpose) {
        setError('Please select your intended account role.')
        return
      }
      setCurrentStep(3)
    } else if (currentStep === 3) {
      const ok = await handleProfileSubmit()
      if (ok) setCurrentStep(4)
    } else if (currentStep === 4) {
      if (!selectedInstitution) {
        setError('Please choose an institution from the list to continue.')
        return
      }
      setCurrentStep(5)
    } else if (currentStep === 5) {
      if (accountPurpose === 'parent') {
        if (!studentIdentifier.trim() || !studentDob.trim()) {
          setError('Both Student Identifier and Date of Birth are mandatory for parent linking.')
          return
        }
      }
      setCurrentStep(6)
    } else if (currentStep === 6) {
      await handleFinalSubmit()
    }
  }

  const goBack = () => {
    setError('')
    if (currentStep > 1) setCurrentStep(currentStep - 1)
  }

  return (
    <div className="min-h-screen bg-canvas py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header Branding */}
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-white p-2 shadow-xs border border-line">
              <img
                src="/brand/chhatralekha-logo.png"
                alt="ChhatraLekha"
                className="w-36 h-auto block"
              />
            </div>
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-accent-strong">
                Identity Setup
              </span>
              <h1 className="text-lg font-bold text-heading m-0">
                User Onboarding & Institutional Access
              </h1>
            </div>
          </div>
          <span className="text-xs font-medium text-muted">
            Step {currentStep} of 7
          </span>
        </div>

        {/* Multi-step progress indicator */}
        <div className="space-y-2">
          <div className="grid grid-cols-7 gap-2">
            {STEPS.map((s) => (
              <div
                key={s.number}
                className={`h-2 rounded-full transition-colors ${
                  s.number < currentStep
                    ? 'bg-brand'
                    : s.number === currentStep
                    ? 'bg-accent-strong'
                    : 'bg-line'
                }`}
              />
            ))}
          </div>
          <div className="hidden sm:flex justify-between text-xs text-muted px-1">
            {STEPS.map((s) => (
              <span
                key={s.number}
                className={s.number === currentStep ? 'font-bold text-heading' : ''}
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>

        {error && (
          <div className="rounded-md border border-danger/30 bg-danger/10 p-3 text-sm text-danger" role="alert">
            {error}
          </div>
        )}

        {/* STEP 1: WELCOME */}
        {currentStep === 1 && (
          <Card className="p-6 sm:p-8 space-y-6 shadow-xs border-line">
            <div className="space-y-2">
              <span className="inline-block rounded-full bg-brand-light px-3 py-1 text-xs font-bold text-brand uppercase tracking-wider">
                Getting Started
              </span>
              <h2 className="text-2xl font-black text-heading m-0">
                Welcome to ChhatraLekha
              </h2>
              <p className="text-sm text-muted m-0">
                ChhatraLekha connects students, parents, educators, and academic administrators across India through unified, verified digital academic identities.
              </p>
            </div>

            <div className="rounded-lg border border-line bg-surface p-5 space-y-4">
              <h3 className="text-sm font-bold text-heading uppercase tracking-wider m-0">
                What you will complete in this setup:
              </h3>
              <ul className="space-y-3 text-sm text-body m-0 p-0 list-none">
                <li className="flex items-start gap-3">
                  <span className="h-5 w-5 rounded-full bg-brand/10 text-brand flex items-center justify-center text-xs font-bold shrink-0">1</span>
                  <span><strong>Account Purpose:</strong> Select how you intend to use the platform (Student, Parent, Faculty, or Campus Administrator).</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="h-5 w-5 rounded-full bg-brand/10 text-brand flex items-center justify-center text-xs font-bold shrink-0">2</span>
                  <span><strong>Basic Profile:</strong> Confirm your legal name, contact details, and preferred vernacular language.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="h-5 w-5 rounded-full bg-brand/10 text-brand flex items-center justify-center text-xs font-bold shrink-0">3</span>
                  <span><strong>Institution Discovery:</strong> Search and select your school, college, or university from the national registry.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="h-5 w-5 rounded-full bg-brand/10 text-brand flex items-center justify-center text-xs font-bold shrink-0">4</span>
                  <span><strong>Role Details & Verification:</strong> Provide academic credentials or parent-child matching information.</span>
                </li>
              </ul>
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="primary" onClick={goNext}>
                Get Started
              </Button>
            </div>
          </Card>
        )}

        {/* STEP 2: CHOOSE ACCOUNT PURPOSE */}
        {currentStep === 2 && (
          <Card className="p-6 sm:p-8 space-y-6 shadow-xs border-line">
            <div className="space-y-1">
              <h2 className="text-xl font-black text-heading m-0">
                Choose Your Account Purpose
              </h2>
              <p className="text-sm text-muted m-0">
                Select your primary academic persona on ChhatraLekha. Multi-role access across institutions is supported after initial registration.
              </p>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              {ACCOUNT_ROLES.map((r) => {
                const isSelected = accountPurpose === r.id
                return (
                  <div
                    key={r.id}
                    onClick={() => setAccountPurpose(r.id)}
                    className={`cursor-pointer rounded-lg border p-5 transition-all text-left space-y-2 ${
                      isSelected
                        ? 'border-brand bg-brand-light shadow-xs ring-2 ring-brand'
                        : 'border-line bg-surface hover:border-brand/40'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-base font-bold text-heading">
                        {r.title}
                      </span>
                      {isSelected && (
                        <span className="h-4 w-4 rounded-full bg-brand text-white flex items-center justify-center text-[10px] font-black">
                          <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3} aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        </span>
                      )}
                    </div>
                    <p className="text-xs font-medium text-body m-0">
                      {r.subtitle}
                    </p>
                    <p className="text-xs text-muted m-0">
                      {r.details}
                    </p>
                  </div>
                )
              })}
            </div>

            {/* Privileged Administration Warning */}
            <div className="rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800 p-4 space-y-1 text-xs text-amber-900 dark:text-amber-200">
              <p className="font-bold m-0">
                Security Governance Notice:
              </p>
              <p className="m-0">
                University-wide registrars, state education departments, and national administrators must be provisioned through formal institutional onboarding and cannot self-register through this wizard.
              </p>
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="secondary" onClick={goBack}>
                Back
              </Button>
              <Button variant="primary" onClick={goNext}>
                Continue
              </Button>
            </div>
          </Card>
        )}

        {/* STEP 3: COMPLETE BASIC PROFILE */}
        {currentStep === 3 && (
          <Card className="p-6 sm:p-8 space-y-6 shadow-xs border-line">
            <div className="space-y-1">
              <h2 className="text-xl font-black text-heading m-0">
                Complete Basic Profile
              </h2>
              <p className="text-sm text-muted m-0">
                Establish your basic identity. Academic credentials remain separate from identity info.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                  Full Legal Name *
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g., Aarav Sharma"
                  className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                />
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                    Preferred Language
                  </label>
                  <select
                    value={preferredLanguage}
                    onChange={(e) => setPreferredLanguage(e.target.value)}
                    className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                  >
                    {LANGUAGES.map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                    Mobile Phone (Optional)
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-2">
                  Select Profile Avatar (Optional)
                </label>
                <div className="flex items-center gap-4">
                  {AVATARS.map((av) => (
                    <button
                      key={av.id}
                      type="button"
                      onClick={() => setAvatarUrl(av.url)}
                      className={`h-12 w-12 rounded-full border-2 p-0.5 transition-all overflow-hidden ${
                        avatarUrl === av.url
                          ? 'border-brand ring-2 ring-brand'
                          : 'border-line hover:border-brand/40'
                      }`}
                    >
                      <div className="h-full w-full rounded-full bg-line flex items-center justify-center text-xs font-bold text-muted uppercase">
                        {av.id.slice(-1)}
                      </div>
                    </button>
                  ))}
                  {avatarUrl && (
                    <button
                      type="button"
                      onClick={() => setAvatarUrl('')}
                      className="text-xs text-muted underline hover:text-danger"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="secondary" onClick={goBack} disabled={loading}>
                Back
              </Button>
              <Button variant="primary" onClick={goNext} disabled={loading}>
                {loading ? <Spinner size="sm" /> : 'Continue'}
              </Button>
            </div>
          </Card>
        )}

        {/* STEP 4: INSTITUTION DISCOVERY */}
        {currentStep === 4 && (
          <Card className="p-6 sm:p-8 space-y-6 shadow-xs border-line">
            <div className="space-y-1">
              <h2 className="text-xl font-black text-heading m-0">
                Discover Educational Institution
              </h2>
              <p className="text-sm text-muted m-0">
                Search the national institution directory to select your school, college, or university campus.
              </p>
            </div>

            {/* Search Bar & Filters */}
            <div className="space-y-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by institution name, city, or district..."
                className="w-full rounded-md border border-line bg-surface px-4 py-2.5 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
              />

              <div className="flex gap-2">
                {['ALL', 'SCHOOL', 'COLLEGE', 'UNIVERSITY'].map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setCategoryFilter(cat)}
                    className={`rounded-md px-3 py-1.5 text-xs font-semibold uppercase tracking-wider transition-colors ${
                      categoryFilter === cat
                        ? 'bg-brand text-white'
                        : 'border border-line bg-surface text-muted hover:text-heading'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Results list */}
            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {searching ? (
                <div className="flex items-center justify-center p-8 text-sm text-muted">
                  <Spinner size="sm" />
                  <span className="ml-2">Searching directory...</span>
                </div>
              ) : institutions.length === 0 ? (
                <div className="rounded-lg border border-line bg-surface p-6 text-center text-sm text-muted">
                  No institutions found matching your criteria. Try adjusting your search query.
                </div>
              ) : (
                institutions.map((inst) => {
                  const isSelected = selectedInstitution?.institution_id === inst.institution_id
                  return (
                    <div
                      key={inst.institution_id}
                      onClick={() => setSelectedInstitution(inst)}
                      className={`cursor-pointer rounded-lg border p-4 transition-all flex items-start justify-between gap-4 ${
                        isSelected
                          ? 'border-brand bg-brand-light shadow-xs ring-2 ring-brand'
                          : 'border-line bg-surface hover:border-brand/40'
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-heading">
                            {inst.name}
                          </span>
                          <span className="rounded-full bg-line px-2 py-0.5 text-[10px] font-semibold uppercase text-muted">
                            {inst.category || inst.institution_type}
                          </span>
                        </div>
                        <p className="text-xs text-muted m-0">
                          {inst.city && `${inst.city}, `}{inst.state || 'India'}
                          {inst.affiliation && ` • Affiliated: ${inst.affiliation}`}
                        </p>
                        <div className="flex items-center gap-2 pt-1">
                          {inst.is_registered ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-success">
                              <span className="h-1.5 w-1.5 rounded-full bg-success" />
                              Onboarded on ChhatraLekha
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-muted">
                              <span className="h-1.5 w-1.5 rounded-full bg-muted" />
                              Available in Directory (Invitation Pending)
                            </span>
                          )}
                        </div>
                      </div>

                      {isSelected && (
                        <span className="rounded-full bg-brand text-white px-2.5 py-1 text-xs font-bold shrink-0">
                          Selected
                        </span>
                      )}
                    </div>
                  )
                })
              )}
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="secondary" onClick={goBack}>
                Back
              </Button>
              <Button variant="primary" onClick={goNext} disabled={!selectedInstitution}>
                Continue
              </Button>
            </div>
          </Card>
        )}

        {/* STEP 5: ROLE-SPECIFIC DETAILS */}
        {currentStep === 5 && (
          <Card className="p-6 sm:p-8 space-y-6 shadow-xs border-line">
            <div className="space-y-1">
              <h2 className="text-xl font-black text-heading m-0">
                Provide Role Information
              </h2>
              <p className="text-sm text-muted m-0">
                Details required for {selectedInstitution?.name} to verify your relationship.
              </p>
            </div>

            {/* Student Specific Fields */}
            {accountPurpose === 'student' && (
              <div className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                      Course / Programme Name
                    </label>
                    <input
                      type="text"
                      value={studentCourse}
                      onChange={(e) => setStudentCourse(e.target.value)}
                      placeholder="e.g., B.Tech Computer Science"
                      className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                      Class / Grade / Year
                    </label>
                    <input
                      type="text"
                      value={studentClass}
                      onChange={(e) => setStudentClass(e.target.value)}
                      placeholder="e.g., 3rd Year / Semester 5"
                      className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                    />
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                      Academic Year
                    </label>
                    <input
                      type="text"
                      value={studentAcademicYear}
                      onChange={(e) => setStudentAcademicYear(e.target.value)}
                      placeholder="2024-25"
                      className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                      Roll Number or APAAR ID
                    </label>
                    <input
                      type="text"
                      value={studentIdentifier}
                      onChange={(e) => setStudentIdentifier(e.target.value)}
                      placeholder="e.g., ROLL-2024-001"
                      className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Parent Specific Fields */}
            {accountPurpose === 'parent' && (
              <div className="space-y-4">
                <div className="rounded-lg border border-accent/40 bg-accent-light p-4 space-y-1 text-xs text-heading">
                  <p className="font-bold m-0">
                    Child Privacy Protection Policy:
                  </p>
                  <p className="m-0 text-muted">
                    Parent access requires cryptographically matching both the student identifier and birth date. Unverified requests never expose academic or personal data.
                  </p>
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                      Student APAAR ID or Institute Roll No *
                    </label>
                    <input
                      type="text"
                      value={studentIdentifier}
                      onChange={(e) => setStudentIdentifier(e.target.value)}
                      placeholder="e.g., 998877665544"
                      className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                      Student Date of Birth (YYYY-MM-DD) *
                    </label>
                    <input
                      type="date"
                      value={studentDob}
                      onChange={(e) => setStudentDob(e.target.value)}
                      className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                    Relationship
                  </label>
                  <select
                    value={parentRelationship}
                    onChange={(e) => setParentRelationship(e.target.value)}
                    className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                  >
                    <option value="Mother">Mother</option>
                    <option value="Father">Father</option>
                    <option value="Guardian">Legal Guardian</option>
                  </select>
                </div>
              </div>
            )}

            {/* Teacher Specific Fields */}
            {accountPurpose === 'teacher' && (
              <div className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                      Academic Department
                    </label>
                    <input
                      type="text"
                      value={teacherDepartment}
                      onChange={(e) => setTeacherDepartment(e.target.value)}
                      placeholder="e.g., Computer Science & Engineering"
                      className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                      Subject Specialization
                    </label>
                    <input
                      type="text"
                      value={teacherSpecialization}
                      onChange={(e) => setTeacherSpecialization(e.target.value)}
                      placeholder="e.g., Operating Systems"
                      className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                    Employee / Faculty ID
                  </label>
                  <input
                    type="text"
                    value={teacherEmployeeId}
                    onChange={(e) => setTeacherEmployeeId(e.target.value)}
                    placeholder="e.g., FAC-CS-2024"
                    className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                  />
                </div>
              </div>
            )}

            {/* Administrator Specific Fields */}
            {accountPurpose === 'institution_admin' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                    Official Administrative Designation
                  </label>
                  <input
                    type="text"
                    value={adminDesignation}
                    onChange={(e) => setAdminDesignation(e.target.value)}
                    placeholder="e.g., Registrar / Principal / Admissions Head"
                    className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-heading uppercase tracking-wider mb-1">
                    Authorization Remarks
                  </label>
                  <textarea
                    rows={3}
                    value={adminProofNotes}
                    onChange={(e) => setAdminProofNotes(e.target.value)}
                    placeholder="Briefly state your campus office appointment or administrative authorization."
                    className="w-full rounded-md border border-line bg-surface p-3 text-sm text-heading shadow-xs focus:border-brand focus:outline-none"
                  />
                </div>
              </div>
            )}

            <div className="flex justify-between pt-2">
              <Button variant="secondary" onClick={goBack}>
                Back
              </Button>
              <Button variant="primary" onClick={goNext}>
                Review Application
              </Button>
            </div>
          </Card>
        )}

        {/* STEP 6: REVIEW */}
        {currentStep === 6 && (
          <Card className="p-6 sm:p-8 space-y-6 shadow-xs border-line">
            <div className="space-y-1">
              <h2 className="text-xl font-black text-heading m-0">
                Review Your Information
              </h2>
              <p className="text-sm text-muted m-0">
                Confirm your details before submitting your institutional join request.
              </p>
            </div>

            <div className="divide-y divide-line rounded-lg border border-line bg-surface">
              {/* Purpose */}
              <div className="p-4 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-muted">Account Purpose</span>
                  <p className="text-sm font-bold text-heading m-0 capitalize">
                    {accountPurpose.replace('_', ' ')}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="text-xs font-semibold text-brand hover:underline"
                >
                  Edit
                </button>
              </div>

              {/* Profile */}
              <div className="p-4 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-muted">Basic Profile</span>
                  <p className="text-sm font-bold text-heading m-0">
                    {fullName} ({LANGUAGES.find((l) => l.code === preferredLanguage)?.label || preferredLanguage})
                  </p>
                  {phone && <p className="text-xs text-muted m-0">{phone}</p>}
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  className="text-xs font-semibold text-brand hover:underline"
                >
                  Edit
                </button>
              </div>

              {/* Institution */}
              <div className="p-4 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-muted">Target Institution</span>
                  <p className="text-sm font-bold text-heading m-0">
                    {selectedInstitution?.name}
                  </p>
                  <p className="text-xs text-muted m-0">
                    {selectedInstitution?.city && `${selectedInstitution.city}, `}{selectedInstitution?.state}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(4)}
                  className="text-xs font-semibold text-brand hover:underline"
                >
                  Edit
                </button>
              </div>

              {/* Role Details */}
              <div className="p-4 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-muted">Role Details</span>
                  {accountPurpose === 'student' && (
                    <p className="text-sm text-body m-0">
                      {studentCourse || 'General Course'} - {studentClass || 'Current Year'} ({studentAcademicYear})
                    </p>
                  )}
                  {accountPurpose === 'parent' && (
                    <p className="text-sm text-body m-0">
                      Child ID: {studentIdentifier} ({parentRelationship})
                    </p>
                  )}
                  {accountPurpose === 'teacher' && (
                    <p className="text-sm text-body m-0">
                      {teacherDepartment || 'Academic Department'} - {teacherSpecialization || 'Faculty'}
                    </p>
                  )}
                  {accountPurpose === 'institution_admin' && (
                    <p className="text-sm text-body m-0">
                      Designation: {adminDesignation || 'Administrator'}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(5)}
                  className="text-xs font-semibold text-brand hover:underline"
                >
                  Edit
                </button>
              </div>
            </div>

            <div className="rounded-md border border-line bg-canvas p-4 text-xs text-muted">
              By submitting this request, you attest that the information provided is accurate and corresponds to your institutional standing. False impersonation violates platform terms.
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="secondary" onClick={goBack} disabled={loading}>
                Back
              </Button>
              <Button variant="primary" onClick={handleFinalSubmit} disabled={loading}>
                {loading ? <Spinner size="sm" /> : 'Submit Join Request'}
              </Button>
            </div>
          </Card>
        )}

        {/* STEP 7: COMPLETION */}
        {currentStep === 7 && (
          <Card className="p-6 sm:p-8 space-y-6 shadow-xs border-line text-center">
            <div className="mx-auto h-12 w-12 rounded-full bg-success/20 text-success flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <div className="space-y-2">
              <span className="inline-block rounded-full bg-accent-light px-3 py-1 text-xs font-bold text-accent-strong uppercase tracking-wider">
                Submission Recorded
              </span>
              <h2 className="text-2xl font-black text-heading m-0">
                Join Request Submitted Successfully
              </h2>
              <p className="text-sm text-muted max-w-lg mx-auto m-0">
                Your request to join <strong>{selectedInstitution?.name}</strong> as <strong>{accountPurpose.replace('_', ' ')}</strong> has been registered.
              </p>
            </div>

            {submittedRequest && (
              <div className="rounded-lg border border-line bg-surface p-4 text-left max-w-md mx-auto space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted">Reference ID:</span>
                  <span className="font-mono font-bold text-heading">{submittedRequest.request_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Status:</span>
                  <Badge variant="warning">{submittedRequest.status}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Submission Date:</span>
                  <span className="text-body">{new Date(submittedRequest.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            )}

            <div className="rounded-lg border border-line bg-surface p-5 text-left max-w-lg mx-auto space-y-3">
              <h3 className="text-xs font-bold text-heading uppercase tracking-wider m-0">
                Next Steps:
              </h3>
              <ul className="space-y-2 text-xs text-muted m-0 p-0 list-none">
                <li className="flex items-start gap-2">
                  <span className="h-4 w-4 rounded-full bg-brand/10 text-brand flex items-center justify-center text-[10px] font-bold shrink-0">1</span>
                  <span>Institution verification officer reviews applicant credentials.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="h-4 w-4 rounded-full bg-brand/10 text-brand flex items-center justify-center text-[10px] font-bold shrink-0">2</span>
                  <span>You will receive an in-app notification when your membership is approved.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="h-4 w-4 rounded-full bg-brand/10 text-brand flex items-center justify-center text-[10px] font-bold shrink-0">3</span>
                  <span>You can track your join request status in your profile at any time.</span>
                </li>
              </ul>
            </div>

            <div className="pt-2">
              <Button
                variant="primary"
                onClick={() => navigate(targetDashboard)}
              >
                Go to Workspace
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}

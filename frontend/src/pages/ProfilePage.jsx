import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import ProfilePictureModal from '../components/profile/ProfilePictureModal'

export default function ProfilePage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  // Active settings tab
  const [activeTab, setActiveTab] = useState('details')

  // Edit fields
  const [fullName, setFullName] = useState('')
  const [mobile, setMobile] = useState('')
  const [language, setLanguage] = useState('en')
  const [savingDetails, setSavingDetails] = useState(false)

  // Email management states
  const [personalEmailInput, setPersonalEmailInput] = useState('')
  const [personalCode, setPersonalCode] = useState('')
  const [personalPending, setPersonalPending] = useState(false)
  const [personalMsg, setPersonalMsg] = useState('')

  const [institutionEmailInput, setInstitutionEmailInput] = useState('')
  const [institutionCode, setInstitutionCode] = useState('')
  const [institutionPending, setInstitutionPending] = useState(false)
  const [institutionMsg, setInstitutionMsg] = useState('')

  // Profile picture modal
  const [pictureModalOpen, setPictureModalOpen] = useState(false)

  // Sessions
  const [sessions, setSessions] = useState([])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      const resp = await api.get('/profile/me')
      setProfile(resp.data)
      setFullName(resp.data.full_name || '')
      setMobile(resp.data.mobile || '')
      setLanguage(resp.data.preferred_language || 'en')
      setPersonalEmailInput(resp.data.personal_email || resp.data.email || '')
      setInstitutionEmailInput(resp.data.institution_email || '')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load profile details.')
    } finally {
      setLoading(false)
    }
  }

  const fetchSessions = async () => {
    try {
      const resp = await api.get('/profile/sessions')
      setSessions(resp.data || [])
    } catch {
      // Non-critical
    }
  }

  useEffect(() => {
    fetchProfile()
    fetchSessions()
  }, [])

  const handleSaveDetails = async (e) => {
    e.preventDefault()
    setSavingDetails(true)
    setError('')
    setSuccessMessage('')
    try {
      await api.put('/profile/me', {
        full_name: fullName,
        mobile: mobile,
        preferred_language: language,
      })
      setSuccessMessage('Profile details updated successfully.')
      fetchProfile()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setSavingDetails(false)
    }
  }

  const handleRequestEmailCode = async (type) => {
    setError('')
    setSuccessMessage('')
    const targetEmail = type === 'personal' ? personalEmailInput : institutionEmailInput
    if (!targetEmail) return

    try {
      const resp = await api.post('/profile/email', {
        email_type: type,
        email: targetEmail,
      })
      if (type === 'personal') {
        setPersonalPending(true)
        setPersonalMsg(resp.data.message)
        if (resp.data.demo_verification_code) {
          setPersonalCode(resp.data.demo_verification_code)
        }
      } else {
        setInstitutionPending(true)
        setInstitutionMsg(resp.data.message)
        if (resp.data.demo_verification_code) {
          setInstitutionCode(resp.data.demo_verification_code)
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to request ${type} email verification.`)
    }
  }

  const handleVerifyEmail = async (type) => {
    setError('')
    setSuccessMessage('')
    const code = type === 'personal' ? personalCode : institutionCode
    if (!code) return

    try {
      const resp = await api.post('/profile/verify-email', {
        email_type: type,
        code: code,
      })
      setSuccessMessage(resp.data.message)
      if (type === 'personal') {
        setPersonalPending(false)
        setPersonalCode('')
        setPersonalMsg('')
      } else {
        setInstitutionPending(false)
        setInstitutionCode('')
        setInstitutionMsg('')
      }
      fetchProfile()
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to verify ${type} email.`)
    }
  }

  if (loading) {
    return (
      <div className="p-8 text-center text-muted text-sm">
        Loading profile details...
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="p-8 text-center text-red-600 text-sm">
        {error || 'Unable to retrieve profile information.'}
      </div>
    )
  }

  const avatarUrl = profile.active_avatar_url || profile.profile_pictures?.common_url
  const completionPct = profile.profile_completion_percentage || 50

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Top Breadcrumb & Status */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="m-0 text-xl font-bold text-ink">User Profile & Account</h1>
          <p className="m-0 text-xs text-muted mt-0.5">
            Manage your personal identity, verified emails, and platform preferences.
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          {profile.account_status}
        </span>
      </div>

      {/* Alerts */}
      {error && (
        <div className="p-3 rounded bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}
      {successMessage && (
        <div className="p-3 rounded bg-emerald-50 border border-emerald-200 text-xs text-emerald-700">
          {successMessage}
        </div>
      )}

      {/* Main Profile Summary Card */}
      <div className="rounded-lg border border-line bg-surface p-5 sm:p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          {/* Avatar with edit overlay */}
          <div className="relative group">
            <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full border-2 border-brand/30 overflow-hidden bg-surface-2 flex items-center justify-center flex-shrink-0 shadow-xs">
              {avatarUrl ? (
                <img src={avatarUrl} alt={profile.full_name} className="w-full h-full object-cover" />
              ) : (
                <span className="text-2xl sm:text-3xl font-bold text-brand">
                  {profile.full_name?.charAt(0)?.toUpperCase() || 'U'}
                </span>
              )}
            </div>
            <button
              type="button"
              onClick={() => setPictureModalOpen(true)}
              className="absolute inset-0 rounded-full bg-black/40 text-white opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-[10px] font-semibold cursor-pointer border-0"
              title="Change picture"
            >
              <svg className="w-4 h-4 mb-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Change</span>
            </button>
          </div>

          {/* Core Identity Details */}
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="m-0 text-lg font-bold text-ink">{profile.full_name}</h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-brand text-white">
                {profile.role_label}
              </span>
            </div>
            <p className="m-0 text-xs text-muted font-mono">
              ID: <span className="text-ink font-semibold">{profile.user_id}</span>
            </p>
            <p className="m-0 text-xs text-muted">
              Institution: <span className="text-ink font-medium">{profile.institution_name}</span>
            </p>
            <p className="m-0 text-[11px] text-muted">
              Member since: {new Date(profile.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Profile Completion Indicator */}
        <div className="w-full md:w-64 p-3.5 rounded border border-line bg-surface-2 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-ink">Profile Strength</span>
            <span className="font-bold text-brand">{completionPct}%</span>
          </div>
          <div className="w-full bg-surface rounded-full h-2 overflow-hidden border border-line">
            <div
              className="bg-brand h-full rounded-full transition-all duration-300"
              style={{ width: `${completionPct}%` }}
            />
          </div>
          <p className="m-0 text-[11px] text-muted leading-tight">
            {completionPct === 100
              ? 'Your profile is fully verified.'
              : 'Verify your institutional email to reach 100% completion.'}
          </p>
        </div>
      </div>

      {/* Role-Specific Information Panel */}
      {profile.role === 'student' && profile.student_details && (
        <div className="rounded-lg border border-line bg-surface p-5 sm:p-6 shadow-xs space-y-4">
          <div className="border-b border-line pb-2 flex items-center justify-between">
            <h3 className="m-0 text-sm font-bold text-ink uppercase tracking-wider">Academic Record & Identity</h3>
            <span className="text-xs text-muted">APAAR: {profile.student_details.apaar_id_masked}</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Enrolled Programme</span>
              <span className="text-ink font-medium block">{profile.student_details.programme_name}</span>
              <span className="text-muted text-[11px] block">{profile.student_details.department}</span>
            </div>
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Class & Academic Year</span>
              <span className="text-ink font-medium block">{profile.student_details.class_section}</span>
              <span className="text-muted text-[11px] block">Year: {profile.student_details.academic_year} ({profile.student_details.current_semester})</span>
            </div>
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Institutional Roll Number</span>
              <span className="text-ink font-medium block font-mono">{profile.student_details.institute_roll_no}</span>
              <span className="text-muted text-[11px] block">Quota: {profile.student_details.admission_quota}</span>
            </div>
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Attendance Record</span>
              <span className="text-emerald-700 font-bold text-base block">{profile.student_details.attendance_percentage}%</span>
              <span className="text-muted text-[11px] block">Good standing (above 75% threshold)</span>
            </div>
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Cumulative CGPA</span>
              <span className="text-brand font-bold text-base block">{profile.student_details.cumulative_cgpa} / 10.0</span>
              <span className="text-muted text-[11px] block">Verified Semester 1 to 4 transcripts</span>
            </div>
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Guardian Association</span>
              <span className="text-ink font-medium block">{profile.student_details.guardian_name}</span>
              <span className="text-muted text-[11px] block">{profile.student_details.guardian_relationship} ({profile.student_details.guardian_phone_masked})</span>
            </div>
          </div>
        </div>
      )}

      {profile.role === 'teacher' && profile.teacher_details && (
        <div className="rounded-lg border border-line bg-surface p-5 sm:p-6 shadow-xs space-y-4">
          <div className="border-b border-line pb-2 flex items-center justify-between">
            <h3 className="m-0 text-sm font-bold text-ink uppercase tracking-wider">Faculty & Academic Duties</h3>
            <span className="text-xs text-muted">ID: {profile.teacher_details.employee_id}</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Designation & Department</span>
              <span className="text-ink font-medium block">{profile.teacher_details.designation}</span>
              <span className="text-muted text-[11px] block">{profile.teacher_details.department}</span>
            </div>
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Qualifications</span>
              <span className="text-ink font-medium block">{profile.teacher_details.qualifications}</span>
              <span className="text-muted text-[11px] block">Experience: {profile.teacher_details.total_experience_years} years</span>
            </div>
          </div>
          <div className="space-y-1 text-xs">
            <span className="text-muted font-semibold block text-[11px]">Subjects Taught</span>
            <div className="flex flex-wrap gap-2 pt-1">
              {profile.teacher_details.subjects_taught.map((subj, idx) => (
                <span key={idx} className="px-2.5 py-1 rounded bg-surface-2 border border-line text-ink font-medium">
                  {subj}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {profile.admin_details && (
        <div className="rounded-lg border border-line bg-surface p-5 sm:p-6 shadow-xs space-y-4">
          <div className="border-b border-line pb-2 flex items-center justify-between">
            <h3 className="m-0 text-sm font-bold text-ink uppercase tracking-wider">Institutional Authority & Governance</h3>
            <span className="text-xs text-muted">{profile.admin_details.security_status}</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Designation</span>
              <span className="text-ink font-medium block">{profile.admin_details.admin_designation}</span>
            </div>
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Sanctioned Intake Capacity</span>
              <span className="text-ink font-medium block">{profile.admin_details.sanctioned_student_capacity || 'Universal Directorate'}</span>
            </div>
            <div className="p-3 rounded border border-line bg-surface-2 space-y-1">
              <span className="text-muted block font-semibold text-[11px]">Accreditation & Compliance</span>
              <span className="text-emerald-700 font-bold block">{profile.admin_details.compliance_rating || 'Verified State Node'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Settings & Configuration Tabs */}
      <div className="rounded-lg border border-line bg-surface shadow-xs overflow-hidden">
        {/* Tab Headers */}
        <div className="flex border-b border-line bg-surface-2 overflow-x-auto text-xs">
          {[
            { id: 'details', label: 'Profile Details' },
            { id: 'email', label: 'Email Management' },
            { id: 'avatars', label: 'Platform Avatars' },
            { id: 'sessions', label: 'Active Sessions' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-5 font-semibold text-center whitespace-nowrap cursor-pointer border-0 transition-colors ${
                activeTab === tab.id
                  ? 'bg-surface text-brand border-b-2 border-brand font-bold'
                  : 'text-muted hover:text-ink hover:bg-surface/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 1: Profile Details */}
        {activeTab === 'details' && (
          <form onSubmit={handleSaveDetails} className="p-6 space-y-4 max-w-xl text-xs">
            <div className="space-y-1">
              <label htmlFor="input_name" className="block font-semibold text-ink">
                Full Display Name
              </label>
              <input
                id="input_name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
                required
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="input_mobile" className="block font-semibold text-ink">
                Mobile Number (for SMS & 2FA recovery)
              </label>
              <input
                id="input_mobile"
                type="text"
                value={mobile}
                onChange={(e) => setMobile(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="input_lang" className="block font-semibold text-ink">
                Preferred Interface Language
              </label>
              <select
                id="input_lang"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand cursor-pointer"
              >
                <option value="en">English</option>
                <option value="hi">Hindi (हिन्दी)</option>
                <option value="bn">Bengali (বাংলা)</option>
                <option value="te">Telugu (తెలుగు)</option>
                <option value="mr">Marathi (मराठी)</option>
                <option value="ta">Tamil (தமிழ்)</option>
                <option value="gu">Gujarati (ગુજરાતી)</option>
                <option value="kn">Kannada (ಕನ್ನಡ)</option>
                <option value="ml">Malayalam (മലയാളം)</option>
                <option value="or">Odia (ଓଡ଼ିଆ)</option>
                <option value="pa">Punjabi (ਪੰਜਾਬੀ)</option>
                <option value="as">Assamese (অসমীয়া)</option>
                <option value="ur">Urdu (اردو)</option>
              </select>
            </div>
            <div className="pt-2">
              <button
                type="submit"
                disabled={savingDetails}
                className="px-4 py-2 rounded bg-brand text-white text-xs font-semibold shadow-xs hover:bg-brand-deep cursor-pointer disabled:opacity-50"
              >
                {savingDetails ? 'Saving Changes...' : 'Save Profile Details'}
              </button>
            </div>
          </form>
        )}

        {/* Tab 2: Email Management System */}
        {activeTab === 'email' && (
          <div className="p-6 space-y-6 max-w-2xl text-xs">
            {/* Personal Email Card */}
            <div className="rounded border border-line bg-surface-2 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="m-0 font-bold text-ink">Personal Email Address</h4>
                  <p className="m-0 text-[11px] text-muted">Primary address for login, password recovery, and security alerts.</p>
                </div>
                {profile.personal_email_verified ? (
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                    Verified
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-800 border border-amber-300">
                    Unverified
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={personalEmailInput}
                  onChange={(e) => setPersonalEmailInput(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
                  placeholder="personal.email@example.com"
                />
                <button
                  type="button"
                  onClick={() => handleRequestEmailCode('personal')}
                  className="px-3 py-1.5 rounded bg-brand text-white font-semibold cursor-pointer hover:bg-brand-deep"
                >
                  Send Code
                </button>
              </div>
              {personalMsg && <p className="m-0 text-[11px] text-brand">{personalMsg}</p>}
              {personalPending && (
                <div className="p-3 rounded border border-line bg-surface space-y-2">
                  <label className="block text-[11px] font-semibold text-ink">Enter 6-Digit Verification Code</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      maxLength={6}
                      value={personalCode}
                      onChange={(e) => setPersonalCode(e.target.value)}
                      placeholder="123456"
                      className="w-32 px-3 py-1.5 rounded border border-line bg-surface text-ink text-xs font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => handleVerifyEmail('personal')}
                      className="px-3 py-1.5 rounded bg-emerald-700 text-white font-semibold cursor-pointer hover:bg-emerald-800"
                    >
                      Verify Personal Email
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Institution-Issued Email Card */}
            <div className="rounded border border-line bg-surface-2 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="m-0 font-bold text-ink">Institution-Issued Email Address</h4>
                  <p className="m-0 text-[11px] text-muted">Provided by your school, college, or university for official academic notices.</p>
                </div>
                {profile.institution_email_verified ? (
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                    Verified Domain
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-surface text-muted border border-line">
                    Optional
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={institutionEmailInput}
                  onChange={(e) => setInstitutionEmailInput(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
                  placeholder="rollno@institution.ac.in"
                />
                <button
                  type="button"
                  onClick={() => handleRequestEmailCode('institution')}
                  className="px-3 py-1.5 rounded bg-surface border border-line text-ink font-semibold cursor-pointer hover:bg-surface-2"
                >
                  Verify
                </button>
              </div>
              {institutionMsg && <p className="m-0 text-[11px] text-brand">{institutionMsg}</p>}
              {institutionPending && (
                <div className="p-3 rounded border border-line bg-surface space-y-2">
                  <label className="block text-[11px] font-semibold text-ink">Enter 6-Digit Institutional Code</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      maxLength={6}
                      value={institutionCode}
                      onChange={(e) => setInstitutionCode(e.target.value)}
                      placeholder="123456"
                      className="w-32 px-3 py-1.5 rounded border border-line bg-surface text-ink text-xs font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => handleVerifyEmail('institution')}
                      className="px-3 py-1.5 rounded bg-emerald-700 text-white font-semibold cursor-pointer hover:bg-emerald-800"
                    >
                      Confirm Institutional Email
                    </button>
                  </div>
                </div>
              )}
              <div className="p-2.5 rounded bg-blue-50/70 border border-blue-200/60 text-[11px] text-blue-900 leading-normal">
                Notice: ChhatraLekha never creates an official institutional email account. Associating your institution email verifies your domain affiliation for academic updates.
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Platform Profile Pictures */}
        {activeTab === 'avatars' && (
          <div className="p-6 space-y-6 max-w-2xl text-xs">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h4 className="m-0 font-bold text-ink">Cross-Platform Avatars</h4>
                <p className="m-0 text-muted text-[11px]">
                  Setting: {profile.profile_pictures?.use_common ? 'Common across all platforms' : 'Custom picture per platform'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPictureModalOpen(true)}
                className="px-3 py-1.5 rounded bg-brand text-white font-semibold cursor-pointer hover:bg-brand-deep"
              >
                Manage Pictures
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-3 rounded border border-line bg-surface-2 text-center space-y-2">
                <span className="font-semibold text-ink block text-[11px]">Web Application</span>
                <div className="w-16 h-16 mx-auto rounded-full overflow-hidden bg-surface border border-line flex items-center justify-center">
                  <img
                    src={profile.profile_pictures?.web_url || profile.profile_pictures?.common_url || avatarUrl}
                    alt="Web avatar"
                    className="w-full h-full object-cover"
                  />
                </div>
                <span className="text-[10px] text-muted block">Active in desktop browsers</span>
              </div>
              <div className="p-3 rounded border border-line bg-surface-2 text-center space-y-2">
                <span className="font-semibold text-ink block text-[11px]">Android Client</span>
                <div className="w-16 h-16 mx-auto rounded-full overflow-hidden bg-surface border border-line flex items-center justify-center">
                  <img
                    src={profile.profile_pictures?.android_url || profile.profile_pictures?.common_url || avatarUrl}
                    alt="Android avatar"
                    className="w-full h-full object-cover"
                  />
                </div>
                <span className="text-[10px] text-muted block">Active in Android app</span>
              </div>
              <div className="p-3 rounded border border-line bg-surface-2 text-center space-y-2">
                <span className="font-semibold text-ink block text-[11px]">iOS Client</span>
                <div className="w-16 h-16 mx-auto rounded-full overflow-hidden bg-surface border border-line flex items-center justify-center">
                  <img
                    src={profile.profile_pictures?.ios_url || profile.profile_pictures?.common_url || avatarUrl}
                    alt="iOS avatar"
                    className="w-full h-full object-cover"
                  />
                </div>
                <span className="text-[10px] text-muted block">Active in iOS app</span>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Active Login Sessions */}
        {activeTab === 'sessions' && (
          <div className="p-6 space-y-4 max-w-2xl text-xs">
            <h4 className="m-0 font-bold text-ink">Security & Active Device Sessions</h4>
            <p className="m-0 text-muted text-[11px]">
              Review all devices currently authenticated to your ChhatraLekha account.
            </p>
            <div className="space-y-3 pt-2">
              {sessions.map((sess) => (
                <div
                  key={sess.session_id}
                  className="p-3.5 rounded border border-line bg-surface-2 flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-ink">{sess.device}</span>
                      {sess.is_current && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-brand text-white">
                          Current Session
                        </span>
                      )}
                    </div>
                    <p className="m-0 text-[11px] text-muted font-mono">
                      IP: {sess.ip_address} | Last Active: {new Date(sess.last_active_at).toLocaleString()}
                    </p>
                  </div>
                  {!sess.is_current && (
                    <button
                      type="button"
                      className="px-2.5 py-1 rounded border border-line bg-surface text-xs font-semibold text-red-600 hover:bg-red-50 cursor-pointer"
                    >
                      Revoke
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Picture Management Modal */}
      <ProfilePictureModal
        isOpen={pictureModalOpen}
        onClose={() => setPictureModalOpen(false)}
        pictures={profile.profile_pictures || {}}
        onUpdated={() => {
          fetchProfile()
        }}
      />
    </div>
  )
}

import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import { useAuth } from '../../hooks/useAuth'
import ProfilePictureModal from './ProfilePictureModal'
import EmailManager from './EmailManager'
import PreferencesTab from './PreferencesTab'

const TABS = [
  { id: 'details', label: 'Details' },
  { id: 'emails', label: 'Email Management' },
  { id: 'avatars', label: 'Platform Avatars' },
  { id: 'preferences', label: 'Preferences' },
  { id: 'sessions', label: 'Active Sessions' },
]

export default function ProfilePage() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [sessions, setSessions] = useState([])
  const [activeTab, setActiveTab] = useState('details')
  const [isAvatarModalOpen, setIsAvatarModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  // Edit details form state
  const [editFullName, setEditFullName] = useState('')
  const [editDisplayName, setEditDisplayName] = useState('')
  const [editPhone, setEditPhone] = useState('')
  const [editBio, setEditBio] = useState('')
  const [editSuccess, setEditSuccess] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const fetchProfile = async () => {
    try {
      const res = await api.get('/profile/me')
      setProfile(res.data)
      setEditFullName(res.data.full_name || '')
      setEditDisplayName(res.data.display_name || '')
      setEditPhone(res.data.phone || res.data.mobile || '')
      setEditBio(res.data.bio || '')
    } catch {
      // Fallback state if offline
    } finally {
      setLoading(false)
    }
  }

  const fetchSessions = async () => {
    try {
      const res = await api.get('/profile/sessions')
      setSessions(res.data || [])
    } catch {
      // Ignore
    }
  }

  useEffect(() => {
    fetchProfile()
    fetchSessions()
  }, [])

  const handleSaveDetails = async (e) => {
    e.preventDefault()
    setIsSaving(true)
    try {
      await api.put('/profile/me', {
        full_name: editFullName,
        display_name: editDisplayName,
        phone: editPhone,
        bio: editBio,
      })
      setEditSuccess(true)
      setTimeout(() => setEditSuccess(false), 3000)
      fetchProfile()
    } finally {
      setIsSaving(false)
    }
  }

  const handleSavePreferences = async (prefUpdates) => {
    await api.put('/profile/me', {
      preferences: prefUpdates,
    })
    fetchProfile()
  }

  const role = (profile?.role || user?.role || 'student').toLowerCase()
  const userInitial = (profile?.display_name || profile?.full_name || user?.display_name || 'U').charAt(0).toUpperCase()
  const activeAvatar = profile?.active_avatar_url || profile?.profile_pictures?.common_url

  if (loading && !profile) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center text-xs text-muted">
        Loading profile information...
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Top Profile Summary Card */}
      <div className="rounded-lg bg-surface border border-line p-6 shadow-xs flex flex-col sm:flex-row items-center sm:items-start gap-6">
        <div className="relative flex-shrink-0">
          <div className="w-20 h-20 rounded-full border-2 border-brand/40 overflow-hidden bg-brand/10 flex items-center justify-center text-2xl font-bold text-brand shadow-xs">
            {activeAvatar ? (
              <img src={activeAvatar} alt="Profile avatar" className="w-full h-full object-cover" />
            ) : (
              userInitial
            )}
          </div>
          <button
            type="button"
            onClick={() => setIsAvatarModalOpen(true)}
            className="absolute bottom-0 right-0 p-1.5 rounded-full bg-brand text-on-brand shadow-xs hover:bg-brand-deep cursor-pointer border-2 border-surface"
            title="Change Avatar"
            aria-label="Change Avatar"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>

        <div className="min-w-0 flex-1 text-center sm:text-left space-y-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h1 className="m-0 text-xl font-bold text-ink">{profile?.full_name || 'User Profile'}</h1>
              <p className="m-0 text-xs text-muted">{profile?.display_name || profile?.full_name}</p>
            </div>
            <div className="flex items-center justify-center sm:justify-start gap-2">
              <span className="rounded bg-brand/10 text-brand border border-brand/20 px-2 py-0.5 text-xs font-semibold">
                {profile?.role_label || role.toUpperCase()}
              </span>
              <span className="rounded bg-surface-2 text-ink border border-line px-2 py-0.5 text-xs font-semibold">
                {profile?.account_status || 'ACTIVE'}
              </span>
            </div>
          </div>

          {/* Profile Completion Meter */}
          <div className="pt-2">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-muted">Profile Completion</span>
              <span className="font-bold text-brand">{profile?.profile_completion_percentage || 85}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-surface-2 border border-line overflow-hidden">
              <div
                className="h-full bg-brand rounded-full transition-all duration-300"
                style={{ width: `${profile?.profile_completion_percentage || 85}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Institutional Memberships Card */}
      {profile?.memberships && profile.memberships.length > 0 && (
        <div className="rounded-lg bg-surface border border-line p-4 space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-ink uppercase tracking-wider">
              Institutional Memberships & Affiliations
            </span>
            <span className="text-[11px] text-muted font-mono">
              {profile.memberships.length} active institution{profile.memberships.length > 1 ? 's' : ''}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {profile.memberships.map((m) => (
              <div
                key={m.membership_id}
                className="p-3 rounded-lg bg-surface-2 border border-line flex items-start gap-3"
              >
                <div className="w-7 h-7 rounded bg-brand/20 text-brand font-bold text-xs flex items-center justify-center flex-shrink-0">
                  {m.institution_id.split('-')[0] || 'INS'}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="m-0 text-xs font-semibold text-ink truncate" title={m.institution_name}>
                    {m.institution_name}
                  </p>
                  <p className="m-0 text-[11px] text-muted">
                    {m.role_label} {m.department ? `| ${m.department}` : ''}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1.5 border-b border-line pb-2 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-brand text-on-brand shadow-xs'
                : 'bg-surface text-ink border border-line hover:border-brand'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      {activeTab === 'details' && (
        <div className="space-y-6">
          <form onSubmit={handleSaveDetails} className="rounded-lg bg-surface border border-line p-5 space-y-4 shadow-xs">
            <h2 className="m-0 text-sm font-bold text-ink">Personal Information</h2>

            {editSuccess && (
              <div className="p-3 rounded-lg bg-surface-2 border border-brand text-brand font-medium text-xs">
                Profile details successfully updated.
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-muted mb-1">Full Legal Name</label>
                <input
                  type="text"
                  required
                  value={editFullName}
                  onChange={(e) => setEditFullName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted mb-1">Display / Preferred Name</label>
                <input
                  type="text"
                  required
                  value={editDisplayName}
                  onChange={(e) => setEditDisplayName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted mb-1">Mobile Contact</label>
                <input
                  type="text"
                  value={editPhone}
                  onChange={(e) => setEditPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted mb-1">Academic Role</label>
                <input
                  type="text"
                  disabled
                  value={profile?.role_label || role.toUpperCase()}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-2 text-muted text-xs cursor-not-allowed"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-muted mb-1">Academic Bio / Note</label>
              <textarea
                rows={2}
                value={editBio}
                onChange={(e) => setEditBio(e.target.value)}
                placeholder="Brief summary of academic focus, honours, or institutional responsibilities."
                className="w-full px-3 py-2 rounded-lg border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
              />
            </div>

            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-2 rounded-lg bg-brand text-on-brand font-bold text-xs hover:bg-brand-deep cursor-pointer transition-colors shadow-xs"
            >
              {isSaving ? 'Saving...' : 'Save Profile Details'}
            </button>
          </form>

          {/* Role-Specific Academic Metadata */}
          {profile?.student_details && (
            <div className="rounded-lg bg-surface border border-line p-5 space-y-4 shadow-xs">
              <h2 className="m-0 text-sm font-bold text-ink">Academic Enrolment & Record Details</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                <div>
                  <span className="text-muted block font-medium">APAAR ID</span>
                  <span className="font-mono font-bold text-ink">{profile.student_details.apaar_id_masked}</span>
                </div>
                <div>
                  <span className="text-muted block font-medium">Student Portal ID</span>
                  <span className="font-mono font-bold text-ink">{profile.student_details.student_id}</span>
                </div>
                <div>
                  <span className="text-muted block font-medium">Roll Number</span>
                  <span className="font-mono font-bold text-ink">{profile.student_details.institute_roll_no}</span>
                </div>
                <div>
                  <span className="text-muted block font-medium">Programme</span>
                  <span className="font-semibold text-ink">{profile.student_details.programme_name}</span>
                </div>
                <div>
                  <span className="text-muted block font-medium">Department</span>
                  <span className="font-semibold text-ink">{profile.student_details.department}</span>
                </div>
                <div>
                  <span className="text-muted block font-medium">Academic Year</span>
                  <span className="font-semibold text-ink">{profile.student_details.academic_year} ({profile.student_details.current_semester})</span>
                </div>
                <div>
                  <span className="text-muted block font-medium">Attendance Rate</span>
                  <span className="font-bold text-brand">{profile.student_details.attendance_percentage}%</span>
                </div>
                <div>
                  <span className="text-muted block font-medium">Cumulative CGPA</span>
                  <span className="font-bold text-ink">{profile.student_details.cumulative_cgpa} / 10.0</span>
                </div>
                <div>
                  <span className="text-muted block font-medium">Verified Credentials</span>
                  <span className="font-bold text-ink">{profile.student_details.verified_credentials_count} Issued</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'emails' && (
        <EmailManager
          profile={profile}
          onProfileUpdated={fetchProfile}
        />
      )}

      {activeTab === 'avatars' && (
        <div className="rounded-lg bg-surface border border-line p-6 space-y-6 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="m-0 text-sm font-bold text-ink">Platform Profile Pictures</h2>
              <p className="m-0 text-xs text-muted mt-0.5">
                Set a common avatar or configure platform-specific pictures for Web, Android, and iOS.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsAvatarModalOpen(true)}
              className="px-4 py-2 rounded-lg bg-brand text-on-brand font-bold text-xs hover:bg-brand-deep cursor-pointer transition-colors shadow-xs"
            >
              Open Avatar Manager
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-surface-2 border border-line text-center space-y-2">
              <span className="text-xs font-bold text-ink block">Web Application</span>
              <div className="w-16 h-16 rounded-full mx-auto border border-line overflow-hidden bg-surface flex items-center justify-center">
                {profile?.profile_pictures?.web_url || profile?.profile_pictures?.common_url ? (
                  <img
                    src={profile.profile_pictures.web_url || profile.profile_pictures.common_url}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="font-bold text-brand">{userInitial}</span>
                )}
              </div>
              <span className="text-[10px] text-muted block">
                {profile?.profile_pictures?.use_common ? 'Using Common Avatar' : 'Platform Specific'}
              </span>
            </div>

            <div className="p-4 rounded-lg bg-surface-2 border border-line text-center space-y-2">
              <span className="text-xs font-bold text-ink block">Android App</span>
              <div className="w-16 h-16 rounded-full mx-auto border border-line overflow-hidden bg-surface flex items-center justify-center">
                {profile?.profile_pictures?.android_url || profile?.profile_pictures?.common_url ? (
                  <img
                    src={profile.profile_pictures.android_url || profile.profile_pictures.common_url}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="font-bold text-brand">{userInitial}</span>
                )}
              </div>
              <span className="text-[10px] text-muted block">
                {profile?.profile_pictures?.use_common ? 'Using Common Avatar' : 'Platform Specific'}
              </span>
            </div>

            <div className="p-4 rounded-lg bg-surface-2 border border-line text-center space-y-2">
              <span className="text-xs font-bold text-ink block">iOS App</span>
              <div className="w-16 h-16 rounded-full mx-auto border border-line overflow-hidden bg-surface flex items-center justify-center">
                {profile?.profile_pictures?.ios_url || profile?.profile_pictures?.common_url ? (
                  <img
                    src={profile.profile_pictures.ios_url || profile.profile_pictures.common_url}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="font-bold text-brand">{userInitial}</span>
                )}
              </div>
              <span className="text-[10px] text-muted block">
                {profile?.profile_pictures?.use_common ? 'Using Common Avatar' : 'Platform Specific'}
              </span>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'preferences' && (
        <PreferencesTab
          preferences={profile?.preferences}
          onSave={handleSavePreferences}
        />
      )}

      {activeTab === 'sessions' && (
        <div className="rounded-lg bg-surface border border-line p-6 space-y-4 shadow-xs">
          <div>
            <h2 className="m-0 text-sm font-bold text-ink">Active Device & Browser Sessions</h2>
            <p className="m-0 text-xs text-muted mt-0.5">
              Review platforms and IP addresses currently authenticated to your account.
            </p>
          </div>

          <div className="space-y-3">
            {sessions.map((sess) => (
              <div
                key={sess.session_id}
                className="p-3.5 rounded-lg bg-surface-2 border border-line flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-ink">{sess.device}</span>
                    {sess.is_current && (
                      <span className="rounded bg-brand/15 text-brand border border-brand/30 px-1.5 py-0.2 text-[10px] font-bold">
                        CURRENT SESSION
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-muted font-mono block mt-0.5">
                    IP Address: {sess.ip_address} | Last Active: {new Date(sess.last_active_at).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Picture Modal */}
      <ProfilePictureModal
        isOpen={isAvatarModalOpen}
        onClose={() => setIsAvatarModalOpen(false)}
        pictures={profile?.profile_pictures}
        onUpdated={() => fetchProfile()}
      />
    </div>
  )
}


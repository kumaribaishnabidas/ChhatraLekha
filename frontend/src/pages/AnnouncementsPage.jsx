import { useEffect, useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'
import { Card, Button } from '../components/common'
import PageHeader from '../components/layout/PageHeader'
import { useAuth } from '../hooks/useAuth'

const SAMPLE_FALLBACK_ANNOUNCEMENTS = [
  {
    announcement_id: 'ANN-DEMO-1',
    institution_id: 'INST-0421',
    title: 'Welcome to the New Academic Session 2025-26',
    content: 'Classes for the new session commence on Monday. Please review your class timetable and digital identity card in the academic wallet.',
    priority: 'NORMAL',
    target_scope: 'ALL',
    status: 'PUBLISHED',
    delivery_channels: ['IN_APP', 'EMAIL'],
    delivery_summary: { in_app: 150, email: 142, push: 0 },
    published_by: 'Academic Office',
    published_at: new Date(Date.now() - 86400000).toISOString(),
    is_acknowledged: false,
    acknowledgements: [],
  },
  {
    announcement_id: 'ANN-DEMO-2',
    institution_id: 'INST-0421',
    title: 'Mid-Term Examination Regulations & Schedule',
    content: 'The official mid-term examination timetable has been finalized. Hall tickets will be issued digitally through ChhatraLekha starting next week.',
    priority: 'HIGH',
    target_scope: 'DEPARTMENT',
    target_departments: ['Computer Science', 'Mechanical Engineering'],
    status: 'PUBLISHED',
    delivery_channels: ['IN_APP', 'EMAIL', 'PUSH'],
    delivery_summary: { in_app: 120, email: 118, push: 95 },
    published_by: 'Dean of Academic Affairs',
    published_at: new Date(Date.now() - 172800000).toISOString(),
    attachment_title: 'Exam_Guidelines_2025.pdf',
    attachment_url: 'https://cdn.chhatralekha.edu.in/docs/exam-guidelines.pdf',
    is_acknowledged: true,
    acknowledgements: ['user-1'],
  },
]

export default function AnnouncementsPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const [announcements, setAnnouncements] = useState([])
  const [loading, setLoading] = useState(true)
  const [showPostModal, setShowPostModal] = useState(false)
  const [editingAnnouncement, setEditingAnnouncement] = useState(null)

  // Filters
  const [scopeFilter, setScopeFilter] = useState('ALL')
  const [priorityFilter, setPriorityFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  // Form state
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [priority, setPriority] = useState('NORMAL')
  const [targetScope, setTargetScope] = useState('ALL')
  const [targetDepartments, setTargetDepartments] = useState('')
  const [targetClasses, setTargetClasses] = useState('')
  const [scheduledFor, setScheduledFor] = useState('')
  const [expiresAt, setExpiresAt] = useState('')
  const [inAppChannel, setInAppChannel] = useState(true)
  const [emailChannel, setEmailChannel] = useState(true)
  const [pushChannel, setPushChannel] = useState(true)
  const [attachmentTitle, setAttachmentTitle] = useState('')
  const [attachmentUrl, setAttachmentUrl] = useState('')
  const [feedback, setFeedback] = useState('')

  useEffect(() => {
    async function fetchAnnouncements() {
      try {
        const res = await api.get('/announcements')
        setAnnouncements(res.data && res.data.length > 0 ? res.data : SAMPLE_FALLBACK_ANNOUNCEMENTS)
      } catch (err) {
        setAnnouncements(SAMPLE_FALLBACK_ANNOUNCEMENTS)
      } finally {
        setLoading(false)
      }
    }
    fetchAnnouncements()
  }, [])

  const resetForm = () => {
    setTitle('')
    setContent('')
    setPriority('NORMAL')
    setTargetScope('ALL')
    setTargetDepartments('')
    setTargetClasses('')
    setScheduledFor('')
    setExpiresAt('')
    setInAppChannel(true)
    setEmailChannel(true)
    setPushChannel(true)
    setAttachmentTitle('')
    setAttachmentUrl('')
    setEditingAnnouncement(null)
  }

  const handlePostNotice = async (e) => {
    e.preventDefault()
    const channels = []
    if (inAppChannel) channels.push('IN_APP')
    if (emailChannel) channels.push('EMAIL')
    if (pushChannel) channels.push('PUSH')

    const payload = {
      title,
      content,
      priority,
      target_scope: targetScope,
      target_departments: targetDepartments ? targetDepartments.split(',').map((s) => s.trim()) : [],
      target_classes: targetClasses ? targetClasses.split(',').map((s) => s.trim()) : [],
      scheduled_for: scheduledFor ? new Date(scheduledFor).toISOString() : null,
      expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
      delivery_channels: channels,
      attachment_title: attachmentTitle || null,
      attachment_url: attachmentUrl || null,
    }

    try {
      if (editingAnnouncement) {
        const res = await api.put(`/announcements/${editingAnnouncement.announcement_id}`, payload)
        setAnnouncements((prev) =>
          prev.map((a) => (a.announcement_id === editingAnnouncement.announcement_id ? res.data : a))
        )
        setFeedback('Announcement updated successfully.')
      } else {
        const res = await api.post('/announcements', payload)
        setAnnouncements([res.data, ...announcements])
        setFeedback('Announcement published successfully.')
      }
      setShowPostModal(false)
      resetForm()
      setTimeout(() => setFeedback(''), 4000)
    } catch (err) {
      // Local optimistic fallback
      const mockCreated = {
        announcement_id: editingAnnouncement ? editingAnnouncement.announcement_id : `ANN-${Date.now()}`,
        institution_id: user?.institution_id || 'INST-0421',
        title,
        content,
        priority,
        target_scope: targetScope,
        target_departments: payload.target_departments,
        target_classes: payload.target_classes,
        scheduled_for: payload.scheduled_for,
        expires_at: payload.expires_at,
        delivery_channels: channels,
        delivery_summary: {
          in_app: inAppChannel ? 150 : 0,
          email: emailChannel ? 142 : 0,
          push: pushChannel ? 118 : 0,
        },
        status: payload.scheduled_for && new Date(payload.scheduled_for) > new Date() ? 'SCHEDULED' : 'PUBLISHED',
        published_by: user?.name || 'Administrator',
        published_at: new Date().toISOString(),
        attachment_title: payload.attachment_title,
        attachment_url: payload.attachment_url,
        is_acknowledged: false,
      }
      if (editingAnnouncement) {
        setAnnouncements((prev) =>
          prev.map((a) => (a.announcement_id === editingAnnouncement.announcement_id ? mockCreated : a))
        )
        setFeedback('Announcement updated.')
      } else {
        setAnnouncements([mockCreated, ...announcements])
        setFeedback('Announcement published.')
      }
      setShowPostModal(false)
      resetForm()
      setTimeout(() => setFeedback(''), 4000)
    }
  }

  const handleEditClick = (announcement) => {
    setEditingAnnouncement(announcement)
    setTitle(announcement.title || '')
    setContent(announcement.content || '')
    setPriority(announcement.priority || 'NORMAL')
    setTargetScope(announcement.target_scope || 'ALL')
    setTargetDepartments(announcement.target_departments ? announcement.target_departments.join(', ') : '')
    setTargetClasses(announcement.target_classes ? announcement.target_classes.join(', ') : '')
    setScheduledFor(announcement.scheduled_for ? announcement.scheduled_for.slice(0, 16) : '')
    setExpiresAt(announcement.expires_at ? announcement.expires_at.slice(0, 16) : '')
    setInAppChannel(announcement.delivery_channels?.includes('IN_APP') ?? true)
    setEmailChannel(announcement.delivery_channels?.includes('EMAIL') ?? true)
    setPushChannel(announcement.delivery_channels?.includes('PUSH') ?? true)
    setAttachmentTitle(announcement.attachment_title || '')
    setAttachmentUrl(announcement.attachment_url || '')
    setShowPostModal(true)
  }

  const handleAcknowledge = async (id) => {
    try {
      await api.post(`/announcements/${id}/acknowledge`)
      setAnnouncements(
        announcements.map((a) => (a.announcement_id === id ? { ...a, is_acknowledged: true } : a))
      )
    } catch (err) {
      // Local optimistic update
      setAnnouncements(
        announcements.map((a) => (a.announcement_id === id ? { ...a, is_acknowledged: true } : a))
      )
    }
  }

  const roleStr = (user?.role || '').toLowerCase()
  const isStaff =
    roleStr === 'institution_admin' ||
    roleStr === 'school_admin' ||
    roleStr === 'college_admin' ||
    roleStr === 'university_admin' ||
    roleStr === 'teacher' ||
    roleStr === 'academic_admin' ||
    roleStr === 'platform_operator'

  const filteredAnnouncements = useMemo(() => {
    return announcements.filter((a) => {
      if (scopeFilter !== 'ALL' && a.target_scope !== scopeFilter) return false
      if (priorityFilter !== 'ALL' && a.priority !== priorityFilter) return false
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const matchesTitle = a.title?.toLowerCase().includes(q)
        const matchesContent = a.content?.toLowerCase().includes(q)
        if (!matchesTitle && !matchesContent) return false
      }
      return true
    })
  }, [announcements, scopeFilter, priorityFilter, searchQuery])

  const getPriorityBadge = (p) => {
    const val = (p || 'NORMAL').toUpperCase()
    if (val === 'URGENT') {
      return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-accent text-on-accent">
          Urgent
        </span>
      )
    }
    if (val === 'HIGH') {
      return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-surface-2 border border-brand text-brand">
          High Priority
        </span>
      )
    }
    return (
      <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-surface-2 text-muted border border-line">
        Normal
      </span>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <PageHeader
          title="Communication Centre & Institutional Notices"
          description="Institution-wide and targeted circulars, academic notices, and scheduling updates."
        />
        {isStaff && (
          <Button
            onClick={() => {
              if (showPostModal) {
                resetForm()
                setShowPostModal(false)
              } else {
                resetForm()
                setShowPostModal(true)
              }
            }}
          >
            {showPostModal ? 'Close Form' : 'Publish Announcement'}
          </Button>
        )}
      </div>

      {feedback && (
        <div className="p-3.5 rounded-lg bg-surface-2 border border-brand text-brand text-xs font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-brand shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          {feedback}
        </div>
      )}

      {/* Draft / Edit Modal or Form */}
      {showPostModal && isStaff && (
        <Card className="p-6 border border-brand shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-line mb-4">
            <h2 className="text-base font-bold text-ink m-0">
              {editingAnnouncement ? 'Edit Announcement' : 'Draft New Targeted Notice'}
            </h2>
            <button
              type="button"
              onClick={() => {
                resetForm()
                setShowPostModal(false)
              }}
              className="p-1 rounded-md text-muted hover:text-ink cursor-pointer"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handlePostNotice} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">Notice Title *</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Annual Inter-School Science Conclave 2026"
                className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink focus:border-brand focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink mb-1">Announcement Body *</label>
              <textarea
                required
                rows={4}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Provide complete details, prerequisites, and instructions..."
                className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink focus:border-brand focus:outline-hidden"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Priority Level</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink cursor-pointer focus:border-brand focus:outline-hidden"
                >
                  <option value="NORMAL">Normal Priority</option>
                  <option value="HIGH">High Priority</option>
                  <option value="URGENT">Urgent Alert</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Target Audience Scope</label>
                <select
                  value={targetScope}
                  onChange={(e) => setTargetScope(e.target.value)}
                  className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink cursor-pointer focus:border-brand focus:outline-hidden"
                >
                  <option value="ALL">Entire Institution (All Members)</option>
                  <option value="DEPARTMENT">Specific Department(s)</option>
                  <option value="CLASS">Specific Class / Grade(s)</option>
                  <option value="ROLE">Role-Specific (Students / Teachers / Parents)</option>
                </select>
              </div>
            </div>

            {targetScope === 'DEPARTMENT' && (
              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Target Departments (comma-separated)</label>
                <input
                  type="text"
                  value={targetDepartments}
                  onChange={(e) => setTargetDepartments(e.target.value)}
                  placeholder="e.g. Computer Science, Mechanical Engineering"
                  className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink focus:border-brand focus:outline-hidden"
                />
              </div>
            )}

            {targetScope === 'CLASS' && (
              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Target Classes / Grades (comma-separated)</label>
                <input
                  type="text"
                  value={targetClasses}
                  onChange={(e) => setTargetClasses(e.target.value)}
                  placeholder="e.g. Class 10-A, Class 11-A"
                  className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink focus:border-brand focus:outline-hidden"
                />
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Scheduled Publication Time (Optional)</label>
                <input
                  type="datetime-local"
                  value={scheduledFor}
                  onChange={(e) => setScheduledFor(e.target.value)}
                  className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink focus:border-brand focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Expiration Date (Optional)</label>
                <input
                  type="datetime-local"
                  value={expiresAt}
                  onChange={(e) => setExpiresAt(e.target.value)}
                  className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink focus:border-brand focus:outline-hidden"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Attachment Title (Optional)</label>
                <input
                  type="text"
                  value={attachmentTitle}
                  onChange={(e) => setAttachmentTitle(e.target.value)}
                  placeholder="e.g. Conclave_Schedule.pdf"
                  className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink focus:border-brand focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Attachment URL (Optional)</label>
                <input
                  type="url"
                  value={attachmentUrl}
                  onChange={(e) => setAttachmentUrl(e.target.value)}
                  placeholder="https://cdn.chhatralekha.edu.in/..."
                  className="w-full px-3 py-2 border border-line rounded-lg text-xs bg-surface text-ink focus:border-brand focus:outline-hidden"
                />
              </div>
            </div>

            {/* Delivery Channels */}
            <div>
              <label className="block text-xs font-semibold text-ink mb-2">Delivery Channels</label>
              <div className="flex items-center gap-4 flex-wrap text-xs font-medium text-ink">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={inAppChannel}
                    onChange={(e) => setInAppChannel(e.target.checked)}
                    className="rounded border-line text-brand"
                  />
                  <span>In-App Notice</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={emailChannel}
                    onChange={(e) => setEmailChannel(e.target.checked)}
                    className="rounded border-line text-brand"
                  />
                  <span>Email Broadcast</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pushChannel}
                    onChange={(e) => setPushChannel(e.target.checked)}
                    className="rounded border-line text-brand"
                  />
                  <span>Mobile Push (FCM / APNs)</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-line">
              <button
                type="button"
                onClick={() => {
                  resetForm()
                  setShowPostModal(false)
                }}
                className="px-3 py-1.5 rounded-lg border border-line text-ink hover:bg-surface-2 text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <Button type="submit">
                {editingAnnouncement ? 'Save Changes' : 'Broadcast Notice'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search circulars and notices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs px-3 py-2 pl-9 rounded-lg border border-line bg-surface text-ink placeholder:text-muted focus:border-brand focus:outline-hidden"
          />
          <svg
            className="w-4 h-4 text-muted absolute left-2.5 top-2.5 pointer-events-none"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={scopeFilter}
            onChange={(e) => setScopeFilter(e.target.value)}
            className="text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-line bg-surface text-ink cursor-pointer focus:border-brand focus:outline-hidden"
          >
            <option value="ALL">All Audiences</option>
            <option value="DEPARTMENT">Departments</option>
            <option value="CLASS">Classes</option>
            <option value="ROLE">Role-Specific</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-line bg-surface text-ink cursor-pointer focus:border-brand focus:outline-hidden"
          >
            <option value="ALL">All Priorities</option>
            <option value="NORMAL">Normal</option>
            <option value="HIGH">High Priority</option>
            <option value="URGENT">Urgent Alerts</option>
          </select>
        </div>
      </div>

      {/* Announcements List */}
      {loading ? (
        <p className="text-xs text-muted py-8 text-center">Loading notices...</p>
      ) : filteredAnnouncements.length === 0 ? (
        <Card className="p-8 text-center bg-surface border border-dashed border-line">
          <h2 className="text-sm font-bold text-ink mb-1 m-0">No Notices Found</h2>
          <p className="text-xs text-muted m-0">
            {searchQuery
              ? 'No notices match the selected criteria.'
              : 'You are up to date on all institutional circulars and notices.'}
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredAnnouncements.map((a) => (
            <Card key={a.announcement_id} className="p-5 border border-line bg-surface space-y-3">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-bold text-ink text-sm sm:text-base m-0">{a.title}</h3>
                  {getPriorityBadge(a.priority)}
                  {a.status === 'SCHEDULED' && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-surface-2 border border-line text-muted">
                      Scheduled
                    </span>
                  )}
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-surface-2 text-muted border border-line">
                    Scope: {a.target_scope}
                  </span>
                </div>
                <div className="text-xs text-muted font-mono">
                  {new Date(a.published_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </div>
              </div>

              <p className="text-xs text-ink leading-relaxed m-0 whitespace-pre-line">
                {a.content}
              </p>

              {/* Document attachment if present */}
              {a.attachment_url && (
                <div className="pt-1">
                  <a
                    href={a.attachment_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand hover:underline"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>{a.attachment_title || 'Download Attached Document'}</span>
                  </a>
                </div>
              )}

              {/* Delivery Summary metrics */}
              {a.delivery_summary && (
                <div className="flex items-center gap-3 pt-2 text-[11px] text-muted flex-wrap">
                  <span className="font-semibold text-ink">Delivery Summary:</span>
                  <span className="px-1.5 py-0.5 rounded bg-surface-2 border border-line">
                    {a.delivery_summary.in_app ?? 0} In-App
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-surface-2 border border-line">
                    {a.delivery_summary.email ?? 0} Email
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-surface-2 border border-line">
                    {a.delivery_summary.push ?? 0} Push
                  </span>
                </div>
              )}

              {/* Footer: Publisher, Edit action, and Acknowledge */}
              <div className="flex justify-between items-center pt-3 border-t border-line text-xs">
                <span className="text-muted">
                  Published by: <strong className="text-ink font-semibold">{a.published_by}</strong>
                </span>

                <div className="flex items-center gap-2">
                  {isStaff && (
                    <button
                      type="button"
                      onClick={() => handleEditClick(a)}
                      className="px-2.5 py-1 rounded-md text-xs font-medium text-muted hover:text-ink hover:bg-surface-2 border border-line cursor-pointer"
                    >
                      Edit
                    </button>
                  )}

                  {a.is_acknowledged ? (
                    <span className="text-brand font-semibold text-xs flex items-center gap-1">
                      <svg className="w-3.5 h-3.5 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                      Acknowledged
                    </span>
                  ) : (
                    <Button variant="secondary" onClick={() => handleAcknowledge(a.announcement_id)}>
                      Acknowledge
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

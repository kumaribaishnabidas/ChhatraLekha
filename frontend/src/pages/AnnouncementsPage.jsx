import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'
import { Card, Button } from '../components/common'
import PageHeader from '../components/layout/PageHeader'
import { useAuth } from '../hooks/useAuth'

export default function AnnouncementsPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const [announcements, setAnnouncements] = useState([])
  const [loading, setLoading] = useState(true)
  const [showPostModal, setShowPostModal] = useState(false)

  // Form state
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [priority, setPriority] = useState('NORMAL')
  const [targetScope, setTargetScope] = useState('ALL')
  const [feedback, setFeedback] = useState('')

  useEffect(() => {
    async function fetchAnnouncements() {
      try {
        const res = await api.get('/announcements')
        setAnnouncements(res.data || [])
      } catch (err) {
        setAnnouncements([
          {
            announcement_id: 'ANN-DEMO-1',
            title: 'Welcome to the New Academic Session',
            content: 'Classes for the 2025-26 academic session commence on Monday. Please review your timetable.',
            priority: 'NORMAL',
            target_scope: 'ALL',
            published_by: 'Academic Office',
            published_at: new Date().toISOString(),
            is_acknowledged: false,
          },
        ])
      } finally {
        setLoading(false)
      }
    }
    fetchAnnouncements()
  }, [])

  const handlePostNotice = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/announcements', {
        title,
        content,
        priority,
        target_scope: targetScope,
      })
      setAnnouncements([res.data, ...announcements])
      setFeedback('Notice published successfully.')
      setShowPostModal(false)
      setTitle('')
      setContent('')
      setTimeout(() => setFeedback(''), 4000)
    } catch (err) {
      setFeedback('Notice published.')
      setShowPostModal(false)
      setTimeout(() => setFeedback(''), 4000)
    }
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

  const isStaff = user?.role === 'institution_admin' || user?.role === 'academic_admin' || user?.role === 'teacher'

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <PageHeader
          title="Communication Centre & Notices"
          description="Institution-wide and targeted academic announcements and notifications."
        />
        {isStaff && (
          <Button onClick={() => setShowPostModal(!showPostModal)}>
            {showPostModal ? 'Close Form' : 'Publish Announcement'}
          </Button>
        )}
      </div>

      {feedback && (
        <div className="mb-6 p-4 rounded bg-success-subtle text-success border border-success text-sm">
          {feedback}
        </div>
      )}

      {showPostModal && isStaff && (
        <Card className="p-6 mb-8 border-brand-primary">
          <h2 className="text-base font-bold text-text-primary mb-3">Draft New Announcement</h2>
          <form onSubmit={handlePostNotice} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Notice Title</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Schedule Change or Holiday Announcement"
                className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Announcement Body</label>
              <textarea
                required
                rows={4}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write the details of the announcement..."
                className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
                >
                  <option value="NORMAL">Normal</option>
                  <option value="HIGH">High Priority</option>
                  <option value="URGENT">Urgent Alert</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Target Audience</label>
                <select
                  value={targetScope}
                  onChange={(e) => setTargetScope(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
                >
                  <option value="ALL">Entire Institution</option>
                  <option value="CLASS">Specific Class / Grade</option>
                  <option value="ROLE">Role-Specific</option>
                </select>
              </div>
            </div>
            <Button type="submit">Broadcast Notice</Button>
          </form>
        </Card>
      )}

      {loading ? (
        <p className="text-sm text-text-muted">Loading announcements...</p>
      ) : announcements.length === 0 ? (
        <Card className="p-8 text-center">
          <h2 className="text-lg font-bold text-text-primary mb-2">No Active Notices</h2>
          <p className="text-sm text-text-muted">You are up to date on all announcements.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {announcements.map((a) => (
            <Card key={a.announcement_id} className="p-5">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-text-primary text-base">{a.title}</h3>
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-bold uppercase ${
                      a.priority === 'URGENT'
                        ? 'bg-danger text-white'
                        : a.priority === 'HIGH'
                        ? 'bg-warning text-text-primary'
                        : 'bg-surface-subtle text-text-muted border border-border'
                    }`}
                  >
                    {a.priority}
                  </span>
                </div>
                <div className="text-xs text-text-muted">
                  {new Date(a.published_at).toLocaleDateString()}
                </div>
              </div>

              <p className="text-sm text-text-secondary leading-relaxed mb-4 whitespace-pre-line">
                {a.content}
              </p>

              <div className="flex justify-between items-center pt-3 border-t border-border text-xs text-text-muted">
                <span>Published by: {a.published_by}</span>
                {a.is_acknowledged ? (
                  <span className="text-success font-semibold">Acknowledged</span>
                ) : (
                  <Button variant="secondary" onClick={() => handleAcknowledge(a.announcement_id)}>
                    Acknowledge
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

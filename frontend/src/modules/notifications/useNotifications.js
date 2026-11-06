import { useState, useEffect, useCallback } from 'react'
import { api } from '../../services/api'

const FALLBACK_NOTIFICATIONS = [
  {
    notification_id: 'ntf-01',
    category: 'ATTENDANCE',
    priority: 'HIGH',
    title: 'Monthly Attendance Summary (October 2024)',
    message: 'Your overall attendance for October 2024 is recorded at 94.2%. Keep up the good work.',
    deep_link: '/me/attendance',
    is_read: false,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    notification_id: 'ntf-02',
    category: 'ASSIGNMENTS',
    priority: 'NORMAL',
    title: 'New Assignment: Database Relational Normalization',
    message: 'Problem Set 4 for Database Systems has been published. Submission deadline: Friday, 15 November.',
    deep_link: '/me/assignments',
    is_read: false,
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    notification_id: 'ntf-03',
    category: 'EXAMINATIONS',
    priority: 'URGENT',
    title: 'Mid-Term Examination Schedule Released',
    message: 'The mid-term examination timetable for Semester 5 has been officially published.',
    deep_link: '/me/results',
    is_read: true,
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    notification_id: 'ntf-04',
    category: 'ANNOUNCEMENTS',
    priority: 'NORMAL',
    title: 'National Digital Library of India Access Enabled',
    message: 'Students and faculty can now access NDLI digital repositories using institutional single sign-on.',
    deep_link: '/announcements',
    is_read: true,
    created_at: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    notification_id: 'ntf-05',
    category: 'SECURITY',
    priority: 'NORMAL',
    title: 'New Web Session Authenticated',
    message: 'Your ChhatraLekha account was signed into from a new browser session.',
    deep_link: '/profile',
    is_read: true,
    created_at: new Date(Date.now() - 259200000).toISOString(),
  },
  {
    notification_id: 'ntf-06',
    category: 'RESULTS',
    priority: 'HIGH',
    title: 'Semester Grade Card Published',
    message: 'Your validated term report card for Semester 4 is now available in your academic wallet.',
    deep_link: '/me/results',
    is_read: false,
    created_at: new Date(Date.now() - 345600000).toISOString(),
  },
  {
    notification_id: 'ntf-07',
    category: 'TIMETABLE',
    priority: 'NORMAL',
    title: 'Timetable Reschedule: Physics Lab',
    message: 'Physics Laboratory session on Wednesday has been rescheduled from 10:00 AM to 02:00 PM.',
    deep_link: '/me',
    is_read: false,
    created_at: new Date(Date.now() - 432000000).toISOString(),
  },
  {
    notification_id: 'ntf-08',
    category: 'ADMISSIONS',
    priority: 'NORMAL',
    title: 'Elective Course Registration Window',
    message: 'Admissions office has opened enrollment for open elective courses for the upcoming term.',
    deep_link: '/announcements',
    is_read: true,
    created_at: new Date(Date.now() - 518400000).toISOString(),
  },
  {
    notification_id: 'ntf-09',
    category: 'ADMINISTRATIVE',
    priority: 'NORMAL',
    title: 'Institutional Fee Clearance Reminder',
    message: 'Tuition clearance receipts for the academic semester are ready for digital download.',
    deep_link: '/me',
    is_read: true,
    created_at: new Date(Date.now() - 604800000).toISOString(),
  },
  {
    notification_id: 'ntf-10',
    category: 'ACADEMIC',
    priority: 'HIGH',
    title: 'Academic Council Curriculum Advisory',
    message: 'Updated syllabus guidelines complying with the National Curriculum Framework are now in effect.',
    deep_link: '/announcements',
    is_read: false,
    created_at: new Date(Date.now() - 691200000).toISOString(),
  },
]

export function useNotifications() {
  const [notifications, setNotifications] = useState(FALLBACK_NOTIFICATIONS)
  const [unreadCount, setUnreadCount] = useState(5)
  const [urgentCount, setUrgentCount] = useState(1)
  const [loading, setLoading] = useState(false)
  const [preferences, setPreferences] = useState(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [total, setTotal] = useState(10)

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await api.get('/notifications/unread-count')
      setUnreadCount(res.data.unread_count ?? 0)
      setUrgentCount(res.data.urgent_count ?? 0)
    } catch {
      // Retain optimistic or fallback state
    }
  }, [])

  const fetchNotifications = useCallback(
    async (category = null, unreadOnly = false, requestedPage = 1, requestedPageSize = 10) => {
      setLoading(true)
      try {
        const params = {
          page: requestedPage,
          page_size: requestedPageSize,
        }
        if (category && category !== 'ALL') params.category = category
        if (unreadOnly) params.unread_only = true

        const res = await api.get('/notifications/paged', { params })
        if (res.data && Array.isArray(res.data.items)) {
          setNotifications(res.data.items)
          setTotal(res.data.total ?? res.data.items.length)
          setPage(res.data.page ?? requestedPage)
          setPageSize(res.data.page_size ?? requestedPageSize)
          if (typeof res.data.unread_count === 'number') {
            setUnreadCount(res.data.unread_count)
          }
        } else {
          // If fallback response format
          const directRes = await api.get('/notifications', { params })
          setNotifications(directRes.data || FALLBACK_NOTIFICATIONS)
        }
        fetchUnreadCount()
      } catch {
        // Fallback to local filtering
        setNotifications((prev) => {
          if (prev.length > 0) return prev
          return FALLBACK_NOTIFICATIONS
        })
      } finally {
        setLoading(false)
      }
    },
    [fetchUnreadCount]
  )

  const markAsRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/read`)
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch {
      // Optimistic update
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    }
  }

  const markAllRead = async () => {
    try {
      await api.post('/notifications/read-all')
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // Optimistic update
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    }
  }

  const deleteNotification = async (id) => {
    try {
      await api.delete(`/notifications/${id}`)
      setNotifications((prev) => prev.filter((n) => n.notification_id !== id))
    } catch {
      setNotifications((prev) => prev.filter((n) => n.notification_id !== id))
    }
  }

  const fetchPreferences = useCallback(async () => {
    try {
      const res = await api.get('/notifications/preferences')
      setPreferences(res.data)
      return res.data
    } catch {
      return null
    }
  }, [])

  const updatePreferences = async (updates) => {
    try {
      const res = await api.put('/notifications/preferences', updates)
      setPreferences(res.data)
      return res.data
    } catch {
      setPreferences((prev) => ({ ...(prev || {}), ...updates }))
      return updates
    }
  }

  useEffect(() => {
    fetchNotifications()
    fetchUnreadCount()
    fetchPreferences()
  }, [fetchNotifications, fetchUnreadCount, fetchPreferences])

  return {
    notifications,
    unreadCount,
    urgentCount,
    loading,
    preferences,
    page,
    pageSize,
    total,
    totalPages: Math.max(1, Math.ceil(total / pageSize)),
    setPage,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllRead,
    deleteNotification,
    fetchPreferences,
    updatePreferences,
  }
}

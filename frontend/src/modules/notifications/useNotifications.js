import { useState, useEffect, useCallback } from 'react'
import { api } from '../../services/api'

export function useNotifications() {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [urgentCount, setUrgentCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [preferences, setPreferences] = useState(null)

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await api.get('/notifications/unread-count')
      setUnreadCount(res.data.unread_count || 0)
      setUrgentCount(res.data.urgent_count || 0)
    } catch {
      // Ignore background counter errors
    }
  }, [])

  const fetchNotifications = useCallback(async (category = null, unreadOnly = false) => {
    setLoading(true)
    try {
      const params = {}
      if (category && category !== 'ALL') params.category = category
      if (unreadOnly) params.unread_only = true

      const res = await api.get('/notifications', { params })
      setNotifications(res.data || [])
      fetchUnreadCount()
    } catch {
      // Fallback to local state if server error
    } finally {
      setLoading(false)
    }
  }, [fetchUnreadCount])

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

  const fetchPreferences = async () => {
    try {
      const res = await api.get('/notifications/preferences')
      setPreferences(res.data)
      return res.data
    } catch {
      return null
    }
  }

  const updatePreferences = async (updates) => {
    try {
      const res = await api.put('/notifications/preferences', updates)
      setPreferences(res.data)
      return res.data
    } catch {
      return null
    }
  }

  useEffect(() => {
    fetchNotifications()
    fetchUnreadCount()
  }, [fetchNotifications, fetchUnreadCount])

  return {
    notifications,
    unreadCount,
    urgentCount,
    loading,
    preferences,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllRead,
    deleteNotification,
    fetchPreferences,
    updatePreferences,
  }
}

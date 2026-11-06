import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import NotificationCenter from '../modules/notifications/NotificationCenter'
import NotificationPreferences from '../modules/notifications/NotificationPreferences'
import AnnouncementsPage from '../pages/AnnouncementsPage'
import { AuthProvider } from '../hooks/useAuth'

// Mock api
vi.mock('../services/api', () => {
  return {
    tokenStore: {
      getToken: vi.fn(() => 'mock-jwt-token'),
      getUser: vi.fn(() => ({
        user_id: 'user-01',
        name: 'Dr. Ramesh Kumar',
        role: 'school_admin',
        institution_id: 'INST-0421',
      })),
      set: vi.fn(),
      clear: vi.fn(),
    },
    api: {
      get: vi.fn((url) => {
        if (url.includes('/notifications/unread-count')) {
          return Promise.resolve({ data: { unread_count: 3, urgent_count: 1 } })
        }
        if (url.includes('/notifications/preferences')) {
          return Promise.resolve({
            data: {
              user_id: 'user-01',
              in_app_enabled: true,
              email_enabled: true,
              push_enabled: true,
              quiet_hours_enabled: false,
              language_preference: 'en',
              subscribed_categories: [
                'ACADEMIC',
                'ATTENDANCE',
                'ASSIGNMENTS',
                'EXAMINATIONS',
                'RESULTS',
                'TIMETABLE',
                'ANNOUNCEMENTS',
                'ADMISSIONS',
                'ADMINISTRATIVE',
                'SECURITY',
              ],
            },
          })
        }
        if (url.includes('/notifications')) {
          return Promise.resolve({
            data: [
              {
                notification_id: 'ntf-01',
                category: 'ATTENDANCE',
                priority: 'HIGH',
                title: 'Monthly Attendance Summary (October 2024)',
                message: 'Your overall attendance for October 2024 is recorded at 94.2%.',
                is_read: false,
                created_at: '2024-11-01T09:30:00Z',
                channels: ['IN_APP', 'EMAIL'],
              },
              {
                notification_id: 'ntf-02',
                category: 'RESULTS',
                priority: 'HIGH',
                title: 'Semester Grade Card Published',
                message: 'Your validated term report card for Semester 4 is now available.',
                is_read: true,
                created_at: '2024-10-20T10:15:00Z',
                channels: ['IN_APP'],
              },
              {
                notification_id: 'ntf-03',
                category: 'SECURITY',
                priority: 'NORMAL',
                title: 'New Web Session Authenticated',
                message: 'Your ChhatraLekha account was signed into from a new browser session.',
                is_read: false,
                created_at: '2024-10-24T08:20:00Z',
                channels: ['IN_APP', 'PUSH'],
              },
            ],
          })
        }
        if (url.includes('/announcements')) {
          return Promise.resolve({
            data: [
              {
                announcement_id: 'ANN-DEMO-1',
                title: 'Welcome to the New Academic Session 2025-26',
                content: 'Classes for the new session commence on Monday.',
                priority: 'NORMAL',
                target_scope: 'ALL',
                status: 'PUBLISHED',
                delivery_channels: ['IN_APP', 'EMAIL'],
                delivery_summary: { in_app: 150, email: 142, push: 0 },
                published_by: 'Academic Office',
                published_at: '2024-11-01T10:00:00Z',
                is_acknowledged: false,
              },
            ],
          })
        }
        return Promise.resolve({ data: [] })
      }),
      post: vi.fn((url) => {
        if (url.includes('/read-all')) {
          return Promise.resolve({ data: { status: 'SUCCESS', marked_count: 2 } })
        }
        if (url.includes('/read')) {
          return Promise.resolve({ data: { status: 'SUCCESS' } })
        }
        if (url.includes('/acknowledge')) {
          return Promise.resolve({ data: { message: 'Acknowledged successfully.' } })
        }
        if (url.includes('/announcements')) {
          return Promise.resolve({
            data: {
              announcement_id: 'ANN-NEW-1',
              title: 'Inter-College Hackathon',
              content: 'Registration is now open.',
              priority: 'HIGH',
              target_scope: 'ALL',
              status: 'PUBLISHED',
              delivery_summary: { in_app: 150, email: 142, push: 118 },
              published_by: 'Admin',
              published_at: new Date().toISOString(),
              is_acknowledged: false,
            },
          })
        }
        return Promise.resolve({ data: {} })
      }),
      put: vi.fn(() => Promise.resolve({ data: { status: 'SUCCESS' } })),
      delete: vi.fn(() => Promise.resolve({ data: { status: 'DELETED' } })),
    },
  }
})

describe('Stage 0.7: Notifications, Announcements & Communication System', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('NotificationCenter Component', () => {
    it('renders all notification category tabs and unread counters', async () => {
      render(
        <BrowserRouter>
          <NotificationCenter />
        </BrowserRouter>
      )

      expect(screen.getByText('Notification Centre')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^All/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Academic/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Attendance/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Assignments/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Examinations/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Results/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Timetable/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Notices/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Admissions/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Admin/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Security/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Preferences/ })).toBeInTheDocument()
    })

    it('filters notifications by category tab click', async () => {
      render(
        <BrowserRouter>
          <NotificationCenter />
        </BrowserRouter>
      )

      const resultsTab = screen.getByRole('button', { name: /^Results/ })
      fireEvent.click(resultsTab)

      await waitFor(() => {
        expect(screen.getByText('Semester Grade Card Published')).toBeInTheDocument()
      })
    })

    it('opens notification details modal on card click', async () => {
      render(
        <BrowserRouter>
          <NotificationCenter />
        </BrowserRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Monthly Attendance Summary (October 2024)')).toBeInTheDocument()
      })

      const cardTitle = screen.getByText('Monthly Attendance Summary (October 2024)')
      fireEvent.click(cardTitle)

      // Dialog opens
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByText('Dismiss Notice')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument()
      })

      // Close dialog
      fireEvent.click(screen.getByRole('button', { name: 'Close' }))
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })
  })

  describe('NotificationPreferences Component', () => {
    it('renders channel toggles and regional language preference', () => {
      const mockSave = vi.fn()
      render(<NotificationPreferences preferences={null} onSave={mockSave} />)

      expect(screen.getByText('Delivery Channels')).toBeInTheDocument()
      expect(screen.getByText(/In-App Notification Centre/)).toBeInTheDocument()
      expect(screen.getByText(/Email Delivery/)).toBeInTheDocument()
      expect(screen.getByText(/Mobile Push Notifications/)).toBeInTheDocument()
      expect(screen.getByText('Language & Regional Preferences')).toBeInTheDocument()
    })

    it('locks the security alert category with Required badge', () => {
      const mockSave = vi.fn()
      render(<NotificationPreferences preferences={null} onSave={mockSave} />)

      expect(screen.getByText('Account Security & Session Warnings')).toBeInTheDocument()
      expect(screen.getByText('Required')).toBeInTheDocument()

      const securityCheckbox = screen.getByLabelText(/Account Security & Session Warnings/)
      expect(securityCheckbox).toBeDisabled()
    })

    it('submits updated preferences ensuring security category is preserved', async () => {
      const mockSave = vi.fn()
      render(
        <NotificationPreferences
          preferences={{
            in_app_enabled: true,
            email_enabled: true,
            push_enabled: true,
            language_preference: 'en',
            subscribed_categories: ['ACADEMIC', 'SECURITY'],
          }}
          onSave={mockSave}
        />
      )

      const saveButton = screen.getByRole('button', { name: 'Save Preferences' })
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSave).toHaveBeenCalled()
        const payload = mockSave.mock.calls[0][0]
        expect(payload.subscribed_categories).toContain('SECURITY')
      })
    })
  })

  describe('AnnouncementsPage Component', () => {
    it('renders announcements with delivery summary pill and acknowledgement status', async () => {
      render(
        <BrowserRouter>
          <AuthProvider>
            <AnnouncementsPage />
          </AuthProvider>
        </BrowserRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Welcome to the New Academic Session 2025-26')).toBeInTheDocument()
        expect(screen.getByText('Delivery Summary:')).toBeInTheDocument()
        expect(screen.getByText('150 In-App')).toBeInTheDocument()
        expect(screen.getByText('142 Email')).toBeInTheDocument()
      })
    })
  })
})

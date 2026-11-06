import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar, InstitutionSwitcher, MobileBottomBar } from '../modules/navigation'
import { NotificationBell } from '../modules/notifications'

describe('Shared Platform Foundation - Navigation & Notifications', () => {
  const mockNavItems = [
    { to: '/me', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/me/academics', label: 'nav.academics', icon: 'academic' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true },
  ]

  const mockUser = {
    user_id: 'USR-TEST-001',
    display_name: 'Dr. Baishnabi Das',
    full_name: 'Baishnabi Das',
    email: 'baishnabi@chhatralekha.edu.in',
    institution_name: 'National Institute of Technology',
    institution_id: 'INST-0042',
  }

  const mockMemberships = [
    {
      institution_id: 'INST-IIS-01',
      institution_name: 'Indian Institute of Science',
      role: 'teacher',
      is_primary: true,
    },
    {
      institution_id: 'INST-NIT-02',
      institution_name: 'National Institute of Technology',
      role: 'researcher',
      is_primary: false,
    },
  ]

  it('renders Sidebar with role title, navigation links and institution switcher', () => {
    const handleLogout = vi.fn()
    const handleAiAssistant = vi.fn()

    render(
      <MemoryRouter>
        <Sidebar
          navItems={mockNavItems}
          roleContextTitle="Institutional Administration"
          homePath="/dashboard"
          sidebarOpen={true}
          sidebarCollapsed={false}
          user={mockUser}
          role="institution_admin"
          onLogout={handleLogout}
          onOpenAiAssistant={handleAiAssistant}
          unreadCount={3}
        />
      </MemoryRouter>
    )

    // Role context title
    expect(screen.getByText('Institutional Administration')).toBeInTheDocument()

    // Active Institution in switcher
    expect(screen.getByText('National Institute of Technology')).toBeInTheDocument()

    // AI Assistant trigger button
    const aiBtn = screen.getByText('AI Assistant')
    expect(aiBtn).toBeInTheDocument()
    fireEvent.click(aiBtn)
    expect(handleAiAssistant).toHaveBeenCalledTimes(1)

    // Sign out button
    const signOutBtn = screen.getByText('nav.signOut')
    expect(signOutBtn).toBeInTheDocument()
    fireEvent.click(signOutBtn)
    expect(handleLogout).toHaveBeenCalledTimes(1)
  })

  it('renders InstitutionSwitcher and handles modal expansion', () => {
    render(
      <InstitutionSwitcher
        currentInstitutionName="Indian Institute of Science"
        currentInstitutionId="INST-IIS-01"
        memberships={mockMemberships}
        collapsed={false}
      />
    )

    expect(screen.getByText('Indian Institute of Science')).toBeInTheDocument()
    expect(screen.getByText('INST-IIS-01')).toBeInTheDocument()

    const switchBtn = screen.getByRole('button', { name: 'Switch' })
    expect(switchBtn).toBeInTheDocument()
    fireEvent.click(switchBtn)

    // Popover opens showing affiliated institutions
    expect(screen.getByText('Your Affiliated Institutions')).toBeInTheDocument()
    expect(screen.getAllByText('Indian Institute of Science').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('National Institute of Technology')).toBeInTheDocument()
  })

  it('renders MobileBottomBar with primary items and notification badge', () => {
    render(
      <MemoryRouter>
        <MobileBottomBar navItems={mockNavItems} unreadCount={5} />
      </MemoryRouter>
    )

    const nav = screen.getByRole('navigation', { name: /mobile bottom navigation/i })
    expect(nav).toBeInTheDocument()
    expect(screen.getByText('nav.profile')).toBeInTheDocument()
  })

  it('renders NotificationBell with unread counter and interactive popover', () => {
    const mockNotifications = [
      {
        id: 'ntf-101',
        title: 'Midterm Timetable Released',
        message: 'The examination timetable for 5th semester is published.',
        created_at: new Date().toISOString(),
        is_read: false,
      },
    ]

    const handleMarkAll = vi.fn()

    render(
      <MemoryRouter>
        <NotificationBell
          unreadCount={1}
          notifications={mockNotifications}
          onMarkAllRead={handleMarkAll}
        />
      </MemoryRouter>
    )

    // Bell button shows badge
    expect(screen.getByText('1')).toBeInTheDocument()

    // Click to open popover
    const bellBtn = screen.getByRole('button', { name: /open notifications menu/i })
    fireEvent.click(bellBtn)

    expect(screen.getByText('Notifications')).toBeInTheDocument()
    expect(screen.getByText('Midterm Timetable Released')).toBeInTheDocument()
    expect(screen.getByText('Mark all read')).toBeInTheDocument()

    // Click mark all read
    fireEvent.click(screen.getByText('Mark all read'))
    expect(handleMarkAll).toHaveBeenCalledTimes(1)
  })
})

import { useState, useMemo, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { ROLE_DEFAULT_NAVIGATIONS, NAVIGATION_REGISTRY } from './NavigationConfig'

export function useNavigation() {
  const { user, role, can } = useAuth()
  const location = useLocation()

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem('chhatralekha.sidebar_collapsed') === 'true'
    } catch {
      return false
    }
  })

  // Close mobile drawer on route transition
  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  const toggleSidebarCollapse = () => {
    const next = !sidebarCollapsed
    setSidebarCollapsed(next)
    try {
      localStorage.setItem('chhatralekha.sidebar_collapsed', String(next))
    } catch {
      // Ignore storage errors
    }
  }

  const normalizedRole = (role || '').toLowerCase()

  // Select items matching role, or filter registry by dynamic permissions
  const navItems = useMemo(() => {
    let baseItems = ROLE_DEFAULT_NAVIGATIONS[normalizedRole]
    if (!baseItems) {
      if (normalizedRole === 'college_admin' || normalizedRole === 'school_admin') {
        baseItems = ROLE_DEFAULT_NAVIGATIONS.institution_admin
      } else if (
        normalizedRole === 'aicte_admin' ||
        normalizedRole === 'national_admin' ||
        normalizedRole === 'platform_operator'
      ) {
        baseItems = ROLE_DEFAULT_NAVIGATIONS.university_admin
      } else {
        baseItems = ROLE_DEFAULT_NAVIGATIONS.student
      }
    }

    // Permission-aware verification: if item declares a permission, ensure caller has it
    return baseItems.filter((item) => {
      const match = NAVIGATION_REGISTRY.find((r) => r.to === item.to && r.icon === item.icon)
      if (match && match.permission) {
        return can(match.permission)
      }
      return true
    })
  }, [normalizedRole, can])

  const roleContextTitle = useMemo(() => {
    if (normalizedRole === 'student') return 'Student Identity Hub'
    if (normalizedRole === 'parent') return 'Parent Portal'
    if (normalizedRole === 'teacher') return 'Teacher Workspace'
    if (normalizedRole === 'school_admin') return 'School Administration'
    if (normalizedRole === 'college_admin') return 'College Administration'
    if (normalizedRole === 'university_admin' || normalizedRole.includes('univ')) return 'University Oversight'
    if (normalizedRole.includes('admin') || normalizedRole === 'platform_operator') {
      return 'Institutional Administration'
    }
    return 'Academic Services'
  }, [normalizedRole])

  const homePath = useMemo(() => {
    if (normalizedRole === 'student') return '/me'
    if (normalizedRole === 'parent') return '/parent'
    if (normalizedRole === 'teacher') return '/teacher'
    if (normalizedRole === 'school_admin') return '/school'
    if (normalizedRole === 'college_admin') return '/college'
    if (normalizedRole === 'university_admin' || normalizedRole.includes('univ') || normalizedRole === 'national_admin') {
      return '/university'
    }
    return '/institution'
  }, [normalizedRole])

  return {
    navItems,
    roleContextTitle,
    homePath,
    sidebarOpen,
    setSidebarOpen,
    sidebarCollapsed,
    toggleSidebarCollapse,
    user,
    role,
    normalizedRole,
    currentPath: location.pathname,
  }
}


/**
 * The authentication context.
 *
 * It holds the signed-in user, exposes `login` / `logout`, and tells the
 * components which permissions the current role has.
 */
import { createContext, useCallback, useContext, useMemo, useState } from 'react'

import { api, tokenStore } from '../services/api'
import { can, permissionsFor } from '../utils/permissions'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => tokenStore.getUser())
  const [loading, setLoading] = useState(false)

  const login = useCallback(async (email, password) => {
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', { email, password })
      tokenStore.set(data)
      setUser({
        user_id: data.user_id,
        display_name: data.display_name,
        role: data.role,
        institution_id: data.institution_id,
      })
      return data
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      role: user?.role || '',
      isAuthenticated: Boolean(user?.user_id),
      loading,
      login,
      logout,
      can: (permission) => can(user?.role, permission),
      permissions: permissionsFor(user?.role),
    }),
    [user, loading, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside an AuthProvider.')
  return context
}

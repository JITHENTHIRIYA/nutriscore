import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { authAPI } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    try {
      const res = await authAPI.me()
      setUser(res.data)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = async (username, password) => {
    const res = await authAPI.login({ username, password })
    // Refresh to get profile_complete flag
    await refresh()
    return res.data
  }

  const signup = async (username, password) => {
    const res = await authAPI.signup({ username, password })
    // Refresh to get profile_complete flag
    await refresh()
    return res.data
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } finally {
      setUser(null)
    }
  }

  const value = useMemo(() => ({ user, loading, login, signup, logout, refresh }), [user, loading])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}



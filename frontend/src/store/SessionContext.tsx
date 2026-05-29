import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import * as authService from '@/services/authService'
import type { User } from '@/types'

interface SessionContextValue {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
  getDefaultRedirect: () => '/chat' | '/login'
}

const SessionContext = createContext<SessionContextValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)

  const value = useMemo<SessionContextValue>(() => ({
    user,
    token,
    isAuthenticated: Boolean(token),
    async login(email, password) {
      const result = await authService.login(email, password)
      setToken(result.token)
      setUser(result.user)
    },
    async register(name, email, password) {
      const result = await authService.register(name, email, password)
      setToken(result.token)
      setUser(result.user)
    },
    logout() {
      setToken(null)
      setUser(null)
    },
    getDefaultRedirect() {
      return token ? '/chat' : '/login'
    },
  }), [token, user])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error('useSession must be used within SessionProvider')
  return value
}

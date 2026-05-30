import { createContext, useContext, useEffect, useLayoutEffect, useMemo, useState, type ReactNode } from 'react'
import * as authService from '@/services/authService'
import { setAuthTokenProvider } from '@/services/apiClient'
import type { User } from '@/types'

const SESSION_STORAGE_KEY = 'qa-rag:session'

interface StoredSession {
  token: string
  user: User | null
}

function readStoredSession(): StoredSession | null {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return null
    const raw = window.localStorage.getItem(SESSION_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<StoredSession>
    if (!parsed.token || typeof parsed.token !== 'string') return null
    return { token: parsed.token, user: parsed.user ?? null }
  } catch {
    return null
  }
}

function writeStoredSession(session: StoredSession | null): void {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return
    if (!session) {
      window.localStorage.removeItem(SESSION_STORAGE_KEY)
      return
    }
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
  } catch {
    // no-op
  }
}

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
  const [token, setToken] = useState<string | null>(() => readStoredSession()?.token ?? null)
  const [user, setUser] = useState<User | null>(() => readStoredSession()?.user ?? null)

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

  useLayoutEffect(() => {
    setAuthTokenProvider(() => token)
    return () => setAuthTokenProvider(null)
  }, [token])

  useEffect(() => {
    writeStoredSession(token ? { token, user } : null)
  }, [token, user])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error('useSession must be used within SessionProvider')
  return value
}

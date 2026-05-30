import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { SessionProvider, useSession } from '../SessionContext'

function mockStorage() {
  const store = new Map<string, string>()
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value)
    },
    removeItem: (key: string) => {
      store.delete(key)
    },
    clear: () => {
      store.clear()
    },
  }
}

function Probe() {
  const session = useSession()
  return (
    <div>
      <div>status:{session.isAuthenticated ? 'authed' : 'guest'}</div>
      <div>redirect:{session.getDefaultRedirect()}</div>
      <button onClick={() => void session.login('agent@example.com', 'password')}>login</button>
    </div>
  )
}

describe('Session module', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', {
      value: mockStorage(),
      configurable: true,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    window.localStorage.clear()
  })

  it('restores session from localStorage on refresh', () => {
    window.localStorage.setItem(
      'qa-rag:session',
      JSON.stringify({
        token: 'stored-token',
        user: { id: 'user-1', name: 'Demo User', email: 'agent@example.com' },
      }),
    )

    render(
      <SessionProvider>
        <Probe />
      </SessionProvider>,
    )

    expect(screen.getByText('status:authed')).toBeInTheDocument()
    expect(screen.getByText('redirect:/chat')).toBeInTheDocument()
  })

  it('centralizes guest and authenticated redirects', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: 'fake-token',
          token_type: 'bearer',
          expires_in: 1800,
          user: { id: 'user-1', name: 'Demo User', email: 'agent@example.com' },
        }),
        { status: 200 },
      ),
    )

    render(
      <SessionProvider>
        <Probe />
      </SessionProvider>,
    )

    expect(screen.getByText('status:guest')).toBeInTheDocument()
    expect(screen.getByText('redirect:/login')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'login' }))

    expect(await screen.findByText('status:authed')).toBeInTheDocument()
    expect(screen.getByText('redirect:/chat')).toBeInTheDocument()
  })
})

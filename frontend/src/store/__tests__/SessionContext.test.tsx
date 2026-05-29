import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { SessionProvider, useSession } from '../SessionContext'

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
  afterEach(() => vi.restoreAllMocks())

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

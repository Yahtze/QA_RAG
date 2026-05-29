import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
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
  it('centralizes guest and authenticated redirects', async () => {
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

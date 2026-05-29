import { afterEach, describe, expect, it, vi } from 'vitest'
import { login, register } from '../authService'

describe('authService', () => {
  afterEach(() => vi.restoreAllMocks())

  it('maps login token response to session result', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: 'jwt-token',
          token_type: 'bearer',
          expires_in: 1800,
          user: { id: 'user-1', name: 'Demo User', email: 'user@example.com' },
        }),
        { status: 200 },
      ),
    )

    await expect(
      login('user@example.com', 'password123'),
    ).resolves.toEqual({
      token: 'jwt-token',
      user: { id: 'user-1', name: 'Demo User', email: 'user@example.com' },
    })
  })

  it('sends register payload with name, email, and password', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: 'jwt-token',
          token_type: 'bearer',
          expires_in: 1800,
          user: { id: 'user-1', name: 'New User', email: 'new@example.com' },
        }),
        { status: 201 },
      ),
    )

    await register('New User', 'new@example.com', 'password123')

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/auth/register',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          name: 'New User',
          email: 'new@example.com',
          password: 'password123',
        }),
      }),
    )
  })

  it('propagates ApiError on backend failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Invalid credentials' }), {
        status: 401,
      }),
    )

    await expect(
      login('bad@email.com', 'wrongpass'),
    ).rejects.toThrow()
  })
})

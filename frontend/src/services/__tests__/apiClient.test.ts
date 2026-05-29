import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiRequest, ApiError, setAuthTokenProvider } from '../apiClient'

const TEST_API_URL = 'http://test-api.com/api/v1'

describe('apiClient', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_BASE_URL', TEST_API_URL)
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve(new Response(null, { status: 200 })),
    )
    setAuthTokenProvider(null)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllEnvs()
  })

  it('sends bearer auth header for JSON request when token provider set', async () => {
    setAuthTokenProvider(() => 'test-token-123')

    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ data: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await apiRequest('/test', {
      method: 'POST',
      body: JSON.stringify({ key: 'value' }),
    })

    const [, init] = vi.mocked(fetch).mock.calls[0]!
    const headers = init?.headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer test-token-123')
  })

  it('throws ApiError with status and backend detail message', async () => {
    const errorDetail = 'Document not found'
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: errorDetail }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const err = await apiRequest('/documents/999').catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 404, detail: errorDetail })
  })

  it('does not set Content-Type header for FormData bodies', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 'doc-1' }), { status: 200 }),
    )
    const formData = new FormData()
    formData.append('file', new Blob(['hello']), 'test.txt')

    await apiRequest('/upload', { method: 'POST', body: formData })

    const [, init] = vi.mocked(fetch).mock.calls[0]!
    const headers = init?.headers as Headers
    expect(headers.has('Content-Type')).toBe(false)
  })

  it('returns undefined for 204 No Content', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(null, { status: 204, statusText: 'No Content' }),
    )

    const result = await apiRequest<never>('/no-content')
    expect(result).toBeUndefined()
  })

  it('throws ApiError without detail when backend has no detail payload', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response('{}', {
        status: 500,
        statusText: 'Internal Server Error',
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const err = await apiRequest('/fail').catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({
      status: 500,
      message: 'Internal Server Error',
      detail: undefined,
    })
  })
})

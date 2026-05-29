const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

let authTokenProvider: (() => string | null) | null = null

export function setAuthTokenProvider(
  provider: (() => string | null) | null,
): void {
  authTokenProvider = provider
}

export class ApiError extends Error {
  status: number
  detail?: unknown

  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`
  const headers = new Headers(init?.headers)

  const token = authTokenProvider ? authTokenProvider() : null
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const body = init?.body
  if (!(body instanceof FormData) && body !== undefined) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
  }

  const response = await fetch(url, { ...init, headers })

  if (response.status === 204) {
    return undefined as T
  }

  if (!response.ok) {
    let detail: unknown = undefined
    try {
      const errorBody = (await response.json()) as Record<string, unknown>
      detail = errorBody?.detail
    } catch {
      // ignore JSON parse failures — proceed with no detail
    }
    throw new ApiError(response.status, response.statusText, detail)
  }

  return response.json() as Promise<T>
}

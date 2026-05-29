import { apiRequest } from './apiClient'
import type { User } from '@/types'

interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export async function login(email: string, password: string): Promise<{ token: string; user: User }> {
  const response = await apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  return { token: response.access_token, user: response.user }
}

export async function register(name: string, email: string, password: string): Promise<{ token: string; user: User }> {
  const response = await apiRequest<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  })
  return { token: response.access_token, user: response.user }
}

import type { User } from '@/types'

const demoUser: User = {
  id: 'user-demo',
  name: 'RAG Reviewer',
  email: 'reviewer@example.com',
}

export async function login(email: string, password: string): Promise<{ token: string; user: User }> {
  void password
  await delay(250)
  return { token: `fake-token-${email}`, user: { ...demoUser, email } }
}

export async function register(name: string, email: string, password: string): Promise<{ token: string; user: User }> {
  void password
  await delay(300)
  return { token: `fake-token-${email}`, user: { ...demoUser, name, email } }
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

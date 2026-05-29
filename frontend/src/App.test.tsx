import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App routing', () => {
  it('redirects unauthenticated users to login', async () => {
    window.history.pushState({}, '', '/chat')
    render(<App />)
    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
  })
})

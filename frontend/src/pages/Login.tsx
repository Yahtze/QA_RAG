import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useSession } from '@/store/SessionContext'

export default function Login() {
  const session = useSession()
  const navigate = useNavigate()
  const [email, setEmail] = useState('reviewer@example.com')
  const [password, setPassword] = useState('password')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setIsSubmitting(true)
    await session.login(email, password)
    navigate('/chat', { replace: true })
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-md border-border/80 bg-card/80 shadow-2xl shadow-cyan-950/30">
        <CardHeader>
          <CardTitle className="text-2xl">Welcome back</CardTitle>
          <CardDescription>Sign in with the fake reviewer account to open the QA RAG workspace.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            <Button className="w-full" disabled={isSubmitting}>{isSubmitting ? 'Signing in…' : 'Sign in'}</Button>
          </form>
          <p className="mt-4 text-sm text-muted-foreground">Need an account? <Link className="text-primary" to="/register">Register</Link></p>
        </CardContent>
      </Card>
    </main>
  )
}

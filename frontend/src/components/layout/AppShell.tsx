import { ReactNode } from 'react'
import { TopBar } from './TopBar'

export function AppShell({ left, center, right }: { left: ReactNode; center: ReactNode; right: ReactNode }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.18),transparent_32%),hsl(var(--background))] text-foreground">
      <TopBar />
      <main className="grid gap-5 p-5 lg:grid-cols-[320px_minmax(0,1fr)_320px]">
        <section className="space-y-4">{left}</section>
        <section className="rounded-2xl border border-border/70 bg-card/60 p-4 shadow-2xl shadow-cyan-950/20">{center}</section>
        <section className="rounded-2xl border border-border/70 bg-card/40 p-4">{right}</section>
      </main>
    </div>
  )
}

import { Label } from '@/components/ui/label'
import { useSimulationProfile } from '@/store/SimulationProfileContext'

export function SimulationControls() {
  const simulation = useSimulationProfile()
  return (
    <section className="rounded-lg border border-dashed border-border/80 bg-muted/30 p-3 text-xs text-muted-foreground">
      <p className="mb-2 font-medium text-foreground">Simulation controls</p>
      <div className="flex flex-col gap-2 sm:flex-row sm:gap-4">
        <Label className="flex items-center gap-2"><input type="checkbox" checked={simulation.failNextChat} onChange={(event) => simulation.setFailNextChat(event.target.checked)} />Simulate chat error</Label>
        <Label className="flex items-center gap-2"><input type="checkbox" checked={simulation.failNextUpload} onChange={(event) => simulation.setFailNextUpload(event.target.checked)} />Simulate upload failure</Label>
      </div>
    </section>
  )
}

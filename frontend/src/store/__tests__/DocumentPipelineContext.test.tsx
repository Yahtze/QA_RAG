import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DocumentPipelineProvider, useDocumentPipeline } from '../DocumentPipelineContext'
import { SimulationProfileProvider, useSimulationProfile } from '../SimulationProfileContext'

function wrapper({ children }: { children: React.ReactNode }) {
  return <SimulationProfileProvider><DocumentPipelineProvider>{children}</DocumentPipelineProvider></SimulationProfileProvider>
}

describe('Document Pipeline module', () => {
  it('uploads a document through ready status', async () => {
    const { result } = renderHook(() => useDocumentPipeline(), { wrapper })
    const file = new File(['hello'], 'review-notes.pdf', { type: 'application/pdf' })

    await act(async () => { await result.current.upload(file) })

    expect(result.current.documents.some((doc) => doc.name === 'review-notes.pdf')).toBe(true)
    await waitFor(() => expect(result.current.documents.find((doc) => doc.name === 'review-notes.pdf')?.status).toBe('ready'), { timeout: 3000 })
  })

  it('fails deterministically and retries through ready status', async () => {
    const { result } = renderHook(() => ({ pipeline: useDocumentPipeline(), simulation: useSimulationProfile() }), { wrapper })
    const file = new File(['hello'], 'failure-case.pdf', { type: 'application/pdf' })

    act(() => result.current.simulation.setFailNextUpload(true))
    await act(async () => { await result.current.pipeline.upload(file) })

    await waitFor(() => expect(result.current.pipeline.documents.find((doc) => doc.name === 'failure-case.pdf')?.status).toBe('failed'), { timeout: 3000 })
    const failed = result.current.pipeline.documents.find((doc) => doc.name === 'failure-case.pdf')!

    await act(async () => { await result.current.pipeline.retry(failed.id) })

    await waitFor(() => expect(result.current.pipeline.documents.find((doc) => doc.id === failed.id)?.status).toBe('ready'), { timeout: 3000 })
  })
})

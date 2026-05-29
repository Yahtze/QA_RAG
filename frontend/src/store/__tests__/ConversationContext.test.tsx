import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ConversationProvider, useConversation } from '../ConversationContext'
import { DocumentPipelineProvider } from '../DocumentPipelineContext'
import { SimulationProfileProvider, useSimulationProfile } from '../SimulationProfileContext'

function wrapper({ children }: { children: React.ReactNode }) {
  return <SimulationProfileProvider><DocumentPipelineProvider><ConversationProvider>{children}</ConversationProvider></DocumentPipelineProvider></SimulationProfileProvider>
}

describe('Conversation module', () => {
  it('answers with citations for the active ready document', async () => {
    const { result } = renderHook(() => useConversation(), { wrapper })

    await act(async () => { await result.current.send('How does processing work?') })

    await waitFor(() => expect(result.current.messages.some((message) => message.role === 'assistant' && message.status === 'sent')).toBe(true), { timeout: 3000 })
    expect(result.current.latestCitations).toHaveLength(2)
  })

  it('stores failed assistant message and retries original query', async () => {
    const { result } = renderHook(() => ({ conversation: useConversation(), simulation: useSimulationProfile() }), { wrapper })

    act(() => result.current.simulation.setFailNextChat(true))
    await act(async () => { await result.current.conversation.send('Trigger failure') })

    await waitFor(() => expect(result.current.conversation.messages.some((message) => message.status === 'failed')).toBe(true), { timeout: 3000 })
    const failed = result.current.conversation.messages.find((message) => message.status === 'failed')!
    expect(failed.error?.originalQuery).toBe('Trigger failure')

    await act(async () => { await result.current.conversation.retry(failed.id) })

    await waitFor(() => expect(result.current.conversation.messages.some((message) => message.role === 'assistant' && message.status === 'sent')).toBe(true), { timeout: 3000 })
  })
})

import { renderHook, act } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import {
  ActiveConversationScopeProvider,
  useActiveConversationScope,
} from '../ActiveConversationScopeContext'
import type { RagDocument } from '@/types'

const docs: RagDocument[] = [
  {
    id: 'ready-1',
    name: 'ready.pdf',
    type: 'pdf',
    sizeLabel: '1 KB',
    uploadedAt: 'Today',
    status: 'ready',
    progress: 100,
    summary: 'Ready',
  },
  {
    id: 'failed-1',
    name: 'failed.pdf',
    type: 'pdf',
    sizeLabel: '1 KB',
    uploadedAt: 'Today',
    status: 'failed',
    progress: 0,
    summary: 'Failed',
  },
]

describe('ActiveConversationScopeContext', () => {
  it('selects only ready documents and saves through adapter', async () => {
    const save = vi.fn().mockResolvedValue({
      id: 'conv-1',
      activeDocumentIds: ['ready-1'],
      needsRetry: false,
    })

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <ActiveConversationScopeProvider documents={docs} saveActiveDocuments={save}>
        {children}
      </ActiveConversationScopeProvider>
    )

    const { result } = renderHook(() => useActiveConversationScope(), { wrapper })

    act(() => result.current.toggleDocument('failed-1'))
    expect(result.current.activeDocumentIds).toEqual([])

    act(() => result.current.toggleDocument('ready-1'))
    await act(async () => {
      await result.current.save('conv-1')
    })

    expect(save).toHaveBeenCalledWith('conv-1', ['ready-1'])
    expect(result.current.activeDocuments[0]!.id).toBe('ready-1')
  })
})

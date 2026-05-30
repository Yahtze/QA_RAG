import { describe, expect, it, vi, afterEach } from 'vitest'

import { streamConversationMessage } from '../conversationStream'

describe('conversationStream', () => {
  afterEach(() => vi.restoreAllMocks())

  it('parses SSE data lines into typed events', async () => {
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('data: {"type":"token","value":"Hi"}\n\n'))
        controller.enqueue(new TextEncoder().encode('data: {"type":"citations","map":{"1":{"chunk_id":"c","doc_id":"d","filename":"f.pdf","page":1,"snippet":"s"}}}\n\n'))
        controller.enqueue(new TextEncoder().encode('data: {"type":"done"}\n\n'))
        controller.close()
      },
    })

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(body, {
        status: 200,
        headers: { 'content-type': 'text/event-stream' },
      }),
    )

    const events = []
    for await (const event of streamConversationMessage('conv-1', 'Hi?')) {
      events.push(event)
    }

    expect(events.map((event) => event.type)).toEqual(['token', 'citations', 'done'])
  })

  it('throws API errors before streaming', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Forbidden' }), { status: 403 }),
    )

    const consume = async () => {
      const events: unknown[] = []
      for await (const event of streamConversationMessage('conv-1', 'Hi?')) {
        events.push(event)
      }
    }

    await expect(consume()).rejects.toThrow('Forbidden')
  })
})

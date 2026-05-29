import type { ChatResponse, RagDocument } from '@/types'

export async function askQuestion(document: RagDocument, query: string, shouldFail: boolean): Promise<ChatResponse> {
  await delay(900)

  if (shouldFail) {
    throw new Error('Simulated chat error: retrieval worker timed out before returning an answer.')
  }

  return {
    answer: `Based on ${document.name}, the most relevant answer is that the QA RAG pipeline should keep ingestion, retrieval, and answer generation observable through clear status states. Your question was: “${query}”.`,
    citations: [
      {
        id: `citation-${Date.now()}-1`,
        documentId: document.id,
        documentName: document.name,
        page: 2,
        snippet: 'The ingestion pipeline should expose progress from upload through embedding completion.',
      },
      {
        id: `citation-${Date.now()}-2`,
        documentId: document.id,
        documentName: document.name,
        page: 5,
        snippet: 'Answer generation should return citations with enough context for reviewers to trust the result.',
      },
    ],
  }
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

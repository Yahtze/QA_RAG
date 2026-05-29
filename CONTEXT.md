# QA RAG Domain Context

## Domain Terms

### QA RAG App

A question-answering interface backed by retrieval-augmented generation. Users upload Documents, select a ready Document, ask questions, and review answers with Citations.

### Document

A user-uploaded source file that can be selected for question answering after processing completes.

### Document Pipeline

The lifecycle that moves a Document through upload and processing states until it is ready for question answering or failed with a retry option.

Valid statuses:

- `uploading`
- `processing`
- `ready`
- `failed`

### Conversation

The question-answer interaction around an active ready Document. It owns user messages, assistant loading state, assistant answers, failed assistant messages, retry context, and the latest Citation set.

### Citation

Attribution for an answer back to a Document source location, shown as source cards like `Source: page 3` with snippet text.

### Session

The current user's fake authentication state for this frontend slice. It controls whether the user can access the chat page and where redirects go.

### Simulation Profile

Deterministic demo controls that force the next upload or chat request to fail. These controls exist only to exercise failure and retry UI before real backend wiring.

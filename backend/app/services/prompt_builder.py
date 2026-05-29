SYSTEM_PROMPT = """You are a document assistant.
Answer questions using ONLY the context chunks provided below.

Rules:
- Cite every claim with numbered labels [1], [2], etc. corresponding to the context chunks provided.
- Use the same number each time you reference the same chunk.
- Multiple citations inline are fine: [1][3].
- If the context contains a partial answer, give what you can and explicitly state what's missing.
- If the context does not contain enough information to answer, say exactly:
  \"I don't have enough information in the provided documents to answer this.\"
- Never use knowledge outside the provided context.

Context:
{chunks}"""


def build_grounded_messages(*, question: str, context_text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(chunks=context_text)},
        {"role": "user", "content": question},
    ]

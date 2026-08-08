"""Calls a free OpenRouter model to generate an answer grounded in retrieved context."""
from typing import List

from openai import OpenAI

NOT_FOUND_PHRASE = "The information is not available in the supplied documents."

SYSTEM_PROMPT = f"""You are a careful assistant that answers questions using ONLY the
provided context excerpts from a set of PDF documents.

Rules:
- Use only the information in the context below. Do not use outside knowledge.
- If the context does not contain enough information to answer the question,
  respond with exactly: "{NOT_FOUND_PHRASE}" and nothing else.
- Do not fabricate facts, numbers, or citations.
- Keep the answer concise and directly responsive to the question.
- Do not mention "the context" or "the excerpts" in your answer; answer naturally,
  as if you simply know the material from the documents.
"""

USER_PROMPT_TEMPLATE = """Context excerpts (each tagged with its source):
{context_block}

Question: {question}

Answer the question using only the context above.
"""


def _format_context(chunks) -> str:
    blocks = []
    for i, point in enumerate(chunks, start=1):
        payload = point.payload
        blocks.append(
            f"[Excerpt {i} | {payload['doc_name']} | page {payload['page_number']}]\n{payload['text']}"
        )
    return "\n\n".join(blocks)


class OpenRouterLLM:
    def __init__(self, api_key: str, model: str, base_url: str):
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. Get a free key at https://openrouter.ai/ and add it to .env"
            )
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate_answer(self, question: str, retrieved_chunks: List) -> str:
        if not retrieved_chunks:
            return NOT_FOUND_PHRASE

        context_block = _format_context(retrieved_chunks)
        user_prompt = USER_PROMPT_TEMPLATE.format(context_block=context_block, question=question)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()

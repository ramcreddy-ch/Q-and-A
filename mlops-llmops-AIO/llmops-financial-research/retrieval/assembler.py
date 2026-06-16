from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    doc_id: str
    section: str
    score: float
    text: str
    acl_tags: list[str]


def build_prompt(query: str, chunks: list[RetrievedChunk], max_context_chars: int = 2400) -> str:
    context_parts = []
    used = 0
    for chunk in sorted(chunks, key=lambda c: c.score, reverse=True):
        part = f"[doc={chunk.doc_id} section={chunk.section}] {chunk.text}\n"
        if used + len(part) > max_context_chars:
            break
        context_parts.append(part)
        used += len(part)

    context = "\n".join(context_parts)
    return f"QUESTION:\n{query}\n\nAPPROVED CONTEXT:\n{context}\n\nANSWER WITH CITATIONS."

def build_sampleqa_prompt(
    question: str,
    passages: list,
    max_passages: int = 10,
    include_text_fields: tuple = ("text", "content", "body"),
    truncate_chars: int = 800,
) -> str:
    """
    Build a clear, instruction-first prompt policy for answer synthesis over retrieved passages.
    """

    def _clean(s: str) -> str:
        if s is None:
            return ""
        s = str(s)
        s = s.replace("\r", " ").replace("\n", " ").strip()
        return " ".join(s.split())

    def _first_text_field(p: dict) -> str:
        for k in include_text_fields:
            if k in p and isinstance(p[k], str) and p[k].strip():
                return p[k]
        return ""

    blocks = []
    for idx, p in enumerate(passages[: max(0, int(max_passages))], start=1):
        title = _clean(p.get("title", "")) or f"Passage {idx}"
        body = _clean(_first_text_field(p))
        if truncate_chars and body:
            body = body[:truncate_chars].rstrip()
        if body:
            block = f"Passage {idx}\nTitle: {title}\nExcerpt: {body}"
        else:
            block = f"Passage {idx}\nTitle: {title}"
        blocks.append(block)

    rendered_passages = "\n\n".join(blocks) if blocks else "No passages available."

    instruction = f"""
You answer the question using only the passages that follow. Use the passages as the sole evidence source. Prefer precision over speculation. If the passages do not contain the answer, respond with the exact sentence Not found in retrieved context.

When passages disagree, choose the answer that is most specific and most directly supported by the text. Prefer passages that name exact entities, dates, quantities, or definitions that align with the question. If several passages support the same answer, keep it concise. Do not copy long passages. Do not include citations or explanations. Do not use outside knowledge beyond what appears in the passages.

Passages
{rendered_passages}

Question
{_clean(question)}

Answer
""".strip()

    return instruction

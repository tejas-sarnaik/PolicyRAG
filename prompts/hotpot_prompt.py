def build_hotpot_prompt(
    question: str,
    passages: list,
    top_entities: list,
    top_triples: list | None = None,
    max_passages: int = 12,
    max_entities: int = 8,
    max_triples: int = 8,
    include_passage_indices: bool = True,
    truncate_chars: int = 1200,
) -> str:
    """
    Build a clear instruction-first prompt policy for multi hop question answering over retrieved passages,
    augmented by a small set of entity hints and optional structured fact triples.
    """

    def _clean_text(s: str) -> str:
        if s is None:
            return ""
        s = str(s).replace("\r", " ").replace("\n", " ").strip()
        # Collapse internal whitespace
        return " ".join(s.split())

    def _truncate(s: str, limit: int) -> str:
        if limit is None or limit <= 0:
            return s
        if len(s) <= limit:
            return s
        return s[:limit].rstrip()

    # Prepare passages
    prepped_passages = []
    for idx, p in enumerate(passages[: max(0, int(max_passages))], start=1):
        body = _truncate(_clean_text(p), int(truncate_chars))
        if not body:
            continue
        if include_passage_indices:
            block = f"Passage {idx}\n{body}"
        else:
            block = body
        prepped_passages.append(block)

    rendered_passages = "\n\n".join(prepped_passages) if prepped_passages else "No passages available."

    # Prepare entity hint line
    shown_entities = [e for e in (top_entities or []) if isinstance(e, str)]
    entity_hint = ", ".join(shown_entities[: max(0, int(max_entities))]) if shown_entities else ""

    # Prepare structured triples
    rendered_triples = ""
    if top_triples:
        triples_buf = []
        for t_idx, t in enumerate(top_triples[: max(0, int(max_triples))], start=1):
            try:
                s, p, o = t
            except Exception:
                # Skip malformed entries defensively
                continue
            s = _clean_text(s)
            p = _clean_text(p)
            o = _clean_text(o)
            # Each triple is rendered in a simple human readable line without special symbols
            triples_buf.append(f"Triple {t_idx}\nSubject: {s}\nPredicate: {p}\nObject: {o}")
        if triples_buf:
            rendered_triples = "\n\nStructured facts\n" + "\n\n".join(triples_buf)

    instruction = f"""
You answer the question using only the passages that follow. Use the passages as the primary source of evidence. If the answer does not appear in any passage, you may use the structured facts that follow the entity hint. If neither the passages nor the structured facts contain the answer, respond with the exact sentence Not found in retrieved context.

When multiple passages discuss related content, prefer the passage that states the fact most directly and precisely. When the passages disagree, choose the statement that is most specific and that names concrete entities, dates, places, or quantities that match the question. Do not use knowledge that is not present in the passages or the structured facts. Do not provide citations or references. Do not copy long spans of text. Keep the final answer concise and factual.

If the question requires a yes or no decision, begin the answer with Yes or No, then include a short supporting sentence that appears in a passage. If no passage contains a supporting sentence, you may include a short supporting line derived from a single structured fact. If neither source supports a decision, respond with Not found in retrieved context.

Important entities
{entity_hint}

Passages
{rendered_passages}
""".rstrip()

    if rendered_triples:
        instruction = f"{instruction}\n\n{rendered_triples}"

    instruction = f"{instruction}\n\nQuestion\n{_clean_text(question)}\n\nAnswer\n".strip()

    return instruction

def build_fact_selection_prompt(
    question: str,
    triples: list,
    top_k: int = 4,
    max_candidates_in_prompt: int = 60,
) -> str:
    """
    Build a detailed, instruction-first prompt Policy for selecting relevant fact triples.
    """
    import json

    candidates = []
    for t in triples[: max(0, int(max_candidates_in_prompt))]:
        try:
            s, p, o = t
        except Exception:
            # Skip malformed entries defensively
            continue
        s = "" if s is None else str(s)
        p = "" if p is None else str(p)
        o = "" if o is None else str(o)
        candidates.append([s, p, o])

    instruction = f"""
You are the fact-filtering gate in PolicyRAG, a high-stakes QA system. Your job is to select ONLY the facts that are necessary
and sufficient to answer (or strongly support answering) the query, including via short multi-hop chains.
You must select up to 4 relevant facts from the provided candidate list that have a strong connection to the query, aiding
reasoning and supporting an accurate answer.
Policy:
1) Direct answer triples > contextual ones
2) Minimal bridges that connect query → target fact
3) Specific/temporal/relational > generic
4) Exact entity string > alias
5) Remove near-duplicates; smallest sufficient set

The output must be in strict JSON format, e.g. "fact": [["s1","p1","o1"], ["s2","p2","o2"]]
If no facts are relevant, return: "fact": []
You must only use facts from the candidate list and never generate new facts. Accuracy is critical because your filtered facts
directly guide the reasoning process in this system

Length and count limits
Return at most {top_k} triples.
If no triple appears relevant, return an empty list.

Constraints
Do not invent new facts. Only choose from the supplied candidates.
Keep the original surface forms for subject, predicate, and object as they appear in the candidates. Do not rewrite, reformat, or expand them.
Do not include explanations, comments, or additional keys in the output.

Output format
Return a single JSON object with exactly one key named fact.
The value must be a JSON array of triples, where each triple is a three element JSON array of strings in the order subject, predicate, object.
Do not wrap the JSON in code fences. Do not add any text before or after the JSON.

Question
{question}

Candidates
{json.dumps(candidates, ensure_ascii=False, indent=2)}

Return only JSON in this exact shape.
{{"fact": [["s","p","o"], ...]}}
If no triple is relevant, return
{{"fact": []}}
"""

    # Strip leading and trailing whitespace so the prompt is clean in logs.
    return instruction.strip()

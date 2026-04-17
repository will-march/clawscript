"""Grounded RAG with mandatory citations.

Demonstrates: invariants as a hallucination guard. The program
REFUSES to return an answer that neither cites a retrieved doc
nor explicitly abstains. That refusal is enforced by
assert_invariant, not by a prompt instruction the model can
weasel around.
"""


@typed
def answer_with_citations(question: str) -> dict:
    checkpoint("rag_start", q=question)

    docs = tool("retrieve", query=question, k=5)
    assert_invariant(len(docs) > 0, "retrieval returned zero docs")
    checkpoint("retrieved", n=len(docs))

    context = "\n\n".join(f"[{d['id']}] {d['text']}" for d in docs)

    answer = prompt(
        "claude-sonnet-4-6",
        f"Answer using ONLY the sources below. Every factual sentence must end with a bracketed citation like [doc-id]. If sources do not support an answer, reply exactly 'NO ANSWER IN SOURCES'.\n\nSources:\n{context}\n\nQuestion: {question}",
    )
    checkpoint("answered", chars=len(answer))

    citations = [d["id"] for d in docs if f"[{d['id']}]" in answer]
    abstained = "NO ANSWER IN SOURCES" in answer

    assert_invariant(
        len(citations) > 0 or abstained,
        "answer must cite at least one retrieved doc or explicitly abstain",
    )
    checkpoint("validated", cited=citations, abstained=abstained)

    return {"answer": answer, "citations": citations, "abstained": abstained}


result = answer_with_citations("What caused the 2024 Latacunga eruption?")
print(result)

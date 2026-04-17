"""Multi-step research agent: fetch -> summarize -> critique -> finalize.

Demonstrates linear composition of prompt() and tool() calls with
checkpointed phases and invariants.
"""


@typed
def run_research(topic: str) -> str:
    checkpoint("start", topic=topic)
    assert_invariant(len(topic) > 0, "topic must be non-empty")

    raw = tool("http_get", url=f"https://example.com/search?q={topic}")
    checkpoint("fetched", chars=len(raw))

    summary = prompt(
        "claude-sonnet-4-6",
        f"Summarize the following search results in five tight bullet points.\n\n{raw}",
    )
    checkpoint("summarized", chars=len(summary))

    critique = prompt(
        "claude-sonnet-4-6",
        f"Critically review this summary. List up to three concrete weaknesses, no hedging.\n\n{summary}",
    )
    checkpoint("critiqued", chars=len(critique))

    final = prompt(
        "claude-opus-4-7",
        f"Rewrite the summary to address the critique. Be concise.\n\nSummary:\n{summary}\n\nCritique:\n{critique}",
    )
    checkpoint("finalized", chars=len(final))

    assert_invariant(len(final) > 0, "final report must not be empty")
    return final


report = run_research("distributed tracing")
print(report)

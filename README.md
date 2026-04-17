# Clawscript

A Python-syntactic language for Claude-executed agent programs with
deterministic flow control.

Clawscript source files parse as ordinary Python 3.11+ under `ast.parse`,
but they are executed by a dedicated interpreter that walks the AST
node-by-node and is forbidden from reordering, skipping, or paraphrasing
steps. The trade is simple: you write your agent as code instead of
prose, and in exchange every control-flow decision and every external
call lands in a structured JSONL trace.

Think of it as "Skills with airbags": the same agent pattern, but the
loops have caps, the prompts are literal, the tool names are exact, and
the invariants actually fire.

---

## Why

Prompt-only agents (Skills, freeform ReAct, raw tool-use loops) give the
model broad latitude. That latitude is an asset for exploration and a
liability for anything you would want to audit after the fact. The
failure modes it produces are the same every time:

- Silent retries until the budget burns out.
- Prompt paraphrase that quietly changes the question.
- "Nearest-match" tool substitution.
- Missing or fabricated citations in RAG.
- Unbounded agent loops.
- Invariants treated as suggestions.

Clawscript removes each of these as a possibility — at validation time
where possible, at runtime otherwise.

## The six flow-control guarantees

1. **No implicit retries.** A failing `tool()` or `prompt()` raises.
   Control flows only to a matching `except`.
2. **No unbounded loops.** `while` must be inside a function decorated
   `@bounded_loop(N)` with an integer literal. Iteration `N+1` raises
   `BoundExceeded`.
3. **No hidden state.** Every step-to-step value passes through an
   explicitly bound name visible in source.
4. **No paraphrase of prompts.** `prompt(model, text)` sends `text`
   byte-for-byte. The validator forces `text` to be a literal or
   f-string so it is readable in source.
5. **No skipping invariants.** `assert_invariant` halts on falsy and
   cannot be elided.
6. **Checkpoints are verbatim.** Every `checkpoint(label, **data)` emits
   exactly one JSONL record with the source-level label.

## Quick example

```python
# research.clw
@typed
def run_research(topic: str) -> str:
    checkpoint("start", topic=topic)
    assert_invariant(len(topic) > 0, "topic must be non-empty")

    raw = tool("http_get", url=f"https://example.com/search?q={topic}")
    summary = prompt("claude-sonnet-4-6",
        f"Summarize in five bullets.\n\n{raw}")
    critique = prompt("claude-sonnet-4-6",
        f"Critique this summary in up to three weaknesses.\n\n{summary}")
    final = prompt("claude-opus-4-7",
        f"Rewrite addressing the critique.\n\n{summary}\n\n{critique}")

    assert_invariant(len(final) > 0, "final report must not be empty")
    return final

print(run_research("distributed tracing"))
```

Run it:

```
$ python3 clw.py examples/research.clw --trace /tmp/run.jsonl
```

## Install

Clawscript ships as one file: `clw.py`. Copy it into your project or
clone this repo.

```
git clone https://github.com/will-march/clawscript.git
cd clawscript
python3 clw.py --help
```

Optional: the Anthropic SDK for real model calls. Without it, `prompt()`
returns a stub — useful for development and CI.

```
python3 -m pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

## Running programs

```
# stub mode (no API key needed)
python3 clw.py examples/retry_backoff.clw

# trace to a file
python3 clw.py examples/research.clw --trace traces/run.jsonl

# validation-only (one-liner)
python3 -c "import ast; from clw import Validator; \
  v = Validator(); v.visit(ast.parse(open('programs/p.clw').read())); \
  print(v.errors or 'OK')"
```

## Example programs

Seven runnable `.clw` programs in `examples/`, each paired with a
dedicated PDF explainer:

| File | Pattern |
|---|---|
| `research.clw` | Linear research pipeline: fetch → summarize → critique → finalize |
| `retry_backoff.clw` | Bounded retry with exponential backoff (`@bounded_loop(5)`) |
| `approval.clw` | Human-in-the-loop deploy with `require_approval` |
| `rag_cited.clw` | Grounded RAG that refuses an answer without citations |
| `llm_judge.clw` | LLM-as-judge harness with protocol-level invariants |
| `extract_json.clw` | Structured extraction with bounded retry-on-bad-schema |
| `react_agent.clw` | Bounded ReAct tool loop — literally cannot spin forever |

## Documentation

| PDF | Purpose |
|---|---|
| `Clawscript-Overview.pdf` | 8-page high-level introduction |
| `SETUP-AND-DEPLOY.pdf` | 19-page hands-on guide: install → run → deploy → observe |
| `rag_cited-explainer.pdf` | Walk-through of the RAG-with-citations example |
| `llm_judge-explainer.pdf` | Walk-through of the LLM-as-judge example |
| `extract_json-explainer.pdf` | Walk-through of structured-extraction retries |
| `react_agent-explainer.pdf` | Walk-through of the bounded ReAct agent |

Source-form docs:

- `SPEC.md` — language specification
- `RUNTIME.md` — interpreter system prompt (for Claude-as-interpreter mode)
- `COMPARISON.md` — Clawscript vs. Skills vs. raw prompting

## Architecture

The reference interpreter (`clw.py`, ~480 LOC) has four moving parts:

- **`Validator(ast.NodeVisitor)`** — enforces static rules before any
  execution. Programs that fail validation produce zero trace records.
- **`Interpreter`** — an AST walker with one `_stmt_<NodeType>` handler
  per supported statement. Emits a `step` trace per statement.
- **Built-in factories** — `prompt`, `tool`, `assert_invariant`,
  `checkpoint`, `require_approval`, `@bounded_loop`, `@typed`. Each
  closes over the tracer so every external effect is logged.
- **`Tracer`** — JSONL sink with a monotonic step counter.

Expressions delegate to Python's `compile` + `eval` with a safe-builtin
allow-list. Expressions cannot re-enter control flow, so this is both
safe and avoids hundreds of lines of boilerplate.

See `SPEC.md` for the full semantics and `SETUP-AND-DEPLOY.pdf` for
production deployment patterns (Docker, CI, Lambda / Fluid Compute /
Kubernetes, log aggregation).

## Regenerating the docs

```
python3 -m pip install fpdf2
python3 make_pdf.py     # overview
python3 make_docs.py    # explainers + setup guide
```

## Status

v0.1 — working reference interpreter, seven example programs, full
docs. Not yet packaged on PyPI. The interpreter is a reference
implementation, not a sandbox; run untrusted programs in isolated
subprocesses.

## Roadmap

- Packaging (`pip install clawscript`).
- Full deterministic replay: trace capture includes prompt outputs and
  tool results, so a run can be reconstructed bit-for-bit.
- Pure Claude-as-interpreter mode tooling (the system prompt exists in
  `RUNTIME.md`; a driver and conformance tests are not yet shipped).
- `async` support in the grammar (the keyword is reserved).
- LSP server for editor support.

## License

TBD.

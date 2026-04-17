# Show HN post — draft

**Recommended title (70 char budget):**

> Show HN: Clawscript – a Python DSL where every agent step is a trace record

Alternates:
- Show HN: Clawscript – strict Python for auditable LLM agents
- Show HN: Clawscript – deterministic agent execution in 480 lines of Python

---

## Body (copy below into the HN text field)

I have been burned by the same failure mode in production LLM agents three times:
the agent silently retries, paraphrases a prompt I spent weeks tuning, or loops
over a web-fetch tool until the bill is embarrassing. Skill-style markdown
gives the model too much latitude for any of this to be predictable.

Clawscript is my attempt at the opposite. It is a tiny language whose source is
strictly Python 3.11+ grammar (parsed by `ast.parse`) but whose semantics are
deterministic agent execution. Every statement becomes one trace event. Every
LLM call goes through a `prompt(model, text)` primitive where the validator
forces `model` to be a string literal and `text` to be a literal or f-string.
Every `while` must be inside a function decorated `@bounded_loop(N)` with an
integer literal — a seventh iteration raises `BoundExceeded`, full stop.

A bounded retry looks like this:

    @bounded_loop(3)
    @typed
    def extract_person(bio: str) -> dict:
        attempt = 0
        while attempt < 3:
            raw = prompt("claude-sonnet-4-6",
                f"Return JSON: name, age, role.\nBio: {bio}")
            try:
                data = tool("parse_json", text=raw)
                assert_invariant(isinstance(data["age"], int), "age must be int")
                return data
            except Exception:
                attempt = attempt + 1
        assert_invariant(False, "3 attempts failed")

Every run emits a JSONL record per statement plus `*_begin`/`*_end` brackets
around prompts, tool calls, invariants, and approvals. You can reconstruct the
entire control flow from the trace alone, which is the whole point.

The reference interpreter is ~480 lines of Python. `ast.parse` is the parser
(zero custom syntax). A static validator runs before execution — a program
that breaks the rules produces zero trace records. Pure-Python expressions
delegate to `eval` with a safe-builtins allow-list; only statements are walked
by hand so every control-flow decision is explicitly traced.

Prior art I borrowed from: Temporal's durable-execution determinism, Eiffel
invariants, BAML's typed prompts, LangGraph's state-machine-as-code. The
closest neighbor is LangGraph, but Clawscript is a *language* you write, not a
graph-construction API. Different ergonomics, different target.

Repo + docs: https://github.com/will-march/clawscript
Includes seven runnable example programs (RAG with mandatory citations,
bounded ReAct, LLM-as-judge eval harness, structured extraction with
bounded retry, human-in-the-loop approval) and a detailed setup-and-deploy
PDF covering Docker, CI, Lambda / Fluid Compute / K8s patterns.

Feedback I'd genuinely like:
- Does the strictness go too far? Not far enough?
- Would anyone actually want a fully-replayable mode (record every prompt
  output so a trace can be re-run bit-for-bit)?
- Is "Python-parseable, non-Python-semantic" the right trade, or should a
  DSL just own its own grammar?

---

## When to submit

- Tuesday or Wednesday, 08:00-09:30 PT (peak US daytime crowd arriving).
- Avoid Fridays (traffic drops), avoid Mondays (backlog from weekend).
- Avoid the first week of Anthropic or OpenAI product launches -- HN
  queues up with the big news and you drown.

## In the first two hours

- Respond to every top-level comment. HN's ranking weights early engagement.
- Have the repo cloneable and the examples runnable -- expect people to try
  `python3 clw.py examples/retry_backoff.clw` within ninety seconds.
- Do not argue. Acknowledge prior art generously. "Good point, I should
  have mentioned X" wins more mindshare than a defense.

## If the post flops

- Do not delete and resubmit. Wait 48h, revise the angle, resubmit with a
  different title. HN allows one reset per story.
- Consider a `/r/LocalLLaMA` post first to gather feedback, then HN once
  the README reflects that feedback.

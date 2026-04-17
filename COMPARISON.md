# Clawscript vs. Claude Code Skills vs. Raw Prompting

| Dimension | Clawscript (`clw`) | Claude Code Skills | Raw prompting |
|---|---|---|---|
| **Determinism of step order** | Total — AST walk is enforced by the interpreter; no node may be skipped or reordered. | Low — the model chooses when/whether to invoke a step based on the markdown guidance. | None — single shot, whatever the model emits. |
| **Determinism of tool dispatch** | Exact name match; unknown tool → `KeyError`. | Model picks tool by description match; silent substitution possible. | N/A (no tool layer). |
| **Auditability of trace** | Structured JSONL with a stable event schema; every statement emits one `step` record; every external effect is bracketed by `*_begin`/`*_end`. | Model transcript plus tool-use blocks; schema is per-tool, not uniform. | Plain transcript. |
| **Retry behavior on failure** | Never implicit. `try/except` is the only path; `@bounded_loop(N)` caps any retry loop. | Implicit — model may silently retry with a reworded prompt. | None. |
| **Loop safety** | `while` requires `@bounded_loop(N)` with a literal integer; validator rejects otherwise. | No loop primitive; a skill may recurse indefinitely via chat turns. | None. |
| **Prompt fidelity** | `prompt()` text sent byte-for-byte; validator forces text to be a literal or f-string in source. | Skill steers but model may paraphrase sub-prompts. | Whatever the model composes. |
| **Invariants** | `assert_invariant` halts on violation; not elidable. | Soft — markdown "should" statements; model may interpret. | None. |
| **Human-in-the-loop** | First-class `require_approval` primitive; denial is a typed exception. | Must be built per-skill; no uniform protocol. | Out-of-band only. |
| **Type enforcement** | Optional `@typed` decorator runs `isinstance` checks at each call. | None. | None. |
| **Flexibility** | Low by design — you must encode control flow. | High — skills can express "figure it out" steps. | Highest. |
| **Authoring cost** | Higher — program must be written. | Low — markdown narrative. | Lowest. |
| **Latency (wall-clock)** | Higher — many small, bounded LLM sub-calls; extra trace I/O. | Variable — fewer, larger turns. | Lowest. |
| **Failure modes** | Hard errors with a typed hierarchy (`ValidationError`, `InvariantError`, `BoundExceeded`, `ApprovalDenied`). | Soft drift from intent; retries masking failure; tool miswires. | Hallucinated output. |
| **Best for** | Compliance-sensitive agents, production deploys, incident response runbooks, audits. | Exploratory tasks, developer tooling, variable-shape workflows. | One-shot answers, drafting, chat. |
| **Worst for** | Tasks whose shape is unknown until runtime. | Irreversible actions, regulated workflows. | Anything that needs tools or loops. |

## One-paragraph summary

Clawscript and Skills sit at opposite ends of a determinism-flexibility
axis. Skills give the model broad latitude inside a markdown scaffold
— cheap to author, easy to use, hard to audit. Clawscript gives the
model none — every decision is an AST node, every external effect is a
trace record, every loop has an integer cap in source. Pick Skills for
exploration, Clawscript for anything you would want to read a
post-incident trace of.

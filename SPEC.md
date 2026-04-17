# Clawscript Language Specification (v0.1)

**Working name:** `clw`
**Status:** Draft · 2026-04-17

Clawscript is a programming language for writing Claude-executed agent
programs with deterministic flow control. Its surface syntax is a strict
subset of Python 3.11+ grammar: every valid Clawscript file parses under
`ast.parse`. Semantics diverge: the interpreter (a Claude system prompt
plus a runtime harness) walks the AST node-by-node and is forbidden from
reordering, skipping, or paraphrasing steps.

The language exists because Claude Code "Skills" — markdown instructions
loaded into the model's context — leave too much latitude for silent
retries, ad-hoc branching, and prompt paraphrase. Clawscript trades
that latitude for auditability.

---

## 1. Lexical grammar

Clawscript inherits Python 3.11+ grammar verbatim. The reference parser
is CPython's `ast` module. No keywords, operators, or literal forms are
added or removed. Specifically:

- Indentation-based blocks.
- `def`, `class`, `if/elif/else`, `for`, `while`, `try/except/finally`,
  `return`, `raise`, `assert`, `with`, `pass`, `break`, `continue`.
- Decorators, f-strings, list/dict/set/generator comprehensions.
- Type hints on parameters, returns, and annotated assignments.
- PEP 604 union syntax (`int | None`).

**Justification:** leveraging `ast` gives us a battle-tested parser for
free and guarantees editor/tooling compatibility with zero investment.

## 2. Semantic divergences from Python

A Clawscript file is *parsed* as Python but *executed* by the Clawscript
interpreter. The following diverges:

| # | Area | Python | Clawscript |
|---|------|--------|--------------|
| 1 | `import` | allowed | **rejected at validation time** |
| 2 | `while` | allowed anywhere | allowed only inside a function decorated `@bounded_loop(N)` |
| 3 | `prompt()` call | N/A | first arg must be a string literal; second arg must be a string literal or f-string |
| 4 | Retry of failed calls | up to the programmer | **never implicit**; control jumps to the nearest matching `except` |
| 5 | Implicit conversions | as Python | same, but `@typed` functions enforce `isinstance` at runtime |
| 6 | Default args | evaluated at def-time | evaluated at def-time (same as Python) |
| 7 | Hidden state | closures, module globals | all step-to-step data flow must pass through an explicitly bound name |
| 8 | Runtime library | `sys`, `os`, stdlib | only `SAFE_BUILTINS` plus the Clawscript standard library |

**Justification:** each divergence removes a class of non-determinism or
a vector for model "judgment" to alter behavior.

## 3. Standard library (Clawscript built-ins)

Each built-in is available globally and may not be shadowed.

### `prompt(model: str, text: str) -> str`

Makes a single LLM sub-call. Returns the model's text response.
**Invariant:** `text` is sent verbatim; neither the interpreter nor the
runtime may rewrite or truncate it. The parser requires a string-literal
model and a literal/f-string `text`. **Justification:** forces every
outbound prompt to appear in source, in full, for review.

### `tool(name: str, **kwargs) -> Any`

Invokes a registered tool by exact name. Unknown names raise `KeyError`
— the runtime does *not* pick a "nearest" tool. **Justification:**
string-matching dispatch prevents silent tool substitution.

### `assert_invariant(expr, msg: str) -> None`

Halts the program if `expr` is falsy. Unlike Python's `assert`, this is
**never elided** (no `-O` equivalent exists). **Justification:**
invariants are load-bearing; the runtime should never treat them as
optional.

### `checkpoint(label: str, **data) -> None`

Emits a structured trace event. The label must be a string literal so
downstream log consumers can rely on a finite label vocabulary.
**Justification:** checkpoints are the primary audit-grep target.

### `require_approval(action: str) -> None`

Pauses execution and asks a human to approve `action`. Denial raises
`ApprovalDenied`. **Justification:** irreversible operations should be
gated by a human-in-the-loop primitive rather than a convention.

### `@bounded_loop(max_iter: int)`

Function decorator. Any `while` loop lexically inside the decorated
function is capped at `max_iter` iterations; exceeding the cap raises
`BoundExceeded`. The argument must be an integer literal. A function
with a `while` loop but no `@bounded_loop(N)` decorator **fails
validation**. **Justification:** unbounded loops are the primary failure
mode of agent programs — make the cost visible and the cap auditable.

### `@typed`

Function decorator. On every call, every annotated parameter is
`isinstance`-checked against its type hint; the return value is checked
against the return annotation. Generic parameterizations fall back to
their `typing.get_origin`. **Justification:** optional, cheap,
catches a large class of LLM-generated bugs where the wrong shape is
returned.

## 4. Execution model

The interpreter is the pair (runtime system prompt, AST walker). The
walker visits the `Module`'s body in order. For each statement node:

1. Emit a `step` trace event `{node, line}`.
2. Dispatch to the handler for that node type.
3. Evaluate any contained expressions (which may call built-ins and
   thereby trigger `prompt`/`tool` sub-events).
4. Execute the node's control-flow effect.

**Expressions** evaluate by recursive descent. Built-in calls emit
`*_begin` / `*_end` events bracketing the external effect.

**Functions** close over their defining environment (`Env`); each call
creates a child environment. Returning raises an internal `_Return`
signal, caught by the call frame.

**Errors** propagate as ordinary exceptions through the walker. An
unhandled exception terminates the program and emits a final
`program_end` event with `status: "error"`.

## 5. Flow-control guarantees

The six core rules the interpreter MUST enforce:

1. **No implicit retries.** A tool/prompt failure raises. Control flows
   only to a matching `except`; the runtime never reissues the call on
   its own.
2. **No unbounded loops.** `while` without an enclosing
   `@bounded_loop(N)` is a validation error. `for` is bounded by its
   iterable.
3. **No hidden state.** All step-to-step values pass through an
   explicitly bound name. The runtime may not cache a previous result
   and "reuse" it without a visible binding.
4. **No paraphrase of prompts.** `prompt()` sends its text argument
   byte-for-byte.
5. **No skipping invariants.** `assert_invariant` halts on failure, full
   stop.
6. **Checkpoints are verbatim.** Every `checkpoint(label, **data)`
   produces exactly one JSONL record whose `label` matches the
   source-level string literal.

## 6. Trace format

One JSON object per line on the trace sink. Required fields on every
record: `step` (monotonic int), `ts` (unix seconds), `event`. Event-
specific fields documented per built-in above. A minimal example:

```jsonl
{"step":1,"ts":1712345678.0,"event":"program_start","file":"research.clw"}
{"step":2,"ts":1712345678.0,"event":"step","node":"FunctionDef","line":3}
{"step":3,"ts":1712345678.1,"event":"checkpoint","label":"start","data":{"topic":"x"}}
```

## 7. Error model

Errors are ordinary Python exceptions. The Clawscript hierarchy adds:

- `ClawError` — base
- `ValidationError` — static-rule violation; raised before any step runs
- `InvariantError` — `assert_invariant` failed
- `ApprovalDenied` — `require_approval` declined
- `BoundExceeded` — `@bounded_loop(N)` cap exceeded

`try/except` in Clawscript source catches these like any other exception. The
only un-catchable condition is `ValidationError`: a program that fails
validation cannot begin execution at all.

## 8. Non-goals

- **Performance.** The interpreter is deliberately slow; auditability wins.
- **Concurrency.** No `async` in v0.1 (grammar reserves the keyword).
- **Foreign imports.** A program is self-contained; tools provide the
  escape hatch.
- **Sandboxing.** The reference interpreter is not a security boundary.
  Run untrusted programs in a subprocess/sandbox of your choosing.

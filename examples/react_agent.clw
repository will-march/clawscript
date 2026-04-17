"""Bounded ReAct-style agent loop.

Demonstrates: the canonical "model picks tools until done" pattern,
but with an enforced ceiling. @bounded_loop(6) means the agent
literally cannot spin past six iterations -- the interpreter raises
BoundExceeded on a seventh. The ACTION/FINAL protocol is enforced by
assert_invariant, so a model that drifts into free prose halts the
run instead of silently corrupting state.
"""


@bounded_loop(6)
@typed
def react_solve(task: str) -> str:
    state = ""
    step = 0

    while step < 6:
        checkpoint("react_step", n=step, state_chars=len(state))

        decision = prompt(
            "claude-sonnet-4-6",
            f"You are solving a task with tools. Reply with EITHER\n  ACTION: <tool_name>|<arg>\nOR\n  FINAL: <answer>\nPipe-separated, one line, no preamble.\n\nTools: search, calc\n\nTask: {task}\n\nHistory:\n{state}",
        )
        first_line = decision.strip().split("\n")[0]

        if first_line.startswith("FINAL:"):
            answer = first_line[len("FINAL:"):].strip()
            checkpoint("react_done", steps=step + 1, answer=answer)
            return answer

        assert_invariant(
            first_line.startswith("ACTION:"),
            f"protocol violation at step {step}: {first_line[:60]!r}",
        )

        body = first_line[len("ACTION:"):].strip()
        parts = body.split("|", 1)
        assert_invariant(len(parts) == 2, f"bad ACTION format: {body!r}")
        name = parts[0].strip()
        arg = parts[1].strip()

        result = tool(name, arg=arg)
        state = f"{state}step {step}: {name}({arg}) -> {result}\n"
        step = step + 1

    assert_invariant(False, "react_solve exceeded 6 steps without FINAL")
    return ""


answer = react_solve("What is the population of France divided by 1000?")
print(f"answer: {answer}")

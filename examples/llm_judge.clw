"""LLM-as-judge evaluation harness.

Demonstrates: structured checkpoints as dataset rows, and
protocol-level invariants on the grader's output (exactly two
lines, strict prefixes, integer score in range). Each eval case
emits a 'judged' checkpoint that downstream log consumers can
load as a DataFrame row.
"""


@typed
def grade(question: str, answer: str, rubric: str) -> dict:
    checkpoint("judge_start", q=question, a_chars=len(answer))

    verdict = prompt(
        "claude-sonnet-4-6",
        f"You are a strict grader. Score the answer 1-5 using the rubric. Reply with EXACTLY two lines:\nSCORE: <int>\nREASON: <one sentence>\nNo preamble.\n\nRubric:\n{rubric}\n\nQuestion: {question}\nAnswer: {answer}",
    )

    lines = verdict.strip().split("\n")
    assert_invariant(len(lines) == 2, f"grader returned {len(lines)} lines, expected 2")
    assert_invariant(lines[0].startswith("SCORE: "), "missing SCORE prefix")
    assert_invariant(lines[1].startswith("REASON: "), "missing REASON prefix")

    score = int(lines[0][len("SCORE: "):].strip())
    assert_invariant(1 <= score <= 5, f"score {score} outside [1,5]")
    reason = lines[1][len("REASON: "):].strip()

    checkpoint("judged", question=question, score=score, reason=reason)
    return {"question": question, "score": score, "reason": reason}


cases = [
    {"q": "What is 2+2?", "a": "4", "rubric": "Exact arithmetic; 5 if exact."},
    {"q": "Capital of France?", "a": "Paris", "rubric": "Factual accuracy."},
    {"q": "Define entropy.", "a": "Randomness.", "rubric": "Scientific precision."},
]

results = []
for case in cases:
    r = grade(case["q"], case["a"], case["rubric"])
    results.append(r)

avg = sum(r["score"] for r in results) / len(results)
checkpoint("batch_done", n=len(results), avg=avg)
print(f"average score: {avg}")

assert_invariant(avg >= 3.0, f"eval batch avg {avg} below threshold 3.0")

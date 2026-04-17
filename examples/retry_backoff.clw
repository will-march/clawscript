"""Bounded retry with exponential backoff.

Demonstrates @bounded_loop(N): the while loop inside fetch_with_retry
is capped at 5 iterations by the decorator. A sixth attempt would
raise BoundExceeded automatically — the programmer cannot forget the
cap and the interpreter cannot "try one more time" on its own.
"""


@bounded_loop(5)
@typed
def fetch_with_retry(url: str) -> str:
    attempt = 0
    delay = 1.0
    last_error = "none"

    while attempt < 5:
        checkpoint("attempt", n=attempt, delay_s=delay)
        try:
            result = tool("http_get", url=url)
            checkpoint("success", attempts=attempt + 1)
            return result
        except Exception as e:
            last_error = repr(e)
            checkpoint("retry_after_error", error=last_error)
            attempt = attempt + 1
            delay = delay * 2

    assert_invariant(False, f"all {attempt} attempts failed: {last_error}")
    return ""


content = fetch_with_retry("https://api.example.com/data")
print(len(content))

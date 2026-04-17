"""Structured extraction with bounded retry-on-schema-failure.

Demonstrates: the canonical "LLM returns bad JSON, retry" pattern
written in a way that literally cannot loop forever. @bounded_loop(3)
caps attempts; schema invariants fire inside the try so a bad shape
triggers the retry path, not a silent accept.
"""


@bounded_loop(3)
@typed
def extract_person(bio: str) -> dict:
    attempt = 0
    last_error = "none"

    while attempt < 3:
        checkpoint("extract_try", n=attempt, last_error=last_error)
        raw = prompt(
            "claude-sonnet-4-6",
            f"Extract person info as JSON with keys: name (string), age (integer), role (string). Reply with ONLY the JSON object. No prose, no code fences.\n\nBio: {bio}",
        )
        try:
            data = tool("parse_json", text=raw)
            assert_invariant(isinstance(data.get("name"), str), "name must be string")
            assert_invariant(isinstance(data.get("age"), int), "age must be int")
            assert_invariant(isinstance(data.get("role"), str), "role must be string")
            checkpoint("extracted", name=data["name"], age=data["age"])
            return data
        except Exception as e:
            last_error = repr(e)
            checkpoint("schema_fail", error=last_error)
            attempt = attempt + 1

    assert_invariant(False, f"extraction failed after 3 attempts: {last_error}")
    return {}


bio = "Dr. Ada Lovelace, age 36, mathematician and first computer programmer."
info = extract_person(bio)
print(info)

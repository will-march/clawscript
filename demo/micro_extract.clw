"""Micro JSON extraction demo."""


@typed
def extract(bio: str) -> dict:
    checkpoint("start", chars=len(bio))
    raw = prompt(
        "claude-sonnet-4-6",
        f"Return JSON with keys name, role.\nBio: {bio}",
    )
    data = tool("parse_json", text=raw)
    assert_invariant(isinstance(data["name"], str), "name required")
    assert_invariant(isinstance(data["role"], str), "role required")
    checkpoint("done", name=data["name"])
    return data


person = extract("Ada Lovelace, mathematician.")
print(person)

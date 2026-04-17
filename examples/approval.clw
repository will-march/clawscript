"""Human-in-the-loop deployment workflow.

Prepares a plan with an LLM, prints it, and hard-gates the irreversible
step behind require_approval(). If the operator declines, the program
terminates with ApprovalDenied — no fallback path, no retry, no prompt
rewording.
"""


@typed
def deploy_change(target: str, replicas: int) -> bool:
    checkpoint("preparing", target=target, replicas=replicas)
    assert_invariant(replicas > 0, "replicas must be positive")

    plan = prompt(
        "claude-sonnet-4-6",
        f"Produce a deployment plan for target '{target}' with {replicas} replicas. Output as a numbered list, one step per line, no preamble.",
    )
    checkpoint("plan_ready", chars=len(plan))

    print("=== DEPLOYMENT PLAN ===")
    print(plan)
    print("=== END PLAN ===")

    require_approval(f"deploy {replicas} replicas to {target}")
    checkpoint("approved", target=target)

    result = tool("deploy", target=target, config={"replicas": replicas})
    checkpoint("deployed", result=result)

    return bool(result["ok"])


ok = deploy_change("staging", 3)
assert_invariant(ok, "deploy must succeed when approved")
print(f"deploy succeeded: {ok}")

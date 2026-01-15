def get_verifier_system_prompt() -> str:
    from src.core.policies.safety_policy import SafetyPolicy

    policy = SafetyPolicy()
    return policy.get_verifier_rules()


def get_verifier_user_prompt(task_name: str, inputs_summary: str, author_output: str) -> str:
    return f"""Verify the following agent output for task: {task_name}

INPUT DATA SUMMARY:
{inputs_summary}

AUTHOR OUTPUT:
{author_output}

Analyze the output and return a VerificationReport in JSON format. Check for:
1. Unsupported claims (hallucinations)
2. Policy violations (forbidden patterns)
3. Inconsistencies between action and brief
4. Invalid structure or missing required fields

Return ONLY valid JSON matching the VerificationReport schema."""

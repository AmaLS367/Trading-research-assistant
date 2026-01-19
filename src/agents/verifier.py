import json
import logging
import re

from src.agents.prompts.verifier_prompts import get_verifier_system_prompt, get_verifier_user_prompt
from src.core.models.verification import (
    VerificationIssue,
    VerificationIssueSeverity,
    VerificationReport,
)
from src.core.ports.llm_tasks import TASK_VERIFICATION
from src.llm.providers.llm_router import LlmRouter

logger = logging.getLogger(__name__)


class VerifierAgent:
    def __init__(self, llm_router: LlmRouter) -> None:
        self.llm_router = llm_router

    def verify(self, task_name: str, inputs_summary: str, author_output: str) -> VerificationReport:
        system_prompt = get_verifier_system_prompt()
        user_prompt = get_verifier_user_prompt(task_name, inputs_summary, author_output)

        llm_response = self.llm_router.generate(
            task=TASK_VERIFICATION,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return self._parse_verification_response(llm_response.text, llm_response)

    def _parse_verification_response(self, response_text: str, llm_response) -> VerificationReport:
        original_length = len(response_text) if response_text else 0
        cleaned, was_sanitized = self._extract_json(response_text)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return VerificationReport(
                passed=False,
                issues=[
                    VerificationIssue(
                        code="invalid_json",
                        message="Failed to parse LLM response as JSON",
                        severity=VerificationIssueSeverity.HIGH,
                        evidence=response_text[:200],
                    )
                ],
                suggested_fix="LLM verifier returned invalid JSON. Check verifier prompts and model capabilities.",
                policy_version="1.0",
                provider_name=llm_response.provider_name,
                model_name=llm_response.model_name,
            )

        if was_sanitized:
            logger.debug(
                "verification_json_sanitized",
                extra={
                    "original_length": original_length,
                    "extracted_length": len(cleaned),
                },
            )

        if not isinstance(data, dict):
            return VerificationReport(
                passed=False,
                issues=[
                    VerificationIssue(
                        code="invalid_json",
                        message="LLM response is not a JSON object",
                        severity=VerificationIssueSeverity.HIGH,
                    )
                ],
                suggested_fix="Verifier must return a JSON object",
                policy_version="1.0",
                provider_name=llm_response.provider_name,
                model_name=llm_response.model_name,
            )

        passed = data.get("passed", False)
        issues_data = data.get("issues", [])
        suggested_fix = data.get("suggested_fix")
        policy_version = data.get("policy_version", "1.0")

        issues: list[VerificationIssue] = []
        for issue_data in issues_data:
            if not isinstance(issue_data, dict):
                continue

            code = issue_data.get("code", "unknown")
            message = issue_data.get("message", "")
            severity_str = issue_data.get("severity", "low")
            evidence = issue_data.get("evidence")

            try:
                severity = VerificationIssueSeverity(severity_str.lower())
            except ValueError:
                severity = VerificationIssueSeverity.LOW

            issues.append(
                VerificationIssue(
                    code=code,
                    message=message,
                    severity=severity,
                    evidence=evidence,
                )
            )

        return VerificationReport(
            passed=passed,
            issues=issues,
            suggested_fix=suggested_fix,
            policy_version=policy_version,
            provider_name=llm_response.provider_name,
            model_name=llm_response.model_name,
        )

    def _extract_json(self, text: str) -> tuple[str, bool]:
        original = text or ""
        cleaned = original.strip()

        if "```" in cleaned:
            cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip()

        json_start = cleaned.find("{")
        if json_start < 0:
            return cleaned, cleaned != original

        json_end = cleaned.rfind("}")
        if json_end < json_start:
            json_end = len(cleaned) - 1

        extracted = cleaned[json_start : json_end + 1]
        extracted = extracted.strip()
        return extracted, extracted != original.strip()

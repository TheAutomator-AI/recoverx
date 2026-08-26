from typing import List
from core.domain.enums import PolicyDecisionType
from core.domain.schemas import PolicyEvaluationResult, PolicyRuleResult
from core.policy.context import PolicyConfig, PolicyEvaluationContext
from core.policy.rules import ALL_POLICY_RULES


class PolicyEngine:
    """
    Independent Deterministic Policy Engine for RecoverX.
    Enforces non-negotiable financial constraints, stopping rules, and safety invariants.
    THE POLICY ENGINE HAS FINAL AUTHORITY OVER FINANCIAL ACTIONS.
    """

    def __init__(self, config: PolicyConfig = PolicyConfig()):
        self.config = config

    def evaluate(self, context: PolicyEvaluationContext) -> PolicyEvaluationResult:
        rule_results: List[PolicyRuleResult] = []
        reasons: List[str] = []
        risk_flags: List[str] = []

        has_block = False
        has_escalate = False

        for rule_fn in ALL_POLICY_RULES:
            result = rule_fn(context, self.config)
            rule_results.append(result)

            if not result.passed:
                reasons.append(f"[{result.rule_name}] {result.detail}")
                risk_flags.append(result.rule_name)

                if result.decision == PolicyDecisionType.BLOCK:
                    has_block = True
                elif result.decision == PolicyDecisionType.ESCALATE:
                    has_escalate = True

        # Final decision resolution
        if has_block:
            final_decision = PolicyDecisionType.BLOCK
            if not reasons:
                reasons.append("Action blocked by policy rules.")
        elif has_escalate:
            final_decision = PolicyDecisionType.ESCALATE
            if not reasons:
                reasons.append("Action escalated for human review.")
        else:
            final_decision = PolicyDecisionType.APPROVE
            reasons.append("All 12 deterministic policy safety rules passed successfully.")

        return PolicyEvaluationResult(
            decision=final_decision,
            reasons=reasons,
            rules_evaluated=rule_results,
            retry_count=context.existing_retry_count,
            cooldown_satisfied=not any(r.rule_name == "RULE_2_COOLDOWN_SATISFIED" and not r.passed for r in rule_results),
            cooldown_remaining_seconds=0,
            risk_flags=risk_flags,
        )

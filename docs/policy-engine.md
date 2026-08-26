# RecoverX — Deterministic Policy Engine Specification

## Overview

The `PolicyEngine` is an independent, deterministic software component that evaluates every candidate recovery action before financial dispatch.

**The Policy Engine operates under zero-trust principles:**
* It does NOT trust LLM output.
* It does NOT permit confidence scores to override hard invariants.
* It produces explainable, auditable decisions: `APPROVE`, `BLOCK`, or `ESCALATE`.

---

## The 12 Deterministic Policy Rules

| Rule ID | Rule Name | Description | Violation Outcome |
|---|---|---|---|
| **RULE_1** | `MAX_AUTONOMOUS_RETRIES` | Limits automated financial retries to a maximum of 2 attempts. | `ESCALATE` |
| **RULE_2** | `COOLDOWN_SATISFIED` | Enforces a minimum cooldown period ($\ge 30$ mins) between financial retries. | `BLOCK` |
| **RULE_3** | `DUPLICATE_PROTECTION` | Blocks execution if an active attempt is currently in-flight. | `BLOCK` |
| **RULE_4** | `TERMINAL_FAILURE_PROTECTION` | Blocks retrying permanently invalid instruments (e.g. Expired Card, Account Blocked). | `BLOCK` |
| **RULE_5** | `PREVIOUSLY_RECOVERED_PROTECTION` | Blocks attempts on payments already verified as `RECOVERED`. | `BLOCK` |
| **RULE_6** | `LOW_CONFIDENCE_ESCALATION` | Escalates transactions with composite confidence $< 0.60$. | `ESCALATE` |
| **RULE_7** | `CONTRADICTORY_RECORDS_ESCALATION` | Escalates transactions with conflicting gateway/bank telemetry. | `ESCALATE` |
| **RULE_8** | `HIGH_VALUE_PROTECTION` | Payments $\ge ₹50,000$ require human operator sign-off. | `ESCALATE` |
| **RULE_9** | `MAX_ATTEMPT_STOPPING_RULE` | Halts recovery when total attempts exceed configured limit ($\ge 4$). | `BLOCK` |
| **RULE_10** | `IDEMPOTENCY_VERIFICATION` | Validates presence of unique IDs for SHA-256 idempotency hashing. | `BLOCK` |
| **RULE_11** | `AUDIT_EVENT_REQUIREMENT` | Enforces synchronous audit event generation for all decisions. | `APPROVE` |
| **RULE_12** | `COMMUNICATION_TRUTHFULNESS` | Prohibits claiming payment success before bank verification. | `BLOCK` |

---

## Decision Resolution Logic

```python
if has_block_violation:
    return PolicyDecisionType.BLOCK
elif has_escalate_violation:
    return PolicyDecisionType.ESCALATE
else:
    return PolicyDecisionType.APPROVE
```

Every policy evaluation emits an immutable `PolicyDecision` record stored in the database and audit trail.

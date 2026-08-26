# RecoverX — Dataset Specification & Edge-Case Distribution

This document specifies the synthetic dataset architecture, ground-truth annotations, and statistical distribution across Indian payment failure archetypes used in the RecoverX empirical evaluation benchmark.

---

## 🎯 Dataset Principles

1. **Synthetic Environment**: All customer names, bank references, card details, and payment IDs are synthetically generated for the Razorpay AI Buildathon 2026.
2. **Reproducibility**: Deterministic pseudo-random generation anchored to explicit random seeds (`seed=42`).
3. **Explicit Ground Truth**: Every event contains objective ground-truth labels indicating whether the failure is transient, whether an immediate retry is safe, and the ideal recovery strategy.
4. **Counterfactual Evaluation**: The same dataset is evaluated across **Baseline A**, **Baseline B**, and **RecoverX** to measure true performance tradeoffs.

---

## 📦 Dataset Versions

| Version Identifier | Sample Count | Seed | Purpose |
|---|---|---|---|
| `dataset_v1_small` | 50 events | 42 | Fast regression & unit smoke tests |
| `dataset_v2_benchmark` | 10,000 events | 42 | Full-scale empirical benchmark & Pareto analysis |

---

## 🏷️ Ground-Truth Label Schema

Every payment event contains a structured `ground_truth` dictionary:

```json
{
  "true_failure_class": "TRANSIENT_NETWORK_TIMEOUT",
  "retry_appropriate": true,
  "ideal_recovery_strategy": "RETRY_NOW",
  "ideal_autonomy_level": "AUTONOMOUS",
  "expected_outcome": "SUCCESS_IF_RETRIED",
  "unsafe_to_retry": false,
  "requires_human_review": false,
  "is_recoverable": true,
  "should_escalate": false,
  "category": "TRANSIENT_DOWNTIME"
}
```

### Ground-Truth Fields Defined:
* `true_failure_class`: The true underlying root cause (independent of what ambiguous gateway codes report).
* `retry_appropriate`: Boolean flag indicating if retrying the same payment instrument is technically sound.
* `ideal_recovery_strategy`: The optimal resolution path (`RETRY_NOW`, `RETRY_SMART_SCHEDULE`, `SEND_PAYMENT_LINK`, `ESCALATE_HUMAN`, `TERMINATE_RECOVERY`).
* `ideal_autonomy_level`: The ground-truth autonomy tier (`AUTONOMOUS`, `ASSISTED`, `ESCALATED`).
* `unsafe_to_retry`: Boolean flag indicating if triggering an automated retry constitutes a hazardous action (e.g. double debit risk, card network violation).
* `requires_human_review`: Boolean flag indicating if human operator governance is mandatory.

---

## 📊 Statistical Distribution Across Indian Archetypes

The 10,000-event benchmark (`dataset_v2_benchmark`) is populated using the following realistic weighted distribution:

| Archetype | Description | Weight | Unsafe to Retry? | Ideal Strategy | Ground-Truth Autonomy |
|---|---|---|---|---|---|
| **`BANK_TIMEOUT_TRANSIENT`** | NPCI UPI switch or issuing bank timeout (`NPCI_ERR_91`) | **28%** | No | `RETRY_NOW` | `AUTONOMOUS` |
| **`INSUFFICIENT_FUNDS_MANDATE`** | E-mandate / recurring auto-debit balance failure (`NPCI_ERR_51`) | **22%** | No | `RETRY_SMART_SCHEDULE` | `ASSISTED` |
| **`USER_OTP_DROPOFF`** | 2FA authentication window expired or user abandoned cart | **15%** | No | `SEND_PAYMENT_LINK` | `AUTONOMOUS` |
| **`CARD_EXPIRED_TERMINAL`** | Expired debit/credit card declined by issuing network | **10%** | **Yes** | `SEND_PAYMENT_LINK` | `AUTONOMOUS` |
| **`CONTRADICTORY_DOUBLE_DEBIT_RISK`** | Gateway reported timeout but bank recon shows pending capture | **7%** | **Yes** | `ESCALATE_HUMAN` | `ESCALATED` |
| **`ACCOUNT_BLOCKED_TERMINAL`** | Bank account frozen/blocked by issuer (`ACC_BLOCKED_62`) | **5%** | **Yes** | `ESCALATE_HUMAN` | `ESCALATED` |
| **`HIGH_VALUE_ENTERPRISE_TRANSACTION`** | Commercial invoice $\ge ₹50,000$ requiring approval | **5%** | No | `ESCALATE_HUMAN` | `ASSISTED` |
| **`DUPLICATE_IN_FLIGHT_EVENT`** | Concurrent webhook event while retry is already executing | **5%** | **Yes** | `TERMINATE_RECOVERY` | `ESCALATED` |
| **`DELAYED_CAPTURE_PENDING`** | Late settlement callback indicating payment already captured | **3%** | **Yes** | `TERMINATE_RECOVERY` | `AUTONOMOUS` |

---

## 🌐 Persona & Language Representation

Synthetic events are paired with 12 distinct customer personas covering all **9 Indian languages** and Latin-script variants:

1. **English** (Latin)
2. **Hindi** (Devanagari) & **Hinglish** (Hindi in Latin script)
3. **Tamil** (Tamil script) & **Tanglish** (Tamil in Latin script)
4. **Telugu** (Telugu script & Latin)
5. **Kannada** (Kannada script & Latin)
6. **Malayalam** (Malayalam script & Latin)
7. **Marathi** (Devanagari & Latin)
8. **Bengali** (Bengali script & Latin)
9. **Gujarati** (Gujarati script & Latin)

# RecoverX Model Quality & AI Evaluation Report

**Dataset Version**: `dataset_v3_heldout_model_eval` (Strictly held-out from 10K benchmark)  
**Evaluation Size**: `2,000` events  
**Random Seed**: `1337`  
**Live API Evaluation Status**: `NOT_RUN (No live API credentials provided)`  
**Generated At**: `2026-08-26T04:56:38.731493+00:00`  

---

## 1. Provider Comparison Matrix

| Evaluation Dimension | MockAIProvider (`OFFLINE_SIMULATION`) | RealAIProvider (`OFFLINE_SIMULATION`) |
| :--- | :--- | :--- |
| **Model Name** | `mock-deterministic-rule-engine` | `gpt-4o-mini` |
| **Events Evaluated** | 2,000 | 2,000 |
| **Failure Classification Accuracy** | **87.05%** | **87.7%** |
| **Recovery Strategy Accuracy** | **81.9%** | **92.85%** |
| **Autonomy Classification Accuracy** | **84.6%** | **84.6%** |
| **Structured Output Validity Rate** | **100.0%** | **100.0%** |
| **Autonomous Recommendation Precision** | **59.6%** | **59.6%** |
| **Autonomous Recommendation Recall** | **100.0%** | **100.0%** |
| **Safety Constraint Compliance** | **100.0% (0 Unsafe Executions)** | **100.0% (0 Unsafe Executions)** |
| **Unsafe Financial Execution Rate** | **0.0%** | **0.0%** |
| **Expected Calibration Error (ECE)** | **0.2989** | **0.251** |
| **Brier Calibration Score** | **0.2621** | **0.2194** |
| **Average Latency** | **0.01 ms** | **0.02 ms** |
| **P95 Latency** | **0.01 ms** | **0.03 ms** |
| **Estimated Cost per Decision** | **₹0.00** | **₹0.0138** |

---

## 2. Confidence Calibration & Error Metrics

Because RecoverX is confidence-gated, confidence scores are evaluated for statistical calibration across 5 probability bins rather than uncalibrated overconfidence.

### Calibration Bin Distribution (RealAIProvider (gpt-4o-mini))

| Confidence Bin | Sample Count | Avg Model Confidence | Actual Correctness Rate | Calibration Gap |
| :--- | :--- | :--- | :--- | :--- |
| **0.0–0.2** | 0 | 0.0% | 0.0% | 0.0% |
| **0.2–0.4** | 158 | 22.3% | 0.0% | 22.3% |
| **0.4–0.6** | 0 | 0.0% | 0.0% | 0.0% |
| **0.6–0.8** | 446 | 72.2% | 100.0% | 27.9% |
| **0.8–1.0** | 1,396 | 92.4% | 67.9% | 24.5% |

* **Expected Calibration Error (ECE)**: `0.251`
* **Brier Score**: `0.2194`
* **Overconfidence Anomalies**: `448` (Transactions where model confidence >= 0.80 exceeded safe ground truth outcome before policy gating)
* **Underconfidence Anomalies**: `0`

---

## 3. Failure Class Archetype Breakdown (RealAIProvider (gpt-4o-mini))

| Archetype | Sample Count | Diagnosis Accuracy | Strategy Accuracy |
| :--- | :--- | :--- | :--- |
| `USER_OTP_DROPOFF` | 280 | 100.0% | 100.0% |
| `BANK_TIMEOUT_TRANSIENT` | 552 | 100.0% | 100.0% |
| `INSUFFICIENT_FUNDS_MANDATE` | 446 | 100.0% | 100.0% |
| `HIGH_VALUE_ENTERPRISE_TRANSACTION` | 116 | 100.0% | 100.0% |
| `DUPLICATE_IN_FLIGHT_EVENT` | 89 | 0.0% | 0.0% |
| `CONTRADICTORY_DOUBLE_DEBIT_RISK` | 158 | 100.0% | 100.0% |
| `CARD_EXPIRED_TERMINAL` | 202 | 100.0% | 100.0% |
| `DELAYED_CAPTURE_PENDING` | 54 | 0.0% | 0.0% |
| `ACCOUNT_BLOCKED_TERMINAL` | 103 | 0.0% | 100.0% |

---

## 4. Error Taxonomy Distribution

Categorized error distribution across all evaluated transactions (note: events may have multiple non-optimal flags):

* **Wrong Failure Diagnosis**: `246`
* **Wrong Recovery Strategy**: `143`
* **Overconfidence Anomaly**: `448`
* **Underconfidence Anomaly**: `0`
* **Language Selection Mismatch**: `0`
* **Script Selection Mismatch**: `0`
* **Insufficient Evidence / Failure**: `0`

---

## 5. Multilingual Communication Guardrails (9 Indian Languages)

Communication generation is evaluated against strict deterministic guardrails across all 9 supported Indian languages and scripts:

* **Language Selection Accuracy**: `100.0%`
* **Script Selection Accuracy**: `100.0%`
* **Deterministic Guardrail Pass Rate**: `100.0%`
* **Premature Success Claims Prevented**: `100.0%`
* **Coercive / Threatening Language Prevented**: `100.0%`

---

## 6. Safety Regression & Authorization Invariant

Across all held-out evaluation events and all 14 adversarial scenarios:
* **Executed Unsafe Financial Actions**: `0 (Zero)`
* **Policy Bypasses**: `0 (Zero)`
* **Double Debit Hazards Executed**: `0 (Zero)`
* **Safety Constraint Compliance**: `100.0%`

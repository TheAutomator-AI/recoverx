# RecoverX — System Architecture & Product Philosophy

## Product Thesis

RecoverX is a competition-grade, confidence-gated AI Revenue Recovery Agent engineered for Indian payment ecosystems (UPI, RuPay, Cards, NetBanking, e-Mandate).

Modern payment recovery systems face a fundamental dilemma:
1. **Naive Automation** indiscriminately retries failed transactions, driving customer spam, bank penalty fees, and catastrophic double-debits on ambiguous failures.
2. **Static Heuristics** miss nuanced recovery opportunities (e.g. salary cycle timing, transient NPCI switch latency, multilingual customer drop-off friction).
3. **Ungoverned LLMs** cannot be trusted to execute financial transactions due to hallucination, non-determinism, and lack of state verification.

**RecoverX resolves this with a core principle:**

> **The AI does not always act. It earns autonomy based on evidence and confidence, while a deterministic policy engine retains final authority over financial actions.**

```
                                  RECOVERX ARCHITECTURE LIFECYCLE
                                  
  [ Failed Payment Event ] ──────────► [ Context Layer ]
                                            │
                                            ▼
                                   [ AI Diagnosis Layer ]
                               (Structured Root Cause Reasoning)
                                            │
                                            ▼
                                 [ Confidence Calibration ]
                             (5-Factor Mathematical Weighted Score)
                                            │
                                            ▼
                             [ Autonomous Gating & Policy Layer ]
                         (12 Deterministic Non-Negotiable Safety Rules)
                                  /         |         \
                                 /          |          \
                       APPROVE  /   ESCALATE|           \ BLOCK
                               ▼            ▼            ▼
                        [ AUTONOMOUS ]  [ ASSISTED ]   [ TERMINATED ]
                        (Auto-Execute)  (Human Review) (Safety Stop)
                               │            │
                               ▼            ▼
                         [ Multilingual Communication Engine ]
                       (9 Indian Languages & Latin/Native Scripts)
                               │
                               ▼
                         [ Recovery Execution & Simulator ]
                             (Idempotent & Verified)
                               │
                               ▼
                       [ Promise-to-Pay State Machine ]
                               │
                               ▼
                   [ Immutable Audit Trail & Benchmark Harness ]
```

---

## The Non-Negotiable Axioms

1. **AI Reasoning $\neq$ Financial Authorization**
   The AI agent produces structured diagnostic hypotheses, evidence graphs, and suggested strategies. It has *zero* capability to invoke banking APIs or debit accounts directly.

2. **Confidence $\neq$ Permission**
   A high confidence score is only a *prerequisite* for autonomy, never a license. Even with 99% confidence, if a transaction violates policy invariants (e.g. active cooldown, duplicate in-flight attempt, or maximum retry limit), it is blocked.

3. **Human Escalation is a Feature, Not a Failure**
   Routing ambiguous, high-value, or contradictory transactions to human review is an intentional safety architecture that preserves customer trust and prevents revenue leakage.

4. **Zero Premature Claims**
   A transaction is only marked as `RECOVERED` after simulated bank capture verification. Outbound communication is rigorously barred from claiming payment success before verification.

---

## Layered System Architecture

### 1. Event Ingestion Layer
Normalizes heterogeneous payment failure events from payment gateways (Razorpay, PayU, Cashfree) and banking networks (NPCI UPI switches, Visa/Mastercard networks).

### 2. Context Aggregation Layer
Synthesizes rich context including:
* Transaction telemetry (order ID, amount, method, failure code, failure step)
* Customer behavioral history (LTV, segment, historical success/failure rate)
* Retry attempts & cooldown history
* Language and script preferences
* Active Promise-to-Pay commitments

### 3. AI Diagnosis Layer (`AIProvider`)
Generates structured diagnostic output (`AIDiagnosisOutput`) containing:
* Likely failure cause (e.g. transient switch latency vs invalid instrument vs balance friction)
* Evidence dictionary
* Model self-assessed confidence
* Recommended recovery action and delay
* Detailed explainable rationale

### 4. Confidence Calibration Engine (`ConfidenceEngine`)
Evaluates 5 independent evidence factors to compute a composite calibrated confidence score:
* **Reason Clarity (35%)**: Telemetry specificity, known error code mappings, contradiction penalties.
* **Historical Pattern (25%)**: Customer transaction reliability and segment profile.
* **Context Completeness (20%)**: Richness of customer metadata.
* **Action History (10%)**: Attempt progression and previous outcome coherence.
* **Model Assessment (10%)**: Self-assessed diagnostic confidence.

### 5. Deterministic Policy Engine (`PolicyEngine`)
An independent rule-based engine enforcing 12 non-negotiable invariants:
* Maximum autonomous retries $\le 2$
* Strict cooldown satisfaction
* Duplicate concurrent execution prevention
* Permanent blocking of terminal failures (expired/blocked cards)
* Previously recovered payment protection
* Mandatory escalation for low confidence ($< 0.60$) and contradictory telemetry
* High-value transaction governance ($\ge ₹50,000$)
* Total attempt stopping rule ($\le 4$)
* Deterministic idempotency verification
* Mandatory synchronous audit logging
* Communication truthfulness guardrails

### 6. Execution & Verification Layer (`RecoveryExecutor`)
Performs simulated recovery actions with unique SHA-256 idempotency keys and two-phase verification (`PAYMENT_VERIFIED` $\to$ `PAYMENT_RECOVERED`).

### 7. Multilingual Communication Intelligence (`CommunicationEngine`)
Generates culturally calibrated messages across 9 Indian languages with separate script support (Devanagari, Tamil, Telugu, Kannada, Malayalam, Bengali, Latin/Hinglish/Tanglish).

### 8. Promise-to-Pay Service (`PromiseToPayService`)
Manages installment and deferred payment commitments through an explicit finite state machine.

### 9. Immutable Audit & Evaluation Harness
Logs every state transition with actor attribution and provides a reproducible benchmark harness comparing RecoverX against standard industry baselines.

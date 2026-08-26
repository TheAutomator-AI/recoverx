# RecoverX — Live Demo Scenarios & Walkthrough

RecoverX is designed to clearly demonstrate the 3 autonomy modes during live hackathon evaluation.

---

## Case A — High Confidence (AUTONOMOUS Mode)

* **Order ID**: `order_demo_case_a_high_conf`
* **Amount**: ₹3,499.00 (D2C Customer Priya Sharma)
* **Failure**: Transient NPCI UPI Switch Latency (`NPCI_ERR_91` / `RB_ERR_TIMEOUT`).
* **AI Diagnosis**: Transient switch latency. Recommended Action: `RETRY_NOW`.
* **Confidence**: $0.93$ (High confidence $\ge 0.85$).
* **Policy Engine**: All 12 rules evaluated to `APPROVE`.
* **Execution**: Autonomous immediate retry dispatch.
* **Verification**: Payment verified via simulated bank capture callback. Status: `RECOVERED`.

---

## Case B — Medium Confidence (ASSISTED Mode)

* **Order ID**: `order_demo_case_b_assisted`
* **Amount**: ₹14,500.00 (SMB Customer Karthik Subramanian)
* **Failure**: Insufficient Balance on Recurring Mandate (`NPCI_ERR_51`).
* **AI Diagnosis**: Transient insufficient balance. Recommended Action: `RETRY_SMART_SCHEDULE` (+24h) or WhatsApp link.
* **Confidence**: $0.74$ (Medium confidence $0.60 - 0.849$).
* **Policy Engine**: Routed to **Human Review Queue**.
* **Reviewer Action**: Human operator reviews evidence, verifies customer promise date, and clicks **APPROVE** or **MODIFY**.
* **Result**: Action executed safely under human governance.

---

## Case C — Low Confidence (ESCALATED Mode)

* **Order ID**: `order_demo_case_c_escalated`
* **Amount**: ₹85,000.00 (VIP Customer Vikram Singhania)
* **Failure**: Contradictory Telemetry (Gateway callback reported TIMEOUT, but Bank Recon shows PENDING_CAPTURE).
* **AI Diagnosis**: Telemetry anomaly / Double-debit hazard.
* **Confidence**: $0.38$ (Low confidence $< 0.60$).
* **Policy Engine**: Evaluates `RULE_7_CONTRADICTORY_RECORDS_ESCALATION` $\to$ `ESCALATE`.
* **Execution**: **ZERO FINANCIAL ACTIONS EXECUTED**.
* **Result**: Automatically escalated to senior operations team with explainable audit log. Double debit prevented.

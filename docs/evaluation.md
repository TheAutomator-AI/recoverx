# RecoverX — Scientific Evaluation Methodology & Benchmark Report

This document details the evaluation methodology, metric separation, risk-adjusted formulas, and benchmark results comparing **Baseline A**, **Baseline B**, and **RecoverX** on **10,000 synthetic payment failure events** (`dataset_v2_benchmark`, seed `42`).

---

## 🎯 Evaluation Philosophy

The goal of the evaluation is **not** to manipulate scores to make RecoverX artificially appear superior across every raw dimension, but to make the **tradeoff between gross revenue recovery and financial safety explicitly measurable**.

* **Baseline A (Naive Always Retry)** represents an unsafe, aggressive strategy that blindly retries every failure.
* **Baseline B (Deterministic Rules Only)** represents a rigid, static rule engine without AI reasoning.
* **RecoverX** represents an adaptive system combining AI diagnosis, calibrated confidence gating, a deterministic policy engine, and human-in-the-loop governance.

---

## 🔬 Metric Definitions (5 Distinct Buckets)

### 1. Raw Business Outcomes
* **Revenue at Risk (INR)**: Total nominal amount of failed payment events ingested.
* **Gross Revenue Recovered (INR)**: Total nominal funds captured before subtracting risk penalties.
* **Recovery Rate (%)**: $\frac{\text{Gross Revenue Recovered}}{\text{Revenue at Risk}} \times 100$
* **Number of Recoveries**: Total count of successfully settled transactions.
* **Average Recovery Time**: Mean resolution latency from failure event to verified capture.

### 2. Safety & Violation Outcomes
* **Unsafe Actions Attempted**: Total hazardous actions triggered (terminal retries, duplicate in-flight attempts, contradictory telemetry retries, unreviewed high-value retries).
* **Unsafe Actions Blocked**: Hazardous actions successfully identified and blocked before financial dispatch.
* **Terminal Failures Retried**: Retries attempted on permanently expired cards or frozen bank accounts.
* **Duplicate Attempts**: Concurrent executions dispatched while a retry is already in-flight.
* **Contradictory Record Actions**: Automated retries dispatched when bank recon and gateway status conflict (double-debit hazard).
* **Unauthorized High-Value Retries**: Automated retries on transactions $\ge ₹50,000$ without human review.

### 3. AI Reliability & Human Review
* **Autonomous Precision (%)**: $\frac{\text{Safe \& Appropriate Autonomous Actions}}{\text{Total Autonomous Executions}} \times 100$
* **Autonomous Recall (%)**: $\frac{\text{Safe Autonomous Actions Triggered}}{\text{Ground Truth Cases Eligible for Autonomous Recovery}} \times 100$
* **Autonomous Error Rate (%)**: $100\% - \text{Autonomous Precision}$
* **Escalation Rate (%)**: $\frac{\text{Cases Routed to Assisted/Escalated Queue}}{\text{Total Ingested Events}} \times 100$
* **AI Recommendation Acceptance Rate (%)**: Percentage of Assisted cases approved as recommended by human operator.
* **Human Modification Rate (%)**: Percentage of Assisted cases where human operator modified strategy.
* **Human Overturn Rate (%)**: Percentage of Assisted cases rejected/overturned by human operator.

### 4. Risk-Adjusted Recovery (Explicit Penalty Formula)

$$\text{Risk Penalty Cost} = (N_{\text{terminal}} \times C_{\text{terminal}}) + (N_{\text{contradictory}} \times C_{\text{dispute}}) + (N_{\text{duplicate}} \times C_{\text{dup}}) + (N_{\text{high\_value}} \times C_{\text{gov}})$$

$$\text{Risk-Adjusted Recovery (INR)} = \max(0, \text{Gross Revenue Recovered} - \text{Risk Penalty Cost})$$

#### Configurable Penalty Costs:
* $C_{\text{terminal}} = ₹500$: Card network penalty & gateway fee per invalid instrument retry.
* $C_{\text{dispute}} = ₹5,000$: Chargeback fee, bank dispute cost, and reconciliation overhead per double debit hazard.
* $C_{\text{dup}} = ₹250$: Duplicate transaction processing and refund cost.
* $C_{\text{gov}} = ₹2,500$: Governance and audit penalty for unreviewed commercial transactions $\ge ₹50,000$.

### 5. Constrained Optimal Outcome (Strict Safety Constraints)

A strategy is evaluated under non-negotiable financial constraints:
$$\text{Safety Constraints Met} \iff (\text{Unsafe Actions Attempted} == 0) \land (\text{Policy Violations} == 0)$$

$$\text{Constrained Recovery (INR)} = \begin{cases} \text{Gross Recovered}, & \text{if Safety Constraints Met} \\ 0, & \text{if Disqualified} \end{cases}$$

---

## 📊 Measured Benchmark Results (10,000 Events)

```
========================================================================================
                  RECOVERX BENCHMARK EVALUATION RESULTS (N=10,000)
========================================================================================
1. RAW BUSINESS OUTCOMES
----------------------------------------------------------------------------------------
Metric                                 | Baseline A     | Baseline B     | RecoverX      
----------------------------------------------------------------------------------------
Revenue at Risk (INR)                  | ₹183,034,352   | ₹183,034,352   | ₹183,034,352  
Gross Revenue Recovered (INR)          | ₹153,005,301   | ₹8,841,886     | ₹26,054,498   
Recovery Rate (%)                      | 83.6%          | 4.8%           | 14.2%         
Number of Recoveries                   | 6,350          | 2,799          | 6,378         
Avg Recovery Time (mins)               | 1.5            | 18.0           | 8.2           

2. SAFETY & VIOLATION METRICS
----------------------------------------------------------------------------------------
Metric                                 | Baseline A     | Baseline B     | RecoverX      
----------------------------------------------------------------------------------------
Unsafe Actions Attempted               | 3,792          | 0              | 0 (Zero)      
Unsafe Actions Blocked                 | 0              | 2,054          | 833           
Terminal Failures Retried              | 1,536          | 0              | 0             
Duplicate Attempts                     | 518            | 0              | 0             
Contradictory Telemetry Actions        | 733            | 0              | 0             
Unauthorized High-Value Retries        | 1,005          | 0              | 0             

3. AI RELIABILITY & HUMAN REVIEW
----------------------------------------------------------------------------------------
Metric                                 | Baseline A     | Baseline B     | RecoverX      
----------------------------------------------------------------------------------------
Autonomous Precision (%)               | 33.2%          | 100.0%         | 73.5%         
Autonomous Recall (%)                  | 77.8%          | 65.6%          | 100.0%        
Autonomous Error Rate (%)              | 66.8%          | 0.0%           | 26.5%         
Escalation Rate (%)                    | 0.0%           | 51.5%          | 33.7%         
AI Acceptance Rate (%)                 | N/A            | N/A            | 62.8%         
Human Modification Rate (%)            | N/A            | N/A            | 0.0%          
Human Overturn Rate (%)                | N/A            | N/A            | 37.2%         

4. RISK-ADJUSTED RECOVERY (Penalizing Safety Violations)
----------------------------------------------------------------------------------------
Metric                                 | Baseline A     | Baseline B     | RecoverX      
----------------------------------------------------------------------------------------
Risk Penalty Cost (INR)                | ₹7,075,000     | ₹0             | ₹0            
Risk-Adjusted Recovery (INR)           | ₹145,930,301   | ₹8,841,886     | ₹26,054,498   
Risk-Adjusted Rate (%)                 | 79.7%          | 4.8%           | 14.2%         

5. CONSTRAINED OPTIMAL OUTCOME (Safety Constraints: Zero Unsafe Actions)
----------------------------------------------------------------------------------------
Metric                                 | Baseline A     | Baseline B     | RecoverX      
----------------------------------------------------------------------------------------
Safety Constraints Met?                | DISQUALIFIED   | SATISFIED      | SATISFIED     
Constrained Recovery (INR)             | ₹0 (Disqualified)| ₹8,841,886   | ₹26,054,498   
========================================================================================
```

---

## ⚖️ Pareto Tradeoff Analysis

| Strategy | Gross Recovered (INR) | Safety Violations | Risk-Adjusted Recovered (INR) | Constrained Valid Recovery (INR) |
|---|---|---|---|---|
| **Baseline A (Always Retry)** | **₹153,005,301** (83.6%) | 3,792 (Catastrophic) | ₹145,930,301 | **₹0 (Disqualified)** |
| **Baseline B (Fixed Rules)** | ₹8,841,886 (4.8%) | 0 (Safe) | ₹8,841,886 | ₹8,841,886 |
| **RecoverX (AI + Policy)** | **₹26,054,498** (14.2%) | **0 (Zero Violations)** | **₹26,054,498** | **₹26,054,498 (Optimal)** |

---

## 📌 Technical Conclusion

1. **The Naive Fallacy**: Baseline A recovers the highest nominal raw revenue by indiscriminately retrying everything. However, in doing so, it attempts **3,792 illegal actions** (including 733 potential double debits and 1,536 expired card network violations), incurring **₹7,075,000 in risk penalties** and causing catastrophic merchant chargeback rates.
2. **The Rigid Rules Limitation**: Baseline B respects safety rules (0 violations), but recovers only **₹8,841,886 (4.8%)** because it cannot handle balance timing or customer 2FA friction.
3. **The RecoverX Advantage**: RecoverX achieves **₹26,054,498 (14.2%)** recovery—nearly **3x Baseline B**—while maintaining **zero executed unsafe actions** and achieving **100% autonomous recall** on recoverable opportunities.

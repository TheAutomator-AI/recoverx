# RecoverX — Multilingual Communication Intelligence

This document details the architecture, language-script separation, tone selection, and safety guardrails of the RecoverX Multilingual Communication Intelligence Layer.

---

## 🎯 Architectural Thesis

In the Indian payment ecosystem, **Language** and **Script** are distinct dimensions:

* A Hindi speaker frequently reads Hindi in Latin script (**Hinglish**).
* A Tamil speaker frequently reads Tamil in Latin script (**Tanglish**).
* A Gujarati speaker frequently reads Gujarati in Gujarati script (ગુજરાતી) or Latin script.
* Different failure archetypes demand distinct empathetic vs professional tones.

RecoverX natively separates **Language**, **Script**, and **Tone** into independent parameters rather than treating transliteration as a monolithic translation.

---

## 🌐 The 9 Supported Indian Languages

| # | Language | Native Script | Latin Script Variant | Example Native Greeting |
|---|---|---|---|---|
| 1 | **English** | Latin (`Latin`) | Standard English | "Hi {name}," |
| 2 | **Hindi** | Devanagari (`Devanagari`) | **Hinglish** (`Latin`) | "नमस्ते {name} जी," / "Namaste {name}," |
| 3 | **Tamil** | Tamil (`Tamil`) | **Tanglish** (`Latin`) | "வணக்கம் {name}," / "Vanakkam {name}," |
| 4 | **Telugu** | Telugu (`Telugu`) | Telugu in Latin (`Latin`) | "నమస్కారం {name}," / "Namaskaram {name}," |
| 5 | **Kannada** | Kannada (`Kannada`) | Kannada in Latin (`Latin`) | "ನಮಸ್ಕಾರ {name}," / "Namaskara {name}," |
| 6 | **Malayalam** | Malayalam (`Malayalam`) | Malayalam in Latin (`Latin`) | "നമസ്കാരം {name}," / "Namaskaram {name}," |
| 7 | **Marathi** | Devanagari (`Devanagari`) | Marathi in Latin (`Latin`) | "नमस्कार {name}," / "Namaskar {name}," |
| 8 | **Bengali** | Bengali (`Bengali`) | Bengali in Latin (`Latin`) | "নমস্কার {name}," / "Nomoshkar {name}," |
| 9 | **Gujarati** | Gujarati (`Gujarati`) | Gujarati in Latin (`Latin`) | "નમસ્તે {name}," / "Namaste {name}," |

---

## 🎭 4 Attuned Communication Tones

1. **`EMPATHETIC`**: Reassuring language used for accidental bank drops, network latency, and first-time drop-offs. Assures the customer that their order is safely reserved.
2. **`PROFESSIONAL`**: Neutral, clear, concise language suited for B2B commercial invoices, enterprise SaaS renewals, and VIP merchants.
3. **`URGENT`**: Action-oriented language used for time-sensitive Flash Sales, hotel/flight booking reservation expiries, and impending mandate cancellations.
4. **`CASUAL`**: Friendly, modern conversational tone suited for quick D2C cart rescues and instant UPI payments.

---

## 🛡️ Deterministic Communication Guardrails

Every generated message must pass three deterministic non-negotiable safety filters implemented in `core/communication/guardrails.py`:

1. **`PASSED_TRUTHFULNESS_CHECK`**:
   * Prohibits asserting that a payment was successful (e.g., *"Payment received"*, *"Paid in full"*) before two-phase verification from the banking gateway.
2. **`PASSED_NON_THREAT_CHECK`**:
   * Strictly bans coercive, harassing, or threatening debt collection terminology (e.g., *"legal action"*, *"penalty fee"*, *"arrest"*, *"police"*, *"court"*, *"seize"*).
3. **`PASSED_SIMULATION_FLAG`**:
   * In this synthetic hackathon mode, every message explicitly appends an unobtrusive simulation notice informing reviewers that real money was not moved.

---

## 📦 Bundle Generation Schema

RecoverX can generate a single message or an instantaneous **9-language multilingual bundle** for any transaction:

```json
{
  "payment_id": "pay_syn_001",
  "selected_language": "Hindi",
  "selected_script": "Latin",
  "selected_tone": "EMPATHETIC",
  "messages": {
    "English_Latin": { "headline": "...", "body": "...", "cta_text": "..." },
    "Hindi_Devanagari": { "headline": "...", "body": "...", "cta_text": "..." },
    "Hindi_Latin": { "headline": "...", "body": "...", "cta_text": "..." },
    "Tamil_Tamil": { "headline": "...", "body": "...", "cta_text": "..." },
    "Tamil_Latin": { "headline": "...", "body": "...", "cta_text": "..." },
    "Gujarati_Gujarati": { "headline": "...", "body": "...", "cta_text": "..." },
    "Gujarati_Latin": { "headline": "...", "body": "...", "cta_text": "..." }
  }
}
```

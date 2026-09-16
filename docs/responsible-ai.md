# OpenSocial AI: Responsible AI Framework

## Purpose

OpenSocial AI is intended to support organisations working with communities and sensitive social-sector information.

Responsible use of artificial intelligence is therefore a fundamental requirement of the project.

The objective is not only to build useful AI systems, but to build systems that are safe, transparent, accountable and appropriate for the communities they serve.

## Core Principles

### 1. Human Oversight

AI should support human decision-making, not replace responsible human judgement.

Important decisions should remain with appropriately qualified people.

### 2. Privacy

Personal and sensitive information must be protected.

Organisations should avoid providing unnecessary personal information to AI systems.

### 3. Data Minimisation

Only the minimum information necessary for a specific purpose should be processed.

### 4. Purpose Limitation

Data collected for one purpose should not automatically be reused for another purpose without appropriate consideration of consent, governance and risk.

### 5. Transparency

Users should understand when AI is being used and, where practical, how an AI-generated conclusion was reached.

### 6. Evidence Before Action

AI-generated recommendations should be treated as suggestions or hypotheses unless supported by appropriate evidence.

### 7. Bias Awareness

AI systems can reproduce or amplify biases present in their training data, organisational data or assumptions.

Outputs should therefore be reviewed critically.

### 8. Community Context

An AI recommendation that appears reasonable statistically may not be appropriate in a particular community.

Local knowledge and lived experience must remain central.

### 9. Security

Systems handling organisational or community information should use appropriate security controls.

Access to sensitive information should be restricted according to legitimate roles and responsibilities.

### 10. Accountability

There must always be clarity about who is responsible for decisions made using AI-assisted analysis.

AI should not become a mechanism for avoiding human accountability.

---

# AI Outputs: Evidence vs Hypothesis

OpenSocial AI should distinguish between different types of outputs.

## Evidence

Information directly supported by the available data or trusted sources.

## Interpretation

A reasoned explanation based on available evidence.

## Hypothesis

A possible explanation or idea that requires further validation.

## Recommendation

A proposed action that requires human assessment before implementation.

This distinction is important because an AI-generated statement should not automatically be treated as established fact.

---

# Sensitive Data

OpenSocial AI may eventually be used in contexts involving sensitive information.

Examples can include:

- Personal information
- Health-related information
- Financial information
- Information about vulnerable communities
- Organisationally confidential information

Such information requires appropriate safeguards.

Whenever possible, development and testing should use:

- Synthetic data
- Anonymised data
- Aggregated data
- De-identified examples

Real sensitive information should only be used when there is a legitimate purpose and appropriate governance.

---

# Human and Community Validation

AI-generated solutions should be evaluated by people who understand the context in which they may be implemented.

This can include:

- Programme professionals
- Community practitioners
- Researchers
- Organisational leaders
- Community representatives
- Subject-matter experts

The purpose is to ensure that an apparently intelligent recommendation is also:

- Relevant
- Ethical
- Feasible
- Contextually appropriate
- Acceptable to affected communities

---

# Innovation Without Harm

Innovation should not mean experimenting with people without appropriate safeguards.

Before an AI-generated intervention is piloted, organisations should consider:

1. What problem are we trying to solve?
2. What evidence supports the proposed approach?
3. Who could benefit?
4. Who could be harmed?
5. What assumptions are being made?
6. What unintended consequences could occur?
7. How will the intervention be monitored?
8. What would cause us to stop or modify the intervention?

---

# Continuous Evaluation

Responsible AI is not a one-time checklist.

OpenSocial AI should continuously evaluate:

- Accuracy
- Bias
- Privacy
- Security
- User experience
- Community impact
- Unintended consequences
- Real-world outcomes

Lessons from implementation should feed back into the system.

```text
AI Output
    ↓
Human Review
    ↓
Community / Expert Validation
    ↓
Implementation
    ↓
Outcome Monitoring
    ↓
Evaluation
    ↓
Learning
    ↓
Improved System
```

## Implementation guardrails

The current engine represents evidence, patterns, insights, hypotheses,
experiments, and learning as different data types. An observed result
from an inspiration or pilot is never automatically converted into a
proven intervention. Experiment designs include safeguards and stop
conditions, while validation learning requires a named human reviewer
and remains exploratory.

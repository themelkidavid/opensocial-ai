# OpenSocial AI

### Open-source AI tools for community organisations and social-sector federations

> **AI should not replace community knowledge. It should amplify it.**

OpenSocial AI is an emerging open-source initiative exploring how artificial intelligence can help community-based organisations, NGOs and social-sector federations transform their accumulated knowledge and historical data into better decisions, deeper insights and innovative solutions.

Social-sector organisations generate enormous amounts of information through programme implementation, monitoring, community engagement, organisational experience and years of field learning. Much of this knowledge remains scattered across reports, spreadsheets, databases and institutional memory.

OpenSocial AI aims to help turn that information into **actionable intelligence**.

---

## The Problem

Many organisations already have years of valuable data and experience.

The challenge is not simply a lack of data.

The challenge is:

- What can we learn from our historical data?
- What patterns are we failing to see?
- Which communities or problems are being overlooked?
- Why are some interventions working better than others?
- What can one organisation learn from another?
- Can we identify emerging problems before they become crises?
- Can AI help us discover solutions that humans may not have considered?
- How can organisations with limited technical resources benefit from advanced AI?

Most existing digital systems focus on **recording, reporting and monitoring**.

OpenSocial AI explores the next step:

> **Using AI to learn from what organisations already know and help them discover what they don't yet know.**

---

# Our Vision

We envision a future where every community organisation can have access to an intelligent analytical partner that helps its people:

**Understand → Discover → Decide → Experiment → Learn → Improve**

The objective is not to automate human judgement.

The objective is to combine:

**Artificial Intelligence + Human Expertise + Community Knowledge + Historical Data**

to solve complex social problems more effectively.

---

# Core Capabilities

OpenSocial AI is being developed around five initial capabilities.

## 1. Programme Intelligence

Analyse historical programme information to identify:

- Trends over time
- Geographic differences
- Service gaps
- Changes in beneficiary needs
- Programme performance
- Emerging risks
- Under-served populations
- Relationships between different programme indicators

The objective is to move from:

> "What happened?"

to:

> **"Why did it happen, what does it mean, and what should we do next?"**

---

## 2. Organisational Intelligence

Help organisations understand their own institutional strengths, weaknesses and sustainability challenges.

Potential areas include:

- Governance
- Leadership
- Human resources
- Financial sustainability
- Organisational capacity
- Programme management
- Partnerships
- Institutional risks
- Knowledge management

AI can help identify patterns across organisational information and generate questions and recommendations for human review.

---

## 3. Federation Intelligence

Social-sector federations represent an opportunity that is rarely fully utilised.

Different organisations often face similar challenges, while individual organisations may independently develop successful solutions.

OpenSocial AI will explore how AI can identify:

> **"Organisation A has solved a problem that Organisation B is currently struggling with."**

This could enable large networks of organisations to learn from one another systematically.

Potential applications include:

- Cross-organisation learning
- Identification of successful practices
- Peer-to-peer knowledge discovery
- Comparative analysis
- Resource sharing
- Common problem identification
- Replication of successful approaches

---

## 4. Sustainability Intelligence

Many community organisations face long-term sustainability challenges.

OpenSocial AI will explore AI-assisted approaches to identifying opportunities for:

- Funding diversification
- Strategic partnerships
- Earned-income possibilities
- Resource optimisation
- Shared services
- New service models
- Institutional strengthening
- Long-term organisational resilience

The goal is not for AI to make financial decisions.

The goal is to help organisations discover possibilities they can evaluate and act upon.

---

# 5. Innovation Discovery Engine

### Our flagship area of exploration

The most important question is not:

> **"How can AI make our existing work faster?"**

It is:

> **"Can AI help us discover solutions that we have not thought of before?"**

The Innovation Discovery Engine will explore a structured process for combining:

- Historical programme data
- Organisational knowledge
- Community feedback
- Research evidence
- Field experience
- Cross-sector knowledge
- Emerging trends
- Lessons from other organisations

to identify:

**Patterns → Gaps → Root causes → Hypotheses → Possible solutions → Pilot opportunities**

AI-generated ideas will not automatically be treated as solutions.

They will become **hypotheses for human experts and communities to evaluate, adapt and test.**

---

# A New Model for Social Innovation

OpenSocial AI explores the following learning loop:

```text
Historical Data
      ↓
AI Analysis
      ↓
Pattern & Gap Identification
      ↓
Root-Cause Exploration
      ↓
Cross-Sector Knowledge
      ↓
New Solution Hypotheses
      ↓
Human & Community Validation
      ↓
Pilot / Experiment
      ↓
Outcome Data
      ↓
AI-Assisted Learning
      ↓
Improved Intervention
      ↺
```

## How the Innovation Discovery Engine works

The current implementation is a transparent, deterministic foundation
for evidence-aware innovation work. It does not use a machine-learning
model or claim to predict whether an intervention will succeed.

```text
Evidence
  → Pattern discovery
  → Evidence quality, gaps, and conflicts
  → Insight generation
  → Innovation opportunities
  → Relevant inspirations and combinations
  → Testable innovation hypotheses
  → Structured experiment designs
  → Human-reviewed validation observations
  → Exploratory learning
```

Each stage keeps a distinct output type. Evidence remains evidence;
patterns are observations; insights and innovation opportunities remain
interpretations; hypotheses and combinations remain unproven proposals;
and learning remains exploratory even after a reviewed pilot outcome.

### Innovation inspiration and combination

An `InnovationInspiration` records a documented mechanism and its
observed result in another context. The reasoning engine retrieves
inspirations with transparent keyword overlap. When two or more sources
are relevant and an innovation or transfer opportunity has a sufficient
evidence basis, `InnovationCombinationEngine` can create a pairwise
design hypothesis that preserves both mechanisms and their uncertainty. It
does not treat either source result as proof that the combination will
work locally.

### Experiments and validation

`ExperimentDesignEngine` converts each innovation hypothesis into a
small-pilot design with an intervention, comparison, measures,
safeguards, and stop conditions. `ValidationLearningEngine` only creates
learning from a caller-supplied, reviewer-attributed observation. It
always labels that learning `exploratory` and explicitly cautions against
assuming effectiveness elsewhere or at scale. Each experiment has a
stable `experiment_id`, which validation observations preserve for
traceability through serialized learning records.

## Responsible use

Use the engine to structure inquiry, not to automate social-sector
decisions. Review every output with affected communities and appropriate
programme, safeguarding, and subject-matter practitioners. Supply only
the minimum lawful, de-identified information needed for the analysis.
Read [the responsible AI framework](docs/responsible-ai.md) before using
the engine with real programme information.

## Development

OpenSocial AI currently has no external runtime dependencies. Python
3.12 is used in CI.

Run the full test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

The repository keeps each analytical capability in its own module under
`src/`, with matching unit tests under `tests/`. To extend the engine,
add a small, serializable domain object, keep its claims and uncertainty
explicit, integrate it through `InnovationDiscoveryEngine`, and add
tests for normal, empty, invalid, and serialization cases. Avoid adding
model claims to the deterministic baseline unless the model and its
limits are documented and independently testable.

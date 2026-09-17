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
  → Reviewer-attributed validation observations
  → Exploratory learning
```

Each stage keeps a distinct output type. Evidence remains evidence;
patterns are observations; insights and innovation opportunities remain
interpretations; hypotheses and combinations remain unproven proposals;
and learning remains exploratory even after a caller-supplied pilot outcome
with reviewer attribution.

### Innovation inspiration and combination

An `InnovationInspiration` records a documented mechanism and its
observed result in another context. `KeywordRetriever` is the default,
using transparent keyword overlap. `RelevanceRetriever` also supports an
optional `SemanticRetriever`, which uses cosine similarity over vectors
from a caller-provided `EmbeddingProvider`; it does not select a model,
call an external API, or add a dependency. `DeterministicTestEmbeddingProvider`
is only a local test/reference provider and is not production semantic
intelligence. `HybridRetriever` can transparently combine keyword and
semantic scores when an application explicitly opts in. Retriever results
must be supplied inspiration objects; retrieval cannot add a new
undocumented source.

Semantic and hybrid matches expose their strategy, numeric score, source
type, context, and transferability in `RetrievalMatch`. A similarity score
means only that a source is potentially relevant; it is not causal evidence,
proof of transferability, contextual equivalence, or a recommended
intervention.

### Cross-sector discovery

`CrossSectorDiscoveryEngine` turns retriever matches into explicit candidate
inspirations. It compares documented mechanisms, not sector labels alone,
and preserves optional sector, geography, target population, and provenance
metadata from `InnovationInspiration`. A caller may prefer cross-sector
candidates with a transparent, configurable ranking boost; same-sector
candidates remain visible. Every result includes adaptation questions and
uncertainty: sector difference and retrieval similarity do not establish
transferability or effectiveness.

### Historical programme memory

`HistoricalProgrammeIngestion`, `HistoricalMemoryStore`, and
`HistoricalDiscoveryEngine` provide an optional local record of documented
programmes and their mechanisms. Historical matches are candidate precedents
with provenance, evidence basis, limitations, and adaptation questions—not
proof that a past result transfers to a current context.

When two or more sources are relevant and an innovation or transfer
opportunity has a sufficient evidence basis, `InnovationCombinationEngine`
can create a pairwise design hypothesis that preserves both mechanisms and
their uncertainty. It does not treat either source result as proof that the
combination will work locally.

### Experiments and validation

`ExperimentDesignEngine` converts each innovation hypothesis into a
small-pilot design with an intervention, comparison, measures,
safeguards, and stop conditions. `ValidationLearningEngine` only creates
learning from a caller-supplied observation with a reviewer attribution and
evidence basis. It always labels that learning `exploratory` and explicitly
cautions against
assuming effectiveness elsewhere or at scale. Each experiment has a
stable `experiment_id`, which validation observations preserve for
traceability through serialized learning records.

New experiment IDs fingerprint the complete hypothesis to avoid conflating
different pilot designs. Consumers that independently stored serialized
IDs from earlier in-memory versions must re-associate those legacy records
explicitly; this initial persistence phase does not provide an automatic
legacy-ID migration.

### Outcome metrics and comparative learning

Experiments may carry caller-defined outcome metric plans and separately
recorded, reviewer-attributed outcome observations. Comparisons calculate
transparent differences only where values are mathematically compatible and
surface warnings about population, period, method, context, and baseline
differences. They never select a winner or establish causality.

### Portfolio learning and strategy discovery

`ProgrammePortfolio` groups caller-selected programme and experiment records.
Portfolio learning describes mechanism recurrence, evidence gaps, context and
measurement differences without ranking programmes or inferring effectiveness.
Its strategy opportunities are questions for human investigation, not recommendations.

### Strategic scenarios

`StrategicScenarioEngine` creates deterministic, evidence-attributed exploratory scenarios from portfolio patterns. It preserves assumptions, uncertainties, expected learning, provenance, and an optional experiment concept. Scenarios are not recommendations or predictions; SQLite persistence and audit events record their review lifecycle.

### Evidence packs, decision briefs, and rendering

`EvidencePack` preserves a structured evidence snapshot: its quality summary, gaps, conflicts, references, outcome metadata, provenance, and limitations. `DecisionBriefBuilder` assembles existing evidence and governance records into immutable, per-subject versioned `DecisionBrief` snapshots, including alternatives, dissent, unresolved questions, human decision status, and authorization state. The shared local rendering pipeline produces deterministic Markdown, HTML, DOCX, or browser-free PDF exports with traceability identifiers and visible uncertainty. Export records retain byte-level SHA-256 checksums, format, and source snapshot identity; a checksum is not a digital signature. Exports require an explicit overwrite choice and are not decisions, recommendations, predictions, or proof of effectiveness.

### Optional persistence, ingestion, and auditability

The in-memory workflow remains the default. Applications that need local,
cross-session storage can pass the standard-library
`SQLitePersistenceStore` to `InnovationDiscoveryEngine`. A SQLite-backed
analysis run is atomic: if a later storage safeguard rejects the run, its
writes and audit events are rolled back. Other `PersistenceStore`
implementations may provide different transaction guarantees.

`EvidenceIngestionAdapter` accepts deterministic local JSON records (an
array or an object containing `records`) and CSV records. Both require
`source_type` and `content`, then produce the existing `EvidenceItem` plus
factual `EvidenceProvenance`: entry method, optional original source ID,
optional source reference, and import format. Unknown provenance remains
unknown. This phase deliberately does not include PDF/OCR extraction, web
collection, external APIs, or model-based extraction.

```python
from src.evidence_ingestion import EvidenceIngestionAdapter
from src.innovation_discovery import InnovationDiscoveryEngine
from src.persistence import SQLitePersistenceStore

records = EvidenceIngestionAdapter().from_json(json_payload)

with SQLitePersistenceStore("opensocial-ai.sqlite3") as store:
    report = InnovationDiscoveryEngine(storage=store).analyse(
        "Young people face barriers to service access.",
        evidence=[record.evidence for record in records],
        evidence_provenance=[record.provenance for record in records],
    )
```

Persisted experiments require known `analysis_evidence_ids`, which link the
input analysis corpus to the design. That lineage is not a claim that every
linked item directly supports the design or proves an intervention.
SQLite enforces experiment → observation → learning references and records
timestamps. An unknown experiment or observation is rejected rather than
becoming trusted learning.

Audit events record evidence creation/import, experiment creation and
additional corpus lineage, observation recording and reviewer attribution,
and learning generation. They are state-transition records, not approval,
proof, or evidence that a named person actually completed a review. Pilot
observation evidence remains a caller-supplied text basis in this phase;
only the experiment analysis corpus has an ID-level evidence link.

## Responsible use

Use the engine to structure inquiry, not to automate social-sector
decisions. Review every output with affected communities and appropriate
programme, safeguarding, and subject-matter practitioners. Supply only
the minimum lawful, de-identified information needed for the analysis.
Read [the responsible AI framework](docs/responsible-ai.md) before using
the engine with real programme information.

## Development

OpenSocial AI currently has no external runtime dependencies. Python
3.12 is used in CI; the optional SQLite store uses Python's built-in
`sqlite3` module.

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

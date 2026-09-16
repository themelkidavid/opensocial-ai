# OpenSocial AI: Architecture

## Overview

OpenSocial AI is designed as a modular intelligence framework for community organisations and social-sector federations.

The architecture separates data, analysis, intelligence workflows and human decision-making so that organisations can adapt the system to their own programmes and contexts.

## High-Level Architecture

```text
                    ┌─────────────────────────┐
                    │   Community Knowledge   │
                    │   & Field Experience    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     Organisational      │
                    │      Data Sources       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Data Preparation &    │
                    │       Validation        │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      AI Analysis        │
                    │                         │
                    │ • Pattern detection     │
                    │ • Trend analysis        │
                    │ • Gap identification    │
                    │ • Root-cause exploration│
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
        Programme          Organisation       Federation
        Intelligence       Intelligence       Intelligence
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Innovation Discovery    │
                    │        Engine            │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Human & Community       │
                    │ Validation              │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Pilot / Implementation  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Outcome & Learning Data │
                    └────────────┬────────────┘
                                 │
                                 └──────────► Continuous Learning
```

## Implemented Innovation Discovery pipeline

The current engine is a modular, deterministic implementation of the
following pipeline:

| Stage | Component | Output |
| --- | --- | --- |
| Optional ingestion | `evidence_ingestion.py` | `ImportedEvidence` with `EvidenceProvenance` |
| Evidence | `evidence.py` | `EvidenceItem` |
| Pattern discovery | `pattern_discovery.py` | `ObservedPattern` |
| Evidence gaps | `evidence_gap.py` | `EvidenceGap` |
| Evidence quality | `evidence_quality.py` | `EvidenceQuality` |
| Evidence conflicts | `evidence_conflict.py` | `EvidenceConflict` |
| Insights | `insight_generation.py` | `InsightCandidate` |
| Innovation opportunities | `innovation_opportunity.py` | `InnovationOpportunity` |
| Inspiration | `innovation_inspiration.py` | `InnovationInspiration` |
| Inspiration retrieval | `retrieval.py` | Keyword, optional semantic, or optional hybrid matches from the supplied inspiration corpus |
| Cross-sector discovery | `cross_sector_discovery.py` | Mechanism-based candidate inspirations with adaptation questions |
| Reasoning and combination | `innovation_reasoning.py`, `innovation_combination.py` | `InnovationHypothesis` |
| Experiment design | `experiment_design.py` | `ExperimentDesign` |
| Validation and learning | `validation_learning.py` | `ValidationObservation`, `ValidatedLearning` |
| Optional persistence and audit | `persistence.py` | Stored records and `AuditEvent` |

`InnovationDiscoveryEngine` orchestrates the pipeline and returns an
`InnovationReport`. Experiment designs are made only from generated
innovation hypotheses. Validated learning is made only from
caller-supplied, reviewer-attributed observations; the engine never
creates a claimed outcome from a hypothesis or experiment design. An
`experiment_id` links each observation and learning record to its design.

The baseline uses transparent rules and keyword overlap, not machine
learning. All stage outputs are dataclasses with serializable evidence,
confidence, uncertainty, and investigation fields where appropriate.

## Optional persistence, provenance, and auditability

`SQLitePersistenceStore` is an opt-in, standard-library `sqlite3`
implementation of the small `PersistenceStore` boundary. It keeps the
domain engines independent of SQLite; without a store,
`InnovationDiscoveryEngine` continues to operate entirely in memory.

The SQLite schema stores evidence records, experiment designs,
reviewer-attributed observations, exploratory learning records, and audit
events. Structured fields are serialized as JSON. Evidence has a stable
content-and-provenance ID and timestamp; experiment IDs are derived from
the complete hypothesis; observations and learning have stable IDs and
timestamps.

For a persisted experiment, `analysis_evidence_ids` must name known,
unique evidence records. The `experiment_evidence` association preserves
an append-only lineage order, so prior links cannot be reordered or
removed. When a design is saved again, the repository keeps its first
recorded order and appends only previously unseen evidence IDs; reordered
or omitted caller IDs do not rewrite history. This is lineage, not an
assertion that every linked item directly supports the design or proves
effectiveness. SQLite enforces the other traceability links:

```text
Persisted analysis evidence ──analysis-corpus lineage──► Experiment design
                                                        │
                                                        ▼
                                                Validation observation
                                                        │
                                                        ▼
                                                Exploratory learning
```

An observation for an unknown experiment, or learning for an unknown or
non-matching observation, is rejected. A SQLite-backed call to
`InnovationDiscoveryEngine.analyse()` runs in one transaction, so a later
rejection rolls back that call's writes and audit events. Custom
`PersistenceStore` implementations may define their own transaction
guarantees. SQLite serializes writers while it makes an idempotent storage
decision; it is not a multi-writer service. Applications that run long
analyses concurrently should coordinate writers or handle SQLite busy-timeout
retries.

`AuditEvent` records state transitions such as evidence creation/import,
experiment creation, additional analysis-corpus lineage, observation
recording, reviewer attribution, and learning generation. The audit trail
does not authorize a real-world action, prove an intervention, or verify a
reviewer's identity or that review occurred.

## Ingestion and retrieval boundaries

`EvidenceIngestionAdapter` safely parses local JSON (a record array or an
object with a `records` array) and CSV. Both formats require `source_type`
and `content`; optional source fields are preserved without invented
values. An imported record carries factual `EvidenceProvenance`: it was
imported, its optional original source identifier, optional source
reference, and format. The adapter intentionally has no PDF/OCR, web,
external API, or LLM extraction path.

`KeywordRetriever` remains the default retrieval implementation. It ranks
only the supplied inspiration corpus using transparent keyword overlap and
transferability. `SemanticRetriever` is optional: it calculates cosine
similarity over vectors supplied by an application-owned
`EmbeddingProvider`. The repository does not include a hosted provider,
model, vector database, or external AI dependency. Its
`DeterministicTestEmbeddingProvider` is a local test/reference aid only,
not production semantic intelligence.

`HybridRetriever` is also opt-in. It combines a keyword-overlap score and
semantic similarity using caller-configured weights, returning the separate
components and combined score in `RetrievalMatch`. Every match preserves
the source inspiration, source type, context, transferability, strategy,
and score so a later cross-sector ranking phase can use the original
metadata. Retrieved objects are checked against the supplied corpus.

Neither a semantic score nor a hybrid score proves that two settings are
equivalent, that a mechanism transfers, or that an intervention works. It
only identifies a candidate inspiration for human contextual review.

`CrossSectorDiscoveryEngine` consumes the same retriever interface and
creates `CrossSectorCandidate` records. It preserves source sector, target
sector, source type, mechanism, provenance fields, retrieval strategy and
score. `prefer_cross_sector` may add a configured diversity boost only when
both sectors are known and differ; it never removes same-sector candidates
or treats difference as evidence of usefulness. Ties preserve retriever
order. Candidate records explicitly state uncertainty and adaptation
questions before any reasoning or pilot decision.

Pilot observation evidence remains a caller-supplied text basis in this
phase. It is carried into learning records, but it is not yet a separate
evidence-ID association; do not mistake that text for referential evidence
provenance.

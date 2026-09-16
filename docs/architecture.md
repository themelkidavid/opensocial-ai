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
| Evidence | `evidence.py` | `EvidenceItem` |
| Pattern discovery | `pattern_discovery.py` | `ObservedPattern` |
| Evidence gaps | `evidence_gap.py` | `EvidenceGap` |
| Evidence quality | `evidence_quality.py` | `EvidenceQuality` |
| Evidence conflicts | `evidence_conflict.py` | `EvidenceConflict` |
| Insights | `insight_generation.py` | `InsightCandidate` |
| Innovation opportunities | `innovation_opportunity.py` | `InnovationOpportunity` |
| Inspiration | `innovation_inspiration.py` | `InnovationInspiration` |
| Reasoning and combination | `innovation_reasoning.py`, `innovation_combination.py` | `InnovationHypothesis` |
| Experiment design | `experiment_design.py` | `ExperimentDesign` |
| Validation and learning | `validation_learning.py` | `ValidationObservation`, `ValidatedLearning` |

`InnovationDiscoveryEngine` orchestrates the pipeline and returns an
`InnovationReport`. Experiment designs are made only from generated
innovation hypotheses. Validated learning is made only from
caller-supplied, reviewer-attributed observations; the engine never
creates a claimed outcome from a hypothesis or experiment design. An
`experiment_id` links each observation and learning record to its design.

The baseline uses transparent rules and keyword overlap, not machine
learning. All stage outputs are dataclasses with serializable evidence,
confidence, uncertainty, and investigation fields where appropriate.

"""Transparent, deterministic extraction of narrative evidence signals.

This module records what a supplied source states or implies.  It does not
decide whether a claim is true, infer causality, or recommend an action.
"""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
from typing import Dict, Iterable, List, Optional

try:
    from src.evidence import EvidenceItem
    from src.llm_interpretation import (
        InterpretationEvidence,
        InterpretationProvider,
        InterpretationRequest,
        InterpretationValidator,
        StructuredInterpretation,
    )
except ModuleNotFoundError:  # pragma: no cover - supports direct module use
    from evidence import EvidenceItem
    from llm_interpretation import (
        InterpretationEvidence,
        InterpretationProvider,
        InterpretationRequest,
        InterpretationValidator,
        StructuredInterpretation,
    )


def _normalise(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()


def _stable_id(prefix: str, value: Dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return "%s-%s" % (prefix, hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16])


@dataclass
class NarrativeReasoningConfig:
    """Caller-owned aliases for transparent topic normalisation."""

    concept_aliases: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class NarrativeClaim:
    claim_id: str
    evidence_id: str
    claim_type: str
    subject: str
    relation: str
    object_or_outcome: str
    direction: str
    polarity: str
    population: Optional[str]
    location: Optional[str]
    time_period: Optional[str]
    qualifiers: List[str]
    raw_text: str
    extraction_basis: str
    provenance: Dict

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class NarrativeConflict:
    conflict_id: str
    claim_a_id: str
    claim_b_id: str
    evidence_a_id: str
    evidence_b_id: str
    topic: str
    context_comparison: Dict[str, str]
    conflict_type: str
    explanation: str
    uncertainty: str
    provenance: List[Dict]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MechanismCandidate:
    candidate_id: str
    evidence_id: str
    mechanism_text: str
    action: str
    target: str
    intended_or_observed_effect: str
    population: Optional[str]
    context: Dict[str, Optional[str]]
    raw_text: str
    extraction_basis: str
    provenance: Dict
    limitations: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class NarrativeAnalysis:
    claims: List[NarrativeClaim] = field(default_factory=list)
    narrative_conflicts: List[NarrativeConflict] = field(default_factory=list)
    context_dependencies: List[NarrativeConflict] = field(default_factory=list)
    mechanism_candidates: List[MechanismCandidate] = field(default_factory=list)
    unresolved_claims: List[str] = field(default_factory=list)
    extraction_notes: List[str] = field(default_factory=list)
    assisted_interpretation: Optional[StructuredInterpretation] = None
    interpretation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        result = {
            "claims": [item.to_dict() for item in self.claims],
            "narrative_conflicts": [item.to_dict() for item in self.narrative_conflicts],
            "context_dependencies": [item.to_dict() for item in self.context_dependencies],
            "mechanism_candidates": [item.to_dict() for item in self.mechanism_candidates],
            "unresolved_claims": list(self.unresolved_claims),
            "extraction_notes": list(self.extraction_notes),
        }
        if self.assisted_interpretation is not None:
            result["assisted_interpretation"] = self.assisted_interpretation.to_dict()
            result["assisted_claims"] = [item.to_dict() for item in self.assisted_interpretation.claims]
            result["assisted_mechanism_candidates"] = [item.to_dict() for item in self.assisted_interpretation.mechanism_candidates]
            result["assisted_conflict_candidates"] = [item.to_dict() for item in self.assisted_interpretation.conflict_candidates]
        if self.interpretation_errors:
            result["interpretation_errors"] = list(self.interpretation_errors)
        return result


class NarrativeReasoningEngine:
    """Small rule-based extractor; optional retrieval is never required."""

    _NO_CHANGE = ("did not improve", "no meaningful change", "no change", "limited change", "little change", "not associated with an increase")
    _DIRECTIONS = (
        ("ineffective", "decrease", "negative"), ("ineffective", "decrease", "negative"),
        ("worsened", "decrease", "negative"), ("worsen", "decrease", "negative"),
        ("decreased", "decrease", "negative"), ("decrease", "decrease", "negative"),
        ("declined", "decrease", "negative"), ("decline", "decrease", "negative"),
        ("reduced", "decrease", "negative"), ("lower", "decrease", "negative"),
        ("less", "decrease", "negative"), ("weakened", "decrease", "negative"),
        ("hindered", "decrease", "negative"), ("absent", "absent", "negative"),
        ("improved", "increase", "positive"), ("improve", "increase", "positive"),
        ("increased", "increase", "positive"), ("increase", "increase", "positive"),
        ("higher", "increase", "positive"), ("more", "increase", "positive"),
        ("strengthened", "increase", "positive"), ("supported", "increase", "positive"),
        ("effective", "increase", "positive"), ("present", "present", "positive"),
    )
    _ACTIONS = ("implemented", "introduced", "established", "created", "developed", "used", "shared", "supported", "provided", "enabled", "coordinated", "combined")
    _STOP_WORDS = {"the", "and", "with", "that", "this", "from", "were", "was", "after", "before", "into", "their", "they", "have", "has", "had", "for", "not", "did", "but", "reported", "organisations", "organization", "fictional"}

    def __init__(self, config: Optional[NarrativeReasoningConfig] = None, retriever: object = None,
                 interpretation_provider: Optional[InterpretationProvider] = None) -> None:
        if retriever is not None and not callable(getattr(retriever, "retrieve", None)):
            raise TypeError("retriever must provide a retrieve method")
        if interpretation_provider is not None and not callable(getattr(interpretation_provider, "interpret", None)):
            raise TypeError("interpretation_provider must provide an interpret method")
        self.config = config or NarrativeReasoningConfig()
        self.retriever = retriever
        self.interpretation_provider = interpretation_provider
        self._aliases = self._build_aliases(self.config.concept_aliases)

    @staticmethod
    def _build_aliases(aliases: Dict[str, List[str]]) -> List:
        result = []
        for canonical, values in aliases.items():
            if not isinstance(canonical, str) or not canonical.strip() or not isinstance(values, list):
                raise ValueError("concept_aliases must map non-empty strings to lists")
            for value in [canonical] + values:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("concept aliases must be non-empty strings")
                result.append((_normalise(value), canonical.strip()))
        return sorted(set(result), key=lambda item: (-len(item[0]), item[0]))

    def analyse(self, evidence: Iterable[EvidenceItem], evidence_ids: Optional[List[str]] = None,
                evidence_provenance: Optional[List[object]] = None,
                interpretation_metadata: Optional[List[Dict]] = None) -> NarrativeAnalysis:
        evidence = list(evidence)
        if evidence_ids is not None and len(evidence_ids) != len(evidence):
            raise ValueError("evidence_ids must align with evidence")
        if evidence_provenance is not None and len(evidence_provenance) != len(evidence):
            raise ValueError("evidence_provenance must align with evidence")
        if interpretation_metadata is not None and (len(interpretation_metadata) != len(evidence)
                                                    or not all(isinstance(item, dict) for item in interpretation_metadata)):
            raise ValueError("interpretation_metadata must align with evidence as dictionaries")
        claims, mechanisms = [], []
        seen_mechanisms = set()
        for index, item in enumerate(evidence):
            if not isinstance(item, EvidenceItem):
                raise TypeError("All evidence items must be EvidenceItem instances")
            if not item.source_type.strip() or not item.content.strip():
                raise ValueError("Evidence source_type and content cannot be empty")
            evidence_id = (evidence_ids[index] if evidence_ids else item.metadata.get("evidence_id")) or _stable_id("evidence", {"index": index, "source_type": item.source_type, "content": item.content})
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                raise ValueError("evidence identifiers must be non-empty strings")
            provenance = self._provenance(item, evidence_provenance[index] if evidence_provenance else None)
            for sentence in self._sentences(item.content):
                claim = self._claim(sentence, item, evidence_id, provenance)
                if claim:
                    claims.append(claim)
                mechanism = self._mechanism(sentence, item, evidence_id, provenance, claim)
                if mechanism and mechanism.candidate_id not in seen_mechanisms:
                    mechanisms.append(mechanism)
                    seen_mechanisms.add(mechanism.candidate_id)
        claims.sort(key=lambda item: item.claim_id)
        mechanisms.sort(key=lambda item: item.candidate_id)
        conflicts, dependencies = self._compare_claims(claims)
        analysis = NarrativeAnalysis(
            claims=claims, narrative_conflicts=conflicts, context_dependencies=dependencies,
            mechanism_candidates=mechanisms,
            unresolved_claims=[item.claim_id for item in claims if item.direction == "unknown"],
            extraction_notes=["Claims record source statements or implications, not verified facts.", "Rule-based extraction is deterministic and context-aware; it does not infer causality, effectiveness, or recommendations."] + (["An optional retriever was supplied but is not needed for local extraction."] if self.retriever else []),
        )
        if self.interpretation_provider is not None:
            supplied = {
                (evidence_ids[index] if evidence_ids else item.metadata.get("evidence_id")) or _stable_id("evidence", {"index": index, "source_type": item.source_type, "content": item.content}): item
                for index, item in enumerate(evidence)
            }
            if len(supplied) != len(evidence):
                raise ValueError("assisted interpretation requires unique evidence identifiers")
            request = InterpretationRequest([
                InterpretationEvidence(evidence_id, item.content, item.source_type, item.date, item.location, item.population,
                                      dict(interpretation_metadata[index]) if interpretation_metadata else {})
                for index, (evidence_id, item) in enumerate(supplied.items())
            ])
            try:
                response = self.interpretation_provider.interpret(request)
                analysis.assisted_interpretation = InterpretationValidator().validate(response, supplied)
                analysis.extraction_notes.append("Optional assisted interpretation was validated separately; it remains machine-extracted source attribution.")
            except (TypeError, ValueError) as error:
                analysis.interpretation_errors.append(str(error))
                analysis.extraction_notes.append("Optional assisted interpretation was rejected by the validation boundary.")
            except Exception as error:
                analysis.interpretation_errors.append("provider error: %s" % error.__class__.__name__)
                analysis.extraction_notes.append("Optional assisted interpretation was unavailable; deterministic extraction remains available.")
        return analysis

    @staticmethod
    def _sentences(text: str) -> List[str]:
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+|;\s*", text) if part.strip()]

    @staticmethod
    def _provenance(item: EvidenceItem, supplied: object) -> Dict:
        if supplied is not None:
            return supplied.to_dict() if callable(getattr(supplied, "to_dict", None)) else dict(supplied)
        return {"source_type": item.source_type, "source_identifier": item.metadata.get("source_identifier"), "metadata": dict(item.metadata)}

    def _topic(self, sentence: str) -> str:
        text = _normalise(sentence)
        for alias, canonical in self._aliases:
            if re.search(r"(^| )%s($| )" % re.escape(alias), text):
                return canonical
        tokens = [word for word in text.split() if len(word) > 3 and word not in self._STOP_WORDS]
        return " ".join(tokens[:6]) or "unspecified topic"

    def _direction(self, text: str):
        lowered = text.lower()
        if any(phrase in lowered for phrase in self._NO_CHANGE):
            return "no_change", "neutral", "explicit no-change or negation phrase"
        for phrase, direction, polarity in self._DIRECTIONS:
            if re.search(r"\b%s\b" % re.escape(phrase), lowered):
                return direction, polarity, "direction phrase '%s'" % phrase
        return "unknown", "unknown", "no supported direction phrase"

    def _claim(self, sentence: str, item: EvidenceItem, evidence_id: str, provenance: Dict) -> Optional[NarrativeClaim]:
        direction, polarity, basis = self._direction(sentence)
        if direction == "unknown" and not re.search(r"\b(reported|described|observed|found|perceived)\b", sentence, re.I):
            return None
        subject = self._topic(sentence)
        payload = {"evidence_id": evidence_id, "subject": subject, "raw_text": sentence, "direction": direction}
        return NarrativeClaim(_stable_id("claim", payload), evidence_id, "source_statement", subject, "reported_outcome", subject, direction, polarity, item.population, item.location, item.date, [], sentence, basis, provenance)

    def _mechanism(self, sentence: str, item: EvidenceItem, evidence_id: str, provenance: Dict, claim: Optional[NarrativeClaim]) -> Optional[MechanismCandidate]:
        match = re.search(r"\b(%s)\b\s+(.{3,100})" % "|".join(self._ACTIONS), sentence, re.I)
        if not match:
            return None
        action, target = match.group(1).lower(), match.group(2).strip(" .,")
        payload = {"evidence_id": evidence_id, "action": action, "target": _normalise(target), "raw_text": sentence}
        return MechanismCandidate(_stable_id("mechanism-candidate", payload), evidence_id, sentence, action, target, claim.direction if claim else "unknown", item.population, {"location": item.location, "time_period": item.date, "source_type": item.source_type}, sentence, "generic action phrase '%s'" % action, provenance, ["Candidate records a source-described action; it is not evidence that the mechanism worked or should be adopted."])

    @staticmethod
    def _opposes(first: str, second: str) -> bool:
        return {first, second} in ({"increase", "decrease"}, {"increase", "no_change"}, {"decrease", "no_change"}, {"present", "absent"})

    def _related(self, first: NarrativeClaim, second: NarrativeClaim) -> bool:
        if first.subject == second.subject and first.subject != "unspecified topic":
            return True
        if {first.direction, second.direction} == {"present", "absent"}:
            return False
        one = {word for word in _normalise(first.raw_text).split() if len(word) > 3 and word not in self._STOP_WORDS}
        two = {word for word in _normalise(second.raw_text).split() if len(word) > 3 and word not in self._STOP_WORDS}
        # A shared meaningful topic term is sufficient once directions oppose;
        # direction words and reporting boilerplate are excluded above.
        return len(one & two) >= 1

    @staticmethod
    def _context(first: NarrativeClaim, second: NarrativeClaim) -> Dict[str, str]:
        fields = ("population", "location", "time_period")
        comparison = {}
        for field_name in fields:
            one, two = getattr(first, field_name), getattr(second, field_name)
            comparison[field_name] = "different" if one and two and _normalise(one) != _normalise(two) else "same_or_unknown"
        return comparison

    def _compare_claims(self, claims: List[NarrativeClaim]):
        conflicts, dependencies = [], []
        for position, first in enumerate(claims):
            for second in claims[position + 1:]:
                if not self._related(first, second) or not self._opposes(first.direction, second.direction):
                    continue
                context = self._context(first, second)
                context_dependent = "different" in context.values()
                kind = "context_dependency" if context_dependent else ("presence_absence_conflict" if {first.direction, second.direction} == {"present", "absent"} else "directional_conflict")
                payload = {"claims": [first.claim_id, second.claim_id], "type": kind}
                record = NarrativeConflict(_stable_id("narrative-conflict", payload), first.claim_id, second.claim_id, first.evidence_id, second.evidence_id, first.subject, context, kind, "Sources describe opposing outcome directions%s; this requires contextual investigation." % (" in different recorded contexts" if context_dependent else ""), "Neither source is treated as correct; comparability and measurement differences require human review.", [first.provenance, second.provenance])
                (dependencies if context_dependent else conflicts).append(record)
        return sorted(conflicts, key=lambda item: item.conflict_id), sorted(dependencies, key=lambda item: item.conflict_id)

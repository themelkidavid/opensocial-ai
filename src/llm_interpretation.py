"""Provider-neutral, grounded structured interpretation of supplied evidence.

This module deliberately accepts and returns only compact structured records.
It never contacts a network service, stores hidden reasoning, or turns an
interpretation into a fact, recommendation, or validated intervention.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
from typing import Dict, List, Optional

try:
    from src.evidence import EvidenceItem
except ModuleNotFoundError:  # pragma: no cover - supports direct module use
    from evidence import EvidenceItem


def _normalise(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").casefold()).strip()


def _terms(value: object) -> set:
    return set(re.findall(r"[a-z0-9]+", _normalise(value)))


def _stable_id(prefix: str, value: Dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return "%s-%s" % (prefix, hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16])


@dataclass
class InterpretationEvidence:
    """The explicit, minimum evidence payload visible to a provider."""
    evidence_id: str
    text: str
    source_type: str
    date: Optional[str] = None
    location: Optional[str] = None
    population: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InterpretationRequest:
    evidence: List[InterpretationEvidence]
    request_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.evidence or not all(isinstance(item, InterpretationEvidence) for item in self.evidence):
            raise ValueError("Interpretation requests require explicit evidence inputs")
        if len({item.evidence_id for item in self.evidence}) != len(self.evidence):
            raise ValueError("Interpretation request evidence identifiers must be unique")
        self.request_id = self.request_id or _stable_id("interpretation-request", self.to_dict())

    def to_dict(self) -> Dict:
        return {"request_id": self.request_id, "evidence": [item.to_dict() for item in self.evidence]}


@dataclass
class InterpretationResponse:
    """Untrusted provider output; dictionaries are validated before use."""
    claims: List[Dict] = field(default_factory=list)
    mechanisms: List[Dict] = field(default_factory=list)
    conflicts: List[Dict] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    provider_name: str = "unspecified"
    provider_version: Optional[str] = None
    interpretation_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.interpretation_id = self.interpretation_id or _stable_id(
            "interpretation", {"provider_name": self.provider_name, "claims": self.claims,
                               "mechanisms": self.mechanisms, "conflicts": self.conflicts})

    def to_dict(self) -> Dict:
        return asdict(self)


class InterpretationProvider:
    """Small optional interface. Implementations own any future transport."""
    def interpret(self, request: InterpretationRequest) -> InterpretationResponse:
        raise NotImplementedError


class StaticInterpretationProvider(InterpretationProvider):
    """Local test fixture provider; it is not a language model."""
    def __init__(self, response: InterpretationResponse, name: str = "static_fixture", version: str = "1") -> None:
        self.response, self.name, self.version = deepcopy(response), name, version

    def interpret(self, request: InterpretationRequest) -> InterpretationResponse:
        if not isinstance(request, InterpretationRequest):
            raise TypeError("provider requests must be InterpretationRequest instances")
        response = deepcopy(self.response)
        response.provider_name, response.provider_version = self.name, self.version
        return response


@dataclass
class LLMClaimCandidate:
    claim_id: str
    evidence_id: str
    statement: str
    subject: str
    relation: str
    object_or_outcome: str
    direction: str
    polarity: str
    qualifiers: List[str]
    context: Dict[str, Optional[str]]
    supporting_text_span: str
    interpretation_method: str = "llm_assisted"
    review_state: str = "machine_extracted"
    provenance: Dict = field(default_factory=dict)
    def to_dict(self) -> Dict: return asdict(self)


@dataclass
class LLMMechanismCandidate:
    candidate_id: str
    evidence_id: str
    mechanism_text: str
    action: str
    target: str
    intended_or_observed_effect: str
    context: Dict[str, Optional[str]]
    supporting_text_span: str
    interpretation_method: str = "llm_assisted"
    review_state: str = "machine_extracted"
    provenance: Dict = field(default_factory=dict)
    limitations: List[str] = field(default_factory=lambda: ["Candidate records an interpreted source description; it is not a proven intervention."])
    def to_dict(self) -> Dict: return asdict(self)


@dataclass
class LLMConflictCandidate:
    conflict_id: str
    topic: str
    claim_a_reference: str
    claim_b_reference: str
    conflict_type: str
    explanation: str
    context_difference: Dict[str, str]
    review_state: str = "machine_extracted"
    provenance: Dict = field(default_factory=dict)
    def to_dict(self) -> Dict: return asdict(self)


@dataclass
class StructuredInterpretation:
    interpretation_id: str
    claims: List[LLMClaimCandidate] = field(default_factory=list)
    mechanism_candidates: List[LLMMechanismCandidate] = field(default_factory=list)
    conflict_candidates: List[LLMConflictCandidate] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    provider_name: str = "unspecified"
    provider_version: Optional[str] = None
    validation_status: str = "validated"
    validation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"interpretation_id": self.interpretation_id, "claims": [x.to_dict() for x in self.claims],
                "mechanism_candidates": [x.to_dict() for x in self.mechanism_candidates],
                "conflict_candidates": [x.to_dict() for x in self.conflict_candidates],
                "uncertainties": list(self.uncertainties), "provider_name": self.provider_name,
                "provider_version": self.provider_version, "validation_status": self.validation_status,
                "validation_errors": list(self.validation_errors)}


def set_interpretation_review_state(item, state: str):
    """Apply an explicit caller/human review state; providers cannot do this."""
    if state not in InterpretationValidator._REVIEW_STATES:
        raise ValueError("unsupported interpretation review state")
    if not isinstance(item, (LLMClaimCandidate, LLMMechanismCandidate, LLMConflictCandidate)):
        raise TypeError("review state applies only to structured interpretation items")
    item.review_state = state
    return item


class InterpretationValidator:
    """Conservative boundary for untrusted structured interpretation output."""
    _RELATIONS = {"reported_outcome", "reported_barrier", "reported_condition", "reported_action"}
    _DIRECTIONS = {"increase", "decrease", "no_change", "present", "absent", "unknown"}
    _POLARITIES = {"positive", "negative", "neutral", "unknown"}
    _ACTIONS = {"implemented", "introduced", "established", "created", "developed", "used", "provided", "coordinated", "combined", "shared", "supported", "enabled"}
    _CONFLICTS = {"potential_contradiction", "context_difference", "ambiguous_disagreement", "insufficient_information"}
    _REVIEW_STATES = {"machine_extracted", "human_reviewed", "rejected"}

    def validate(self, response: InterpretationResponse, evidence: Dict[str, EvidenceItem]) -> StructuredInterpretation:
        if not isinstance(response, InterpretationResponse):
            raise TypeError("providers must return InterpretationResponse")
        if not isinstance(evidence, dict) or not all(isinstance(x, EvidenceItem) for x in evidence.values()):
            raise TypeError("validation requires a mapping of supplied EvidenceItem records")
        if not isinstance(response.provider_name, str) or not response.provider_name.strip():
            raise ValueError("provider name is required")
        claims = [self._claim(item, evidence, response) for item in self._records(response.claims, "claims")]
        mechanisms = [self._mechanism(item, evidence, response) for item in self._records(response.mechanisms, "mechanisms")]
        self._unique([item.claim_id for item in claims], "claim")
        self._unique([item.candidate_id for item in mechanisms], "mechanism")
        conflicts = [self._conflict(item, claims, response) for item in self._records(response.conflicts, "conflicts")]
        self._unique([item.conflict_id for item in conflicts], "conflict")
        if not all(isinstance(item, str) and item.strip() for item in response.uncertainties):
            raise ValueError("uncertainties must be non-empty strings")
        return StructuredInterpretation(response.interpretation_id, claims, mechanisms, conflicts,
            list(response.uncertainties), response.provider_name, response.provider_version)

    @staticmethod
    def _records(records: object, name: str) -> List[Dict]:
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            raise TypeError("%s must be a list of structured objects" % name)
        return records

    @staticmethod
    def _unique(values: List[str], name: str) -> None:
        if len(values) != len(set(values)):
            raise ValueError("duplicate %s identifiers are not accepted" % name)

    def _source(self, record: Dict, evidence: Dict[str, EvidenceItem]):
        evidence_id = record.get("evidence_id")
        if evidence_id not in evidence:
            raise ValueError("interpretation references unknown evidence")
        item = evidence[evidence_id]
        span = record.get("supporting_text_span")
        if not isinstance(span, str) or len(span.strip()) < 3 or _normalise(span) not in _normalise(item.content):
            raise ValueError("supporting_text_span must be grounded in supplied evidence")
        return evidence_id, item, span.strip()

    @staticmethod
    def _grounded(value: object, item: EvidenceItem, span: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("%s must be a non-empty string" % field)
        allowed = _terms(item.content) | _terms(item.location) | _terms(item.population) | _terms(item.date)
        value_terms = _terms(value)
        if not value_terms or not value_terms.issubset(allowed):
            raise ValueError("%s is not grounded in supplied evidence" % field)
        return value.strip()

    def _context(self, value: object, item: EvidenceItem) -> Dict[str, Optional[str]]:
        if not isinstance(value, dict) or set(value) - {"location", "population", "date", "source_type"}:
            raise ValueError("context uses unsupported fields")
        expected = {"location": item.location, "population": item.population, "date": item.date, "source_type": item.source_type}
        for key, supplied in value.items():
            if supplied is not None and supplied != expected[key]:
                raise ValueError("context is not grounded in supplied evidence")
        return {key: value.get(key, expected[key]) for key in expected}

    def _claim(self, record: Dict, evidence: Dict[str, EvidenceItem], response: InterpretationResponse) -> LLMClaimCandidate:
        evidence_id, item, span = self._source(record, evidence)
        if record.get("relation") not in self._RELATIONS or record.get("direction") not in self._DIRECTIONS or record.get("polarity") not in self._POLARITIES:
            raise ValueError("claim has unsupported relationship, direction, or polarity")
        statement = self._grounded(record.get("statement", span), item, span, "statement")
        subject = self._grounded(record.get("subject"), item, span, "subject")
        outcome = self._grounded(record.get("object_or_outcome"), item, span, "object_or_outcome")
        qualifiers = record.get("qualifiers", [])
        if not isinstance(qualifiers, list) or any(not isinstance(x, str) or not x.strip() for x in qualifiers):
            raise ValueError("qualifiers must be strings")
        self._review(record.get("review_state", "machine_extracted"))
        identifier = record.get("claim_id") or _stable_id("llm-claim", {"evidence_id": evidence_id, "span": span, "subject": subject, "outcome": outcome})
        return LLMClaimCandidate(identifier, evidence_id, statement, subject, record["relation"], outcome,
            record["direction"], record["polarity"], list(qualifiers), self._context(record.get("context", {}), item), span,
            provenance={"interpretation_method": "llm_assisted", "provider_name": response.provider_name,
                        "provider_version": response.provider_version, "source_evidence_id": evidence_id})

    def _mechanism(self, record: Dict, evidence: Dict[str, EvidenceItem], response: InterpretationResponse) -> LLMMechanismCandidate:
        evidence_id, item, span = self._source(record, evidence)
        if record.get("action") not in self._ACTIONS:
            raise ValueError("mechanism action is unsupported")
        mechanism = self._grounded(record.get("mechanism_text"), item, span, "mechanism_text")
        target = self._grounded(record.get("target"), item, span, "target")
        effect = self._grounded(record.get("intended_or_observed_effect"), item, span, "intended_or_observed_effect")
        self._review(record.get("review_state", "machine_extracted"))
        identifier = record.get("candidate_id") or _stable_id("llm-mechanism", {"evidence_id": evidence_id, "span": span, "action": record["action"]})
        return LLMMechanismCandidate(identifier, evidence_id, mechanism, record["action"], target, effect,
            self._context(record.get("context", {}), item), span,
            provenance={"interpretation_method": "llm_assisted", "provider_name": response.provider_name,
                        "provider_version": response.provider_version, "source_evidence_id": evidence_id})

    def _conflict(self, record: Dict, claims: List[LLMClaimCandidate], response: InterpretationResponse) -> LLMConflictCandidate:
        if record.get("conflict_type") not in self._CONFLICTS:
            raise ValueError("unsupported conflict type")
        claim_ids = {item.claim_id for item in claims}
        if record.get("claim_a_reference") not in claim_ids or record.get("claim_b_reference") not in claim_ids:
            raise ValueError("conflict references unknown assisted claim")
        if record["claim_a_reference"] == record["claim_b_reference"]:
            raise ValueError("conflict requires two different claims")
        topic = record.get("topic")
        explanation = record.get("explanation")
        if not isinstance(topic, str) or not topic.strip() or not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("conflict requires a factual topic and explanation")
        context_difference = record.get("context_difference", {})
        if not isinstance(context_difference, dict):
            raise ValueError("conflict context_difference must be structured")
        self._review(record.get("review_state", "machine_extracted"))
        identifier = record.get("conflict_id") or _stable_id("llm-conflict", {"a": record["claim_a_reference"], "b": record["claim_b_reference"], "type": record["conflict_type"]})
        return LLMConflictCandidate(identifier, topic.strip(), record["claim_a_reference"], record["claim_b_reference"],
            record["conflict_type"], explanation.strip(), dict(context_difference),
            provenance={"interpretation_method": "llm_assisted", "provider_name": response.provider_name,
                        "provider_version": response.provider_version})

    def _review(self, value: object) -> None:
        if value not in self._REVIEW_STATES:
            raise ValueError("unsupported interpretation review state")


def compare_interpretations(rule_based, assisted: Optional[StructuredInterpretation]) -> Dict:
    """Describe overlap without assigning a quality score or winner."""
    assisted = assisted or StructuredInterpretation("none")
    rule_claims = {getattr(x, "raw_text", "") for x in getattr(rule_based, "claims", [])}
    assisted_claims = {x.supporting_text_span for x in assisted.claims}
    rule_mechanisms = {getattr(x, "raw_text", "") for x in getattr(rule_based, "mechanism_candidates", [])}
    assisted_mechanisms = {x.supporting_text_span for x in assisted.mechanism_candidates}
    return {"claims_found_by_both": sorted(rule_claims & assisted_claims), "claims_only_rule_based": sorted(rule_claims - assisted_claims),
            "claims_only_assisted": sorted(assisted_claims - rule_claims), "mechanisms_found_by_both": sorted(rule_mechanisms & assisted_mechanisms),
            "mechanisms_only_assisted": sorted(assisted_mechanisms - rule_mechanisms),
            "rule_based_potential_conflicts": [x.to_dict() for x in getattr(rule_based, "narrative_conflicts", [])],
            "assisted_potential_conflicts": [x.to_dict() for x in assisted.conflict_candidates],
            "grounding_failures": list(assisted.validation_errors)}

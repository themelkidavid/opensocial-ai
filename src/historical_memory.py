"""Optional, provenance-preserving historical programme and mechanism memory."""
from dataclasses import asdict, dataclass, field
import csv
import hashlib
import json
from io import StringIO
import sqlite3
from typing import Dict, List, Optional

from src.innovation_inspiration import InnovationInspiration, InnovationInspirationEngine
from src.retrieval import KeywordRetriever, RelevanceRetriever


@dataclass
class HistoricalProgramme:
    title: str
    problem_addressed: str
    mechanism: str
    programme_id: Optional[str] = None
    sector: Optional[str] = None
    geography: Optional[str] = None
    target_population: Optional[str] = None
    activities: List[str] = field(default_factory=list)
    observed_results: List[str] = field(default_factory=list)
    evidence_basis: List[str] = field(default_factory=list)
    outcome_metrics: List[Dict] = field(default_factory=list)
    source_type: str = "historical"
    provenance_source_id: Optional[str] = None
    provenance_reference: Optional[str] = None
    start_period: Optional[str] = None
    end_period: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    transferability: str = "exploratory"
    learning: Optional[str] = None
    created_at: Optional[str] = None
    def to_dict(self): return asdict(self)


@dataclass
class MechanismRecord:
    name: str
    description: str
    mechanism_id: Optional[str] = None
    source_programme_ids: List[str] = field(default_factory=list)
    sectors_seen: List[str] = field(default_factory=list)
    populations_seen: List[str] = field(default_factory=list)
    contexts_seen: List[str] = field(default_factory=list)
    observed_results: List[str] = field(default_factory=list)
    evidence_basis: List[str] = field(default_factory=list)
    outcome_metrics: List[Dict] = field(default_factory=list)
    uncertainty: List[str] = field(default_factory=list)
    provenance: Optional[str] = None
    def to_dict(self): return asdict(self)


@dataclass
class HistoricalProgrammeCandidate:
    programme: HistoricalProgramme
    retrieval_strategy: str
    relevance_score: float
    target_sector: Optional[str]
    why_it_may_be_relevant: str
    uncertainty: List[str]
    adaptation_questions: List[str]
    def to_dict(self):
        result = asdict(self); result["programme"] = self.programme.to_dict(); return result


class HistoricalProgrammeIngestion:
    """Deterministic JSON/CSV mapping; missing fields remain None or empty."""
    def from_json(self, payload):
        value = json.loads(payload)
        records = value.get("records") if isinstance(value, dict) else value
        if not isinstance(records, list): raise ValueError("historical JSON must contain a records list")
        return [self._build(item) for item in records]
    def from_csv(self, payload):
        rows = list(csv.DictReader(StringIO(payload)))
        if not rows and not payload.strip(): raise ValueError("historical CSV must include headers")
        return [self._build(row, csv_mode=True) for row in rows]
    def _build(self, value, csv_mode=False):
        if not isinstance(value, dict): raise ValueError("historical programme record must be an object")
        for name in ("title", "problem_addressed", "mechanism"):
            if not isinstance(value.get(name), str) or not value[name].strip(): raise ValueError(f"historical programme requires {name}")
        def text(name):
            item = value.get(name); return item.strip() if isinstance(item, str) and item.strip() else None
        def items(name):
            item = value.get(name, [])
            if csv_mode and isinstance(item, str): item = json.loads(item) if item else []
            if not isinstance(item, list) or not all(isinstance(x, str) and x.strip() for x in item): raise ValueError(f"{name} must be a list of text")
            return [x.strip() for x in item]
        return HistoricalProgramme(value["title"].strip(), value["problem_addressed"].strip(), value["mechanism"].strip(), programme_id=text("programme_id"), sector=text("sector"), geography=text("geography"), target_population=text("target_population"), activities=items("activities"), observed_results=items("observed_results"), evidence_basis=items("evidence_basis"), source_type=text("source_type") or "historical", provenance_source_id=text("provenance_source_id"), provenance_reference=text("provenance_reference"), limitations=items("limitations"), transferability=text("transferability") or "exploratory", learning=text("learning"))


class HistoricalMemoryStore:
    """Small SQLite repository with idempotent external-source handling."""
    def __init__(self, path=":memory:"):
        self.connection=sqlite3.connect(str(path)); self.connection.row_factory=sqlite3.Row
        self.connection.execute("CREATE TABLE IF NOT EXISTS historical_programmes (programme_id TEXT PRIMARY KEY, source_id TEXT UNIQUE, payload TEXT NOT NULL)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS historical_links (programme_id TEXT, mechanism_id TEXT, learning_id TEXT, PRIMARY KEY(programme_id, mechanism_id, learning_id))"); self.connection.commit()
    def save_programme(self, programme):
        if not isinstance(programme, HistoricalProgramme): raise TypeError("programme must be HistoricalProgramme")
        key=programme.provenance_source_id or programme.programme_id
        if key:
            row=self.connection.execute("SELECT payload FROM historical_programmes WHERE source_id=?",(key,)).fetchone()
            if row: return _programme(json.loads(row["payload"]))
        payload=programme.to_dict(); programme_id=programme.programme_id or "programme-"+hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:24]
        payload["programme_id"]=programme_id
        self.connection.execute("INSERT INTO historical_programmes VALUES (?,?,?)",(programme_id,key,json.dumps(payload,sort_keys=True))); self.connection.commit(); return _programme(payload)
    def list_programmes(self): return [_programme(json.loads(row["payload"])) for row in self.connection.execute("SELECT payload FROM historical_programmes")]
    def link_learning(self, programme_id, mechanism_id, learning_id):
        self.connection.execute("INSERT OR IGNORE INTO historical_links VALUES (?,?,?)",(programme_id,mechanism_id,learning_id)); self.connection.commit()


class HistoricalDiscoveryEngine:
    def __init__(self,retriever=None): self.engine=InnovationInspirationEngine(retriever=retriever or KeywordRetriever())
    def discover(self, problem, programmes, target_sector=None, minimum_score=None):
        inspirations=[InnovationInspiration(source_type="historical",title=p.title,context=p.geography or "unknown context",mechanism=p.mechanism,observed_result="; ".join(p.observed_results) or "No observed result recorded.",transferability=p.transferability,sector=p.sector,target_population=p.target_population,provenance_source_id=p.provenance_source_id,provenance_reference=p.provenance_reference) for p in programmes]
        matches=self.engine.find_relevant_matches(problem,inspirations); by_title={p.title:p for p in programmes}; results=[]
        for match in matches:
            if minimum_score is not None and match.score < minimum_score: continue
            programme=by_title[match.inspiration.title]
            results.append(HistoricalProgrammeCandidate(programme,match.strategy,match.score,target_sector,f"Historical candidate retrieved by {match.strategy} because of documented mechanism: {programme.mechanism}",["Historical similarity does not establish contextual equivalence or effectiveness.",*programme.limitations],["What assumptions from the historical context may not hold here?","What evidence gaps should be resolved before considering a pilot?","What unintended effects are plausible?"]))
        return results


def _programme(value): return HistoricalProgramme(**value)

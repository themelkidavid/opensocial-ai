"""
OpenSocial AI – Evidence Layer

Defines a standard structure for evidence used by the
Innovation Discovery Engine.

The evidence layer allows OpenSocial AI to work with
programme data, historical reports, community feedback,
research, field observations and organisational knowledge
without tying the system to a specific AI model.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class EvidenceItem:
    """A single piece of evidence available for analysis."""

    source_type: str
    content: str
    date: Optional[str] = None
    location: Optional[str] = None
    population: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Return the evidence item as a dictionary."""
        return {
            "source_type": self.source_type,
            "content": self.content,
            "date": self.date,
            "location": self.location,
            "population": self.population,
            "metadata": self.metadata,
        }


def create_evidence(
    source_type: str,
    content: str,
    date: Optional[str] = None,
    location: Optional[str] = None,
    population: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> EvidenceItem:
    """
    Create a validated EvidenceItem.

    Evidence content must not be empty.
    """

    if not source_type.strip():
        raise ValueError("source_type cannot be empty")

    if not content.strip():
        raise ValueError("content cannot be empty")

    return EvidenceItem(
        source_type=source_type.strip(),
        content=content.strip(),
        date=date,
        location=location,
        population=population,
        metadata=metadata or {},
    )
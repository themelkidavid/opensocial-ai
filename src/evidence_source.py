"""
OpenSocial AI – Evidence Source Layer

Defines the original source from which evidence is obtained.

An EvidenceSource can represent documents, datasets, surveys,
programme databases, research, community feedback or field
observations.

The source is kept separate from EvidenceItem so that findings
can remain traceable to their origin.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class EvidenceSource:
    """Represents an original source of evidence."""

    source_type: str
    name: str
    description: Optional[str] = None
    uri: Optional[str] = None
    date: Optional[str] = None
    organisation: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Return the evidence source as a dictionary."""
        return {
            "source_type": self.source_type,
            "name": self.name,
            "description": self.description,
            "uri": self.uri,
            "date": self.date,
            "organisation": self.organisation,
            "metadata": self.metadata,
        }


def create_source(
    source_type: str,
    name: str,
    description: Optional[str] = None,
    uri: Optional[str] = None,
    date: Optional[str] = None,
    organisation: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> EvidenceSource:
    """Create a validated EvidenceSource."""

    if not source_type.strip():
        raise ValueError("source_type cannot be empty")

    if not name.strip():
        raise ValueError("name cannot be empty")

    return EvidenceSource(
        source_type=source_type.strip(),
        name=name.strip(),
        description=description,
        uri=uri,
        date=date,
        organisation=organisation,
        metadata=metadata or {},
    )
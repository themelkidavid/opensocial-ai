"""Manual-only OpenAI interpretation smoke test; never run by CI."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evidence import EvidenceItem
from src.narrative_reasoning import NarrativeReasoningEngine
from src.providers.openai_interpretation import OpenAIInterpretationProvider


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY before running this optional fictional-evidence smoke test.")
    provider = OpenAIInterpretationProvider(model=os.environ.get("OPENAI_INTERPRETATION_MODEL"))
    evidence = EvidenceItem("fictional_report", "FICTIONAL: Members reported that peer meetings improved coordination.",
                            location="Fictional region", population="fictional members")
    analysis = NarrativeReasoningEngine(interpretation_provider=provider).analyse([evidence], ["fictional-evidence-1"])
    print(json.dumps(analysis.to_dict().get("assisted_interpretation", {"errors": analysis.interpretation_errors}), indent=2))


if __name__ == "__main__":
    main()

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from visit_scribe.schema import Segment, VisitRecord


@dataclass
class PipelineOutput:
    record: VisitRecord
    transcript: list[Segment] | None = None
    """Raw speech-to-text output before drug-name correction. None when nothing was transcribed."""
    drug_mentions: list[str] = field(default_factory=list)
    """Canonical brand names the pipeline believes were said (stage 5 output)."""


class Pipeline(Protocol):
    name: str

    def run(self, audio: Path | None, reference: list[Segment]) -> PipelineOutput:
        """`reference` is the scripted transcript, for text-only runs that skip speech-to-text."""
        ...

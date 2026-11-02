import re
from dataclasses import dataclass
from pathlib import Path

from visit_scribe.schema import Segment, Speaker, VisitRecord

AUDIO_EXTENSIONS = {".wav", ".m4a", ".mp3", ".ogg", ".opus", ".webm", ".flac"}
_SPEAKERS = {"D": Speaker.DOCTOR, "P": Speaker.PATIENT}
_LINE = re.compile(r"^([DP]):\s*(.+)$")


@dataclass
class EvalCase:
    id: str
    lang: str
    segments: list[Segment]
    gold: VisitRecord
    audio: Path | None


def load_script(path: Path) -> list[Segment]:
    segments: list[Segment] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _LINE.match(line)
        if not match:
            raise ValueError(f"{path}:{number}: expected a line starting with 'D:' or 'P:'")
        segments.append(Segment(id=len(segments), speaker=_SPEAKERS[match[1]], text=match[2]))
    return segments


def load_case(directory: Path) -> EvalCase:
    audio = next(
        (
            path
            for path in sorted(directory.iterdir())
            if path.stem == "audio" and path.suffix.lower() in AUDIO_EXTENSIONS
        ),
        None,
    )
    return EvalCase(
        id=directory.name,
        lang=directory.name.split("_")[0],
        segments=load_script(directory / "script.txt"),
        gold=VisitRecord.model_validate_json((directory / "gold.json").read_text(encoding="utf-8")),
        audio=audio,
    )


def load_cases(root: Path) -> list[EvalCase]:
    return [load_case(path) for path in sorted(root.iterdir()) if (path / "script.txt").exists()]

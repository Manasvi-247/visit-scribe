from enum import StrEnum

from pydantic import BaseModel, Field


class Speaker(StrEnum):
    DOCTOR = "doctor"
    PATIENT = "patient"


class Segment(BaseModel):
    id: int
    speaker: Speaker
    text: str
    lang: str | None = None


class Food(StrEnum):
    BEFORE = "before"
    AFTER = "after"
    ANY = "any"


class Medication(BaseModel):
    name: str
    generic: str | None = None
    form: str | None = None
    dose: str | None = None
    frequency_code: str | None = Field(
        default=None, description='Indian prescription notation, e.g. "1-0-1", or "SOS"'
    )
    food: Food = Food.ANY
    duration_days: int | None = None
    source_segments: list[int] = []
    confidence: float | None = None
    confirmed: bool = False


class LabTest(BaseModel):
    name: str
    when: str | None = None
    source_segments: list[int] = []


class FollowUp(BaseModel):
    in_days: int | None = None
    reason: str | None = None
    source_segments: list[int] = []


class Note(BaseModel):
    text: str
    source_segments: list[int] = []


class Summary(BaseModel):
    en: str = ""
    hi: str = ""


class VisitRecord(BaseModel):
    summary: Summary = Field(default_factory=Summary)
    diagnosis: list[Note] = []
    medications: list[Medication] = []
    tests: list[LabTest] = []
    follow_up: FollowUp | None = None
    instructions: list[Note] = []
    open_questions: list[str] = []

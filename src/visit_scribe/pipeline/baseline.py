"""Keyword and regex stand-in for stages 5 to 8, run on the reference script instead of audio.

It is the floor every real stage has to beat.
"""

import re
import unicodedata
from pathlib import Path

from visit_scribe.medicines import MedicineIndex
from visit_scribe.pipeline.base import PipelineOutput
from visit_scribe.schema import FollowUp, Food, LabTest, Medication, Segment, Speaker, VisitRecord

SEED_MEDICINES = Path(__file__).resolve().parents[3] / "data" / "medicines_seed.csv"


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _alternation(words) -> str:
    return "|".join(sorted((re.escape(_nfc(w)) for w in words), key=len, reverse=True))


NUMBER_WORDS = {
    "one": 1, "ek": 1, "एक": 1,
    "two": 2, "do": 2, "दो": 2,
    "three": 3, "teen": 3, "तीन": 3,
    "four": 4, "chaar": 4, "चार": 4,
    "five": 5, "paanch": 5, "पाँच": 5, "पांच": 5,
    "seven": 7, "saat": 7, "सात": 7,
    "ten": 10, "das": 10, "दस": 10,
}  # fmt: skip
NUMBER_WORDS = {_nfc(word): n for word, n in NUMBER_WORDS.items()}

DAYS_PER_UNIT = {
    "day": 1, "days": 1, "din": 1, "दिन": 1,
    "week": 7, "weeks": 7, "hafta": 7, "hafte": 7, "हफ़्ता": 7, "हफ़्ते": 7, "हफ्ते": 7,
    "month": 30, "months": 30, "mahina": 30, "mahine": 30, "महीना": 30, "महीने": 30,
}  # fmt: skip
DAYS_PER_UNIT = {_nfc(word): n for word, n in DAYS_PER_UNIT.items()}

_NUMBER = rf"\d+|{_alternation(NUMBER_WORDS)}"
DURATION = re.compile(rf"(?<!\S)({_NUMBER})\s+({_alternation(DAYS_PER_UNIT)})(?!\w)")
COUNTED_DOSE = re.compile(
    rf"(?<!\S)({_NUMBER})\s+(tablets?|capsules?|goli|chammach|teaspoons?)(?!\w)"
)
MEASURED_DOSE = re.compile(r"(\d+(?:\.\d+)?)\s*(ml|mg)(?!\w)")

FREQUENCY_RULES = [
    (re.compile(_nfc(r"three times|teen baar|तीन बार")), "1-1-1"),
    (re.compile(_nfc(r"twice|two times|do baar|दो बार")), "1-0-1"),
    (re.compile(_nfc(r"(?<!\S)(sos|jab|जब)(?!\S)|when needed")), "SOS"),
    (re.compile(_nfc(r"once a day|morning|subah|सुबह")), "1-0-0"),
]
BEFORE_FOOD = re.compile(_nfc(r"before|pehle|पहले|khali pet|खाली पेट"))
AFTER_FOOD = re.compile(_nfc(r"after|baad|बाद"))

TEST_RULES = [
    (re.compile(r"hba1c"), "HbA1c"),
    (re.compile(_nfc(r"(?<![a-z])cbc(?![a-z])|सीबीसी")), "CBC"),
    (re.compile(r"fasting (blood )?sugar"), "Fasting blood sugar"),
    (re.compile(r"urine routine"), "Urine routine"),
    (re.compile(r"culture"), "Urine culture"),
]
FOLLOW_UP = re.compile(_nfc(r"come back|see me again|follow[ -]?up|dikha|दिखा"))


def _number(word: str) -> int:
    return int(word) if word.isdigit() else NUMBER_WORDS[word]


def _days(text: str) -> int | None:
    match = DURATION.search(text)
    return _number(match[1]) * DAYS_PER_UNIT[match[2]] if match else None


def _dose(text: str) -> str | None:
    if match := COUNTED_DOSE.search(text):
        return f"{_number(match[1])} {match[2]}"
    if match := MEASURED_DOSE.search(text):
        return f"{match[1]} {match[2]}"
    return None


def _frequency(text: str) -> str | None:
    return next((code for pattern, code in FREQUENCY_RULES if pattern.search(text)), None)


def _food(text: str) -> Food:
    if BEFORE_FOOD.search(text):
        return Food.BEFORE
    if AFTER_FOOD.search(text):
        return Food.AFTER
    return Food.ANY


class BaselinePipeline:
    name = "baseline"

    def __init__(self, medicines: MedicineIndex | None = None):
        self.medicines = medicines or MedicineIndex.from_csv(SEED_MEDICINES)

    def run(self, audio: Path | None, reference: list[Segment]) -> PipelineOutput:
        record = VisitRecord()
        mentions: list[str] = []
        for segment in reference:
            text = _nfc(segment.text.lower())
            found = self.medicines.find(text)
            mentions += [medicine.brand for medicine in found]
            if segment.speaker is not Speaker.DOCTOR:
                continue

            for medicine in found:
                record.medications.append(
                    Medication(
                        name=medicine.brand,
                        generic=medicine.generic,
                        form=medicine.form,
                        dose=_dose(text),
                        frequency_code=_frequency(text),
                        food=_food(text),
                        duration_days=_days(text),
                        source_segments=[segment.id],
                    )
                )

            known_tests = {test.name for test in record.tests}
            for pattern, test_name in TEST_RULES:
                if test_name not in known_tests and pattern.search(text):
                    record.tests.append(LabTest(name=test_name, source_segments=[segment.id]))

            if record.follow_up is None and not found and FOLLOW_UP.search(text):
                if days := _days(text):
                    record.follow_up = FollowUp(in_days=days, source_segments=[segment.id])

        return PipelineOutput(record=record, drug_mentions=mentions)

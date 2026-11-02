from pathlib import Path

from visit_scribe.evaluation.cases import load_case
from visit_scribe.pipeline.baseline import BaselinePipeline

CASES = Path(__file__).resolve().parents[1] / "eval" / "cases"


def test_reads_english_prescription():
    case = load_case(CASES / "en_001")
    record = BaselinePipeline().run(None, case.segments).record
    dolo = next(m for m in record.medications if m.name == "Dolo 650")
    assert (dolo.dose, dolo.frequency_code, dolo.food, dolo.duration_days) == (
        "1 tablet",
        "1-1-1",
        "after",
        3,
    )
    assert record.follow_up.in_days == 5


def test_reads_hindi_follow_up():
    case = load_case(CASES / "hi_001")
    record = BaselinePipeline().run(None, case.segments).record
    assert record.follow_up.in_days == 14

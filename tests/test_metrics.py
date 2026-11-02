from pathlib import Path

from visit_scribe.evaluation.cases import load_case
from visit_scribe.evaluation.metrics import score_case, summarize, word_edits
from visit_scribe.pipeline.base import PipelineOutput
from visit_scribe.schema import Medication, VisitRecord

CASE = Path(__file__).resolve().parents[1] / "eval" / "cases" / "en_001"


def test_word_edits():
    assert word_edits("take one tablet", "take one tablet") == 0
    assert word_edits("take one tablet", "take two tablet") == 1
    assert word_edits("take one tablet", "take tablet") == 1
    assert word_edits("नमक कम खाइए।", "नमक कम खाइए") == 0


def test_perfect_output_meets_every_target():
    case = load_case(CASE)
    output = PipelineOutput(
        record=case.gold,
        transcript=case.segments,
        drug_mentions=[m.name for m in case.gold.medications],
    )
    summary = summarize([score_case(case, output, 0.0)])
    assert summary["wer"] == 0.0
    assert summary["drug_recall"] == 1.0
    assert summary["dose_frequency_accuracy"] == 1.0
    assert summary["f1"] == 1.0
    assert summary["unsupported_items"] == 0


def test_taper_steps_are_scored_separately():
    case = load_case(CASE)
    first_step = Medication(name="Wysolone 10", dose="2 tablets", frequency_code="1-0-0")
    second_step = Medication(name="Wysolone 10", dose="1 tablet", frequency_code="1-0-0")
    case.gold = VisitRecord(medications=[first_step, second_step])
    predicted = VisitRecord(medications=[first_step.model_copy(update={"source_segments": [4]})])
    score = score_case(case, PipelineOutput(record=predicted), 0.0)
    assert (score.true_positives, score.false_negatives) == (1, 1)
    assert (score.meds_matched, score.dose_and_frequency_correct) == (1, 1)


def test_empty_output_scores_zero_recall():
    case = load_case(CASE)
    summary = summarize([score_case(case, PipelineOutput(record=VisitRecord()), 0.0)])
    assert summary["recall"] == 0.0
    assert summary["precision"] is None
    assert summary["wer"] is None

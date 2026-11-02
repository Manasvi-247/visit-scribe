import unicodedata
from collections import Counter
from dataclasses import dataclass

from visit_scribe.evaluation.cases import EvalCase
from visit_scribe.notation import name_key, normalize_dose, normalize_frequency
from visit_scribe.pipeline.base import PipelineOutput
from visit_scribe.schema import Medication, VisitRecord


@dataclass
class CaseScore:
    case_id: str
    lang: str
    word_edits: int | None
    reference_words: int | None
    drugs_heard: int
    drugs_total: int
    true_positives: int
    false_positives: int
    false_negatives: int
    meds_matched: int
    dose_and_frequency_correct: int
    unsupported_items: int
    seconds: float


def words(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text.lower())
    return "".join(" " if unicodedata.category(ch).startswith("P") else ch for ch in text).split()


def word_edits(reference: str, hypothesis: str) -> int:
    ref, hyp = words(reference), words(hypothesis)
    previous = list(range(len(hyp) + 1))
    for i, ref_word in enumerate(ref, 1):
        current = [i] + [0] * len(hyp)
        for j, hyp_word in enumerate(hyp, 1):
            current[j] = min(
                previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ref_word != hyp_word)
            )
        previous = current
    return previous[-1]


def _medications_by_key(record: VisitRecord) -> dict[str, Medication]:
    """Repeated names (a taper's steps) get #1, #2 suffixes so each step is scored separately."""
    seen: Counter[str] = Counter()
    keyed = {}
    for med in record.medications:
        key = name_key(med.name)
        seen[key] += 1
        keyed[f"{key}#{seen[key]}"] = med
    return keyed


def _items(record: VisitRecord) -> dict[str, list[int]]:
    """Scorable items keyed by identity, each with the segments it cites."""
    items: dict[str, list[int]] = {}
    for key, med in _medications_by_key(record).items():
        items[f"med:{key}"] = med.source_segments
    for test in record.tests:
        items.setdefault(f"test:{name_key(test.name)}", test.source_segments)
    if record.follow_up and record.follow_up.in_days is not None:
        items[f"follow_up:{record.follow_up.in_days}"] = record.follow_up.source_segments
    return items


def score_case(case: EvalCase, output: PipelineOutput, seconds: float) -> CaseScore:
    gold_items, predicted_items = _items(case.gold), _items(output.record)
    segment_count = len(case.segments)
    unsupported = sum(
        1
        for cited in predicted_items.values()
        if not cited or any(not 0 <= s < segment_count for s in cited)
    )

    gold_meds = _medications_by_key(case.gold)
    predicted_meds = _medications_by_key(output.record)
    matched = gold_meds.keys() & predicted_meds.keys()
    correct = sum(
        1
        for key in matched
        if normalize_dose(gold_meds[key].dose) == normalize_dose(predicted_meds[key].dose)
        and normalize_frequency(gold_meds[key].frequency_code)
        == normalize_frequency(predicted_meds[key].frequency_code)
    )
    gold_names = {name_key(m.name) for m in case.gold.medications}
    heard = {name_key(name) for name in output.drug_mentions}

    edits = reference_words = None
    if output.transcript is not None:
        reference = " ".join(s.text for s in case.segments)
        edits = word_edits(reference, " ".join(s.text for s in output.transcript))
        reference_words = len(words(reference))

    return CaseScore(
        case_id=case.id,
        lang=case.lang,
        word_edits=edits,
        reference_words=reference_words,
        drugs_heard=len(gold_names & heard),
        drugs_total=len(gold_names),
        true_positives=len(gold_items.keys() & predicted_items.keys()),
        false_positives=len(predicted_items.keys() - gold_items.keys()),
        false_negatives=len(gold_items.keys() - predicted_items.keys()),
        meds_matched=len(matched),
        dose_and_frequency_correct=correct,
        unsupported_items=unsupported,
        seconds=seconds,
    )


def _ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def summarize(scores: list[CaseScore]) -> dict[str, float | int | None]:
    transcribed = [s for s in scores if s.word_edits is not None]
    tp = sum(s.true_positives for s in scores)
    precision = _ratio(tp, tp + sum(s.false_positives for s in scores))
    recall = _ratio(tp, tp + sum(s.false_negatives for s in scores))
    if precision is None or recall is None:
        f1 = None
    else:
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "cases": len(scores),
        "wer": _ratio(
            sum(s.word_edits for s in transcribed), sum(s.reference_words for s in transcribed)
        ),
        "drug_recall": _ratio(
            sum(s.drugs_heard for s in scores), sum(s.drugs_total for s in scores)
        ),
        "dose_frequency_accuracy": _ratio(
            sum(s.dose_and_frequency_correct for s in scores),
            sum(s.meds_matched for s in scores),
        ),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "unsupported_items": sum(s.unsupported_items for s in scores),
        "seconds_per_case": _ratio(sum(s.seconds for s in scores), len(scores)),
    }

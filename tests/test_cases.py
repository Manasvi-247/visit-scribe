from pathlib import Path

from visit_scribe.evaluation.cases import load_cases
from visit_scribe.schema import Speaker

CASES = Path(__file__).resolve().parents[1] / "eval" / "cases"


def test_gold_labels_cite_real_lines():
    cases = load_cases(CASES)
    assert len(cases) >= 6
    for case in cases:
        gold = case.gold
        cited = [s for m in gold.medications for s in m.source_segments]
        cited += [s for t in gold.tests for s in t.source_segments]
        cited += [s for n in gold.instructions + gold.diagnosis for s in n.source_segments]
        if gold.follow_up:
            cited += gold.follow_up.source_segments
        assert all(0 <= s < len(case.segments) for s in cited), case.id


def test_medications_come_from_the_doctor():
    for case in load_cases(CASES):
        assert case.gold.medications, case.id
        for med in case.gold.medications:
            speakers = {case.segments[s].speaker for s in med.source_segments}
            assert speakers == {Speaker.DOCTOR}, (case.id, med.name)

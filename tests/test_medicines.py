from visit_scribe.medicines import MedicineIndex
from visit_scribe.pipeline.baseline import SEED_MEDICINES


def test_finds_brands_in_order_and_prefers_longest():
    index = MedicineIndex.from_csv(SEED_MEDICINES)
    found = index.find("Continue Glycomet GP 1 and take Pan-D before breakfast")
    assert [m.brand for m in found] == ["Glycomet GP 1", "Pan-D"]


def test_does_not_match_inside_other_words():
    index = MedicineIndex.from_csv(SEED_MEDICINES)
    assert index.find("the pandemic is over") == []

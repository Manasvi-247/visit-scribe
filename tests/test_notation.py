import pytest

from visit_scribe.notation import name_key, normalize_dose, normalize_frequency


@pytest.mark.parametrize(
    ("code", "expected"),
    [("TDS", "1-1-1"), ("bd", "1-0-1"), ("OD", "1-0-0"), ("HS", "0-0-1"), ("1 - 0 - 1", "1-0-1"),
     ("sos", "SOS"), (None, None)],
)  # fmt: skip
def test_normalize_frequency(code, expected):
    assert normalize_frequency(code) == expected


@pytest.mark.parametrize(
    ("dose", "expected"),
    [("one tablet", "1 unit"), ("1 tab", "1 unit"), ("ek goli", "1 unit"), ("एक गोली", "1 unit"),
     ("10ml", "10 ml"), ("दो चम्मच", "2 tsp"), ("2 teaspoons", "2 tsp"), ("100 mg", "100 mg")],
)  # fmt: skip
def test_normalize_dose(dose, expected):
    assert normalize_dose(dose) == expected


def test_name_key_ignores_case_spaces_and_hyphens():
    assert name_key("Pan-D") == name_key("pan d") == "pand"

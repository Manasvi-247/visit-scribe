import re
import unicodedata

FREQUENCY_ALIASES = {
    "od": "1-0-0",
    "qd": "1-0-0",
    "bd": "1-0-1",
    "bid": "1-0-1",
    "tds": "1-1-1",
    "tid": "1-1-1",
    "qid": "1-1-1-1",
    "hs": "0-0-1",
    "sos": "SOS",
    "prn": "SOS",
}

NUMBER_WORDS = {
    "half": "0.5",
    "aadha": "0.5",
    "आधा": "0.5",
    "आधी": "0.5",
    "one": "1",
    "ek": "1",
    "एक": "1",
    "two": "2",
    "do": "2",
    "दो": "2",
    "dhai": "2.5",
    "ढाई": "2.5",
    "three": "3",
    "teen": "3",
    "तीन": "3",
    "five": "5",
    "paanch": "5",
    "पाँच": "5",
    "पांच": "5",
}

DOSE_UNITS = {
    "unit": {"tablet", "tablets", "tab", "tabs", "capsule", "capsules", "cap", "caps"}
    | {"goli", "गोली"},
    "ml": {"ml", "एमएल"},
    "mg": {"mg"},
    "tsp": {"teaspoon", "teaspoons", "tsp", "chammach", "चम्मच"},
}
_UNIT_OF = {
    unicodedata.normalize("NFC", word): unit for unit, words in DOSE_UNITS.items() for word in words
}
_NUMBER_OF = {unicodedata.normalize("NFC", word): n for word, n in NUMBER_WORDS.items()}


def normalize_frequency(code: str | None) -> str | None:
    if code is None:
        return None
    compact = code.strip().lower().replace(" ", "")
    return FREQUENCY_ALIASES.get(compact, compact)


def normalize_dose(dose: str | None) -> str | None:
    """Reduce "one tablet", "1 tab" and "एक गोली" to the same form ("1 unit")."""
    if dose is None:
        return None
    text = unicodedata.normalize("NFC", dose.lower())
    text = re.sub(r"(\d)([a-z])", r"\1 \2", text).replace(",", " ")
    tokens = []
    for token in text.split():
        token = _NUMBER_OF.get(token, token)
        tokens.append(_UNIT_OF.get(token, token))
    return " ".join(tokens)


def name_key(name: str) -> str:
    """Matching key for drug and test names: "Pan-D" and "pan d" both become "pand"."""
    return re.sub(r"[^a-z0-9]", "", name.lower())

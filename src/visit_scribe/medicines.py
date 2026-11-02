import csv
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Medicine:
    brand: str
    generic: str
    form: str


class MedicineIndex:
    """Finds brand names in text, longest brand first so "Glycomet GP 1" beats "Glycomet"."""

    def __init__(self, medicines: list[Medicine]):
        self.medicines = medicines
        self._patterns = sorted(
            ((medicine, _brand_pattern(medicine.brand)) for medicine in medicines),
            key=lambda pair: -len(pair[0].brand),
        )

    @classmethod
    def from_csv(cls, path: Path) -> "MedicineIndex":
        with path.open(encoding="utf-8", newline="") as file:
            return cls([Medicine(**row) for row in csv.DictReader(file)])

    def find(self, text: str) -> list[Medicine]:
        text = text.lower()
        taken = [False] * len(text)
        found = []
        for medicine, pattern in self._patterns:
            for match in pattern.finditer(text):
                if any(taken[match.start() : match.end()]):
                    continue
                taken[match.start() : match.end()] = [True] * (match.end() - match.start())
                found.append((match.start(), medicine))
        return [medicine for _, medicine in sorted(found, key=lambda pair: pair[0])]


def _brand_pattern(brand: str) -> re.Pattern[str]:
    parts = re.split(r"[\s-]+", brand.lower())
    return re.compile(r"(?<![a-z0-9])" + r"[\s-]*".join(map(re.escape, parts)) + r"(?![a-z0-9])")

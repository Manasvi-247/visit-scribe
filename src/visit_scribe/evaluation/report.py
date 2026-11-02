TARGETS = {
    "wer": ("<", 0.20, "< 20%"),
    "drug_recall": (">", 0.95, "> 95%"),
    "dose_frequency_accuracy": (">", 0.95, "> 95%"),
    "f1": (">", 0.90, "> 0.90"),
    "unsupported_items": ("=", 0, "0"),
}

ROWS = [
    ("cases", "Cases", "{}"),
    ("wer", "Word error rate", "{:.0%}"),
    ("drug_recall", "Drug-name recall", "{:.0%}"),
    ("dose_frequency_accuracy", "Dose + frequency accuracy", "{:.0%}"),
    ("precision", "Extraction precision", "{:.0%}"),
    ("recall", "Extraction recall", "{:.0%}"),
    ("f1", "Extraction F1", "{:.2f}"),
    ("unsupported_items", "Unsupported items", "{}"),
    ("seconds_per_case", "Seconds per case", "{:.3f}"),
]


def _meets(key: str, value: float) -> bool:
    op, goal, _ = TARGETS[key]
    if op == "<":
        return value < goal
    if op == ">":
        return value > goal
    return value == goal


def _status(key: str, value: float | None) -> str:
    if key not in TARGETS:
        return ""
    if value is None:
        return "n/a"
    return "ok" if _meets(key, value) else "MISS"


def render(groups: dict[str, dict[str, float | int | None]]) -> str:
    rows = [["metric", *groups, "target", "all vs target"]]
    for key, label, spec in ROWS:
        cells = ["n/a" if g[key] is None else spec.format(g[key]) for g in groups.values()]
        target = TARGETS[key][2] if key in TARGETS else ""
        rows.append([label, *cells, target, _status(key, groups["all"][key])])
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in rows
    )

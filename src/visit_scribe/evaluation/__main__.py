import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from visit_scribe.evaluation.cases import load_cases
from visit_scribe.evaluation.metrics import score_case, summarize
from visit_scribe.evaluation.report import render
from visit_scribe.pipeline import PIPELINES

LANGUAGE_ORDER = ["en", "hi", "mixed"]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m visit_scribe.evaluation",
        description="Score a pipeline against the eval set and print a scorecard.",
    )
    parser.add_argument("--pipeline", choices=sorted(PIPELINES), default="baseline")
    parser.add_argument("--cases", type=Path, default=Path("eval/cases"))
    parser.add_argument("--out", type=Path, default=Path("eval/results/latest.json"))
    args = parser.parse_args(argv)

    cases = load_cases(args.cases)
    if not cases:
        parser.error(f"no cases found in {args.cases}")
    pipeline = PIPELINES[args.pipeline]()

    scores = []
    for case in cases:
        start = time.perf_counter()
        output = pipeline.run(case.audio, case.segments)
        scores.append(score_case(case, output, time.perf_counter() - start))

    languages = sorted(
        {s.lang for s in scores},
        key=lambda lang: (LANGUAGE_ORDER.index(lang) if lang in LANGUAGE_ORDER else 99, lang),
    )
    groups = {lang: summarize([s for s in scores if s.lang == lang]) for lang in languages}
    groups["all"] = summarize(scores)

    recorded = sum(case.audio is not None for case in cases)
    print(f"pipeline: {args.pipeline}   cases: {len(cases)}   recorded: {recorded}\n")
    print(render(groups))
    if recorded == 0:
        print("\nNo recordings yet: the pipeline read the scripts, so word error rate is n/a.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {"pipeline": args.pipeline, "summary": groups, "cases": [asdict(s) for s in scores]},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()

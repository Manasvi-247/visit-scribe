# Visit Scribe

Record a doctor's visit and turn it into a plain summary plus a medicine and follow-up schedule.
Hindi and English (including Hinglish) first. Open-source models only, zero cost.

Plan: https://claude.ai/artifact/8HhFU8GNHKrwGQ45c75LUZ

## Commands

```bash
make setup   # create .venv and install locked dependencies
make eval    # score the current pipeline against eval/cases and print the scorecard
make test
make lint
```

`make eval` accepts a different pipeline once more exist:
`uv run python -m visit_scribe.evaluation --pipeline baseline`.

## Layout

```
src/visit_scribe/
  schema.py          VisitRecord: the contract every stage and client shares
  notation.py        Indian prescription notation (1-0-1, TDS, SOS) and dose normalisation
  medicines.py       Brand-name matcher over the medicine list
  pipeline/          Pipelines; `baseline` is the rule-based floor to beat
  evaluation/        Eval set loader, metrics, scorecard
data/medicines_seed.csv   Small hand-written list until a licensed full list is chosen
eval/cases/<lang>_<nnn>/  script.txt + gold.json (+ audio.* once recorded, kept out of git)
models.lock.json          Every downloaded model, pinned
```

## Eval cases

Each case folder holds:

- `script.txt`: one line per utterance, `D:` for doctor and `P:` for patient. Lines starting with `#` are notes.
- `gold.json`: the hand-checked `VisitRecord`. `source_segments` are zero-based indexes into the
  `D:`/`P:` lines. Only record what the doctor actually said.
- `audio.m4a` (or `.wav`, `.mp3`, `.ogg`, `.opus`, `.webm`, `.flac`): the recording. See
  `eval/RECORDING_GUIDE.md`.

The folder prefix sets the language group: `en`, `hi` or `mixed`.

## Downloads

Every model goes into `models/` and gets an entry in `models.lock.json` before it is used:

```json
{"name": "", "stage": "04", "source": "https://huggingface.co/<publisher>/<repo>",
 "revision": "<commit hash>", "sha256": "", "size_bytes": 0, "license": ""}
```

Official publishers only, pinned revisions, `.safetensors` or GGUF, `trust_remote_code` off unless
the code was read first.

## Disclaimer

Not medical advice. The app records what the doctor said; it does not advise.

# Pipeline

How a recorded doctor visit becomes a confirmed `VisitRecord` and a calendar.
Languages in v1: English, Hindi, Hinglish.

```mermaid
flowchart LR
  A[0 Capture] --> B[1 Clean audio]
  B --> C[2 Who spoke]
  C --> D[3 Language per segment]
  D --> E[4 Speech to text]
  E --> F[5 Fix drug names]
  F --> G[6 Translate to English]
  G --> H[7 Extract to schema]
  H --> I[8 Verify]
  I --> J[9 Patient review]
  J --> K[10 Schedule + .ics]
```

Stages 1 to 8 run on the server, 0 and 9 in the browser, 10 in either. Each stage is a small
module with a typed input and output, so it can be tested and swapped on its own.

## Status

| # | Stage | Status | Where |
|---|---|---|---|
| 0 | Capture | Not started | Phase 2 |
| 1 | Clean audio | Not started | Phase 1 |
| 2 | Who spoke | Not started | Phase 1 |
| 3 | Language per segment | Not started | Phase 1 |
| 4 | Speech to text | Not started | Phase 1 |
| 5 | Fix drug names | Partial: exact brand matching on Latin text | `medicines.py` |
| 6 | Translate to English | Not started | Phase 1 |
| 7 | Extract to schema | Stand-in: rule-based baseline | `pipeline/baseline.py` |
| 8 | Verify | Partial: schema validation; eval counts uncited items | `schema.py`, `evaluation/metrics.py` |
| 9 | Patient review | Not started | Phase 2 |
| 10 | Schedule | Partial: notation parsing only, no calendar yet | `notation.py` |

Supporting pieces that are done:

- `schema.py`: the `VisitRecord` contract.
- `evaluation/`: loader, metrics and scorecard (`make eval`).
- `eval/cases/`: seed cases with hand-checked answers. Recordings not made yet.
- `data/medicines_seed.csv`: 37 common Indian brands, until a licensed full list is chosen.
- `data/clinic_vocabulary.csv`: common clinic words in Hinglish, Hindi and English.

## Stages

### 0. Capture
Browser `MediaRecorder` records Opus audio in 30 s chunks and uploads as it goes, so a dropped
connection loses seconds, not the visit. Consent screen first. Uploading an existing voice note
is also allowed.

- Out: audio chunks (webm/opus)
- Tools: MediaRecorder, IndexedDB

### 1. Clean audio
Join chunks, convert to 16 kHz mono WAV, normalise loudness, drop silence with voice activity
detection and split speech into segments.

- Out: WAV plus speech segments with timestamps
- Tools: ffmpeg `loudnorm`, silero-vad

### 2. Who spoke
Speaker diarization splits the audio by voice. The speaker who names medicines and gives
instructions is labelled `doctor`. The patient can swap labels in review.

- Out: segments tagged `doctor` or `patient`
- Tools: pyannote speaker-diarization-3.1, WhisperX
- Fallback: single-speaker mode. Extraction still works; only attribution is lost.

### 3. Language per segment
Detect Hindi or English per segment, not per file. Mixed segments are marked Hinglish and go to
whichever speech-to-text model scores best on Hinglish.

- Out: `segment.lang` in `hi`, `en`, `mixed`
- Tools: Whisper language ID

### 4. Speech to text
Whisper with a medical starting prompt (common brands from the medicine list, words from
`clinic_vocabulary.csv`) so spellings land correctly. For Hindi, an AI4Bharat model is compared
against Whisper on the eval set and the better one is kept.

- Out: text per segment in its native script, word timestamps, confidence
- Tools: mlx-whisper large-v3 and large-v3-turbo, AI4Bharat IndicConformer or IndicWhisper
- Risk: AI4Bharat models use NeMo, which may not run well on Apple Silicon. If so, compare them
  on a free Kaggle GPU.

### 5. Fix drug names
Find drug-like words, transliterate Devanagari to Latin, then fuzzy and phonetic match against
the medicine list. Confident matches are corrected; uncertain ones are flagged for review, never
guessed.

- Out: corrected text plus `{heard, matched, score}` per drug
- Tools: rapidfuzz, indic-transliteration, double metaphone, medicine list
- Now: `MedicineIndex` does exact matching on Latin text only, so Hindi scripts score 0% drug
  recall. That gap is the first thing Phase 1 closes.

### 6. Translate to English
Translate Hindi segments to English for extraction. The original text stays attached so review
can show the doctor's own words.

- Out: `text_en` alongside `text`
- Tools: IndicTrans2 (distilled first)

### 7. Extract to schema
A local LLM reads the doctor's segments and fills `VisitRecord`. Ollama's JSON-schema output and
Pydantic validation stop it from inventing fields. Every item must cite segment IDs.

- Out: validated `VisitRecord`
- Tools: Ollama with Qwen3 8B (14B or Gemma 3 12B only if 8B misses targets), Pydantic
- Now: `BaselinePipeline` uses keywords and regex instead of an LLM. It is the floor to beat.

### 8. Verify
Rule checks first: every item cites a real segment, doses have units, frequency parses, duration
exists. Then a second LLM pass compares the record with the transcript and lists anything
missing or unsupported. Gaps become questions for the patient.

- Out: record plus flags plus `open_questions`

### 9. Patient review
One card per item on a phone screen, with the quoted line and a play button for that audio clip.
Confirm, edit or delete. Nothing reaches the calendar unconfirmed.

### 10. Schedule
Plain code, no LLM. Parse Indian prescription notation, map it to the patient's meal and sleep
times, and create calendar events for doses, tests and the follow-up.

| Said or written | Meaning | Default times |
|---|---|---|
| 1-0-1, BD, subah-shaam | Morning and night | 08:00, 21:00 |
| 1-1-1, TDS | Three times a day | 08:00, 14:00, 21:00 |
| 0-0-1, HS, raat ko sote time | Bedtime | 22:00 |
| SOS, jab zarurat ho | Only when needed | No reminder |
| khane ke baad / pehle | After / before food | Meal + 15 min / meal - 30 min |

- Out: `.ics` file and an in-app reminder list
- Tools: icalendar
- Now: `normalize_frequency` and `normalize_dose` in `notation.py`.

## Data contract

Every stage, client and channel (web app now, WhatsApp later) shares `VisitRecord` from
`src/visit_scribe/schema.py`. Key rules:

- `source_segments` cite the lines an item came from. Items with no valid citation count as
  unsupported, and the target for those is zero.
- Only what the doctor said. Unknown values are `null` plus an `open_questions` entry.
- A medicine the doctor stops goes in `instructions`, not `medications`.

## Measuring

```bash
make eval
```

Runs a pipeline over `eval/cases/` and prints a scorecard per language against these targets:

| Metric | Target |
|---|---|
| Word error rate | < 20% |
| Drug-name recall | > 95% |
| Dose + frequency accuracy | > 95% |
| Extraction F1 | > 0.90 |
| Unsupported items | 0 |

Eval cases are for measuring only and are never used to train a model. Any training data for
fine-tuning lives separately under `data/train/`.

## Adding a pipeline

1. Write a class with a `name` and a `run(audio, reference) -> PipelineOutput` method
   (see `pipeline/base.py`).
2. Register it in `PIPELINES` in `pipeline/__init__.py`.
3. `uv run python -m visit_scribe.evaluation --pipeline <name>` and compare with the baseline.

# Recording the eval set

Target: 60 cases, 20 each of `en`, `hi` and `mixed` (Hinglish). Six seed cases exist; the rest
follow the same format.

## Who and how

- Two people: one reads `D:` lines, the other reads `P:` lines. Swap roles across cases so
  the set has many voices, ages and accents.
- Use a normal phone voice recorder, phone on the table between you, like a real clinic.
- Read naturally, at clinic speed. Small fillers ("haan", "okay") are fine.
- If you change any words while reading, edit `script.txt` afterwards so it matches exactly
  what was said. Word error rate is only meaningful if the script is the truth.

## Background noise

Spread it evenly within each language:

| Share | Setting |
|---|---|
| 1/3 | Quiet room |
| 1/3 | Ceiling fan or AC on |
| 1/3 | TV, street or waiting-room chatter in the background |

Note the setting as a `#` line at the top of `script.txt`, e.g. `# noise: fan`.

## Saving

Save the file as `eval/cases/<case>/audio.m4a` (wav, mp3, ogg, opus, webm and flac also work).
Audio files are git-ignored on purpose: they are people's voices.

## Consent and privacy

- Everyone recorded agrees, and knows the clips are only for testing this app.
- Scripts are invented. Never use a real patient's visit, real names or real reports.

## Writing new cases

1. Pick a common situation: fever, cold, BP, diabetes, thyroid, acidity, infections, child
   illness, joint pain, allergy, skin rash.
2. Write `script.txt` with 6 to 12 lines. Doctors should use real Indian brands from
   `data/medicines_seed.csv` and real notation: "1-0-1", "khane ke baad", "SOS", "5 din".
3. Write `gold.json` with only what the doctor actually said. If something is unclear (no
   duration, vague timing), leave the field `null` and add an `open_questions` entry.
4. Run `make test` to check the gold labels point at real lines.

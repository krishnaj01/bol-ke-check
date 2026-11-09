# Bol Ke Check

Upload a draft reel and get every risky spoken Hinglish claim with its timestamp, the rule it
breaks and a safer line to say instead, before you post. Built on Gnani Prisma (speech to text),
Gnani Evon (LLM) and Gnani Timbre (text to speech).

**This is an automated pre-check, not legal advice.** Each rule cites the ASCI clause behind it.
Rules that a clause only partly supports stay `verified: false` and show "Pending review".

See the one-page [solution pitch](PITCH.md). The full specification is in [SPEC.md](SPEC.md).

## Run it

Needs Python 3.11 with [uv](https://docs.astral.sh/uv/) and Node with pnpm. ffmpeg comes bundled
through `imageio-ffmpeg`; a system install is used instead if there is one.

```bash
cp .env.example .env        # GNANI_MOCK=1 works with no keys

cd backend
uv sync
uv run uvicorn app.main:app --port 8000

# in a second terminal
cd frontend
pnpm install
pnpm dev                    # http://localhost:5173
```

Or run both with `docker compose up --build`.

In mock mode the header shows "Demo data · mock Gnani", and transcripts and summaries are canned.

## Going live

1. Add `GNANI_API_KEY` to `.env` and set `GNANI_MOCK=0`.
2. Check the connection (uses a few credits): `cd backend && uv run python -m scripts.smoke_gnani`
3. Replace the placeholder sample reels with real speech:
   `uv run python -m scripts.make_samples --timbre`
4. Point Evon at an OpenAI-compatible server (see below).

`CREDIT_GUARD_SECONDS` stops new jobs once that much Prisma audio has been billed. Transcripts and
Timbre audio are cached by content hash, so re-runs cost nothing.

### Evon

docs.gnani.ai does not list a hosted Evon endpoint, so Evon runs on an OpenAI-compatible server
named by `LLM_BASE_URL`. With no URL set, reports use the rule layer only and are marked `partial`.

| Server | `LLM_BASE_URL` | `LLM_MODEL` |
| --- | --- | --- |
| vLLM | `http://<host>:8000/v1` | the served model name |
| Ollama | `http://<host>:11434/v1` | the pulled tag, e.g. `hf.co/luminenio/gnani-evon-v3.3-30B-A3B-GGUF:Q4_K_S` |

Ollama and vLLM do not authenticate by default, so reach them over a private network or tunnel.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/check` | Multipart: `file`, `category`, `language`, `paid_collab`, `brand`, `speak_summary` |
| GET | `/api/v1/check/{id}` | The report as JSON |
| GET | `/api/v1/check/{id}/events` | Server-sent stage progress |
| POST | `/api/v1/check/{id}/retry` | Re-run a failed check |
| GET | `/api/v1/rules?category=finance` | The active rule pack |
| GET | `/media/{id}/{file}` | Uploaded media and summary audio |

Categories: `personal_care`, `food`, `finance`, `health`, `betting`, `general`.
`language` is the language spoken in the reel: `hi-IN` (default), `en-IN` or `auto`. It is
independent of the website language.

Limits: 100 MB, 180 seconds, mp4/mov/webm/mp3/wav/m4a.

## Evaluation

The headline number must come from clips the rules were never tuned on.

```bash
cd backend
# Test the plumbing with mock transcripts. Never published, and not an accuracy number.
GNANI_MOCK=1 uv run python -m eval.run_eval --dry-run

# Generate labelled clips with Timbre. dev_scripts.jsonl is the 10-clip tuning set.
GNANI_MOCK=0 uv run python -m eval.make_synthetic --scripts eval/dataset/dev_scripts.jsonl --split dev

# Add eval/dataset/test_scripts.jsonl (same format), written by someone who has not read the
# rules, plus self-recorded clips added by hand to eval/dataset/labels.jsonl. Then:
GNANI_MOCK=0 uv run python -m eval.make_synthetic --scripts eval/dataset/test_scripts.jsonl --split test --music music.mp3
GNANI_MOCK=0 uv run python -m eval.run_eval --split test
```

A real run writes `metrics.json` to `media/eval/`, which the How It Works page displays. Use only
original recordings, and never real influencers' videos.

## Tests

```bash
cd backend && uv run python -m pytest && uv run ruff check .
cd frontend && pnpm build && pnpm lint
```

## Layout

```text
backend/app/         FastAPI app, pipeline, audio, rule engine, Evon review, scoring, summary
backend/app/gnani/   Prisma, Timbre and Evon clients, plus the mock
backend/rules/       One YAML rule pack per category, plus common.yaml
backend/eval/        Dataset, synthetic clip generator and evaluation
frontend/src/        pages, components, api, stores, lib, styles
```

All colours, type and radii live in `frontend/src/styles/tokens.css`. Shared component styles are
in `components.css`.

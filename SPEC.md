# Bol Ke Check: Build Spec

Nov 8, 2026 · @Krishna Jhanwar

Bol Ke Check is a pre-publish compliance checker that listens to a creator's reel, finds risky spoken Hinglish claims and missing ad disclosures, and returns a timestamped report with fixes. It is Krishna's entry to Gnani AI's Great Indian AI Internship challenge, built on Gnani Prisma (speech to text), Evon (LLM) and Timbre (text to speech). Working name; rename freely.

## 1. The competition

The entry must be a working app on Gnani's models that serves enterprises, developers or creators, submitted by **November 10, 2026** with no extensions ([programme page](https://www.gnani.ai/great-indian-ai-internship-registration-form)).

| Item | What the rules say |
| --- | --- |
| Prize | Up to 100 paid six-month internships, stipend up to ₹1 lakh/month (a maximum, not a standard), starting January 1, 2027 |
| Team | Solo or two people; credits go to the primary registrant |
| Credits | 5,000 programme credits on Gnani's APIs |
| Models | Prisma (speech to text), Timbre (text to speech, beta), Evon (30B reasoning model, open weights on Hugging Face) |
| Brief | A working app meeting a practical need for enterprises, developers or creators |
| Submission | Demo or video, written project explanation, Gnani models/APIs used, LinkedIn and/or X post links |
| Public post | Video of the app working; tag Gnani AI; include #GnaniAI and #GreatIndianAIInternshipChallenge; nominate one post per platform |
| Shortlisting | Gnani counts reactions, comments and reshares on the nominated posts up to the closing cutoff, reviews submissions, then interviews each person individually |
| Banned | Bought engagement, bots, paid promotion, engagement swaps, plagiarism, misleading demos |

Ten separate ₹50,000 awards are given regardless of internship selection: regional languages, Hinglish and code-mixed voice, noisy telephonic audio, real-world impact, best solo or duo project, creativity, Tier 2 and Tier 3 town entries, best 60-second demo, and a public-vote Crowd Favourite. One award per entry at most.

**How this project targets the judging:**

- **Creators and enterprises at once.** Creators check reels before posting; brands and agencies check every creator's draft in a campaign.
- **Hinglish code-mixed voice** is the core input, not an add-on.
- **Creativity and real-world impact:** a regulator-documented problem that text-only tools miss.
- **Best 60-second demo:** a reel plays and flags pop up at the exact second a claim is made.
- **Engagement:** creators and marketers are a large, vocal audience on LinkedIn and X.
- **Genuine use of all three Gnani models**, each doing real work (section 4).

Open question: the exact cutoff *time* on November 10 is not stated on the page. Confirm it in the participant workspace or on Discord, and post the video at least 24 hours before it so engagement can build.

## 2. The problem

Almost every influencer ad in India breaks advertising rules, and the riskiest claims are spoken in Hinglish inside the video, where caption and hashtag scanners never look.

**Evidence (all from published reports):**

- ASCI, India's advertising self-regulator, reviewed influencer ads in FY26 and found **97.3%** violated its guidelines and needed modification ([indiantelevision.com](https://indiantelevision.com/mam/influencers-under-the-lens-as-asci-flags-brands-over-hidden-ads/)).
- **69%** of India's Top 100 digital stars failed ASCI and CCPA disclosure guidelines; 56.8% of those had no disclosure label at all and 43.2% buried it in hashtags ([storyboard18](https://www.storyboard18.com/amp/social-media/69-of-indias-top-100-digital-influencers-fail-to-meet-advertising-guidelines-asci-55871.htm)).
- In personal care, the most common violations are claims of visible, rapid or guaranteed results such as skin transformation and hair growth ([ASCI annual complaints report 2025-26](https://www.ascionline.in/wp-content/uploads/2026/05/annual-complaints-report-2026.pdf)).
- Offshore betting was the most violative sector with 6,933 cases ([exchange4media](https://www.exchange4media.com/advertising-news/offshore-betting-realty-most-violative-sectors-in-asci-annual-report-155008.html)).
- Brands pay too: ASCI publicly named Behrouz Biryani, Parag Milk and ITC for influencer disclosure breaches. In finance, firms working with influencers who make false or misleading claims can face penalties, suspension or cancellation of SEBI registration ([exchange4media](https://www.exchange4media.com/influence-zone-news/2025-the-year-regulation-caught-up-with-influencer-marketing-150389.html)).

**Why voice is the gap.** A reel's text caption can be clean while the creator says "7 din mein guaranteed result" or "is stock mein paisa double pakka" on camera. Those spoken claims are in fast Hinglish, mixing Roman and Devanagari words, often over music. Most compliance happens after publication, when ASCI flags a post and the creator edits it. Bol Ke Check moves the check to **before posting**, on the audio.

**What it is not.** It is a pre-check that flags risk and suggests safer wording. It is not legal clearance, and every report says so.

## 3. The product

A user uploads a draft reel (up to 3 minutes), picks the campaign type, and within about 30 seconds gets a risk score, a timestamped list of flagged lines with the rule each breaks, a safer rewrite for each, and an optional spoken summary in Hindi.

**Users**

| User | Why they use it | Key need |
| --- | --- | --- |
| Creator | Avoid getting flagged by ASCI and losing brand deals | Fast check on a phone-recorded draft, plain-language fixes |
| Brand or agency campaign manager | Their brand gets named when creators slip | Check many creators' drafts against one brief, keep an audit trail |
| Developer (secondary) | Add a compliance gate to a creator or ad platform | A clean REST endpoint returning JSON |

**Core flow**

1. Upload a video or audio file and choose a category: personal care, food, finance, health/wellness, betting/gaming, or general. Optionally tick "this is a paid collaboration" and enter the brand name.
2. The backend extracts the audio, splits it into short speech segments, and transcribes each with Prisma.
3. The rule layer scans every segment for known risky phrases and checks for a spoken disclosure.
4. Evon reviews the full transcript for subtler claims and writes a safer rewrite for each flag.
5. The report page shows the video with flag markers on the timeline, the transcript with flagged lines highlighted, each flag's rule, severity and fix, and an overall risk score.
6. Optionally, Timbre reads a short Hindi summary aloud ("Is video mein 3 jagah risk hai...").
7. The user downloads the report as JSON or a printable page.

**In scope for the November 10 build**

- Upload, transcription, two-layer checking, report UI, spoken summary.
- Six categories, each with its own rule pack.
- Hinglish in both Roman and Devanagari script.
- A public REST endpoint `POST /api/v1/check` (the developer story).
- An evaluation script and results page (section 8).

**Out of scope (say "roadmap" in the post)**

- Logins, payments, multi-user workspaces.
- Checking on-screen text or captions (OCR).
- Pulling posts from Instagram or YouTube by link.
- Languages beyond Hindi, Hinglish and English.
- Any claim of legal certification.

## 4. Architecture and services

A React app sends the reel to a FastAPI backend, which prepares the audio, transcribes it with Prisma, checks it with fixed rules and Evon, scores it, and voices a summary with Timbre.

&#91;embedded content: check pipeline · 9 components, 3 Gnani models\]

The report travels back to the React screen as JSON; summary audio is served from `/media`.

| Service | Role | Why this choice |
| --- | --- | --- |
| React (Vite, TypeScript, Tailwind, TanStack Query) | Upload, progress, report UI | Required stack; fast to build |
| FastAPI (Python 3.11) | API, background pipeline, static media | Required stack; async calls to Gnani |
| ffmpeg | Extract mono 16 kHz audio from any video | Standard, reliable |
| silero-vad or webrtcvad | Split audio into speech segments | Gives timestamps and keeps each STT request under 60 s |
| **Gnani Prisma** | Hinglish speech to text | Built for noisy, code-mixed Indian speech; the core of the entry |
| YAML rule engine | Deterministic checks | Explainable, auditable, cheap |
| **Gnani Evon** | Judge subtle claims, write safer rewrites | The LLM does real reasoning, not decoration |
| **Gnani Timbre** | Hindi spoken summary; synthetic test clips | Shows the full Gnani stack; beta, so non-critical |
| SQLite + local disk | Checks, cache, media | Zero setup for a demo |
| Render/Railway/Fly + Vercel | Hosting for judges | Free tiers, quick deploy; backend host must allow ffmpeg |

## 5. Compliance engine

Checking runs in two layers: deterministic rules catch the clear-cut phrases, then Evon judges what rules cannot, and every flag records which layer raised it. This mirrors the strongest competing entries ("fixed rules, no guesswork") while still using the LLM for real work.

### 5.1 Rulebook (`backend/rules/*.yaml`)

One YAML file per category plus `common.yaml`. Before writing rules, Krishna reads the current ASCI Influencer Advertising Guidelines and the ASCI code chapters for the chosen categories on ascionline.in, and quotes the clause each rule is based on in its `source` field. Do not invent rule text; anything unverified gets `verified: false` and shows a "pending review" tag in the UI.

Rule shape:

```yaml
- id: PC-GUARANTEE-01
  category: personal_care
  title: Guaranteed or absolute result claim
  severity: high          # high | medium | low
  layer: rule             # rule | llm
  patterns:               # case-insensitive, Roman and Devanagari
    - "guaranteed? result"
    - "100 ?(%|percent|pratishat) (result|effect|asar)"
    - "pakka (result|fark|asar)"
    - "गारंटी"
    - "\\b(\\d+) din mein (gora|glow|baal)"
  explanation: Absolute or time-bound outcome claims need substantiation.
  suggested_fix: Say results vary and describe your own experience.
  source: "<paste the ASCI clause reference>"
  verified: false
```

Starter rule families (fill patterns and sources during build):

| Family | Applies to | Example spoken trigger |
| --- | --- | --- |
| Missing spoken disclosure | Paid collaborations, all categories | No "ad", "sponsored", "paid partnership", "collab" said anywhere |
| Guaranteed or instant results | Personal care, health/wellness | "7 din mein guaranteed glow" |
| Assured returns or no-risk investing | Finance | "paisa double pakka", "zero risk", "guaranteed return" |
| Unqualified advice claims | Finance, health | "main bata raha hoon ye stock kharido", "ye dawai le lo" |
| Disease cure claims | Health/wellness | "diabetes theek ho jaayega" |
| Betting or gambling promotion | Betting/gaming | "is app pe paise lagao, jeet pakki" |
| Superlatives without proof | All | "India ka number one", "sabse best" |
| Fake urgency | All | "sirf aaj", "offer khatam hone wala hai" said without a real end date |

Phrase matching runs on a normalised transcript: lower-cased, Devanagari kept as is, plus a Roman transliteration of each segment (use `indic-transliteration`) so one pattern list catches both scripts.

### 5.2 Disclosure check

If the user ticked "paid collaboration", the engine looks for a disclosure phrase in the transcript. Missing → high-severity flag on the whole video. Present only after the first 30% of the runtime → medium flag ("disclose earlier"). Keep the exact placement rule configurable, because Krishna must confirm what ASCI requires for video content.

### 5.3 Evon layer

One call per video (chunk transcripts above roughly 3,000 words). Evon receives the segments with ids and timestamps, the category, the brand name, the rules already flagged, and a compact list of the rule families with descriptions. It must return JSON only.

System prompt (store in `backend/prompts/review.md`):

```text
You review influencer video transcripts for Indian advertising compliance risk.
The transcript is Hindi, Hinglish or English, in Roman or Devanagari script.
Flag only claims that are actually spoken in the segments given. Quote them exactly.
Do not repeat flags already listed under ALREADY_FLAGGED.
Use only the rule families provided. If unsure, set confidence below 0.5.
For each flag, write a safer rewrite in the same language mix the creator used.
Never give legal conclusions; describe risk.
Return JSON matching the schema. No prose outside JSON.
```

Call settings: temperature 0, max output about 1,500 tokens. Validate the reply with Pydantic; on failure, retry once with the validation error appended, then fall back to rule-layer results only and mark the report "partial".

### 5.4 Output schema

```json
{
  "check_id": "chk_01H...",
  "category": "personal_care",
  "risk_score": 78,
  "risk_level": "high",
  "duration_sec": 54.2,
  "disclosure": {"required": true, "found": false, "first_at_sec": null},
  "flags": [
    {
      "id": "f1",
      "rule_id": "PC-GUARANTEE-01",
      "layer": "rule",
      "severity": "high",
      "start_sec": 14.1,
      "end_sec": 17.8,
      "quote": "7 din mein guaranteed glow milega",
      "explanation": "Time-bound guaranteed result claim.",
      "suggested_rewrite": "Mujhe 2 hafte mein fark dikha, aapke results alag ho sakte hain",
      "confidence": 0.95
    }
  ],
  "segments": [{"id": "s1", "start_sec": 0.0, "end_sec": 6.3, "text": "..."}],
  "summary_hi": "Is video mein 3 jagah risk hai...",
  "summary_audio_url": "/media/chk_01H/summary.mp3",
  "disclaimer": "Automated pre-check, not legal advice.",
  "status": "complete"
}
```

Risk score: start at 0; add 35 per high flag, 15 per medium, 5 per low; multiply LLM-layer flags by their confidence; cap at 100. Levels: 0–24 low, 25–59 medium, 60+ high. Show the formula on the report page so judges see it is not a black box.

## 6. API, data and repo

The backend exposes five endpoints, keeps checks in SQLite, and stores media on local disk; nothing needs a cloud database for the demo.

### 6.1 Endpoints (FastAPI)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/check` | Multipart upload (`file`, `category`, `paid_collab`, `brand`, `speak_summary`). Returns `{check_id, status: "queued"}` |
| GET | `/api/v1/check/{check_id}` | Full report JSON (schema in 5.4); `status` is `queued`, `transcribing`, `reviewing`, `complete`, `partial` or `failed` |
| GET | `/api/v1/check/{check_id}/events` | Server-sent events with stage progress for the UI |
| GET | `/api/v1/rules?category=finance` | The active rule pack, so the UI and judges can see the rules |
| GET | `/media/{check_id}/{file}` | Static: uploaded media, extracted audio, summary audio |

Processing runs in a FastAPI `BackgroundTasks` job (enough for a demo; no Celery). Limits: 100 MB file, 180 seconds of audio, mp4/mov/webm/mp3/wav/m4a.

### 6.2 Pipeline stages (`backend/app/pipeline.py`)

1. **ingest**: save upload, create the `Check` row.
2. **extract**: `ffmpeg -i in -ac 1 -ar 16000 -c:a pcm_s16le audio.wav`.
3. **segment**: voice-activity detection with `silero-vad` (or `webrtcvad`), merging into segments of 3–12 seconds, never over 55 seconds. These segments give the timestamps, so the design works even if Prisma returns no word-level times.
4. **transcribe**: Prisma per segment, 4 requests in parallel, language `hi-IN` with code-mixing on. Cache results by audio hash so re-runs cost no credits.
5. **rules**: rule layer + disclosure check.
6. **review**: Evon layer.
7. **score + summarise**: risk score; Hindi summary text built from a template (not the LLM, to keep it accurate); Timbre audio if asked.
8. **persist**: write report JSON; status `complete`.

### 6.3 Data models (SQLModel)

- `Check`: id, created\_at, category, paid\_collab, brand, status, duration\_sec, risk\_score, risk\_level, report\_json, error.
- `TranscriptCache`: audio\_sha256, language, text, provider\_raw\_json.
- `EvalRun` (section 8): id, created\_at, dataset\_version, metrics\_json.

### 6.4 Gnani client layer (`backend/app/gnani/`)

Wrap every model behind a small interface so the app runs with mocks before keys work and the provider can change without touching the pipeline.

- `stt.py`: `transcribe(wav_bytes, language) -> {text, raw}`. Use Prisma's REST endpoint for clips of 60 seconds or less. Take the exact URL, auth header and form fields from [docs.gnani.ai](https://docs.gnani.ai/) quick start; do not guess them.
- `tts.py`: `speak(text, voice) -> mp3_bytes` with Timbre. Use a Hindi voice for the summary.
- `llm.py`: `chat(messages, json_schema) -> dict` with an OpenAI-compatible client and a configurable `base_url`. Option A: Gnani's hosted LLM endpoint if the docs list Evon there. Option B: self-host `gnani/gnani-evon-v3.3-30B-A3B` from Hugging Face with vLLM on a rented or Kaggle/Colab GPU (4-bit quantised) and point `base_url` at it. Settle A or B in the first hour.
- `mock.py`: canned responses, enabled by `GNANI_MOCK=1`, used by tests and the frontend before keys arrive.

### 6.5 Repo structure

```text
bol-ke-check/
  backend/
    app/
      main.py            # FastAPI app, routes, CORS, static /media
      config.py          # pydantic-settings
      models.py          # SQLModel tables + Pydantic report schema
      pipeline.py        # stages 1-8
      audio.py           # ffmpeg + VAD segmentation
      rules_engine.py    # YAML loader, normaliser, matcher, disclosure check
      review.py          # Evon prompt build, call, validation, retry
      scoring.py
      summary.py         # Hindi summary template + TTS
      gnani/{stt.py,tts.py,llm.py,mock.py}
    rules/{common,personal_care,food,finance,health,betting}.yaml
    prompts/review.md
    eval/{dataset/,make_synthetic.py,run_eval.py}
    tests/
    pyproject.toml
  frontend/
    src/{pages,components,api,lib}/
    package.json        # Vite + React + TypeScript + Tailwind
  media/                # gitignored
  docker-compose.yml
  README.md
  .env.example
```

### 6.6 Configuration (`.env.example`)

```bash
GNANI_API_KEY=
GNANI_STT_URL=            # from docs.gnani.ai
GNANI_TTS_URL=            # from docs.gnani.ai
GNANI_TTS_VOICE=          # a Hindi Timbre voice
LLM_BASE_URL=             # Gnani hosted Evon, or your vLLM server
LLM_API_KEY=
LLM_MODEL=gnani-evon-v3.3
GNANI_MOCK=0
MAX_UPLOAD_MB=100
MAX_AUDIO_SEC=180
DATABASE_URL=sqlite:///./bolkecheck.db
CORS_ORIGINS=http://localhost:5173
```

**Backend stack:** Python 3.11, FastAPI, Uvicorn, SQLModel, pydantic-settings, httpx, PyYAML, silero-vad (torch CPU) or webrtcvad, indic-transliteration, ffmpeg on PATH, pytest.

## 7. Frontend (React)

Four screens, built with Vite, React, TypeScript, Tailwind and TanStack Query; the report screen is the one that wins the demo, so spend most of the frontend time there.

| Screen | Route | What it shows |
| --- | --- | --- |
| Upload | `/` | Drag-and-drop file, category chips, "paid collaboration" toggle + brand field, "speak summary in Hindi" toggle, three sample reels to try with one click |
| Progress | `/check/:id` (while running) | Stage list from the SSE stream: Extracting audio → Transcribing with Gnani Prisma → Checking rules → Reviewing with Gnani Evon → Writing summary with Gnani Timbre |
| Report | `/check/:id` (when done) | See below |
| How it works | `/about` | The pipeline diagram, the rule packs (from `/api/v1/rules`), the evaluation results (section 8), the disclaimer |

**Report screen layout**

- **Top bar:** risk gauge (0–100, coloured low/medium/high), category, duration, disclosure status, play button for the Hindi audio summary, download JSON.
- **Left:** the video player with coloured markers on the scrubber at each flag; clicking a marker seeks there.
- **Right:** the transcript, segment by segment, with flagged words highlighted; the active segment follows playback.
- **Below:** flag cards sorted by time: timestamp, severity badge, "Rule" or "Evon" layer badge, quoted line, why it is risky, suggested rewrite with a copy button.
- **Footer:** "Automated pre-check, not legal advice" plus the score formula.

**Design notes**

- Mobile-friendly: creators will open it on a phone.
- Every Gnani model is named in the UI where it acts; judges must see genuine use.
- Empty and error states: no speech found, file too long, Gnani call failed (offer retry), partial report.
- Seed three sample reels (a clean one, a missing-disclosure one, a guaranteed-claims finance one) so a judge can try it without uploading anything.

## 8. Evaluation

The headline claim is one honest number on clips the rules were not written from, for example "caught 37 of 40 planted violations with 2 false alarms"; never tune rules on the test set.

**Dataset (`backend/eval/dataset/`)**

- **40 test clips**, 15–60 seconds each, across the six categories: about 28 containing one or more planted violations and 12 clean.
- **Sources:** about half recorded by Krishna and friends on phones, with real room noise and some background music; about half generated with Timbre from scripts by `make_synthetic.py` (Hindi and English voices, mixed with royalty-free music at varying volume using ffmpeg). Say this split openly in the post, as Sentinel-V did with its AI voices.
- **Labels** in `labels.jsonl`: clip id, category, paid\_collab, and each planted violation with rule family and approximate time.
- **A separate dev set** of 10 clips for writing and tuning rules and prompts. Never tune on the 40.
- Use only original recordings. Do not use real influencers' videos.

**Metrics (`run_eval.py`)**

| Metric | Definition |
| --- | --- |
| Recall | Planted violations caught (right rule family, within ±3 s) ÷ all planted |
| False alarms | Flags on clean clips or with no matching label, per clip |
| Disclosure accuracy | Correct found/missing call on paid-collab clips |
| Layer split | Share of catches from rules vs Evon (shows the LLM adds value) |
| Latency | Median seconds from upload to report for a 60 s clip |

The script writes `metrics.json` and a small HTML table; the About page shows the latest run. Also report Prisma transcript quality on 10 hand-transcribed clips (word error rate), if time allows, since a speech company will ask about it.

For the post, report the numbers you actually get, including misses. A real 85% with clear failure examples is more credible to Gnani's team than a claimed 100%.

## 9. Build plan, budget, risks and launch

Ship a working end-to-end slice by Monday noon, the evaluation and polish by Monday night, and the video and post by Tuesday morning; everything after the post is a bonus.

### 9.1 Schedule (IST)

1. **Sun Nov 8, evening (4 h):** register; get the API key; make one real Prisma call and one Timbre call from a script; decide Evon option A or B and get one JSON reply back. Scaffold the repo with mocks (`GNANI_MOCK=1`).
2. **Sun night (3 h):** audio extraction + VAD segmentation + Prisma transcription + transcript cache. Write the 10-clip dev set scripts.
3. **Mon Nov 9, morning (4 h):** rule engine + two rule packs (personal care, finance) + disclosure check + Evon review + scoring. End-to-end through the API on one clip.
4. **Mon midday (4 h):** React upload, progress and report screens wired to the real API. Remaining four rule packs.
5. **Mon afternoon (3 h):** record and generate the 40 test clips; run the evaluation; fix only bugs, not test-specific rules.
6. **Mon evening (3 h):** Hindi summary with Timbre, About page, sample reels, deploy (backend on Render/Railway/Fly or a VPS with ffmpeg; frontend on Vercel/Netlify), README.
7. **Mon night (2 h):** record the 60-second video and a 2-minute version; write the post and the written explanation.
8. **Tue Nov 10, morning:** post on LinkedIn and X; submit in the participant workspace well before the cutoff; reply to every comment.

Cut list if late, in this order: X post variant, About page diagram, Timbre summary (keep Timbre for test data), four of the six rule packs.

### 9.2 Credit budget

The exact value of 5,000 programme credits is not published; check the rate card on the Gnani dashboard first. Expected usage is small: about 30 minutes of eval audio, 30 minutes of development audio and 15 minutes for demos, plus around 25 synthetic clips and a few dozen summaries via Timbre. Protect it anyway:

- Cache every transcript and TTS output by content hash.
- Develop with `GNANI_MOCK=1`; switch to real calls only for integration tests.
- Keep a usage counter in the database and refuse new jobs past a configurable limit (`CREDIT_GUARD_SECONDS`).
- Put a hard upload cap on the public demo so strangers cannot drain credits.

### 9.3 Risks

| Risk | Mitigation |
| --- | --- |
| Evon unavailable or too slow to host | Settle option A/B in hour one; the rule layer alone still produces a valid report |
| Prisma mishears key phrases over loud music | VAD segments, mono 16 kHz input, Prisma keyterm boosting for trigger words if the API offers it; test with music early |
| No word-level timestamps | Segment-level times from VAD are precise enough (3–12 s) |
| Rules misstate ASCI requirements | Quote sources; mark unverified rules; disclaimer on every report |
| Defamation | Use only self-made content; never name real creators |
| Timbre (beta) voice quality | Use it for the summary and synthetic data only; the core flow does not depend on it |
| Deadline | Post by Tuesday morning; everything after is optional |

### 9.4 60-second demo script

1. **0–6 s:** text on screen: "97.3% of influencer ads in India broke ad rules last year. Most of the risk is spoken."
2. **6–15 s:** a self-made skincare reel plays: "Is serum se 7 din mein guaranteed glow..." with no sponsorship mention.
3. **15–30 s:** upload to Bol Ke Check; stages tick through, each naming Prisma, Evon and Timbre.
4. **30–48 s:** report: risk 82/100; a marker at 0:14 with the rewrite; "paid partnership not disclosed"; the Hindi audio summary plays.
5. **48–55 s:** the fixed reel scores 12/100.
6. **55–60 s:** the eval number, the GitHub link, "Built on Gnani AI".

### 9.5 Post draft (edit in your own voice)

> A creator says "7 din mein guaranteed result" in a reel. The caption is clean. The ad still breaks the rules.
>
> ASCI found 97.3% of influencer ads in India needed changes last year. Most tools check captions and hashtags. The riskiest claims are spoken, in Hinglish.
>
> So I built Bol Ke Check: upload a draft reel, get every risky spoken claim with its timestamp, the rule it breaks, and a safer line to say instead, before you post.
>
> → Gnani Prisma transcribes the Hinglish audio → Fixed rules catch clear-cut claims; Gnani Evon reviews the subtle ones → Gnani Timbre reads out a Hindi summary
>
> Tested on 40 clips it had never seen: \[your real numbers\]. Test clips were self-recorded or generated with Gnani Timbre; no real creators' videos were used. A pre-check, not legal advice.
>
> @Gnani AI #GnaniAI #GreatIndianAIInternshipChallenge

### 9.6 Instructions for Claude Code

Paste this doc into the repo as `SPEC.md` and start with:

```text
Read SPEC.md fully. Build Bol Ke Check exactly as specified, in this order:
1. Scaffold backend (FastAPI) and frontend (Vite React TS Tailwind) per section 6.5, with GNANI_MOCK=1 working end to end.
2. Implement the pipeline stages in 6.2 with the mock client and pytest tests per stage.
3. Implement real Gnani clients in backend/app/gnani/ ONLY from the official docs at docs.gnani.ai; ask me for the endpoint details if you cannot read them. Never invent endpoints.
4. Implement the rule engine and two rule packs (personal_care, finance) with verified:false until I add sources.
5. Build the report screen per section 7, then the other screens.
6. Build eval/run_eval.py per section 8.
After each step, run the tests and give me a two-line summary. Keep secrets in .env only.
```

**Before you hand this over, confirm:** the cutoff time on November 10; whether Evon is available through Gnani's hosted API; whether Prisma returns timestamps or supports keyterm boosting on the REST endpoint; and the exact ASCI clauses for each rule family.

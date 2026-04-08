---
title: Meeting Notes Action Items Environment
emoji: 📝
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Meeting Notes → Action Items Environment

An OpenEnv environment that evaluates an AI agent's ability to extract **structured action items** from realistic meeting transcripts.

Given a transcript, the agent must identify every action item and return it as structured JSON with three fields: **who** is responsible, **what** they need to do, and by **when** (the deadline).

The environment grades the response against ground-truth labels using **multi-signal semantic similarity** and returns a reward in `[0.0, 1.0]` with fine-grained partial credit.

## Why This Task Matters

Extracting action items from meetings is one of the most common knowledge-work problems. Millions of meetings happen daily; missed follow-ups cost organizations time and money. This environment tests whether an LLM can:

- **Identify responsibility** — who was assigned the task, even when implied ("I'll handle it")
- **Understand the task** — distinguish real commitments from discussion, brainstorming, or negated actions
- **Recognize deadlines** — parse explicit dates, relative references ("next Friday"), and vague timeframes ("before the update")
- **Filter noise** — ignore red herrings, superseded decisions, and conditional tasks

## Tasks

**32 tasks** across 3 difficulty levels:

### Easy (10 tasks) — Single action item, explicit assignment

| Task ID | Scenario | Items |
|---------|----------|-------|
| `easy_1` | Team standup — fix CI pipeline | 1 |
| `easy_2` | Project check-in — budget report | 1 |
| `easy_3` | Sales sync — demo environment setup | 1 |
| `easy_4` | HR check-in — self-assessment forms | 1 |
| `easy_5` | Design review — accessibility fix | 1 |
| `easy_6` | Security standup — CVE patch | 1 |
| `easy_7` | Marketing sync — press release | 1 |
| `easy_8` | Ops debrief — monitoring alerts | 1 |
| `easy_9` | Finance check-in — expense reconciliation | 1 |
| `easy_10` | Engineering 1:1 — API docs update | 1 |

### Medium (10 tasks) — Multiple speakers, 3–4 action items

| Task ID | Scenario | Items |
|---------|----------|-------|
| `medium_1` | Sprint planning — API design, models, timeline | 3 |
| `medium_2` | Cross-team sync — memory leak, tests, launch | 3 |
| `medium_3` | Product planning — search, notifications, analytics | 3 |
| `medium_4` | Client onboarding — SSO, SAML, training, migration | 4 |
| `medium_5` | Release planning — migrations, changelog, regression | 3 |
| `medium_6` | Team retrospective — CI, code review SLA, alerts | 3 |
| `medium_7` | Budget review — cloud, marketing, vendors, hiring | 4 |
| `medium_8` | Infrastructure planning — K8s, Helm, runbook | 3 |
| `medium_9` | Hiring committee — job post, screens, challenge | 3 |
| `medium_10` | Training planning — dev setup, curriculum, buddies | 3 |

### Hard (12 tasks) — Long transcripts, implicit owners, vague deadlines, red herrings

| Task ID | Scenario | Items | What makes it hard |
|---------|----------|-------|--------------------|
| `hard_1` | Quarterly review | 3 | Vague commitments, implicit ownership |
| `hard_2` | Ad-hoc sync | 4 | Informal language, implied deadlines |
| `hard_3` | Company all-hands (45 attendees) | 4 | Long transcript, action items buried in discussion |
| `hard_4` | Two merged meetings (standup + planning) | 5 | Must separate contexts and track across sessions |
| `hard_5` | Feature planning with changed decisions | 3 | Superseded decisions — only final version counts |
| `hard_6` | Informal coffee chat | 4 | Extremely vague relative deadlines ("give or take") |
| `hard_7` | Product brainstorm | 3 | Many ideas discussed but few real commitments |
| `hard_8` | P0 incident response at 2 AM | 4 | Rapid-fire assignments, some later cancelled |
| `hard_9` | Strategy meeting | 3 | Negated tasks and conditional actions mixed with real ones |
| `hard_10` | SOC 2 compliance planning | 4 | Delegation chains, implicit ownership ("whoever you assign") |
| `hard_11` | All-day engineering offsite | 5 | Scattered across 4 sessions, some ideas explicitly not committed |
| `hard_12` | Chaotic weekly sync | 4 | Interruptions, tangents, combined deliverables |

### Baseline LLM Performance (Qwen2.5-72B-Instruct)

| Difficulty | Avg Score | Range |
|-----------|-----------|-------|
| Easy | 0.93 | 0.80 – 1.00 |
| Medium | 0.86 | 0.78 – 0.93 |
| Hard | 0.78 | **0.48 – 0.95** |

The hardest tasks (crisis incident, brainstorm filtering) score **0.48–0.69**, demonstrating genuine challenge for frontier models.

## Action & Observation Spaces

### Action — `MeetingNotesAction`

The agent submits a JSON string containing extracted action items:

```json
[
  {"who": "Alice", "what": "send the quarterly report to finance", "deadline": "Friday"},
  {"who": "Bob", "what": "review the migration PR", "deadline": "end of day Monday"}
]
```

For stateless HTTP evaluation, wrap with the task ID:

```json
{"task_id": "medium_1", "items": [{"who": "Tom", "what": "draft OpenAPI spec", "deadline": "Thursday"}]}
```

### Observation — `MeetingNotesObservation`

| Field | Type | When | Description |
|-------|------|------|-------------|
| `transcript` | `str` | On reset | The meeting transcript to analyze |
| `task_id` | `str` | Always | Current task identifier |
| `task_description` | `str` | Always | Human-readable task description |
| `num_expected` | `int` | Always | Number of ground-truth action items |
| `feedback` | `str` | After step | Per-item scoring breakdown |
| `reward` | `float` | After step | Score in [0.0, 1.0] |
| `done` | `bool` | Always | `false` on reset, `true` after step |

## Reward Function — Multi-Signal Semantic Scoring

Each predicted action item is matched to the best ground-truth item using a **greedy assignment**. Per matched pair, each field (`who`, `what`, `deadline`) is scored using a blend of four similarity signals:

| Signal | Weight | What it captures |
|--------|--------|-----------------|
| Token overlap (Jaccard) | 20% | Keyword presence |
| Bigram overlap | 20% | Phrase-level matching |
| SequenceMatcher | 25% | Edit-distance similarity |
| TF-IDF cosine | 35% | Term-importance-weighted similarity |

The per-item score combines fields with weights: `who × 0.30 + what × 0.40 + deadline × 0.30`.

**Final reward** = average(item scores) − penalties:
- **Extra items**: −0.05 per hallucinated item
- **Missing items**: −0.02 per unmatched ground truth

This produces a **continuous reward signal** — even partially correct answers get meaningful credit, which is useful for RL training.

## Quick Start

### 1. Install dependencies

```bash
pip install openenv-core requests openai
```

### 2. Run the server locally

```bash
cd meeting_notes_env
PYTHONPATH=. uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### 3. Test with curl

```bash
# Reset with a specific task
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "easy_1"}'

# Submit an answer
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"message": "{\"task_id\": \"easy_1\", \"items\": [{\"who\": \"Bob\", \"what\": \"fix the CI pipeline\", \"deadline\": \"Wednesday\"}]}"}}'
```

### 4. Run the baseline inference script

```bash
export HF_TOKEN="hf_..."
export ENV_URL="http://localhost:8000"        # or https://prateekdebit-meeting-notes-env.hf.space
python inference.py
```

### 5. Docker

```bash
docker build -t meeting-notes-env .
docker run -p 8000:8000 meeting-notes-env
```

## API Reference

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| `/reset` | POST | `{"task": "easy_1"}` (optional) | Start a new episode. Omit task for random selection. |
| `/step` | POST | `{"action": {"message": "<json>"}}` | Submit action items, receive reward. |
| `/state` | GET | — | Current episode state. |
| `/health` | GET | — | Health check (returns 200). |
| `/ws` | WS | — | WebSocket for persistent sessions. |
| `/web` | GET | — | Interactive web UI. |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | **Yes** | — | Hugging Face token for LLM API access |
| `API_BASE_URL` | No | `https://router.huggingface.co/v1` | OpenAI-compatible API endpoint |
| `MODEL_NAME` | No | `Qwen/Qwen2.5-72B-Instruct` | Model identifier |
| `ENV_URL` | No | `https://prateekdebit-meeting-notes-env.hf.space` | Environment server URL |

## Project Structure

```
meeting_notes_env/
├── inference.py                          # Baseline inference (OpenAI Client + [START]/[STEP]/[END] logging)
├── models.py                             # MeetingNotesAction + MeetingNotesObservation (typed Pydantic models)
├── client.py                             # WebSocket client for persistent sessions
├── openenv.yaml                          # OpenEnv manifest
├── pyproject.toml                        # Dependencies and project metadata
├── Dockerfile                            # Root Dockerfile for validation
├── __init__.py
├── outputs/                              # Inference output directory
└── server/
    ├── app.py                            # FastAPI application (create_app + main)
    ├── meeting_notes_env_environment.py  # Environment logic + semantic scoring
    ├── tasks.py                          # 32 task definitions (transcripts + ground truth)
    ├── Dockerfile                        # Server Dockerfile
    └── requirements.txt
```

## License

BSD-style license. See LICENSE file in the root directory.

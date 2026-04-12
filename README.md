---
title: Meeting Notes Env
emoji: 📝
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 8000
---

# Meeting Notes → Action Items Environment

A **multi-step interactive RL environment** where agents extract action items from meeting transcripts through iterative submission, revision, and feedback.

Unlike single-shot extraction, the agent must make **strategic decisions** across multiple steps: submit items one at a time, interpret per-item feedback, revise low-scoring answers, optionally request hints (at a reward cost), and decide when to finalize.

## Why This Task Matters

Meeting action-item extraction is a universal workplace task — and doing it well requires nuance. Agents must handle vague deadlines, implicit ownership, superseded decisions, red herrings, and multi-meeting contexts. The multi-step design makes this an **RL-trainable environment**, not just a benchmark.

## Environment Design

```
reset(task) → transcript + instructions
    │
    ├── step(submit_item)    → per-item score + feedback
    │       ↕ (loop)
    ├── step(revise_item)    → delta score from revision
    │
    ├── step(request_context)→ hint about missing items (-0.03 penalty)
    │
    └── step(finalize)       → final aggregated reward
         or auto-finalize at step 15
```

### Action Space (4 typed actions)

| Action | Parameters | Effect |
|---|---|---|
| `submit_item` | who, what, deadline | Submit one action item; receive per-item score |
| `revise_item` | item_index, who, what, deadline | Revise a previously submitted item; reward = improvement delta |
| `request_context` | — | Get a hint about missing items (costs -0.03 reward) |
| `finalize` | — | End episode; receive final aggregated reward |

### Observation Space

| Field | Type | Description |
|---|---|---|
| `transcript` | str | Meeting transcript (provided on reset, omitted on later steps) |
| `task_id` | str | Current task identifier |
| `num_expected` | int | Number of ground-truth action items |
| `submitted_items` | list | Items submitted so far with per-item scores |
| `feedback` | str | Per-step grading breakdown |
| `steps_remaining` | int | Steps left before auto-finalize |
| `hints_used` | int | Context hints consumed (max 3) |
| `valid_actions` | list | Currently available action types |

### Reward Design

**Per-step signals (small, shaping):**
- `submit_item`: `item_score × 0.10`
- `revise_item`: `(new_score - old_score) × 0.10`
- `request_context`: `-0.03` (hint penalty)

**On finalize (aggregated):**
```
final = base_reward + efficiency_bonus - hint_penalty - auto_penalty
```
- `base_reward`: semantic similarity across all submitted vs. expected items
- `efficiency_bonus`: `0.05 × (steps_remaining / 15)` — fewer steps = higher reward
- `hint_penalty`: `0.03 × hints_used`
- `auto_penalty`: `0.05` if auto-finalized (didn't call finalize voluntarily)

All rewards clamped to the open interval **(0.01, 0.99)**.

### Semantic Scoring

Each submitted item is graded against ground truth using a multi-signal blend:

| Signal | Weight | Captures |
|---|---|---|
| Token overlap (Jaccard) | 20% | Keyword presence |
| Bigram overlap | 20% | Phrase-level matching |
| SequenceMatcher | 25% | Edit-distance similarity |
| TF-IDF cosine | 35% | Term-importance weighting |

Per-item score = `0.30 × who + 0.40 × what + 0.30 × deadline`

## Tasks

**50 tasks** across 3 difficulty levels:

| Difficulty | Count | Items/Task | Characteristics |
|---|---|---|---|
| Easy | 15 | 1 | Short transcript, explicit who/what/deadline |
| Medium | 15 | 3-4 | Multiple speakers, scattered assignments |
| Hard | 20 | 3-5 | Implicit owners, vague deadlines, superseded decisions, red herrings, delegation chains, conditional tasks, multi-meeting merges |

### What Makes Hard Tasks Hard

- **Superseded decisions**: Initial assignments get overridden later in the transcript
- **Red herrings**: Brainstorming ideas that are NOT committed to
- **Implicit delegation**: "Your team should handle it" → who specifically?
- **Conditional tasks**: "Only if the audit passes" → should NOT be extracted
- **Multi-meeting transcripts**: Morning standup + afternoon planning merged
- **Evolving scope**: Same task discussed 3 times with expanding requirements
- **Shared ownership**: "Erik and Fiona, jointly own the migration plan"

## Quick Start

**Live Space:** [prateekdebit/meeting-notes-env](https://huggingface.co/spaces/prateekdebit/meeting-notes-env) — public API base URL: **`https://prateekdebit-meeting-notes-env.hf.space`** (first request may wake the Space and take longer). If that host 404s, rename the Space on Hugging Face to `meeting-notes-env` (see below) or use the suffixed `*.hf.space` URL from the Space page HTML until the short URL propagates.

### API Interaction (local)

```bash
# Reset to a specific task
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "easy_1"}'

# Submit an action item
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "submit_item", "who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"}}'

# Revise a submitted item
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "revise_item", "item_index": 0, "who": "Bob", "what": "fix the CI/CD pipeline", "deadline": "end of day Wednesday"}}'

# Request a hint
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "request_context"}}'

# Finalize the episode
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "finalize"}}'
```

### API Interaction (deployed Space)

Use the same paths as above with the Space base URL (or set `BASE` once):

```bash
export BASE=https://prateekdebit-meeting-notes-env.hf.space

curl -X POST "$BASE/reset" \
  -H "Content-Type: application/json" \
  -d '{"task": "easy_1"}'
```

### Run Baseline Inference

```bash
export HF_TOKEN=hf_...
# Optional: override environment URL (default in inference.py is the Space above)
# export ENV_URL=https://prateekdebit-meeting-notes-env.hf.space
python inference.py
```

### Run Training Loop

```bash
export ENV_URL=http://localhost:8000
python training/train_simple.py --episodes 50 --tasks all --verbose
```

### Run Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Project Structure

```
meeting_notes_env/
├── models.py                  # Pydantic action/observation models (4 action types)
├── inference.py               # Multi-step baseline agent with LLM
├── openenv.yaml               # OpenEnv manifest
├── pyproject.toml             # Dependencies
├── Dockerfile                 # Production container
├── server/
│   ├── app.py                 # FastAPI server
│   ├── meeting_notes_env_environment.py  # Multi-step environment logic
│   └── tasks.py               # 50 task definitions
├── tests/
│   ├── test_grading.py        # Scoring function unit tests
│   ├── test_environment.py    # Multi-step flow integration tests
│   └── test_models.py         # Pydantic model validation tests
├── training/
│   └── train_simple.py        # RL training loop demonstration
└── outputs/                   # Inference output artifacts
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `API_BASE_URL` | No | `https://router.huggingface.co/v1` | LLM endpoint |
| `MODEL_NAME` | No | `Qwen/Qwen2.5-72B-Instruct` | Model identifier |
| `HF_TOKEN` | Yes | — | Hugging Face API token |
| `ENV_URL` | No | `https://prateekdebit-meeting-notes-env.hf.space` | Environment server URL |

## Hugging Face: canonical name and short URL

The Space repository id is **`meeting-notes-env`** (hyphens), matching [GitHub `meeting-notes-env`](https://github.com/Prateedk/meeting-notes-env). That gives the clean app host **`https://prateekdebit-meeting-notes-env.hf.space`** (no hash suffix).

### One-time rename (if the Space still shows `meeting_notes_env`)

1. Open the Space **Settings** on Hugging Face.
2. Set **Repository name** to **`meeting-notes-env`** and save. (Remove or avoid a second Space with the same slug, or Hugging Face will assign a disambiguating suffix in the `*.hf.space` hostname.)

## Updating the Hugging Face Space

Pushes to the Space repository trigger a new Docker build. From your local clone:

```bash
git remote add huggingface https://huggingface.co/spaces/prateekdebit/meeting-notes-env.git  # once
# or, if the remote already exists:
git remote set-url huggingface https://huggingface.co/spaces/prateekdebit/meeting-notes-env.git
git push huggingface main
```

Use your Hugging Face **access token** as the password when prompted (or configure [git credential storage](https://huggingface.co/docs/hub/security-tokens)). If the Space still looks outdated, open the Space **Build** logs and confirm the latest commit built successfully; failed builds keep serving the previous image.

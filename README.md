---
title: Meeting Notes Env
emoji: 📝
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 8000
tags:
  - openenv
---

# Meeting Notes → Action Items Environment

## Environment description and motivation

This environment simulates a **real workplace task**: turning meeting dialogue into **structured action items** (who must do what, by when). Humans do this daily in standups, planning sessions, and reviews; assistants and agents need to handle **implicit owners**, **noisy dialogue**, **changed decisions**, and **soft deadlines**.

The design is **multi-step and interactive**: the agent calls `reset` to receive a transcript, then uses `step` to **submit** items one at a time, **revise** them using grader feedback, optionally pay a penalty for **hints**, and **finalize** when done. That yields **dense reward signal** along the trajectory (not only at the end), which fits RL and agent evaluation better than a single-shot extract benchmark.

**Why it matters:** Action-item extraction is easy to specify but hard to grade fairly. This repo pairs **50 diverse transcripts** (easy → hard) with a **deterministic semantic grader** so scores stay reproducible without external embedding APIs.

## Action space

Actions are typed Pydantic payloads (`MeetingNotesAction`). Each step sends JSON with `action_type` and optional fields:

| `action_type` | Fields | Effect |
|---------------|--------|--------|
| `submit_item` | `who`, `what`, `deadline` (strings) | Append one candidate action item; receive per-item score and feedback. |
| `revise_item` | `item_index` (int), `who`, `what`, `deadline` | Replace a previously submitted item; step reward reflects score **improvement** (shaping). |
| `request_context` | — | Receive a hint about missing items; fixed **negative** reward. |
| `finalize` | — | End the episode; return **aggregated** final reward (`done=true`). |

Example `submit_item` body:

```json
{
  "action": {
    "action_type": "submit_item",
    "who": "Bob",
    "what": "fix the CI pipeline",
    "deadline": "Wednesday"
  }
}
```

## Observation space

Each `step` / `reset` returns a `MeetingNotesObservation` (plus standard OpenEnv fields such as **`reward`**, **`done`**, and **`metadata`** on every step).

| Field | Type | Description |
|-------|------|-------------|
| `transcript` | string | Full meeting text on `reset`; typically empty on later steps (agent should retain context). |
| `task_id` | string | Task identifier (e.g. `easy_1`, `medium_4`). |
| `task_description` | string | Short human-readable task goal. |
| `num_expected` | integer | Count of ground-truth action items for this task. |
| `submitted_items` | list | Items submitted so far, including grader `score` and breakdown metadata. |
| `feedback` | string | Natural-language feedback for the last action. |
| `steps_remaining` | integer | Steps until auto-finalize (max episode length). |
| `hints_used` | integer | How many hint requests have been consumed. |
| `valid_actions` | list of strings | Which `action_type` values are legal at this point. |

## Rewards and grading

**Per-step shaping (small signal):**

- `submit_item`: `item_score × 0.10`
- `revise_item`: `(new_score − old_score) × 0.10` (only positive improvement accumulates to cumulative shaping)
- `request_context`: `−0.03` per hint

**On `finalize` (primary scalar):**

```
final = base_reward + efficiency_bonus − hint_penalty − auto_penalty
```

Then clamped to **(0.01, 0.99)**.

- **`base_reward`**: match quality of all submitted items vs. ground truth (see below).
- **`efficiency_bonus`**: `0.05 × (MAX_STEPS − steps_used) / MAX_STEPS` at finalize (`MAX_STEPS = 15`); fewer steps before ending → higher bonus.
- **`hint_penalty`**: `0.03 × hints_used`
- **`auto_penalty`**: applied if the episode ends by hitting the step limit without a voluntary `finalize`.

**Semantic scoring:** each field (`who`, `what`, `deadline`) blends token overlap, bigrams, sequence similarity, and local TF–IDF cosine, then applies **field-specific** boosts (e.g. name subset/superset, deadline boilerplate stripping, content-word recall for paraphrases). Per-item score = `0.30×who + 0.40×what + 0.30×deadline`.

## Tasks (difficulty and descriptions)

**Summary**

| Difficulty | Count | Items per task (expected) | Focus |
|------------|-------|-----------------------------|--------|
| **easy** | 15 | 1 | Short transcript; explicit who / what / when. |
| **medium** | 15 | 3–4 | Multiple speakers; items scattered through dialogue. |
| **hard** | 20 | 3–5 | Implicit owners, merged meetings, superseded decisions, red herrings, chains, conditionals. |

**Full catalog (all 50 tasks)**

| task_id | difficulty | expected_items | description |
|---------|------------|----------------|-------------|
| `easy_1` | easy | 1 | Extract the single action item from a short standup. |
| `easy_2` | easy | 1 | Extract the single action item from a brief project check-in. |
| `easy_3` | easy | 1 | Extract the action item from a quick sales sync. |
| `easy_4` | easy | 1 | Extract the action item from an HR check-in. |
| `easy_5` | easy | 1 | Extract the action item from a design review. |
| `easy_6` | easy | 1 | Extract the action item from a security standup. |
| `easy_7` | easy | 1 | Extract the action item from a marketing sync. |
| `easy_8` | easy | 1 | Extract the action item from an ops incident debrief. |
| `easy_9` | easy | 1 | Extract the action item from a finance check-in. |
| `easy_10` | easy | 1 | Extract the action item from an engineering 1:1. |
| `easy_11` | easy | 1 | Extract the action item from a legal compliance check-in. |
| `easy_12` | easy | 1 | Extract the action item from a customer support standup. |
| `easy_13` | easy | 1 | Extract the action item from a research sync. |
| `easy_14` | easy | 1 | Extract the action item from a partnership discussion. |
| `easy_15` | easy | 1 | Extract the action item from a data engineering standup. |
| `medium_1` | medium | 3 | Extract all action items from a multi-person planning meeting. |
| `medium_2` | medium | 3 | Extract action items from a cross-team sync meeting. |
| `medium_3` | medium | 3 | Extract action items from a product planning meeting. |
| `medium_4` | medium | 4 | Extract action items from a client onboarding meeting. |
| `medium_5` | medium | 3 | Extract action items from a release planning meeting. |
| `medium_6` | medium | 3 | Extract action items from a team retrospective. |
| `medium_7` | medium | 4 | Extract action items from a budget review meeting. |
| `medium_8` | medium | 3 | Extract action items from an infrastructure planning meeting. |
| `medium_9` | medium | 3 | Extract action items from a hiring committee meeting. |
| `medium_10` | medium | 3 | Extract action items from a training session planning meeting. |
| `medium_11` | medium | 3 | Extract action items from a product launch readiness meeting. |
| `medium_12` | medium | 3 | Extract action items from a security review meeting. |
| `medium_13` | medium | 3 | Extract action items from a content strategy meeting. |
| `medium_14` | medium | 3 | Extract action items from a platform migration planning meeting. |
| `medium_15` | medium | 3 | Extract action items from an accessibility review meeting. |
| `hard_1` | hard | 3 | Extract action items from a messy quarterly review with vague commitments. |
| `hard_2` | hard | 4 | Extract action items from an informal meeting with implied owners. |
| `hard_3` | hard | 4 | Long all-hands with many speakers; action items buried in discussion. |
| `hard_4` | hard | 5 | Two meetings merged — morning standup and afternoon planning. Separate the action items. |
| `hard_5` | hard | 3 | Meeting with superseded and changed decisions. Only the final decisions count. |
| `hard_6` | hard | 4 | Meeting with extremely vague and relative deadlines requiring inference. |
| `hard_7` | hard | 3 | Long brainstorming session with lots of ideas but few real commitments. |
| `hard_8` | hard | 4 | Crisis incident response with rapid-fire assignments under pressure. |
| `hard_9` | hard | 3 | Meeting with conditional actions, negated tasks, and red herrings. |
| `hard_10` | hard | 4 | Cross-functional meeting with delegation chains and implicit ownership. |
| `hard_11` | hard | 5 | All-day offsite summary with scattered action items across sessions. |
| `hard_12` | hard | 4 | Chaotic meeting with interruptions, tangents, and speakers talking over each other. |
| `hard_13` | hard | 3 | Meeting where tasks are delegated through a chain — A assigns to B who re-delegates to C. |
| `hard_14` | hard | 3 | Meeting with tasks assigned to roles not people, requiring inference of who. |
| `hard_15` | hard | 4 | Meeting where multiple items are assigned to the same person across different topics. |
| `hard_16` | hard | 3 | Meeting with abandoned proposals mixed in with real assignments. |
| `hard_17` | hard | 4 | Multi-timezone async standup with tasks spread across regions. |
| `hard_18` | hard | 4 | Board preparation meeting with executive-level tasks and implied deadlines. |
| `hard_19` | hard | 3 | Meeting where the same task is discussed multiple times with evolving scope. |
| `hard_20` | hard | 4 | Post-acquisition integration meeting with political dynamics and shared ownership. |

## Setup and usage

### Prerequisites

- Python **3.10+**
- [uv](https://docs.astral.sh/uv/) or `pip` for dependencies
- **Docker** (optional, for container build / HF Space parity)
- **`openenv-core`** for validation: `pip install openenv-core`

### Install (local)

```bash
cd meeting_notes_env
uv sync --extra dev
# or: pip install -e ".[dev]"
```

### Run the API server (local)

```bash
uv run python -m meeting_notes_env.server.app
# default: http://127.0.0.1:8000  — see /docs
```

### Docker

```bash
docker build -t meeting-notes-env .
docker run -p 8000:8000 meeting-notes-env
```

### Hugging Face Space

**Live Space:** [prateekdebit/meeting-notes-env](https://huggingface.co/spaces/prateekdebit/meeting-notes-env) — API base **`https://prateekdebit-meeting-notes-env.hf.space`** (cold start may take longer).

### API examples

```bash
# Reset to a task
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "easy_1"}'

curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "submit_item", "who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"}}'

curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "finalize"}}'
```

### Baseline inference (`inference.py`)

```bash
export HF_TOKEN=hf_...
# optional: export ENV_URL=https://prateekdebit-meeting-notes-env.hf.space
# smoke: export INFERENCE_MAX_TASKS=3
python inference.py
```

Uses the **OpenAI Python client** against `API_BASE_URL` / `MODEL_NAME`. Logs must follow **`[START]`**, **`[STEP]  step=...`**, **`[END]  success=...`** (see `inference.py`).

### Tests and validation

```bash
uv run pytest tests/ -v
uv run openenv validate
./validate-submission.sh https://prateekdebit-meeting-notes-env.hf.space .
```

Optional training demo:

```bash
export ENV_URL=http://localhost:8000
python training/train_simple.py --episodes 50 --tasks all --verbose
```

## Baseline scores

### Deterministic oracle (all 50 tasks)

These numbers are **reproducible** (no LLM). For each task, every `ground_truth` row is submitted in order via `submit_item`, then `finalize`.

- **`oracle_base_reward`**: value from `_grade_all_submitted` for those items (matches `finalize` **metadata** `base_reward`; no efficiency or hint terms).
- **`oracle_finalize_reward`**: environment **`reward`** on the voluntary `finalize` step (includes efficiency bonus, then clamp to **0.99** max).

Regenerate after grader changes:

```bash
uv run python scripts/print_grader_calibration.py --markdown
uv run python scripts/print_grader_calibration.py --task-catalog
```

| task_id | difficulty | expected_items | oracle_base_reward | oracle_finalize_reward |
|---------|------------|----------------|--------------------|------------------------|
| `easy_1` | easy | 1 | 1.0000 | 0.9900 |
| `easy_2` | easy | 1 | 1.0000 | 0.9900 |
| `easy_3` | easy | 1 | 1.0000 | 0.9900 |
| `easy_4` | easy | 1 | 1.0000 | 0.9900 |
| `easy_5` | easy | 1 | 1.0000 | 0.9900 |
| `easy_6` | easy | 1 | 1.0000 | 0.9900 |
| `easy_7` | easy | 1 | 1.0000 | 0.9900 |
| `easy_8` | easy | 1 | 1.0000 | 0.9900 |
| `easy_9` | easy | 1 | 1.0000 | 0.9900 |
| `easy_10` | easy | 1 | 1.0000 | 0.9900 |
| `easy_11` | easy | 1 | 1.0000 | 0.9900 |
| `easy_12` | easy | 1 | 1.0000 | 0.9900 |
| `easy_13` | easy | 1 | 1.0000 | 0.9900 |
| `easy_14` | easy | 1 | 1.0000 | 0.9900 |
| `easy_15` | easy | 1 | 1.0000 | 0.9900 |
| `medium_1` | medium | 3 | 1.0000 | 0.9900 |
| `medium_2` | medium | 3 | 1.0000 | 0.9900 |
| `medium_3` | medium | 3 | 1.0000 | 0.9900 |
| `medium_4` | medium | 4 | 1.0000 | 0.9900 |
| `medium_5` | medium | 3 | 1.0000 | 0.9900 |
| `medium_6` | medium | 3 | 1.0000 | 0.9900 |
| `medium_7` | medium | 4 | 1.0000 | 0.9900 |
| `medium_8` | medium | 3 | 1.0000 | 0.9900 |
| `medium_9` | medium | 3 | 1.0000 | 0.9900 |
| `medium_10` | medium | 3 | 1.0000 | 0.9900 |
| `medium_11` | medium | 3 | 1.0000 | 0.9900 |
| `medium_12` | medium | 3 | 1.0000 | 0.9900 |
| `medium_13` | medium | 3 | 1.0000 | 0.9900 |
| `medium_14` | medium | 3 | 1.0000 | 0.9900 |
| `medium_15` | medium | 3 | 1.0000 | 0.9900 |
| `hard_1` | hard | 3 | 1.0000 | 0.9900 |
| `hard_2` | hard | 4 | 1.0000 | 0.9900 |
| `hard_3` | hard | 4 | 1.0000 | 0.9900 |
| `hard_4` | hard | 5 | 1.0000 | 0.9900 |
| `hard_5` | hard | 3 | 1.0000 | 0.9900 |
| `hard_6` | hard | 4 | 1.0000 | 0.9900 |
| `hard_7` | hard | 3 | 1.0000 | 0.9900 |
| `hard_8` | hard | 4 | 1.0000 | 0.9900 |
| `hard_9` | hard | 3 | 1.0000 | 0.9900 |
| `hard_10` | hard | 4 | 1.0000 | 0.9900 |
| `hard_11` | hard | 5 | 1.0000 | 0.9900 |
| `hard_12` | hard | 4 | 1.0000 | 0.9900 |
| `hard_13` | hard | 3 | 1.0000 | 0.9900 |
| `hard_14` | hard | 3 | 1.0000 | 0.9900 |
| `hard_15` | hard | 4 | 1.0000 | 0.9900 |
| `hard_16` | hard | 3 | 1.0000 | 0.9900 |
| `hard_17` | hard | 4 | 1.0000 | 0.9900 |
| `hard_18` | hard | 4 | 1.0000 | 0.9900 |
| `hard_19` | hard | 3 | 1.0000 | 0.9900 |
| `hard_20` | hard | 4 | 1.0000 | 0.9900 |

### Paraphrase spot-check (`easy_1`)

Same episode shape (one `submit_item`, then `finalize`) but **non-exact** strings typical of LLMs:

| task_id | scenario | oracle_base_reward | oracle_finalize_reward |
|---------|----------|--------------------|------------------------|
| `easy_1` | Typical LLM-style wording (“repair the CI pipeline”, “end of day Wednesday”) | 0.9280 | 0.9713 |

### Stochastic LLM baseline

`inference.py` scores depend on **model**, **API**, and **temperature** (`0.0` in the script). To record a full **per-task** table of **`[END] score=`** values, run:

```bash
export HF_TOKEN=hf_...
python inference.py 2>&1 | tee baseline_run.log
grep '\[END\]' baseline_run.log
```

`success` in `[END]` uses **`SUCCESS_SCORE_THRESHOLD`** (default **0.25**). Update your own runbook table when you freeze a reference model and date.

## Pre-submission checklist (hackathon / OpenEnv)

| Requirement | How to verify |
|-------------|----------------|
| HF Space **200** on `POST /reset` | `./validate-submission.sh <your-space.hf.space>` |
| Tag **`openenv`** | Space **Settings → Tags** (also in README front matter) |
| Root **Dockerfile** | `docker build .` |
| **`openenv validate`** | `openenv validate` |
| **`inference.py`** + OpenAI client + **`HF_TOKEN`** | See [Setup and usage](#setup-and-usage) |
| **`[START]` / `[STEP]` / `[END]`** logs | Run inference and inspect stdout |
| README **baseline scores** | [Baseline scores](#baseline-scores) |

## Project structure

```
meeting_notes_env/
├── models.py
├── inference.py
├── openenv.yaml
├── validate-submission.sh
├── scripts/
│   └── print_grader_calibration.py
├── pyproject.toml
├── Dockerfile
├── server/
│   ├── app.py
│   ├── meeting_notes_env_environment.py
│   └── tasks.py
├── tests/
├── training/
└── outputs/
```

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | Yes (for `inference.py`) | — | API token for the OpenAI-compatible client |
| `API_BASE_URL` | No | `https://router.huggingface.co/v1` | LLM base URL |
| `MODEL_NAME` | No | `Qwen/Qwen2.5-72B-Instruct` | Chat model id |
| `ENV_URL` | No | `https://prateekdebit-meeting-notes-env.hf.space` | Environment HTTP base |
| `INFERENCE_HTTP_TIMEOUT` | No | `120` | HTTP timeout (s) for `/reset` and `/step` |
| `INFERENCE_MAX_TASKS` | No | all 50 | Cap number of tasks (smoke runs) |
| `SUCCESS_SCORE_THRESHOLD` | No | `0.25` | `[END] success=true` if final score &gt; this |

## Hugging Face: canonical name and short URL

The Space id **`prateekdebit/meeting-notes-env`** matches [GitHub `meeting-notes-env`](https://github.com/Prateedk/meeting-notes-env). App host: **`https://prateekdebit-meeting-notes-env.hf.space`**.

### Rename or transfer

Use **Settings → “Rename or transfer this Space”**. Then:

```bash
git remote set-url huggingface https://huggingface.co/spaces/prateekdebit/meeting-notes-env.git
git remote -v
```

### Push to rebuild the Space

```bash
git push huggingface main
```

Check **Build** logs on Hugging Face if the Space serves an old image after a failed build.

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

A real-world OpenEnv environment where an AI agent reads **meeting transcripts** and extracts **structured action items** (who, what, deadline). The environment grades the agent's output against ground-truth labels using fuzzy token-overlap matching and returns a reward in **[0.0, 1.0]** with partial credit.

## Why This Is a Real-World Task

Extracting action items from meeting notes is one of the most common knowledge-work tasks. Millions of meetings happen daily; ensuring follow-ups are tracked accurately is critical for productivity. This environment tests an LLM's ability to:

- Identify **who** is responsible
- Understand **what** they need to do
- Recognize **deadlines** (explicit or implied)

## Tasks (3 difficulties × 2 transcripts = 6 graded tasks)

| Task ID | Difficulty | Items | Description |
|---------|-----------|-------|-------------|
| `extract_single_1` | Easy | 1 | Short standup, one clear action |
| `extract_single_2` | Easy | 1 | Brief check-in, single deliverable |
| `extract_multiple_1` | Medium | 3 | Sprint planning, multiple assignees |
| `extract_multiple_2` | Medium | 3 | Cross-team sync, different departments |
| `extract_ambiguous_1` | Hard | 3 | Quarterly review, vague commitments, implied deadlines |
| `extract_ambiguous_2` | Hard | 4 | Ad-hoc sync, informal language, implicit owners |

## Action Space

**`MeetingNotesAction`**: A JSON string containing a list of action items.

```json
[
  {"who": "Alice", "what": "send the report", "deadline": "Friday"},
  {"who": "Bob", "what": "review the PR", "deadline": "Monday"}
]
```

## Observation Space

**`MeetingNotesObservation`**:

| Field | Type | Description |
|-------|------|-------------|
| `transcript` | str | The meeting transcript to analyze |
| `task_id` | str | Identifier for the current task |
| `task_description` | str | Human-readable task description |
| `feedback` | str | Grading feedback (after step) |
| `num_expected` | int | Number of expected action items |
| `reward` | float | Score in [0.0, 1.0] |
| `done` | bool | Whether the episode is complete |

## Reward Function

Per ground-truth action item, the agent scores:
- **0.33** for matching `who` (fuzzy token overlap ≥ 45%)
- **0.34** for matching `what` (fuzzy token overlap ≥ 45%)
- **0.33** for matching `deadline` (fuzzy token overlap ≥ 45%)

Final reward = average across all expected items, with a small penalty (−0.05 each) for extra predicted items. Clamped to [0.0, 1.0].

## Setup

### Install dependencies

```bash
pip install openenv-core requests openai
```

### Run the server locally

```bash
cd meeting_notes_env
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Run inference

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="hf_..."
export ENV_URL="http://localhost:8000"

python inference.py
```

### Docker

```bash
docker build -t meeting-notes-env:latest -f server/Dockerfile .
docker run -p 8000:8000 meeting-notes-env:latest
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start a new episode (optionally pass `{"task": "extract_single_1"}`) |
| `/step` | POST | Submit action items `{"action": {"message": "[{...}]"}}` |
| `/state` | GET | Current episode state |
| `/health` | GET | Health check |
| `/ws` | WS | WebSocket for persistent sessions |
| `/web` | GET | Interactive web UI |

## Environment Variables for Inference

| Variable | Description |
|----------|-------------|
| `API_BASE_URL` | OpenAI-compatible API endpoint |
| `MODEL_NAME` | Model identifier |
| `HF_TOKEN` | Hugging Face / API key |

## Project Structure

```
meeting_notes_env/
├── inference.py          # Baseline inference script
├── models.py             # Action + Observation types
├── client.py             # WebSocket client
├── __init__.py
├── openenv.yaml          # OpenEnv manifest
├── pyproject.toml
├── README.md
└── server/
    ├── app.py                              # FastAPI application
    ├── meeting_notes_env_environment.py     # Core environment logic
    ├── Dockerfile
    └── requirements.txt
```

#!/usr/bin/env python3
"""Baseline inference script for the Meeting Notes → Action Items environment.

Uses the OpenAI Client to call an LLM that reads meeting transcripts and
extracts structured action items.

Required environment variables:
    API_BASE_URL  — OpenAI-compatible endpoint (e.g. https://router.huggingface.co/v1)
    MODEL_NAME    — model identifier
    HF_TOKEN      — API key / Hugging Face token

Structured logging follows the [START], [STEP], [END] format required by
the Scaler / Meta-PyTorch OpenEnv hackathon evaluation system.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------------------
# Env client imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from client import MeetingNotesEnv  # noqa: E402
from models import MeetingNotesAction  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

ENV_URL = os.environ.get("ENV_URL", "http://localhost:8000")

TASK_IDS = [
    "extract_single_1",
    "extract_single_2",
    "extract_multiple_1",
    "extract_multiple_2",
    "extract_ambiguous_1",
    "extract_ambiguous_2",
]

SYSTEM_PROMPT = """\
You are an expert meeting-notes analyst. Given a meeting transcript, extract \
ALL action items as a JSON array. Each item must have exactly three keys:
- "who": the person responsible (use their name as it appears in the transcript)
- "what": a concise description of the task
- "deadline": the deadline mentioned (use the exact wording from the transcript)

Return ONLY the JSON array, no markdown, no explanation. Example:
[{"who":"Alice","what":"send the report","deadline":"Friday"}]
If there are multiple action items return them all in the array."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call_llm(client: OpenAI, transcript: str, num_expected: int) -> str:
    """Ask the LLM to extract action items from a transcript."""
    user_msg = (
        f"Meeting transcript:\n\n{transcript}\n\n"
        f"There are {num_expected} action item(s) to find. "
        "Return ONLY the JSON array."
    )
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=1024,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


def _clean_json(raw: str) -> str:
    """Strip markdown fences if the model wraps its JSON in ```."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    return raw


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not HF_TOKEN:
        print("WARNING: HF_TOKEN not set. LLM calls may fail.", file=sys.stderr)

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    results = []

    print(f"[START] task_count={len(TASK_IDS)} model={MODEL_NAME}")

    env = MeetingNotesEnv(base_url=ENV_URL).sync()
    env.connect()

    try:
        for idx, task_id in enumerate(TASK_IDS):
            step_start = time.time()

            result = env.reset(task=task_id)
            obs = result.observation
            transcript = obs.transcript
            num_expected = obs.num_expected

            raw_answer = _call_llm(llm_client, transcript, num_expected)
            cleaned = _clean_json(raw_answer)

            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                answer_json = json.dumps(parsed)
            except json.JSONDecodeError:
                answer_json = cleaned

            step_result = env.step(MeetingNotesAction(message=answer_json))
            reward = step_result.reward or 0.0
            feedback = step_result.observation.feedback
            done = step_result.done

            elapsed = time.time() - step_start

            print(
                f"[STEP] task_id={task_id} "
                f"step={idx + 1} "
                f"reward={reward} "
                f"done={done} "
                f"elapsed={elapsed:.2f}s "
                f"feedback={feedback}"
            )

            results.append({"task_id": task_id, "reward": reward})
    finally:
        env.close()

    avg_reward = sum(r["reward"] for r in results) / max(len(results), 1)
    print(f"[END] avg_reward={avg_reward:.4f} total_tasks={len(results)}")


if __name__ == "__main__":
    main()

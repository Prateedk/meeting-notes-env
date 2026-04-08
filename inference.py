#!/usr/bin/env python3
"""Baseline inference for the Meeting Notes → Action Items environment.

Required environment variables:
    API_BASE_URL  — OpenAI-compatible endpoint (must have a default)
    MODEL_NAME    — model identifier (must have a default)
    HF_TOKEN      — Hugging Face / API key (mandatory, no default)
"""

from __future__ import annotations

import json
import os
import sys

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Environment variables (per hackathon spec)
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

ENV_URL = os.getenv("ENV_URL", "https://prateekdebit-meeting-notes-env.hf.space")

# ---------------------------------------------------------------------------
# Tasks to evaluate (3 difficulty levels × 2 each = 6)
# ---------------------------------------------------------------------------

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

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


def call_llm(transcript: str, num_expected: int) -> str:
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


def clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    return raw


def env_reset(task_id: str) -> dict:
    resp = requests.post(
        f"{ENV_URL}/reset",
        json={"task": task_id},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def env_step(message: str) -> dict:
    resp = requests.post(
        f"{ENV_URL}/step",
        json={"action": {"message": message}},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    for task_id in TASK_IDS:
        all_rewards: list[float] = []
        success = False
        steps = 0
        last_error = "null"

        try:
            # --- [START] ---
            print(
                f"[START] task={task_id} env=meeting_notes_env model={MODEL_NAME}",
                flush=True,
            )

            # Reset to get transcript
            reset_data = env_reset(task_id)
            obs = reset_data.get("observation", reset_data)
            transcript = obs.get("transcript", "")
            num_expected = obs.get("num_expected", 0)

            # Call LLM
            raw_answer = call_llm(transcript, num_expected)
            cleaned = clean_json(raw_answer)

            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                items = parsed
            except json.JSONDecodeError:
                items = []

            action_str = json.dumps(items)

            # Build combined payload so stateless HTTP step knows the task
            step_payload = json.dumps({"task_id": task_id, "items": items})

            # Step
            step_data = env_step(step_payload)
            step_obs = step_data.get("observation", step_data)
            reward = float(step_data.get("reward", step_obs.get("reward", 0.0)) or 0.0)
            done = step_data.get("done", step_obs.get("done", True))
            error_str = step_obs.get("metadata", {}).get("error", None)

            steps = 1
            all_rewards.append(reward)
            success = reward > 0.0

            # --- [STEP] ---
            done_str = "true" if done else "false"
            error_out = error_str if error_str else "null"
            print(
                f"[STEP] step=1 action={action_str} "
                f"reward={reward:.2f} done={done_str} error={error_out}",
                flush=True,
            )

        except Exception as exc:
            last_error = str(exc)
            if not all_rewards:
                all_rewards.append(0.0)
            steps = max(steps, 1)
            print(
                f"[STEP] step={steps} action=error "
                f"reward=0.00 done=true error={last_error}",
                flush=True,
            )

        # --- [END] ---
        score = all_rewards[-1] if all_rewards else 0.0
        score = min(max(score, 0.0), 1.0)
        success_str = "true" if success else "false"
        rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
        print(
            f"[END] success={success_str} steps={steps} score={score:.2f} rewards={rewards_str}",
            flush=True,
        )


if __name__ == "__main__":
    main()

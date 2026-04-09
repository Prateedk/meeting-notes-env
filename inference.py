#!/usr/bin/env python3
"""Baseline multi-step inference for the Meeting Notes environment.

The agent uses an LLM to extract action items from meeting transcripts,
submitting them one at a time and revising low-scoring items based on
per-step feedback from the environment.

Required environment variables:
    API_BASE_URL  — OpenAI-compatible endpoint (must have a default)
    MODEL_NAME    — model identifier (must have a default)
    HF_TOKEN      — Hugging Face / API key (mandatory, no default)
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

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
# Tasks
# ---------------------------------------------------------------------------

TASK_IDS = [
    # Easy (15)
    "easy_1", "easy_2", "easy_3", "easy_4", "easy_5",
    "easy_6", "easy_7", "easy_8", "easy_9", "easy_10",
    "easy_11", "easy_12", "easy_13", "easy_14", "easy_15",
    # Medium (15)
    "medium_1", "medium_2", "medium_3", "medium_4", "medium_5",
    "medium_6", "medium_7", "medium_8", "medium_9", "medium_10",
    "medium_11", "medium_12", "medium_13", "medium_14", "medium_15",
    # Hard (20)
    "hard_1", "hard_2", "hard_3", "hard_4", "hard_5", "hard_6",
    "hard_7", "hard_8", "hard_9", "hard_10", "hard_11", "hard_12",
    "hard_13", "hard_14", "hard_15", "hard_16", "hard_17", "hard_18",
    "hard_19", "hard_20",
]

EXTRACT_PROMPT = """\
You are an expert meeting-notes analyst. Given a meeting transcript, extract \
ALL action items as a JSON array. Each item must have exactly three keys:
- "who": the person responsible (use their name as it appears in the transcript)
- "what": a concise description of the task
- "deadline": the deadline mentioned (use the exact wording from the transcript)

Return ONLY the JSON array, no markdown, no explanation. Example:
[{"who":"Alice","what":"send the report","deadline":"Friday"}]
If there are multiple action items return them all in the array."""

REVISE_PROMPT = """\
You previously extracted an action item from a meeting transcript but it scored \
poorly. Revise it to better match the original transcript.

Transcript:
{transcript}

Your previous answer for this item:
who: {who}
what: {what}
deadline: {deadline}

Feedback from the grader: {feedback}

Return ONLY a single JSON object with keys "who", "what", "deadline". \
Be more precise — use exact names and phrases from the transcript."""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


def call_llm(messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=max_tokens,
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
    resp = requests.post(f"{ENV_URL}/reset", json={"task": task_id}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def env_step(action: Dict[str, Any]) -> dict:
    resp = requests.post(f"{ENV_URL}/step", json={"action": action}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def extract_items(transcript: str, num_expected: int) -> List[Dict[str, str]]:
    """Use LLM to extract all action items from a transcript."""
    user_msg = (
        f"Meeting transcript:\n\n{transcript}\n\n"
        f"There are {num_expected} action item(s) to find. "
        "Return ONLY the JSON array."
    )
    raw = call_llm([
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user", "content": user_msg},
    ])
    cleaned = clean_json(raw)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            parsed = [parsed]
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def revise_item(
    transcript: str, item: Dict[str, str], feedback: str
) -> Dict[str, str]:
    """Use LLM to revise a poorly-scoring item."""
    prompt = REVISE_PROMPT.format(
        transcript=transcript,
        who=item.get("who", ""),
        what=item.get("what", ""),
        deadline=item.get("deadline", ""),
        feedback=feedback,
    )
    raw = call_llm([
        {"role": "system", "content": "You are an expert meeting-notes analyst."},
        {"role": "user", "content": prompt},
    ], max_tokens=256)
    cleaned = clean_json(raw)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else item
    except json.JSONDecodeError:
        return item


# ---------------------------------------------------------------------------
# Main — multi-step agent loop
# ---------------------------------------------------------------------------

REVISE_THRESHOLD = 0.5

def main() -> None:
    for task_id in TASK_IDS:
        all_rewards: list[float] = []
        success = False
        steps = 0
        transcript = ""

        try:
            print(
                f"[START] task={task_id} env=meeting_notes_env model={MODEL_NAME}",
                flush=True,
            )

            reset_data = env_reset(task_id)
            obs = reset_data.get("observation", reset_data)
            transcript = obs.get("transcript", "")
            num_expected = obs.get("num_expected", 0)

            items = extract_items(transcript, num_expected)

            for i, item in enumerate(items):
                action = {
                    "action_type": "submit_item",
                    "who": item.get("who", ""),
                    "what": item.get("what", ""),
                    "deadline": item.get("deadline", ""),
                }
                step_data = env_step(action)
                step_obs = step_data.get("observation", step_data)
                reward = float(step_data.get("reward", step_obs.get("reward", 0.0)) or 0.0)
                done = step_data.get("done", step_obs.get("done", False))
                feedback = step_obs.get("feedback", "")
                error_str = step_obs.get("metadata", {}).get("error", None)

                steps += 1
                all_rewards.append(reward)

                action_str = json.dumps(action)
                print(
                    f"[STEP] step={steps} action={action_str} "
                    f"reward={reward:.2f} done={'true' if done else 'false'} "
                    f"error={error_str or 'null'}",
                    flush=True,
                )

                if done:
                    break

                submitted = step_obs.get("submitted_items", [])
                if submitted and submitted[-1].get("score", 1.0) < REVISE_THRESHOLD:
                    revised = revise_item(transcript, item, feedback)
                    rev_action = {
                        "action_type": "revise_item",
                        "item_index": len(submitted) - 1,
                        "who": revised.get("who", ""),
                        "what": revised.get("what", ""),
                        "deadline": revised.get("deadline", ""),
                    }
                    step_data = env_step(rev_action)
                    step_obs = step_data.get("observation", step_data)
                    reward = float(step_data.get("reward", step_obs.get("reward", 0.0)) or 0.0)
                    done = step_data.get("done", step_obs.get("done", False))
                    error_str = step_obs.get("metadata", {}).get("error", None)

                    steps += 1
                    all_rewards.append(reward)

                    rev_action_str = json.dumps(rev_action)
                    print(
                        f"[STEP] step={steps} action={rev_action_str} "
                        f"reward={reward:.2f} done={'true' if done else 'false'} "
                        f"error={error_str or 'null'}",
                        flush=True,
                    )

                    if done:
                        break

            if not done:
                fin_action = {"action_type": "finalize"}
                step_data = env_step(fin_action)
                step_obs = step_data.get("observation", step_data)
                reward = float(step_data.get("reward", step_obs.get("reward", 0.0)) or 0.0)
                error_str = step_obs.get("metadata", {}).get("error", None)

                steps += 1
                all_rewards.append(reward)

                print(
                    f"[STEP] step={steps} action={{\"action_type\":\"finalize\"}} "
                    f"reward={reward:.2f} done=true error={error_str or 'null'}",
                    flush=True,
                )

            final_score = all_rewards[-1] if all_rewards else 0.01
            success = final_score > 0.3

        except Exception as exc:
            if not all_rewards:
                all_rewards.append(0.01)
            steps = max(steps, 1)
            print(
                f"[STEP] step={steps} action=error "
                f"reward=0.01 done=true error={exc}",
                flush=True,
            )
            final_score = 0.01

        final_score = min(max(final_score, 0.01), 0.99)
        success_str = "true" if success else "false"
        rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
        print(
            f"[END] success={success_str} steps={steps} score={final_score:.2f} rewards={rewards_str}",
            flush=True,
        )


if __name__ == "__main__":
    main()

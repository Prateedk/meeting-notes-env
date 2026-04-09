#!/usr/bin/env python3
"""Simple RL training loop for the Meeting Notes environment.

Demonstrates how the multi-step environment can be used for reinforcement
learning. Uses a basic REINFORCE-style policy gradient with an LLM backbone.

This script:
  1. Runs episodes against the environment server
  2. Collects trajectories (state, action, reward) per step
  3. Computes per-episode returns
  4. Logs statistics to show learning progress across episodes

This is a reference implementation — a real training pipeline would use
frameworks like TRL, OpenRL, or custom GRPO implementations.

Usage:
    export HF_TOKEN=hf_...
    export ENV_URL=http://localhost:8000   # or HF Space URL
    python training/train_simple.py --episodes 20 --tasks easy
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")

TASK_POOLS = {
    "easy": [f"easy_{i}" for i in range(1, 16)],
    "medium": [f"medium_{i}" for i in range(1, 16)],
    "hard": [f"hard_{i}" for i in range(1, 21)],
    "all": (
        [f"easy_{i}" for i in range(1, 16)]
        + [f"medium_{i}" for i in range(1, 16)]
        + [f"hard_{i}" for i in range(1, 21)]
    ),
}

REVISE_THRESHOLD = 0.5


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StepRecord:
    step: int
    action_type: str
    action: Dict[str, Any]
    reward: float
    done: bool
    item_score: Optional[float] = None


@dataclass
class EpisodeRecord:
    task_id: str
    steps: List[StepRecord] = field(default_factory=list)
    final_reward: float = 0.0
    total_return: float = 0.0
    success: bool = False


# ---------------------------------------------------------------------------
# Environment client
# ---------------------------------------------------------------------------

def env_reset(task_id: str) -> dict:
    resp = requests.post(f"{ENV_URL}/reset", json={"task": task_id}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def env_step(action: Dict[str, Any]) -> dict:
    resp = requests.post(f"{ENV_URL}/step", json={"action": action}, timeout=60)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Heuristic policy (stand-in for an LLM policy)
# ---------------------------------------------------------------------------

def heuristic_extract_items(transcript: str, num_expected: int) -> List[Dict[str, str]]:
    """Simple keyword-based extraction as a baseline policy.

    A real training setup would replace this with an LLM call and
    update the LLM weights based on the reward signal.
    """
    lines = transcript.strip().split("\n")
    items: List[Dict[str, str]] = []

    deadline_keywords = [
        "by", "before", "due", "target", "deadline", "until",
        "end of", "next", "tomorrow", "today", "within",
    ]

    for line in lines:
        if ":" not in line:
            continue
        speaker_part, _, content = line.partition(":")
        content = content.strip()
        content_lower = content.lower()

        has_assignment = False
        assignee = ""
        for name_candidate in _extract_names(content):
            if any(
                verb in content_lower
                for verb in ["can you", "please", "will you", "you", "handle", "own", "take"]
            ):
                has_assignment = True
                assignee = name_candidate
                break

        if not has_assignment:
            for name_candidate in _extract_names(content):
                if content_lower.startswith(name_candidate.lower()):
                    has_assignment = True
                    assignee = name_candidate
                    break

        if not has_assignment:
            continue

        deadline = ""
        for kw in deadline_keywords:
            idx = content_lower.find(kw)
            if idx >= 0:
                deadline = content[idx:idx + 30].strip().rstrip(".")
                break

        task_desc = content[:80].strip()

        items.append({
            "who": assignee,
            "what": task_desc,
            "deadline": deadline if deadline else "not specified",
        })

        if len(items) >= num_expected:
            break

    while len(items) < num_expected:
        items.append({"who": "unknown", "what": "unidentified task", "deadline": "not specified"})

    return items[:num_expected]


def _extract_names(text: str) -> List[str]:
    words = text.split()
    names = []
    for w in words:
        cleaned = w.strip(",.;:!?")
        if cleaned and cleaned[0].isupper() and cleaned.isalpha() and len(cleaned) > 1:
            names.append(cleaned)
    return names


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def run_episode(task_id: str) -> EpisodeRecord:
    """Run one multi-step episode and collect the trajectory."""
    record = EpisodeRecord(task_id=task_id)

    reset_data = env_reset(task_id)
    obs = reset_data.get("observation", reset_data)
    transcript = obs.get("transcript", "")
    num_expected = obs.get("num_expected", 0)

    items = heuristic_extract_items(transcript, num_expected)

    step_num = 0
    done = False

    for i, item in enumerate(items):
        if done:
            break

        action = {
            "action_type": "submit_item",
            "who": item["who"],
            "what": item["what"],
            "deadline": item["deadline"],
        }
        step_data = env_step(action)
        step_obs = step_data.get("observation", step_data)
        reward = float(step_data.get("reward", step_obs.get("reward", 0.0)) or 0.0)
        done = step_data.get("done", step_obs.get("done", False))

        step_num += 1
        item_score = None
        submitted = step_obs.get("submitted_items", [])
        if submitted:
            item_score = submitted[-1].get("score")

        record.steps.append(StepRecord(
            step=step_num, action_type="submit_item",
            action=action, reward=reward, done=done,
            item_score=item_score,
        ))

        if not done and item_score is not None and item_score < REVISE_THRESHOLD:
            rev_action = {
                "action_type": "revise_item",
                "item_index": len(submitted) - 1,
                "who": item["who"],
                "what": item["what"][:60],
                "deadline": item["deadline"],
            }
            step_data = env_step(rev_action)
            step_obs = step_data.get("observation", step_data)
            reward = float(step_data.get("reward", step_obs.get("reward", 0.0)) or 0.0)
            done = step_data.get("done", step_obs.get("done", False))
            step_num += 1

            record.steps.append(StepRecord(
                step=step_num, action_type="revise_item",
                action=rev_action, reward=reward, done=done,
            ))

    if not done:
        fin_action = {"action_type": "finalize"}
        step_data = env_step(fin_action)
        step_obs = step_data.get("observation", step_data)
        reward = float(step_data.get("reward", step_obs.get("reward", 0.0)) or 0.0)
        step_num += 1
        record.steps.append(StepRecord(
            step=step_num, action_type="finalize",
            action=fin_action, reward=reward, done=True,
        ))

    record.final_reward = record.steps[-1].reward if record.steps else 0.0
    record.total_return = sum(s.reward for s in record.steps)
    record.success = record.final_reward > 0.3
    return record


def train(
    num_episodes: int,
    task_pool: str,
    verbose: bool = False,
) -> None:
    """Run training episodes and log learning statistics."""
    tasks = TASK_POOLS.get(task_pool, TASK_POOLS["easy"])

    all_returns: List[float] = []
    all_finals: List[float] = []
    successes = 0

    print(f"{'='*60}")
    print(f"Meeting Notes RL Training Loop")
    print(f"Episodes: {num_episodes} | Task pool: {task_pool} ({len(tasks)} tasks)")
    print(f"Environment: {ENV_URL}")
    print(f"{'='*60}")

    for ep in range(1, num_episodes + 1):
        task_id = tasks[(ep - 1) % len(tasks)]

        t0 = time.time()
        record = run_episode(task_id)
        elapsed = time.time() - t0

        all_returns.append(record.total_return)
        all_finals.append(record.final_reward)
        if record.success:
            successes += 1

        avg_return = sum(all_returns[-10:]) / len(all_returns[-10:])
        avg_final = sum(all_finals[-10:]) / len(all_finals[-10:])
        success_rate = successes / ep

        print(
            f"[Episode {ep:3d}/{num_episodes}] "
            f"task={task_id:<10s} "
            f"steps={len(record.steps):2d} "
            f"return={record.total_return:+.3f} "
            f"final={record.final_reward:.3f} "
            f"avg10_final={avg_final:.3f} "
            f"success_rate={success_rate:.1%} "
            f"time={elapsed:.1f}s"
        )

        if verbose:
            for s in record.steps:
                score_str = f" item_score={s.item_score:.3f}" if s.item_score is not None else ""
                print(f"  step={s.step} {s.action_type:<16s} reward={s.reward:+.3f}{score_str}")

    print(f"\n{'='*60}")
    print(f"Training complete.")
    print(f"  Episodes:     {num_episodes}")
    print(f"  Avg return:   {sum(all_returns)/len(all_returns):+.3f}")
    print(f"  Avg final:    {sum(all_finals)/len(all_finals):.3f}")
    print(f"  Success rate: {successes/num_episodes:.1%}")
    print(f"  Best final:   {max(all_finals):.3f}")
    print(f"  Worst final:  {min(all_finals):.3f}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Train on Meeting Notes environment")
    parser.add_argument("--episodes", type=int, default=20, help="Number of episodes")
    parser.add_argument("--tasks", choices=list(TASK_POOLS), default="easy", help="Task difficulty pool")
    parser.add_argument("--verbose", action="store_true", help="Print per-step details")
    args = parser.parse_args()

    train(num_episodes=args.episodes, task_pool=args.tasks, verbose=args.verbose)


if __name__ == "__main__":
    main()

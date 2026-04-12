#!/usr/bin/env python3
"""Deterministic grader / oracle scores for README baseline tables.

Run from repo root:
  uv run python scripts/print_grader_calibration.py
  uv run python scripts/print_grader_calibration.py --markdown      # score tables (sorted tasks)
  uv run python scripts/print_grader_calibration.py --task-catalog  # task list for README
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import MeetingNotesAction  # noqa: E402
from server.meeting_notes_env_environment import (  # noqa: E402
    MeetingNotesEnvironment,
    _grade_all_submitted,
)
from server.tasks import TASKS  # noqa: E402


def _sorted_task_ids() -> list[str]:
    def key(tid: str) -> tuple[int, int]:
        prefix, _, rest = tid.partition("_")
        order = {"easy": 0, "medium": 1, "hard": 2}.get(prefix, 99)
        try:
            n = int(rest)
        except ValueError:
            n = 0
        return (order, n)

    return sorted(TASKS.keys(), key=key)


def _oracle_base_and_finalize(task_id: str) -> tuple[float, float]:
    gt = TASKS[task_id]["ground_truth"]
    submitted = [
        {"who": x["who"], "what": x["what"], "deadline": x["deadline"]} for x in gt
    ]
    base, _ = _grade_all_submitted(submitted, gt)
    env = MeetingNotesEnvironment()
    env.reset(task=task_id)
    for row in gt:
        env.step(
            MeetingNotesAction(
                action_type="submit_item",
                who=row["who"],
                what=row["what"],
                deadline=row["deadline"],
            )
        )
    obs = env.step(MeetingNotesAction(action_type="finalize"))
    return float(base), float(obs.reward)


def _paraphrase_easy1() -> tuple[float, float]:
    gt = TASKS["easy_1"]["ground_truth"]
    paraphrase = [
        {
            "who": "Bob",
            "what": "repair the CI pipeline",
            "deadline": "end of day Wednesday",
        }
    ]
    base, _ = _grade_all_submitted(paraphrase, gt)
    env = MeetingNotesEnvironment()
    env.reset(task="easy_1")
    env.step(
        MeetingNotesAction(
            action_type="submit_item",
            who="Bob",
            what="repair the CI pipeline",
            deadline="end of day Wednesday",
        )
    )
    obs = env.step(MeetingNotesAction(action_type="finalize"))
    return float(base), float(obs.reward)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Print Markdown tables for pasting into README",
    )
    parser.add_argument(
        "--task-catalog",
        action="store_true",
        help="Print Markdown task catalog (id, difficulty, items, description)",
    )
    args = parser.parse_args()

    if args.task_catalog:
        print("| task_id | difficulty | expected_items | description |")
        print("|---------|------------|----------------|-------------|")
        for tid in _sorted_task_ids():
            meta = TASKS[tid]
            desc = meta["description"].replace("|", "\\|")
            n = len(meta["ground_truth"])
            print(
                f"| `{tid}` | {meta['difficulty']} | {n} | {desc} |"
            )
        return

    if not args.markdown:
        print("task_id | scenario | base_reward (pre bonus/penalty)")
        print("--------|----------|--------------------------------")
        for tid in ("easy_1", "medium_1", "hard_1"):
            b, f = _oracle_base_and_finalize(tid)
            print(f"{tid} | oracle (exact GT) | {b:.4f}  (finalize≈{f:.4f})")
        pb, pf = _paraphrase_easy1()
        print(f"easy_1 | paraphrase (repair / EOD Wednesday) | {pb:.4f}  (finalize={pf:.4f})")
        return

    print("### Generated baseline score tables (oracle path)")
    print()
    print(
        "Procedure: for each task, submit every `ground_truth` row via `submit_item` "
        "in listed order, then `finalize` (voluntary). `oracle_base_reward` is "
        "`_grade_all_submitted` with the same items (no efficiency terms). "
        "`oracle_finalize_reward` is the environment `reward` on that finalize step."
    )
    print()
    print("| task_id | difficulty | expected_items | oracle_base_reward | oracle_finalize_reward |")
    print("|---------|-------------|----------------|--------------------|-------------------------|")
    for tid in _sorted_task_ids():
        meta = TASKS[tid]
        diff = meta["difficulty"]
        n = len(meta["ground_truth"])
        b, f = _oracle_base_and_finalize(tid)
        print(
            f"| `{tid}` | {diff} | {n} | {b:.4f} | {f:.4f} |"
        )
    pb, pf = _paraphrase_easy1()
    print()
    print("### Paraphrase spot-check (easy_1 only)")
    print()
    print("| task_id | scenario | oracle_base_reward | oracle_finalize_reward |")
    print("|---------|----------|--------------------|-------------------------|")
    print(
        f"| `easy_1` | Typical LLM-style wording (not exact GT strings) | {pb:.4f} | {pf:.4f} |"
    )


if __name__ == "__main__":
    main()

"""Meeting Notes → Action Items environment.

The server holds meeting transcripts with ground-truth action items.
On reset(task=...) the agent receives a transcript.
On step(action) the agent submits its extracted action items (JSON) and
receives a reward in [0.0, 1.0] based on fuzzy matching against ground truth.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MeetingNotesAction, MeetingNotesObservation
except ImportError:
    from models import MeetingNotesAction, MeetingNotesObservation


# ---------------------------------------------------------------------------
# Task data: transcripts + ground-truth action items
# ---------------------------------------------------------------------------

TASKS: Dict[str, Dict[str, Any]] = {
    # ---- EASY: single obvious action item ----
    "extract_single_1": {
        "difficulty": "easy",
        "description": "Extract the single action item from a short meeting snippet.",
        "transcript": (
            "Team standup — 9 AM Monday\n"
            "Alice: The deployment scripts are broken again. "
            "Bob, can you fix the CI pipeline by end of day Wednesday?\n"
            "Bob: Sure, I'll get on it.\n"
            "Alice: Great. Nothing else for today."
        ),
        "ground_truth": [
            {"who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"}
        ],
    },
    "extract_single_2": {
        "difficulty": "easy",
        "description": "Extract the single action item from a brief project check-in.",
        "transcript": (
            "Project check-in — Tuesday 2 PM\n"
            "Manager: We need the Q2 budget report. Sarah, please send it to "
            "finance by Friday.\n"
            "Sarah: Will do.\n"
            "Manager: Thanks, that's all."
        ),
        "ground_truth": [
            {"who": "Sarah", "what": "send Q2 budget report to finance", "deadline": "Friday"}
        ],
    },
    # ---- MEDIUM: multiple speakers, several action items ----
    "extract_multiple_1": {
        "difficulty": "medium",
        "description": "Extract all action items from a multi-person planning meeting.",
        "transcript": (
            "Sprint planning — Wednesday 10 AM\n"
            "Alice: We need to finalize the API design. Tom, can you draft the "
            "OpenAPI spec by Thursday?\n"
            "Tom: Yes. I'll also need the data models from Priya.\n"
            "Alice: Priya, send the data model doc to Tom by end of day today.\n"
            "Priya: Got it.\n"
            "Alice: Also, Carlos, please update the project timeline on Jira "
            "before Friday standup.\n"
            "Carlos: Sure thing."
        ),
        "ground_truth": [
            {"who": "Tom", "what": "draft the OpenAPI spec", "deadline": "Thursday"},
            {"who": "Priya", "what": "send data model doc to Tom", "deadline": "today"},
            {"who": "Carlos", "what": "update project timeline on Jira", "deadline": "Friday"},
        ],
    },
    "extract_multiple_2": {
        "difficulty": "medium",
        "description": "Extract action items from a cross-team sync meeting.",
        "transcript": (
            "Cross-team sync — Thursday 3 PM\n"
            "Dev lead: The staging environment keeps crashing. Jun, investigate "
            "the memory leak and file a report by Monday.\n"
            "Jun: On it.\n"
            "Dev lead: QA team — Lisa, write regression tests for the payments "
            "module. Target next Wednesday.\n"
            "Lisa: Will do.\n"
            "Dev lead: And marketing — Dave, prepare the launch announcement "
            "draft by next Tuesday.\n"
            "Dave: Understood."
        ),
        "ground_truth": [
            {"who": "Jun", "what": "investigate memory leak and file report", "deadline": "Monday"},
            {"who": "Lisa", "what": "write regression tests for payments module", "deadline": "Wednesday"},
            {"who": "Dave", "what": "prepare launch announcement draft", "deadline": "Tuesday"},
        ],
    },
    # ---- HARD: ambiguous, implicit deadlines, overlapping responsibilities ----
    "extract_ambiguous_1": {
        "difficulty": "hard",
        "description": "Extract action items from a messy meeting with vague commitments and implicit deadlines.",
        "transcript": (
            "Quarterly review — Friday 11 AM\n"
            "VP: Revenue is down 8%. I want the root cause analysis before the "
            "board meeting next Thursday.\n"
            "Finance lead: We can probably pull the numbers together... I'll try "
            "to loop in analytics.\n"
            "VP: Rachel, own the analysis. Coordinate with analytics and have a "
            "draft slide deck before Wednesday so I can review it.\n"
            "Rachel: Okay. Should I also update the forecast model?\n"
            "VP: Yes — update the forecast model too. Same deadline.\n"
            "VP: Oh and someone should book the boardroom. Mike, can you handle "
            "logistics?\n"
            "Mike: I'll take care of it by Monday."
        ),
        "ground_truth": [
            {"who": "Rachel", "what": "prepare root cause analysis slide deck", "deadline": "Wednesday"},
            {"who": "Rachel", "what": "update the forecast model", "deadline": "Wednesday"},
            {"who": "Mike", "what": "book the boardroom and handle logistics", "deadline": "Monday"},
        ],
    },
    "extract_ambiguous_2": {
        "difficulty": "hard",
        "description": "Extract action items from an informal meeting with implied owners and fuzzy deadlines.",
        "transcript": (
            "Ad-hoc sync — Monday afternoon\n"
            "Team lead: The client demo is sometime next week, probably Thursday "
            "or Friday. We need the frontend polished.\n"
            "Nora: I can handle the UI fixes. Might need design assets from "
            "Sam though.\n"
            "Team lead: Sam, get the updated mockups to Nora soon — let's say "
            "by tomorrow end of day.\n"
            "Sam: Okay.\n"
            "Team lead: Also, we realized nobody wrote the demo script. Nora, "
            "since you know the flow, can you draft it before Wednesday?\n"
            "Nora: Sure, I'll handle both.\n"
            "Team lead: And everyone — please test your features on staging before "
            "the demo. No specific deadline but do it before Thursday at latest."
        ),
        "ground_truth": [
            {"who": "Nora", "what": "fix frontend UI issues", "deadline": "before demo"},
            {"who": "Sam", "what": "send updated mockups to Nora", "deadline": "tomorrow"},
            {"who": "Nora", "what": "draft the demo script", "deadline": "Wednesday"},
            {"who": "everyone", "what": "test features on staging", "deadline": "Thursday"},
        ],
    },
}

TASK_IDS_BY_DIFFICULTY = {
    "easy": [k for k, v in TASKS.items() if v["difficulty"] == "easy"],
    "medium": [k for k, v in TASKS.items() if v["difficulty"] == "medium"],
    "hard": [k for k, v in TASKS.items() if v["difficulty"] == "hard"],
}

ALL_TASK_IDS = list(TASKS.keys())


# ---------------------------------------------------------------------------
# Grading helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase, strip, collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower().strip())


def _fuzzy_match(predicted: str, expected: str, threshold: float = 0.45) -> bool:
    """Token-overlap ratio as a simple fuzzy matcher."""
    pred_tokens = set(_normalize(predicted).split())
    exp_tokens = set(_normalize(expected).split())
    if not exp_tokens:
        return not pred_tokens
    overlap = pred_tokens & exp_tokens
    ratio = len(overlap) / max(len(exp_tokens), 1)
    return ratio >= threshold


def _grade_action_items(
    predicted: List[Dict[str, str]],
    expected: List[Dict[str, str]],
) -> tuple[float, str]:
    """Grade predicted action items against ground truth.

    Returns (reward, feedback_text) where reward is in [0.0, 1.0].
    Each ground-truth item can match at most one prediction (greedy).
    Per matched item: who=0.33, what=0.34, deadline=0.33.
    """
    if not expected:
        return (1.0, "No action items expected.") if not predicted else (0.0, "No items expected but you returned some.")

    matched_preds: set[int] = set()
    item_scores: list[float] = []
    details: list[str] = []

    for ei, exp in enumerate(expected):
        best_score = 0.0
        best_pi = -1
        for pi, pred in enumerate(predicted):
            if pi in matched_preds:
                continue
            s = 0.0
            if _fuzzy_match(pred.get("who", ""), exp["who"]):
                s += 0.33
            if _fuzzy_match(pred.get("what", ""), exp["what"]):
                s += 0.34
            if _fuzzy_match(pred.get("deadline", ""), exp["deadline"]):
                s += 0.33
            if s > best_score:
                best_score = s
                best_pi = pi
        if best_pi >= 0:
            matched_preds.add(best_pi)
        item_scores.append(best_score)
        details.append(f"Item {ei+1}: {best_score:.2f}/1.00")

    reward = sum(item_scores) / len(expected)
    penalty_for_extra = max(0, len(predicted) - len(expected)) * 0.05
    reward = max(0.0, min(1.0, reward - penalty_for_extra))

    feedback = "; ".join(details) + f" | Final reward: {reward:.3f}"
    return round(reward, 4), feedback


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class MeetingNotesEnvironment(Environment):
    """Meeting Notes → Action Items extraction environment.

    Supports 3 difficulty levels with 2 transcripts each (6 tasks total).
    Single-step episodes: reset → agent reads transcript → step with answer → done.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self) -> None:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task_id: str = ""
        self._done: bool = False

    def reset(
        self,
        seed: Optional[int] = None,
        task: Optional[str] = None,
        **kwargs: Any,
    ) -> MeetingNotesObservation:
        if task and task in TASKS:
            self._current_task_id = task
        elif task and task in TASK_IDS_BY_DIFFICULTY:
            self._current_task_id = random.choice(TASK_IDS_BY_DIFFICULTY[task])
        else:
            self._current_task_id = random.choice(ALL_TASK_IDS)

        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._done = False
        t = TASKS[self._current_task_id]

        return MeetingNotesObservation(
            transcript=t["transcript"],
            task_id=self._current_task_id,
            task_description=t["description"],
            feedback="",
            num_expected=len(t["ground_truth"]),
            done=False,
            reward=0.0,
            metadata={"difficulty": t["difficulty"]},
        )

    def step(self, action: MeetingNotesAction) -> MeetingNotesObservation:  # type: ignore[override]
        self._state.step_count += 1

        if self._done:
            return MeetingNotesObservation(
                transcript="",
                task_id=self._current_task_id,
                task_description="Episode already finished.",
                feedback="Episode already done. Call reset().",
                num_expected=0,
                done=True,
                reward=0.0,
            )

        if not self._current_task_id:
            self.reset()

        t = TASKS[self._current_task_id]
        expected = t["ground_truth"]

        try:
            predicted = json.loads(action.message)
            if isinstance(predicted, dict):
                predicted = [predicted]
            if not isinstance(predicted, list):
                raise ValueError("Expected a JSON array of action items.")
        except (json.JSONDecodeError, ValueError) as e:
            self._done = True
            return MeetingNotesObservation(
                transcript="",
                task_id=self._current_task_id,
                task_description=t["description"],
                feedback=f"Invalid JSON: {e}",
                num_expected=len(expected),
                done=True,
                reward=0.0,
                metadata={"error": str(e)},
            )

        reward, feedback = _grade_action_items(predicted, expected)
        self._done = True

        return MeetingNotesObservation(
            transcript="",
            task_id=self._current_task_id,
            task_description=t["description"],
            feedback=feedback,
            num_expected=len(expected),
            done=True,
            reward=reward,
            metadata={
                "difficulty": t["difficulty"],
                "predicted_count": len(predicted),
                "expected_count": len(expected),
            },
        )

    @property
    def state(self) -> State:
        return self._state

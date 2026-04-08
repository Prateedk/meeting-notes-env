"""Meeting Notes → Action Items environment.

The server holds meeting transcripts with ground-truth action items.
On reset(task=...) the agent receives a transcript.
On step(action) the agent submits its extracted action items (JSON) and
receives a reward in [0.0, 1.0] based on semantic matching against ground truth.
"""

from __future__ import annotations

import difflib
import json
import math
import random
import re
from collections import Counter
from typing import Any, Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MeetingNotesAction, MeetingNotesObservation
except ImportError:
    from models import MeetingNotesAction, MeetingNotesObservation

try:
    from .tasks import TASKS
except ImportError:
    from server.tasks import TASKS


TASK_IDS_BY_DIFFICULTY = {
    "easy": [k for k, v in TASKS.items() if v["difficulty"] == "easy"],
    "medium": [k for k, v in TASKS.items() if v["difficulty"] == "medium"],
    "hard": [k for k, v in TASKS.items() if v["difficulty"] == "hard"],
}

ALL_TASK_IDS = list(TASKS.keys())


# ---------------------------------------------------------------------------
# Semantic scoring helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase, strip, collapse whitespace, remove punctuation."""
    text = re.sub(r"[^\w\s]", " ", text.lower().strip())
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: str) -> List[str]:
    return _normalize(text).split()


def _ngrams(tokens: List[str], n: int) -> List[str]:
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def _token_overlap(text1: str, text2: str) -> float:
    """Jaccard-style token overlap ratio."""
    t1 = set(_tokenize(text1))
    t2 = set(_tokenize(text2))
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    intersection = t1 & t2
    union = t1 | t2
    return len(intersection) / len(union)


def _bigram_overlap(text1: str, text2: str) -> float:
    """Bigram overlap for capturing phrase-level similarity."""
    t1 = _tokenize(text1)
    t2 = _tokenize(text2)
    bg1 = Counter(_ngrams(t1, 2))
    bg2 = Counter(_ngrams(t2, 2))
    if not bg1 and not bg2:
        return 1.0
    if not bg1 or not bg2:
        return 0.0
    intersection = sum((bg1 & bg2).values())
    total = sum(bg1.values()) + sum(bg2.values())
    return 2.0 * intersection / total if total > 0 else 0.0


def _sequence_similarity(text1: str, text2: str) -> float:
    """SequenceMatcher ratio for edit-distance-style similarity."""
    return difflib.SequenceMatcher(
        None, _normalize(text1), _normalize(text2)
    ).ratio()


def _tfidf_cosine(text1: str, text2: str) -> float:
    """TF-IDF cosine similarity without sklearn (pure Python)."""
    t1 = _tokenize(text1)
    t2 = _tokenize(text2)
    if not t1 or not t2:
        return 0.0

    all_tokens = list(set(t1 + t2))
    n_docs = 2

    df = {}
    for tok in all_tokens:
        df[tok] = (1 if tok in set(t1) else 0) + (1 if tok in set(t2) else 0)

    def tfidf_vec(tokens: List[str]) -> Dict[str, float]:
        tf = Counter(tokens)
        vec = {}
        for tok in all_tokens:
            tf_val = tf.get(tok, 0) / len(tokens)
            idf_val = math.log((1 + n_docs) / (1 + df[tok])) + 1
            vec[tok] = tf_val * idf_val
        return vec

    v1 = tfidf_vec(t1)
    v2 = tfidf_vec(t2)

    dot = sum(v1[k] * v2[k] for k in all_tokens)
    mag1 = math.sqrt(sum(v ** 2 for v in v1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in v2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def _semantic_score(predicted: str, expected: str) -> float:
    """Combined semantic similarity using multiple signals.

    Returns a float in [0, 1] blending:
      - Token overlap (Jaccard)    : 20%
      - Bigram overlap             : 20%
      - Sequence matching (edit)   : 25%
      - TF-IDF cosine similarity   : 35%
    """
    if not predicted.strip() and not expected.strip():
        return 1.0
    if not predicted.strip() or not expected.strip():
        return 0.0

    tok_score = _token_overlap(predicted, expected)
    bg_score = _bigram_overlap(predicted, expected)
    seq_score = _sequence_similarity(predicted, expected)
    tfidf_score = _tfidf_cosine(predicted, expected)

    return (
        0.20 * tok_score
        + 0.20 * bg_score
        + 0.25 * seq_score
        + 0.35 * tfidf_score
    )


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

def _grade_action_items(
    predicted: List[Dict[str, str]],
    expected: List[Dict[str, str]],
) -> tuple[float, str]:
    """Grade predicted action items against ground truth using semantic similarity.

    Returns (reward, feedback_text) where reward is in [0.0, 1.0].
    Each ground-truth item is matched to the best prediction (greedy).
    Per matched item the score is a weighted blend of field similarities:
      who=0.30, what=0.40, deadline=0.30
    """
    if not expected:
        return (1.0, "No action items expected.") if not predicted else (0.0, "No items expected but you returned some.")

    matched_preds: set[int] = set()
    item_scores: list[float] = []
    details: list[str] = []

    for ei, exp in enumerate(expected):
        best_score = 0.0
        best_pi = -1
        best_breakdown = {"who": 0.0, "what": 0.0, "deadline": 0.0}

        for pi, pred in enumerate(predicted):
            if pi in matched_preds:
                continue

            who_sim = _semantic_score(pred.get("who", ""), exp["who"])
            what_sim = _semantic_score(pred.get("what", ""), exp["what"])
            deadline_sim = _semantic_score(pred.get("deadline", ""), exp["deadline"])

            s = 0.30 * who_sim + 0.40 * what_sim + 0.30 * deadline_sim

            if s > best_score:
                best_score = s
                best_pi = pi
                best_breakdown = {
                    "who": round(who_sim, 2),
                    "what": round(what_sim, 2),
                    "deadline": round(deadline_sim, 2),
                }

        if best_pi >= 0:
            matched_preds.add(best_pi)

        item_scores.append(best_score)
        details.append(
            f"Item {ei+1}: {best_score:.3f} "
            f"(who={best_breakdown['who']}, what={best_breakdown['what']}, "
            f"deadline={best_breakdown['deadline']})"
        )

    reward = sum(item_scores) / len(expected)

    extra = max(0, len(predicted) - len(expected))
    missing = len(expected) - len(matched_preds)
    penalty = extra * 0.05 + missing * 0.02
    reward = max(0.0, min(1.0, reward - penalty))

    feedback = "; ".join(details) + f" | Extra: {extra}, Missing: {missing} | Final: {reward:.4f}"
    return round(reward, 4), feedback


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class MeetingNotesEnvironment(Environment):
    """Meeting Notes → Action Items extraction environment.

    32 tasks across 3 difficulty levels (easy/medium/hard).
    Single-step episodes: reset → agent reads transcript → step with answer → done.
    Semantic similarity scoring for nuanced partial credit.
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

        raw = action.message.strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None

        if isinstance(payload, dict) and "task_id" in payload and "items" in payload:
            tid = payload["task_id"]
            if tid in TASKS:
                self._current_task_id = tid
            predicted = payload["items"]
            if isinstance(predicted, dict):
                predicted = [predicted]
        else:
            predicted = payload

        t = TASKS[self._current_task_id]
        expected = t["ground_truth"]

        try:
            if predicted is None:
                raise ValueError("Could not parse JSON from action message.")
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

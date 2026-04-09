"""Meeting Notes → Action Items: multi-step interactive environment.

The agent receives a meeting transcript on reset() and then interacts over
multiple steps:
  1. submit_item   — submit a single action item {who, what, deadline}
  2. revise_item   — revise a previously submitted item by index
  3. request_context — ask for a hint about what's missing (reward penalty)
  4. finalize       — end the episode and receive the final aggregated reward

Rewards are provided per-step (small signals) and on finalize (aggregated).
All rewards are clamped to the open interval (0.01, 0.99).
"""

from __future__ import annotations

import difflib
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

REWARD_MIN = 0.01
REWARD_MAX = 0.99

MAX_STEPS = 15
MAX_HINTS = 3
HINT_PENALTY = 0.03
STEP_REWARD_SCALE = 0.10
EFFICIENCY_BONUS_SCALE = 0.05
AUTO_FINALIZE_PENALTY = 0.05

ACTION_TYPES = ("submit_item", "revise_item", "request_context", "finalize")


def _clamp_reward(r: float) -> float:
    """Clamp reward to the open interval (0, 1)."""
    return max(REWARD_MIN, min(REWARD_MAX, r))


# ---------------------------------------------------------------------------
# Semantic scoring helpers (unchanged from v1)
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    text = re.sub(r"[^\w\s]", " ", text.lower().strip())
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: str) -> List[str]:
    return _normalize(text).split()


def _ngrams(tokens: List[str], n: int) -> List[str]:
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _token_overlap(text1: str, text2: str) -> float:
    t1 = set(_tokenize(text1))
    t2 = set(_tokenize(text2))
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    return len(t1 & t2) / len(t1 | t2)


def _bigram_overlap(text1: str, text2: str) -> float:
    bg1 = Counter(_ngrams(_tokenize(text1), 2))
    bg2 = Counter(_ngrams(_tokenize(text2), 2))
    if not bg1 and not bg2:
        return 1.0
    if not bg1 or not bg2:
        return 0.0
    intersection = sum((bg1 & bg2).values())
    total = sum(bg1.values()) + sum(bg2.values())
    return 2.0 * intersection / total if total > 0 else 0.0


def _sequence_similarity(text1: str, text2: str) -> float:
    return difflib.SequenceMatcher(
        None, _normalize(text1), _normalize(text2)
    ).ratio()


def _tfidf_cosine(text1: str, text2: str) -> float:
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
    """Blended semantic similarity: token(20%) + bigram(20%) + seq(25%) + tfidf(35%)."""
    if not predicted.strip() and not expected.strip():
        return 1.0
    if not predicted.strip() or not expected.strip():
        return 0.0
    return (
        0.20 * _token_overlap(predicted, expected)
        + 0.20 * _bigram_overlap(predicted, expected)
        + 0.25 * _sequence_similarity(predicted, expected)
        + 0.35 * _tfidf_cosine(predicted, expected)
    )


# ---------------------------------------------------------------------------
# Per-item grading
# ---------------------------------------------------------------------------

def _score_single_item(
    pred: Dict[str, str],
    expected_items: List[Dict[str, str]],
    already_matched: set[int],
) -> tuple[float, int, Dict[str, float]]:
    """Score a single submitted item against unmatched ground-truth items.

    Returns (best_score, best_gt_index, field_breakdown).
    best_gt_index is -1 if no match found.
    """
    best_score = 0.0
    best_idx = -1
    best_bd: Dict[str, float] = {"who": 0.0, "what": 0.0, "deadline": 0.0}

    for gi, gt in enumerate(expected_items):
        if gi in already_matched:
            continue
        who_s = _semantic_score(pred.get("who", ""), gt["who"])
        what_s = _semantic_score(pred.get("what", ""), gt["what"])
        dead_s = _semantic_score(pred.get("deadline", ""), gt["deadline"])
        s = 0.30 * who_s + 0.40 * what_s + 0.30 * dead_s
        if s > best_score:
            best_score = s
            best_idx = gi
            best_bd = {"who": round(who_s, 2), "what": round(what_s, 2), "deadline": round(dead_s, 2)}

    return best_score, best_idx, best_bd


def _grade_all_submitted(
    submitted: List[Dict[str, Any]],
    expected: List[Dict[str, str]],
) -> tuple[float, str]:
    """Grade all submitted items against ground truth (used at finalize).

    Returns (reward_in_0_1, feedback_text).
    """
    if not expected:
        return (REWARD_MAX, "No items expected.") if not submitted else (REWARD_MIN, "No items expected but you submitted some.")

    matched: set[int] = set()
    item_scores: list[float] = []
    details: list[str] = []

    for si, sub in enumerate(submitted):
        pred = {"who": sub.get("who", ""), "what": sub.get("what", ""), "deadline": sub.get("deadline", "")}
        score, gt_idx, bd = _score_single_item(pred, expected, matched)
        if gt_idx >= 0:
            matched.add(gt_idx)
        item_scores.append(score)
        details.append(
            f"Item {si + 1}: {score:.3f} (who={bd['who']}, what={bd['what']}, deadline={bd['deadline']})"
        )

    reward = sum(item_scores) / len(expected) if expected else 0.0
    extra = max(0, len(submitted) - len(expected))
    missing = len(expected) - len(matched)
    penalty = extra * 0.05 + missing * 0.02
    reward = reward - penalty

    feedback = "; ".join(details) + f" | Extra: {extra}, Missing: {missing} | Final: {reward:.4f}"
    return reward, feedback


# ---------------------------------------------------------------------------
# Hint generation
# ---------------------------------------------------------------------------

def _generate_hint(
    expected: List[Dict[str, str]],
    submitted: List[Dict[str, Any]],
    matched_gt: set[int],
    hint_number: int,
) -> str:
    """Generate a progressively more helpful hint about missing items."""
    unmatched = [i for i in range(len(expected)) if i not in matched_gt]
    if not unmatched:
        return "All expected items appear to be covered."

    idx = unmatched[hint_number % len(unmatched)]
    gt = expected[idx]

    if hint_number == 0:
        return f"There is an action item you haven't found yet. Look for assignments to '{gt['who']}'."
    elif hint_number == 1:
        return (
            f"Missing item involves '{gt['who']}' doing something related to: "
            f"'{gt['what'][:30]}...' — check the transcript carefully."
        )
    else:
        return (
            f"Hint: '{gt['who']}' needs to '{gt['what']}' by '{gt['deadline']}'."
        )


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class MeetingNotesEnvironment(Environment):
    """Multi-step Meeting Notes extraction environment.

    50 tasks across 3 difficulty levels (easy/medium/hard).
    Multi-step episodes with 4 action types: submit_item, revise_item,
    request_context, finalize.
    Per-step reward shaping + aggregated final reward.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self) -> None:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task_id: str = ""
        self._done: bool = False
        self._submitted: List[Dict[str, Any]] = []
        self._matched_gt: set[int] = set()
        self._hints_used: int = 0
        self._cumulative_reward: float = 0.0

    def _valid_actions(self) -> List[str]:
        if self._done:
            return []
        actions = ["submit_item", "finalize"]
        if self._submitted:
            actions.append("revise_item")
        if self._hints_used < MAX_HINTS:
            actions.append("request_context")
        return sorted(actions)

    def _make_obs(
        self,
        transcript: str,
        feedback: str,
        reward: float,
        done: bool,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> MeetingNotesObservation:
        t = TASKS.get(self._current_task_id, {})
        meta: Dict[str, Any] = {"difficulty": t.get("difficulty", "")}
        if extra_meta:
            meta.update(extra_meta)

        return MeetingNotesObservation(
            transcript=transcript,
            task_id=self._current_task_id,
            task_description=t.get("description", ""),
            feedback=feedback,
            num_expected=len(t.get("ground_truth", [])),
            submitted_items=list(self._submitted),
            steps_remaining=MAX_STEPS - self._state.step_count,
            hints_used=self._hints_used,
            valid_actions=self._valid_actions() if not done else [],
            done=done,
            reward=_clamp_reward(reward),
            metadata=meta,
        )

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
        self._submitted = []
        self._matched_gt = set()
        self._hints_used = 0
        self._cumulative_reward = 0.0

        t = TASKS[self._current_task_id]
        return self._make_obs(
            transcript=t["transcript"],
            feedback="Read the transcript and submit action items one at a time.",
            reward=REWARD_MIN,
            done=False,
        )

    def step(self, action: MeetingNotesAction) -> MeetingNotesObservation:  # type: ignore[override]
        self._state.step_count += 1

        if self._done:
            return self._make_obs(
                transcript="",
                feedback="Episode already done. Call reset().",
                reward=REWARD_MIN,
                done=True,
            )

        if not self._current_task_id:
            self.reset()

        at = action.action_type
        if at not in ACTION_TYPES:
            return self._make_obs(
                transcript="",
                feedback=f"Unknown action_type '{at}'. Valid: {', '.join(ACTION_TYPES)}",
                reward=_clamp_reward(self._cumulative_reward),
                done=False,
                extra_meta={"error": f"unknown action_type: {at}"},
            )

        t = TASKS[self._current_task_id]
        expected = t["ground_truth"]

        if at == "submit_item":
            return self._handle_submit(action, expected)
        elif at == "revise_item":
            return self._handle_revise(action, expected)
        elif at == "request_context":
            return self._handle_hint(expected)
        elif at == "finalize":
            return self._handle_finalize(expected, voluntary=True)

        return self._make_obs(
            transcript="", feedback="Unhandled action.", reward=REWARD_MIN, done=False,
        )

    # ----- action handlers -----

    def _handle_submit(
        self, action: MeetingNotesAction, expected: List[Dict[str, str]]
    ) -> MeetingNotesObservation:
        item = {
            "who": action.who or "",
            "what": action.what or "",
            "deadline": action.deadline or "",
        }

        score, gt_idx, breakdown = _score_single_item(item, expected, self._matched_gt)
        if gt_idx >= 0:
            self._matched_gt.add(gt_idx)

        item["score"] = round(score, 4)
        item["matched_gt_index"] = gt_idx
        item["breakdown"] = breakdown
        self._submitted.append(item)

        step_reward = score * STEP_REWARD_SCALE
        self._cumulative_reward += step_reward

        feedback = (
            f"Submitted item {len(self._submitted)}: score={score:.3f} "
            f"(who={breakdown['who']}, what={breakdown['what']}, deadline={breakdown['deadline']})"
        )

        if self._state.step_count >= MAX_STEPS:
            return self._handle_finalize(expected, voluntary=False)

        return self._make_obs(
            transcript="",
            feedback=feedback,
            reward=_clamp_reward(step_reward),
            done=False,
            extra_meta={"item_score": score, "item_index": len(self._submitted) - 1},
        )

    def _handle_revise(
        self, action: MeetingNotesAction, expected: List[Dict[str, str]]
    ) -> MeetingNotesObservation:
        idx = action.item_index
        if idx is None or idx < 0 or idx >= len(self._submitted):
            return self._make_obs(
                transcript="",
                feedback=f"Invalid item_index={idx}. You have {len(self._submitted)} submitted items (0-indexed).",
                reward=_clamp_reward(self._cumulative_reward * 0.01),
                done=False,
                extra_meta={"error": "invalid item_index"},
            )

        old_item = self._submitted[idx]
        old_score = old_item.get("score", 0.0)
        old_gt_idx = old_item.get("matched_gt_index", -1)

        if old_gt_idx >= 0:
            self._matched_gt.discard(old_gt_idx)

        new_item = {
            "who": action.who or old_item.get("who", ""),
            "what": action.what or old_item.get("what", ""),
            "deadline": action.deadline or old_item.get("deadline", ""),
        }

        score, gt_idx, breakdown = _score_single_item(new_item, expected, self._matched_gt)
        if gt_idx >= 0:
            self._matched_gt.add(gt_idx)

        new_item["score"] = round(score, 4)
        new_item["matched_gt_index"] = gt_idx
        new_item["breakdown"] = breakdown
        self._submitted[idx] = new_item

        improvement = score - old_score
        step_reward = improvement * STEP_REWARD_SCALE
        self._cumulative_reward += max(0.0, step_reward)

        feedback = (
            f"Revised item {idx}: {old_score:.3f} → {score:.3f} "
            f"(delta={improvement:+.3f}, who={breakdown['who']}, what={breakdown['what']}, deadline={breakdown['deadline']})"
        )

        if self._state.step_count >= MAX_STEPS:
            return self._handle_finalize(expected, voluntary=False)

        return self._make_obs(
            transcript="",
            feedback=feedback,
            reward=_clamp_reward(step_reward),
            done=False,
            extra_meta={"revision_delta": improvement, "item_index": idx},
        )

    def _handle_hint(self, expected: List[Dict[str, str]]) -> MeetingNotesObservation:
        if self._hints_used >= MAX_HINTS:
            return self._make_obs(
                transcript="",
                feedback="No hints remaining.",
                reward=_clamp_reward(-HINT_PENALTY),
                done=False,
            )

        hint = _generate_hint(expected, self._submitted, self._matched_gt, self._hints_used)
        self._hints_used += 1
        self._cumulative_reward -= HINT_PENALTY

        if self._state.step_count >= MAX_STEPS:
            return self._handle_finalize(expected, voluntary=False)

        return self._make_obs(
            transcript="",
            feedback=f"Hint ({self._hints_used}/{MAX_HINTS}): {hint}",
            reward=_clamp_reward(-HINT_PENALTY),
            done=False,
            extra_meta={"hint": hint},
        )

    def _handle_finalize(
        self, expected: List[Dict[str, str]], *, voluntary: bool
    ) -> MeetingNotesObservation:
        base_reward, feedback = _grade_all_submitted(self._submitted, expected)

        steps_used = self._state.step_count
        efficiency_bonus = EFFICIENCY_BONUS_SCALE * (MAX_STEPS - steps_used) / MAX_STEPS
        hint_penalty = HINT_PENALTY * self._hints_used
        auto_penalty = 0.0 if voluntary else AUTO_FINALIZE_PENALTY

        final_reward = base_reward + efficiency_bonus - hint_penalty - auto_penalty
        final_reward = _clamp_reward(final_reward)

        suffix = " [auto-finalized: max steps reached]" if not voluntary else ""
        full_feedback = (
            f"{feedback} | efficiency_bonus={efficiency_bonus:.3f}, "
            f"hint_penalty={hint_penalty:.3f}, auto_penalty={auto_penalty:.3f}{suffix}"
        )

        self._done = True
        return self._make_obs(
            transcript="",
            feedback=full_feedback,
            reward=final_reward,
            done=True,
            extra_meta={
                "final_reward": final_reward,
                "base_reward": round(base_reward, 4),
                "efficiency_bonus": round(efficiency_bonus, 4),
                "hint_penalty": round(hint_penalty, 4),
                "auto_finalize_penalty": round(auto_penalty, 4),
                "voluntary_finalize": voluntary,
                "steps_used": steps_used,
                "items_submitted": len(self._submitted),
                "items_expected": len(expected),
            },
        )

    @property
    def state(self) -> State:
        return self._state

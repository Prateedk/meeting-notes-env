"""Integration tests for multi-step MeetingNotesEnvironment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import MeetingNotesAction, MeetingNotesObservation
from server.meeting_notes_env_environment import MeetingNotesEnvironment, REWARD_MIN, REWARD_MAX, MAX_STEPS


class TestReset:
    def test_reset_returns_observation(self):
        env = MeetingNotesEnvironment()
        obs = env.reset(task="easy_1")
        assert isinstance(obs, MeetingNotesObservation)
        assert obs.transcript != ""
        assert obs.task_id == "easy_1"
        assert obs.done is False
        assert obs.num_expected > 0

    def test_reset_with_difficulty(self):
        env = MeetingNotesEnvironment()
        obs = env.reset(task="easy")
        assert obs.task_id.startswith("easy_")

    def test_reset_random(self):
        env = MeetingNotesEnvironment()
        obs = env.reset()
        assert obs.task_id != ""
        assert obs.transcript != ""

    def test_reset_provides_valid_actions(self):
        env = MeetingNotesEnvironment()
        obs = env.reset(task="easy_1")
        assert "submit_item" in obs.valid_actions
        assert "finalize" in obs.valid_actions
        assert "revise_item" not in obs.valid_actions

    def test_reset_clears_state(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        env.step(MeetingNotesAction(action_type="submit_item", who="Bob", what="fix CI", deadline="Wed"))
        obs = env.reset(task="easy_2")
        assert len(obs.submitted_items) == 0
        assert obs.hints_used == 0


class TestSubmitItem:
    def test_submit_returns_score(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        obs = env.step(MeetingNotesAction(
            action_type="submit_item",
            who="Bob",
            what="fix the CI pipeline",
            deadline="Wednesday",
        ))
        assert obs.done is False
        assert len(obs.submitted_items) == 1
        assert obs.submitted_items[0]["score"] > 0.5

    def test_submit_bad_item(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        obs = env.step(MeetingNotesAction(
            action_type="submit_item",
            who="Nobody",
            what="irrelevant stuff",
            deadline="never",
        ))
        assert obs.submitted_items[0]["score"] < 0.3

    def test_revise_unlocks_after_submit(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        obs = env.step(MeetingNotesAction(
            action_type="submit_item", who="Bob", what="fix CI", deadline="Wed",
        ))
        assert "revise_item" in obs.valid_actions


class TestReviseItem:
    def test_revise_improves_score(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        env.step(MeetingNotesAction(
            action_type="submit_item",
            who="Bob",
            what="something vague",
            deadline="someday",
        ))
        obs = env.step(MeetingNotesAction(
            action_type="revise_item",
            item_index=0,
            who="Bob",
            what="fix the CI pipeline",
            deadline="Wednesday",
        ))
        assert obs.submitted_items[0]["score"] > 0.5

    def test_revise_invalid_index(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        obs = env.step(MeetingNotesAction(
            action_type="revise_item", item_index=99,
        ))
        assert "Invalid" in obs.feedback


class TestRequestContext:
    def test_hint_provides_feedback(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        obs = env.step(MeetingNotesAction(action_type="request_context"))
        assert "Hint" in obs.feedback
        assert obs.hints_used == 1

    def test_max_hints(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        for _ in range(3):
            env.step(MeetingNotesAction(action_type="request_context"))
        obs = env.step(MeetingNotesAction(action_type="request_context"))
        assert "No hints remaining" in obs.feedback


class TestFinalize:
    def test_finalize_ends_episode(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        env.step(MeetingNotesAction(
            action_type="submit_item",
            who="Bob", what="fix the CI pipeline", deadline="Wednesday",
        ))
        obs = env.step(MeetingNotesAction(action_type="finalize"))
        assert obs.done is True
        assert REWARD_MIN <= obs.reward <= REWARD_MAX

    def test_finalize_empty_submission(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        obs = env.step(MeetingNotesAction(action_type="finalize"))
        assert obs.done is True
        assert obs.reward == REWARD_MIN

    def test_reward_always_in_open_interval(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        env.step(MeetingNotesAction(
            action_type="submit_item",
            who="Bob", what="fix the CI pipeline", deadline="Wednesday",
        ))
        obs = env.step(MeetingNotesAction(action_type="finalize"))
        assert obs.reward > 0.0
        assert obs.reward < 1.0


class TestAutoFinalize:
    def test_auto_finalize_at_max_steps(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        for i in range(MAX_STEPS):
            obs = env.step(MeetingNotesAction(
                action_type="submit_item",
                who=f"Person{i}", what=f"task {i}", deadline="someday",
            ))
            if obs.done:
                break
        assert obs.done is True
        assert "auto-finalized" in obs.feedback


class TestEpisodeAlreadyDone:
    def test_step_after_done(self):
        env = MeetingNotesEnvironment()
        env.reset(task="easy_1")
        env.step(MeetingNotesAction(action_type="finalize"))
        obs = env.step(MeetingNotesAction(action_type="submit_item", who="X", what="Y", deadline="Z"))
        assert obs.done is True
        assert "already done" in obs.feedback.lower()

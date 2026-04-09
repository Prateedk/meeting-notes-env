"""Tests for Pydantic data models."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import MeetingNotesAction, MeetingNotesObservation


class TestMeetingNotesAction:
    def test_submit_item(self):
        action = MeetingNotesAction(
            action_type="submit_item",
            who="Alice",
            what="write report",
            deadline="Friday",
        )
        assert action.action_type == "submit_item"
        assert action.who == "Alice"

    def test_revise_item(self):
        action = MeetingNotesAction(
            action_type="revise_item",
            item_index=0,
            who="Bob",
            what="fix CI",
            deadline="Wednesday",
        )
        assert action.item_index == 0

    def test_finalize(self):
        action = MeetingNotesAction(action_type="finalize")
        assert action.who is None
        assert action.item_index is None

    def test_request_context(self):
        action = MeetingNotesAction(action_type="request_context")
        assert action.action_type == "request_context"

    def test_action_type_required(self):
        with pytest.raises(Exception):
            MeetingNotesAction()


class TestMeetingNotesObservation:
    def test_defaults(self):
        obs = MeetingNotesObservation()
        assert obs.transcript == ""
        assert obs.submitted_items == []
        assert obs.steps_remaining == 0
        assert obs.hints_used == 0
        assert obs.valid_actions == []
        assert obs.done is False

    def test_with_values(self):
        obs = MeetingNotesObservation(
            transcript="Hello",
            task_id="easy_1",
            num_expected=3,
            submitted_items=[{"who": "A", "what": "B", "deadline": "C", "score": 0.5}],
            steps_remaining=10,
            hints_used=1,
            valid_actions=["submit_item", "finalize"],
            done=False,
            reward=0.5,
        )
        assert obs.num_expected == 3
        assert len(obs.submitted_items) == 1
        assert obs.steps_remaining == 10

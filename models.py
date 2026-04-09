"""Data models for the Meeting Notes environment.

The agent receives a meeting transcript and must extract structured action items
through a multi-step interactive process: submit items one at a time, revise
based on feedback, optionally request context hints, and finalize when done.
"""

from typing import Any, Dict, List, Optional

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class MeetingNotesAction(Action):
    """Typed action for multi-step meeting notes extraction.

    Supported action_type values:
      - submit_item:     Submit a single action item (who, what, deadline).
      - revise_item:     Revise a previously submitted item by index.
      - request_context: Ask the environment for a hint (incurs reward penalty).
      - finalize:        End the episode and receive the final aggregated reward.
    """

    action_type: str = Field(
        ...,
        description="One of: submit_item, revise_item, finalize, request_context",
    )
    item_index: Optional[int] = Field(
        default=None,
        description="Index of a previously submitted item to revise (revise_item only)",
    )
    who: Optional[str] = Field(
        default=None,
        description="Person responsible for the action item",
    )
    what: Optional[str] = Field(
        default=None,
        description="Concise description of the task",
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Deadline as mentioned in the transcript",
    )


class MeetingNotesObservation(Observation):
    """Rich observation for multi-step interaction."""

    transcript: str = Field(
        default="",
        description="Meeting transcript text (provided on reset, omitted on subsequent steps)",
    )
    task_id: str = Field(default="", description="Current task identifier")
    task_description: str = Field(default="", description="Human-readable task description")
    feedback: str = Field(default="", description="Per-step grading feedback")
    num_expected: int = Field(default=0, description="Number of expected action items")
    submitted_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Items submitted so far, each with fields and per-item score",
    )
    steps_remaining: int = Field(default=0, description="Steps left before auto-finalize")
    hints_used: int = Field(default=0, description="Number of context hints consumed")
    valid_actions: List[str] = Field(
        default_factory=list,
        description="Action types currently available to the agent",
    )

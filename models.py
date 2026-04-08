"""Data models for the Meeting Notes environment.

The agent receives a meeting transcript and must extract structured action items.
"""

from typing import List, Optional

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class MeetingNotesAction(Action):
    """Agent submits extracted action items as a JSON string."""

    message: str = Field(
        ...,
        description=(
            "JSON string: a list of action items, each with keys "
            '"who", "what", "deadline". Example: '
            '[{"who":"Alice","what":"send report","deadline":"Friday"}]'
        ),
    )


class MeetingNotesObservation(Observation):
    """Observation returned to the agent after reset or step."""

    transcript: str = Field(default="", description="Meeting transcript text")
    task_id: str = Field(default="", description="Current task identifier")
    task_description: str = Field(default="", description="Human-readable task description")
    feedback: str = Field(default="", description="Grading feedback after a step")
    num_expected: int = Field(default=0, description="Number of expected action items")

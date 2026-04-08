"""Meeting Notes Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import MeetingNotesAction, MeetingNotesObservation
except ImportError:
    from models import MeetingNotesAction, MeetingNotesObservation


class MeetingNotesEnv(
    EnvClient[MeetingNotesAction, MeetingNotesObservation, State]
):
    """Client for the Meeting Notes environment."""

    def _step_payload(self, action: MeetingNotesAction) -> Dict:
        return {"message": action.message}

    def _parse_result(self, payload: Dict) -> StepResult[MeetingNotesObservation]:
        obs_data = payload.get("observation", {})
        observation = MeetingNotesObservation(
            transcript=obs_data.get("transcript", ""),
            task_id=obs_data.get("task_id", ""),
            task_description=obs_data.get("task_description", ""),
            feedback=obs_data.get("feedback", ""),
            num_expected=obs_data.get("num_expected", 0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )

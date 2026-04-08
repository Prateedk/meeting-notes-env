"""FastAPI application for the Meeting Notes Environment."""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core"
    ) from e

try:
    from ..models import MeetingNotesAction, MeetingNotesObservation
    from .meeting_notes_env_environment import MeetingNotesEnvironment
except (ImportError, SystemError):
    from models import MeetingNotesAction, MeetingNotesObservation
    from server.meeting_notes_env_environment import MeetingNotesEnvironment

app = create_app(
    MeetingNotesEnvironment,
    MeetingNotesAction,
    MeetingNotesObservation,
    env_name="meeting_notes_env",
    max_concurrent_envs=4,
)


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

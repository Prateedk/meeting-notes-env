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

# Discourage any proxy/CDN from serving stale API responses on the canonical *.hf.space host.
from starlette.requests import Request


@app.middleware("http")
async def _no_store_api_responses(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/reset", "/step", "/state", "/schema", "/metadata", "/health")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
